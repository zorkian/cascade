import redis
import subprocess
import time


REDIS_CONNS = {}
RC_LAST_CLEAR = time.time()


def redis_conn(host, port, use_cache=False):
    # Poor man's cache clearing every minute.
    global RC_LAST_CLEAR, REDIS_CONNS
    if time.time() > RC_LAST_CLEAR + 60:
        REDIS_CONNS = {}
        RC_LAST_CLEAR = time.time()

    if use_cache:
        if (host, port) in REDIS_CONNS:
            rd = REDIS_CONNS[(host, port)]
            try:
                if rd.ping():
                    return rd
            except redis.exceptions.ConnectionError:
                pass
    else:
        if (host, port) in REDIS_CONNS:
            del REDIS_CONNS[(host, port)]

    # Fall through to reconnecting.
    rd = redis.StrictRedis(host=host, port=port, socket_timeout=1)
    try:
        if rd.ping():
            REDIS_CONNS[(host, port)] = rd
            return rd
    except redis.exceptions.ConnectionError:
        pass
    return None


def run_command(args):
    try:
        return subprocess.check_output(args)
    except subprocess.CalledProcessError:
        return ''
