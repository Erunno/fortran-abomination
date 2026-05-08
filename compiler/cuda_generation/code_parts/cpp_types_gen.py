from tkinter import Variable

from compiler.typing import TerminalType, Type


class CppTyper:
    TYPE_TO_CPP_TYPE_STR = {
        "integer": "int",
    }

    def get_cpp_type_str(self, variable: Type) -> str:
        base_type = variable.get_underlying_type()
        result = self.TYPE_TO_CPP_TYPE_STR[base_type.name.lower()]
        
        if variable.is_array():
            result += "*"
    
        return result
    
        
    def get_size_t(self) -> str:
        return "size_t"
