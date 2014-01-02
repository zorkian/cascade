import logging
import random
import time

from config import get_self_fqdn
from redis_manager import healthy_root_redis
from topology import get_best_source


def health_check_leaf(local_rd, info):
    # There is a chance that prodstate.py has restarted and last time we self-selected to be
    # a branch, but this time we're not. If we're in the list of branches, then we should remove
    # ourselves.
    local_branches = local_rd.smembers('prodstate:branches')
    root_rd = None
    if get_self_fqdn() in local_branches:
        root_rd, _ = healthy_root_redis(local_rd)
        if root_rd:
            logging.warning('Leaf node removing myself from list of branches.')
            root_rd.srem('prodstate:branches', get_self_fqdn())

    # If we have slaves, update the root so it can count our clients.
    if info.get('connected_slaves', 0) > 0:
        if not root_rd:
            root_rd, _ = healthy_root_redis(local_rd)
        if root_rd:
            root_rd.sadd('prodstate:draining-branches', get_self_fqdn())

    # Following from the above case, if our branch is no longer in the branches list, we could
    # nicely choose to move off of them. We don't, however, because then we can cause rebalance
    # storms when prodstate gets rolled globally (and self-selected branches all move).
    #
    # Instead, let the periodic rebalance take care of the problem, since it won't pick leaf nodes
    # next time.

    # Periodic Rebalance:
    #
    # With some percentage chance (this fires every 1 second) we want to pick a new branch and
    # move to it. This provides dumb but probably effective rebalancing for the tree.
    if random.random() <= 0.0017:  # 1 in 600 (10 minute average)
        leaf_rebalance(local_rd, info)


def leaf_rebalance(local_rd, info):
    branch_host, branch_ip = get_best_source(local_rd)
    if not branch_host:
        logging.error('Periodic rebalance found no available, healthy branches!')
        return
    if branch_ip == info['master_host']:
        # If we manage to select our own branch again, let's just pretend this didn't happen.
        # This rebalance was not meant to be.
        return
    logging.info('Periodic rebalance, picked new branch: %s(%s).' % (branch_host, branch_ip))
    local_rd.slaveof(host=branch_ip, port=2578)
    time.sleep(3)  # Give a little extra time to start the sync.
