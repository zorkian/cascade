import logging
import time

from redis_manager import healthy_root_redis
from config import get_self_fqdn


def health_check_branch(local_rd, info):
    root_rd, root_ip = healthy_root_redis(local_rd)
    if not root_rd:
        logging.error('Failed to connect to root instance on %s!' % root_ip)
        return
    root_rd.sadd('prodstate:branches', get_self_fqdn())

    # Since we know we're up to date, check if we're using a random branch and, if so, let's try
    # to promote ourselves up to the root.
    if info['master_host'] != root_ip:
        logging.info('I am a branch and not connected to the root, reparenting!')
        local_rd.slaveof(host=root_ip, port=2578)
        time.sleep(3)
        return
