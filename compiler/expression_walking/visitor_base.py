class AstVisitor:
    def _visit(self, node, *args, **kwargs):

        visit_methods = [method for method in self.__class__.__dict__.values() if hasattr(method, '_is_visit_method')]
        default_visit_method = next((method for method in visit_methods if hasattr(method, '_is_default_visit_method')), None)

        node_type = node.__class__.__name__.lower()

        visit_method = default_visit_method

        for method in visit_methods:
            if node_type in method._handled_node_types:
                visit_method = method
                break
        
        if visit_method is None:
            raise Exception(f"No visit method found for node type {node_type} and no default visit method defined")

        return visit_method(self, node, *args, **kwargs)
    

    @staticmethod
    def default_visit():
        def decorator(func):
            func._is_default_visit_method = True
            func._handled_node_types = []
            func._is_visit_method = True
            return func
        return decorator
    
    @staticmethod
    def accept(*nodes):
        def decorator(func):
            func._handled_node_types = [n.lower() for n in nodes]
            func._is_visit_method = True
            return func
        return decorator