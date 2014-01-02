import tempfile
import atexit
import socket
import logging
import time
import os

from config import get_self_fqdn, get_role, get_redis_binary, get_redis_configs
from utils import redis_conn, run_command
from topology import get_best_source


def healthy_root_redis(local_rd):
    if not local_rd:
        return None
    root_host = local_rd.get('cascade:root')
    try:
        root_ip = socket.gethostbyname(root_host)
    except socket.gaierror:
        logging.error('Failed to resolve root node: %s.' % root_host)
        return None
    if root_host == get_self_fqdn():
        return (local_rd, root_ip)  # hack.
    return (redis_conn(host=root_ip, port=2578), root_ip)


def launch_new_redis():
    # root nodes launch without a source.
    if get_role() == 'root':
        logging.info('Launching new root Redis.')
        config_file = write_redis_config_file(None)
    else:
        branch_host, branch_ip = get_best_source(None, prefer_root=(get_role() == 'branch'))
        if not branch_host:
            logging.error('Unable to launch local Redis, no healthy branches found!')
            time.sleep(5)
            return
        logging.info('Launching local Redis off of branch: %s(%s).' % (branch_host, branch_ip))
        config_file = write_redis_config_file(branch_ip)
    if not config_file:
        logging.error('Failed to write configuration file!')
        time.sleep(5)
        return
    logging.info('Starting Redis from config: %s' % config_file)
    run_command([get_redis_binary(), config_file])
    time.sleep(5)


def healthy_local_redis(tryct=0):
    if tryct > 0:
        logging.info('Failure #%d getting healthy local redis, retrying after a pause...' % tryct)
        time.sleep(min(tryct, 10))

    local_rd = redis_conn(host='localhost', port=2578)
    if local_rd:
        return local_rd

    logging.info('Local redis-server not found or not responding.')
    pid_of = run_command(['/usr/bin/pgrep', '-f', 'redis-server \*:2578']).rstrip()
    if not pid_of:
        # It doesn't exist, so let's try to spawn one for our current role.
        launch_new_redis()
    elif tryct >= 3:
        # If it's been more than 10 tries, we call shenanigans and shoot it. SIGKILL is fine, since
        # we have the AOF. We might lose whatever it was doing at the very end, but we accept that.
        logging.warning('Killing existing redis-server...')
        run_command(['/usr/bin/pkill', '-9', '-f', 'redis-server \*:2578'])

    # Final logic is to just retry with an increased try count.
    return healthy_local_redis(tryct=tryct + 1)


def write_redis_config_file(master_ip):
    '''
    Writes out a configuration file for our role to a temporary file that we try to unlink when
    we exit.
    '''
    config, role = {}, get_role()

    cfgs = get_redis_configs()
    if 'common' in cfgs:
        config = cfgs['common']
    if role in cfgs:
        config.update(cfgs[role])
    config['port'] = 2578
    config['daemonize'] = 'yes'
    if role != 'root':
        config['slaveof'] = master_ip + ' 2578'

    fd, tmpfile = tempfile.mkstemp(prefix='cascade-%s-' % role)
    logging.debug('Writing config to: %s' % tmpfile)

    def unlink_tmpfile():  # Cleanup.
        os.unlink(tmpfile)
    atexit.register(unlink_tmpfile)

    def redis_val(inp):
        if type(inp) == bool:
            return 'yes' if inp else 'no'
        return str(inp)

    with os.fdopen(fd, 'w') as tmp:
        tmp.write('\n'.join(['%s %s' % (key, redis_val(config[key])) for key in config]))
    return tmpfile
