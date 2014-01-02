import logging
import random
import socket
import time

from config import get_bootstrap_nodes, get_self_fqdn
from utils import redis_conn


def get_best_source(local_rd, prefer_root=False):
    '''
    Tries to identify the best source to pull data from. This basically creates a list of all
    branches, the root, both local fallbacks and possibly stale data from Redis. Then we try to
    find a source that is up to date.

    This also calls the plugin infrastructure which helps us identify and prioritize nodes to
    use as sources.
    '''
    # These are the fallbacks that should probably exist.
    roots = []
    nodes = get_bootstrap_nodes()

    # Also, if we have data in our local Redis (which might be stale) then let's include that,
    # it doesn't hurt to have it.
    if local_rd:
        root = local_rd.get('prodstate:root')
        if root:
            roots.append(root)
        branches = local_rd.smembers('prodstate:branches')
        if branches:
            nodes.extend(branches)

    # Remove all roots from nodes to prevent using them overly.
    for root in roots:
        if root in nodes:
            nodes.remove(root)

    # Remove duplicates (branches shouldn't get "extra" work because they're also fallbacks), then
    # shuffle so we get random ones.
    nodes = list(set(nodes))
    random.shuffle(nodes)

    # TODO: call plugin here.

    # Now put roots at the front or back, depending. This ignores adjacency.
    if prefer_root:
        nodes = roots + nodes
    else:
        nodes.extend(roots)

    # TODO: Maybe we should weight by how many leaf nodes a given branch has right now? This
    # might not be necessary...

    # Now try nodes until we find one that meets our criteria.
    for try_host in nodes:
        if try_host == get_self_fqdn():
            continue
        try:
            try_ip = socket.gethostbyname(try_host)
        except socket.gaierror:
            logging.error('Possible source: %s is unresolvable.' % try_host)
            continue
        conn = redis_conn(host=try_ip, port=2578)
        if not conn:
            logging.info('Possible source: %s is down/unavailable.' % try_host)
            continue
        l_time = conn.get('time')
        if not l_time:
            logging.info('Possible source: %s has no time/is blank.' % try_host)
            continue
        delta = time.time() - float(l_time)
        if delta > 20:
            logging.info('Possible source: %s is %0.2f seconds behind.' % (try_host, delta))
            continue
        logging.info('Possible source: %s is %0.2f seconds behind - ACCEPTED.' % (try_host, delta))
        return (try_host, try_ip)

    # TODO: what if everybody is behind? no healthy?
    logging.error('Found no healthy sources.')
    return (None, None)
