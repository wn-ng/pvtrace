
from __future__ import annotations
from typing import Optional, Sequence
from anytree import NodeMixin, Walker, PostOrderIter, LevelOrderIter
from pvtrace.light.ray import Ray
from pvtrace.light.light import Light
from pvtrace.trace.context import Context, Kind
import numpy as np
import logging
logger = logging.getLogger(__name__)


class Scene(object):
    """ A scene graph of nodes.
    """

    def __init__(self, root=None):
        super(Scene, self).__init__()
        self.root = root
    
    def finalise_nodes(self):
        """ Update bounding boxes of node hierarchy in prepration for tracing.
        """
        root = self.root
        if root is not None:

            # Clear any existing bounding boxes
            for node in PostOrderIter(root):
                node.bounding_box = None

            # More efficiency to calcualte from leaves to root because because
            # the parent's bounding box calculation requires the size of the 
            # child's bounding box.
            leaves = self.root.leaves
            for leaf_node in leaves:
                node = leaf_node
                while True:
                    _ = node.bounding_box  # will force recalculation
                    node = node.parent
                    if node is None:
                        break

    @property
    def light_nodes(self) -> Sequence[Light]:
        """ Returns all lights in the scene.
        """
        root = self.root
        found_nodes = []
        for node in LevelOrderIter(root):
            if isinstance(node.light, Light):
                found_nodes.append(node)
        return found_nodes

    def intersections(self, ray_origin, ray_direction) -> Sequence[Tuple[Node, Tuple]]:
        """ Intersections with ray and scene. Ray is defined in the root node's
        coordinate system.
        """
        # to-do: Prune which nodes are queried for intersections by first
        # intersecting the ray with bounding boxes of the node.
        root = self.root
        if root is None:
            return tuple()

        def distance_sort_key(i):
            v = np.array(i.point) - np.array(ray_origin)
            d = np.linalg.norm(v)
            return d
        
        all_intersections = self.root.intersections(ray_origin, ray_direction)
        # Convert intersection point to root frame/node.
        all_intersections = map(lambda x: x.to(root), all_intersections)
        # Sort by distance to ray
        all_intersections = tuple(sorted(all_intersections, key=distance_sort_key))
        return all_intersections
    
