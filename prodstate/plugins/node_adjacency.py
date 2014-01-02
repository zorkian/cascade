#!/usr/bin/env python
#
# Implements adjacency logic for sorting a list of possible branches into a priority order.
#

from base_plugin import ProdstatePlugin

class NodeAdjacency(ProdstatePlugin):
    def run(self, *args, **kwargs):
        print args, kwargs
