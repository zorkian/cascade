import time
import logging

from utils import redis_conn
from config import get_self_fqdn, get_self_ip


BRANCH_SLAVE_COUNTS = {}


def health_check_root(local_rd, info):
    # The important staleness ping. Lets everybody know what's what.
    local_rd.set('time', time.time())

    # We are root and we are not a branch. Make sure state is correct.
    if local_rd.get('cascade:root') != get_self_fqdn():
        local_rd.set('cascade:root', get_self_fqdn())
    local_rd.srem('cascade:branches', get_self_fqdn())

    # General purpose error notices...
    if info.get('connected_slaves', 0) == 0:
        logging.error('I am a root node, but have no branches connected!')
    if info['role'] != 'master':
        logging.error('I am a root node, but redis-server.role is: %s!' % info['role'])

    # Root nodes also healthceck down to branches so that we can make sure that our list of
    # valid branches stays relatively up to date.
    # TODO: This needs to be smarter and handle branches that have gone south on latency? Or maybe
    # some other cases? Also, if we start hitting connect timeouts here, this can slow down the
    # whole loop. This also causes us to connect to every branch every second, which might chew
    # up ephemeral ports if we get lots of branches. Persistent connections? Threads to watch
    # each branch?
    for key in ('cascade:branches', 'cascade:draining-branches'):
        for branch_host in local_rd.smembers(key):
            branch_rd = redis_conn(host=branch_host, port=2578, use_cache=True)
            if not branch_rd:
                logging.warning('Branch %s has gone MIA, removing from list.' % branch_host)
                local_rd.srem(key, branch_host)
                continue
            branch_info = branch_rd.info('replication')
            # Regular branches are auto-pruned from the list if they go off-root.
            if key == 'cascade:branches' and branch_info['master_host'] != get_self_ip():
                logging.info('Supposed branch %s is not connected to us, pruning.' % branch_host)
                local_rd.srem(key, branch_host)
            # Draining branches get pruned at 0.
            elif key == 'cascade:draining-branches' and branch_info['connected_slaves'] == 0:
                logging.info('Drained branch %s finished, removing.' % branch_host)
                local_rd.srem(key, branch_host)
            BRANCH_SLAVE_COUNTS[branch_host] = branch_info['connected_slaves']
