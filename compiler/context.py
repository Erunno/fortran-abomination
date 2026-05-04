from compiler.fparser_tree_abstraction import FparserTree
from compiler.typing import ArrayType, TerminalType

class Variable:
    def __init__(self, name, type, attributes=[]):
        self.name = name
        self.type = type
        self.attributes = attributes

    def is_input(self):
        return "intent(in)" in self.attributes

    def is_output(self):
        return "intent(out)" in self.attributes
    
    def __string__(self):
        return f"Variable(name={self.name}, type={self.type}, attributes={self.attributes})"
    
    @staticmethod
    def from_(intrinsic_type_ast, variable_ast, attributes):
        base_type_name = str(intrinsic_type_ast[0]).lower()
        base_type = TerminalType(base_type_name)

        variable_ast = FparserTree(variable_ast)
        variable_name = str(variable_ast.get_all_nodes_in_children_of_type("Name")[0])

        def is_array_dim_spec(node):
            return node.__class__.__name__.lower().endswith("_Shape_Spec".lower())

        shape_list = variable_ast.get_nodes(is_array_dim_spec)

        final_type = base_type

        for shape in shape_list:
            final_type = ArrayType(final_type, shape)


        return Variable(variable_name, final_type, attributes)

class Context:
    def _load_specifications(self, ast):
        tree = FparserTree(ast)
        specification_statements = tree.get_all_nodes_of_type("Type_Declaration_Stmt")

        all_variables = []
        for specification in specification_statements:
            variables = self._load_variables_from_specification(specification)
            all_variables.extend(variables)

        return all_variables
    
    def _load_variables_from_specification(self, specification_ast):
        tree = FparserTree(specification_ast)

        intrinsic_type = tree.get_all_nodes_of_type("Intrinsic_Type_Spec")
        variable_list = tree.get_all_nodes_of_type("Entity_Decl")
        attributes = [str(attr) for attr in tree.get_all_nodes_of_type("Attr_Spec")]

        variables = []
        for var in variable_list:
            variables.append(Variable.from_(intrinsic_type, var, attributes))

        return variables

class LocalContext(Context):
    def __init__(self, specifications_ast):
        self.specifications_ast = FparserTree(specifications_ast)
        self.variables = self._load_specifications(self.specifications_ast)


    def get_variable_by_name(self, name) -> Variable:
        for variable in self.variables:
            if variable.name == name:
                return variable
        
        raise Exception(f"Variable with name {name} not found in context")