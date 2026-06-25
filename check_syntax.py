import ast
import sys

with open(sys.argv[1]) as f:
    source = f.read()

try:
    ast.parse(source)
    print("Syntax OK")
except SyntaxError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)