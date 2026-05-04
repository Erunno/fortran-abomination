from fparser.two.parser import ParserFactory
from fparser.common.readfortran import FortranFileReader

reader = FortranFileReader("C:\\Users\\matya\\source\\repos\\fortran-tool-v2\\fortran-stencils\\gol_module.f90",
                               ignore_comments=False)

f2008_parser = ParserFactory().create(std="f2008")
parse_tree = f2008_parser(reader)

# print(parse_tree.subclasses)

for subclass in parse_tree.subclasses:
    # if parse_tree.subclasses[subclass] != []:
    if "subroutine" in subclass.lower():
        print(f"Subclass: {subclass}")
        for item in parse_tree.subclasses[subclass]:
            print(f"  Item: {item}")

print (parse_tree.subclasses['Subroutine_Body'])