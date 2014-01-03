from cascade.base_plugin import CascadePlugin


class NodeAdjacency(CascadePlugin):
    '''
    Demo plugin. Doesn't actually do anything, but shows how to create a filter_sources plugin.
    '''
    def filter_sources(self, sources):
        return sources
