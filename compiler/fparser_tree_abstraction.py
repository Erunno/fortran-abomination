class FparserTree:
    def __init__(self, tree):
        if tree.__class__ == FparserTree:
            tree = tree.tree

        self.tree = tree

    def get_all_nodes_of_type(self, node_type: str) -> list:
        def add_if_node_is_of_type(node, acc):
            if node_type.lower() == node.__class__.__name__.lower():
                acc.append(node)
            return acc
        
        nodes = self.reduce_nodes(add_if_node_is_of_type, [])
        
        return nodes
    
    def get_all_nodes_in_children_of_type(self, node_type: str) -> list:
        if not hasattr(self.tree, "children"):
            return []
        
        return [child for child in self.tree.children if child.__class__.__name__.lower() == node_type.lower()]
    
    def reduce_nodes(self, reduction_function, accumulator_init_value) -> list:
        return self._reduce_impl(self.tree, reduction_function, accumulator_init_value)

    def _reduce_impl(self, node, reduction_function, acc):
        acc = reduction_function(node, acc)

        if hasattr(node, "children"):
            for child in node.children:
                acc = self._reduce_impl(child, reduction_function, acc)

        return acc
