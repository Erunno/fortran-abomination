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
        attributes = [str(attr).lower() for attr in tree.get_all_nodes_of_type("Attr_Spec_List")]

        variables = []
        for var in variable_list:
            variables.append(Variable.from_(intrinsic_type, var, attributes))

        return variables
    
    def get_variable_by_name(self, name) -> Variable:
        raise NotImplementedError("This method should be implemented by subclasses of Context")

    def is_call_context(self):
        return False
    
class LocalContext(Context):
    def __init__(self, specifications_ast, declaration_ast):
        self.specifications_ast = FparserTree(specifications_ast)
        self.declaration_ast = FparserTree(declaration_ast)
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
    
    def get_call_arg_names(self):
        arg_list = self.declaration_ast.get_all_nodes_of_type("Dummy_Arg_List")
        arg_list = FparserTree(arg_list[0]).children()
        return [str(arg) for arg in arg_list]

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


class ContextWithArguments(Context):
    def __init__(self,
                 function_local_context: LocalContext,
                 caller_context: Context,
                 call_arguments: list[Variable]):
        self.function_local_context = function_local_context
        self.call_arguments = call_arguments
        self.caller_context = caller_context

        function_arg_list = function_local_context.get_call_arg_names()
        if len(function_arg_list) != len(call_arguments):
            raise Exception(f"Number of call arguments ({len(call_arguments)}) does not match number of function arguments ({len(function_arg_list)})")
        
        self.translation_dict = {arg_name: arg for arg_name, arg in zip(function_arg_list, call_arguments)}

    def get_variable_by_name(self, name) -> Variable:
        if name in self.translation_dict:
            return self.translation_dict[name]
        return self.function_local_context.get_variable_by_name(name)
    
    def is_call_context(self):
        return True

    def __str__(self):
        function_local_context_str = str(self.function_local_context)
        tabbed_function_local_context_str = "\t" + function_local_context_str.replace("\n", "\n\t")

        caller_context_str = str(self.caller_context)
        tabbed_caller_context_str = "\t" + caller_context_str.replace("\n", "\n\t")

        arguments_str = "\n".join([str(arg) for arg in self.call_arguments])
        tabbed_arguments_str = "\t" + arguments_str.replace("\n", "\n\t")

        return f"ContextWithArguments(call_arguments=\n{tabbed_arguments_str}, \n\tfunction_local_context={tabbed_function_local_context_str}, \ncaller_context=\n{tabbed_caller_context_str}\n)"