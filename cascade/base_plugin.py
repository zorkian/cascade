class CascadePlugin(object):
    '''
    Implements the base plugin class. Please inherit from this and override the methods that you
    want to plug in to.
    '''

    def filter_sources(self, sources):
        '''
        This method is called when Cascade has calculated a list of sources. The sources parameter
        is a list of unique hostnames that will be tried, top to bottom, until a valid source is
        found.

        This function should return a list of hostnames. You can add or remove hosts at will or
        even completely discard the input sources. The returned hostnames should be resolvable by
        the local machine.

        Default implementation: return sources unchanged.
        '''
        return sources
