from compiler.context import Variable
from compiler.typing import TerminalType, Type


class CppTyper:
    TYPE_TO_CPP_TYPE_STR = {
        "integer": "int",
        "real(kind = knd)": "double"
    }

    TYPE_TO_FORTRAN_TYPE_STR = {
        "integer": "integer",
        "real(kind = knd)": "real(kind = knd)"
    }

    def get_cpp_type_str(self, variable: Type) -> str:
        base_type = variable.get_underlying_type()
        result = self.TYPE_TO_CPP_TYPE_STR[base_type.name.lower()]
        
        if variable.is_array():
            result += "*"
    
        return result
    
    def size_of(self, type: Type) -> str:
        type_str = self.TYPE_TO_CPP_TYPE_STR[type.name.lower()]  
        return f'sizeof({type_str})'

    def get_size_t(self) -> str:
        return "size_t"

class FortranTyper:
    TYPE_TO_FORTRAN_TYPE_STR = {
        "integer": "integer(c_int)",
        "real(kind = knd)": "real(kind = knd)"
    }

    def get_fortran_type_for_cpp_bind(self, variable: Type) -> str:
        base_type = variable.get_underlying_type().name.lower()

        if variable.is_array():
            return f"{base_type}, dimension(*)"

        return self.TYPE_TO_FORTRAN_TYPE_STR[base_type] + ", value, intent(in)"
    
    def get_size_t_cpp_bind(self) -> str:
        return "integer(c_size_t), value, intent(in)"