from compiler.fparser_tree_abstraction import FparserTree, LoopStatement
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
    
    def is_input_output(self):
        return "intent(inout)" in self.attributes
    
    def name(self):
        return self.name

    def __str__(self):
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

class IterationVariable:
    def __init__(self, original_variable: Variable, loop_statement: LoopStatement):
        self.original_variable = original_variable
        self.loop_statement = loop_statement

    def name(self):
        return self.original_variable.name

    def is_named(self, name):
        return self.name() == name
    
    def __str__(self):
        return f"IterationVariable(name={self.name()}, original_variable={self.original_variable})"

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
    
    def get_variable_by_name(self, name) -> Variable:
        raise NotImplementedError("This method should be implemented by subclasses of Context")

class LocalContext(Context):
    def __init__(self, specifications_ast):
        self.specifications_ast = FparserTree(specifications_ast)
        self.variables = self._load_specifications(self.specifications_ast)


    def get_variable_by_name(self, name) -> Variable:
        for variable in self.variables:
            if variable.name == name:
                return variable
        
        raise Exception(f"Variable with name {name} not found in context")
    

    def __str__(self):
        variables_str = "\n".join([str(var) for var in self.variables])
        tabbed_variables_str = "\t" + variables_str.replace("\n", "\n\t")
        return f"LocalContext(variables=\n{tabbed_variables_str}\n)"

class DoLoopContext(Context):
    def __init__(self, do_statement: LoopStatement, parent_context: Context):
        self.parent_context = parent_context

        iter_var_name = do_statement.iteration_variable_name()
        self.iteration_variable = IterationVariable(
            self.parent_context.get_variable_by_name(iter_var_name),
            do_statement)

    def get_variable_by_name(self, name) -> Variable | IterationVariable:
        if self.iteration_variable.is_named(name):
            return self.iteration_variable
        
        return self.parent_context.get_variable_by_name(name)

    def __str__(self):
        parent_context_str = str(self.parent_context)
        tabbed_parent_context_str = "\t" + parent_context_str.replace("\n", "\n\t")
        return f"DoLoopContext(iteration_variable={self.iteration_variable}, parent_context=\n{tabbed_parent_context_str}\n)"
