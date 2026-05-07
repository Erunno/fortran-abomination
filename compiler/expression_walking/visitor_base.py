from compiler.kernel_abstraction import Kernel

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
    

    def _default_visit(self, node, *args, **kwargs):
        visit_methods = [method for method in self.__class__.__dict__.values() if hasattr(method, '_is_visit_method')]
        default_visit_method = next((method for method in visit_methods if hasattr(method, '_is_default_visit_method')), None)

        if default_visit_method is None:
            raise Exception(f"No default visit method defined for {self.__class__.__name__}")

        return default_visit_method(self, node, *args, **kwargs)

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
    
    @staticmethod
    def use_visit_all_children_as_default():

        @AstVisitor.default_visit()
        def visit_all_children(self, node, *args, **kwargs):
            if hasattr(node, "children"):
                return [result for child in node.children for result in self._visit(child, *args, **kwargs)]
            
            if hasattr(node, "__getitem__") and not isinstance(node, str):
                return [result for item in node for result in self._visit(item, *args, **kwargs)]

            return []

        def decorator(cls):
            cls.__visit_all_children_default__ = visit_all_children
            return cls

        return decorator

    
    def _visit_all_code_lines_of(self, kernel: Kernel, post_process=lambda x: x):
        if post_process == 'flatten':
            post_process = lambda x: [item for sublist in x for item in sublist]

        return post_process([self._visit(line, context)
                for line, context in kernel.enum_lines_with_context()
               ])

    def _visit_all_do_stmt_ranges_of(self, kernel: Kernel, post_process=lambda x: x):
        if post_process == 'flatten':
            post_process = lambda x: [item for sublist in x for item in sublist]

        return post_process([self._visit(range, context)
                for range, context in kernel.enum_do_stmt_ranges_with_context()
               ])
