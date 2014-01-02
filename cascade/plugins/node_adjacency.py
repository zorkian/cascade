#!/usr/bin/env python
#
# Implements adjacency logic for sorting a list of possible branches into a priority order.
#

from base_plugin import CascadePlugin

class NodeAdjacency(CascadePlugin):
    def run(self, *args, **kwargs):
        print args, kwargs
