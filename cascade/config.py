import yaml
import os
import socket
import logging

from base_plugin import CascadePlugin
from annex import Annex


CFG = {
    'SELF_FQDN': socket.getfqdn(),
    'SELF_IP': socket.gethostbyname(socket.getfqdn()),
    'ROLE': 'leaf',
    'PLUGINS': [],

    'REDIS_BINARY': '/usr/local/bin/redis-server',
    'REDIS_CONFIGS': {},
    'BOOTSTRAP_NODES': [],
}


def load_config(cfg_file):
    '''
    Given a file, try to load it as a YAML dictionary. If it isn't one, then it's probably not
    a valid cascade configuration.
    '''
    if not os.path.exists(cfg_file):
        return False
    logging.info('Loading configuration file: %s' % cfg_file)
    cfg = yaml.load(open(cfg_file).read())
    if type(cfg) != dict:
        return False

    if 'bootstrapfile' in cfg:
        with open(cfg['bootstrapfile']) as nodes:
            CFG['BOOTSTRAP_NODES'] = nodes.read().split('\n')

    if 'redis' in cfg:
        if 'configs' in cfg['redis']:
            CFG['REDIS_CONFIGS'] = cfg['redis']['configs']
        if 'binary' in cfg['redis']:
            assert os.path.exists(cfg['redis']['binary']), "redis.binary needs to exist"
            CFG['REDIS_BINARY'] = cfg['redis']['binary']

    if 'plugindir' in cfg:
        CFG['PLUGINS'] = Annex(CascadePlugin, [cfg['plugindir']])

    return True


def get_bootstrap_nodes():
    '''
    Returns a list of hosts that are the bootstrap nodes: defaults that may or may not be
    good, but we expect at least a few to be alive so that machines joining the tree can
    have a starting place.
    '''
    return CFG['BOOTSTRAP_NODES']


def get_self_fqdn():
    '''
    We use our own hostname in various places and this is what we put into the tree to tell
    people how to connect to us.
    '''
    return CFG['SELF_FQDN']


def get_role():
    '''
    Returns the current role of this instance.
    '''
    return CFG['ROLE']


def set_role(role):
    '''
    Changes the existing instances role.
    '''
    CFG['ROLE'] = role or CFG['ROLE']


def get_redis_binary():
    '''
    Return location of our Redis binary.
    '''
    return CFG['REDIS_BINARY']


def get_self_ip():
    '''
    Returns our IP address, as resolved by resolving our FQDN.
    '''
    return CFG['SELF_IP']


def get_redis_configs():
    '''
    Return our dict containing Redis configurations.
    '''
    return CFG['REDIS_CONFIGS']


def get_plugins():
    '''
    Return list of plugins that are loaded.
    '''
    return CFG['PLUGINS']
