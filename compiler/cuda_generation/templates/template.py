import re


class Template:
    def __init__(self, file_path):
        self.code_path = file_path
        with open(file_path, 'r') as f:
            self.code = f.read() 

    def replace_placeholder(self, placeholder_name, replacement_code, tabs=0):
        tabs_str = "    " * tabs
        replacement_code = "\n".join([tabs_str + line for line in replacement_code.splitlines()])
        regex_pattern = r"[ \t]*\$" + re.escape(placeholder_name) + r"\$"
        self.code = re.sub(regex_pattern, replacement_code, self.code)

    def write_to_file(self, output_file_path):
        with open(output_file_path, 'w') as f:
            f.write(self.code)

    def print_code(self):
        print(self.code)

    def get_fresh_instance(self) -> "Template":
        return Template(self.code_path)