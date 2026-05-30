import ast
import sys
from pathlib import Path

class LoggingFstringTransformer(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.AST:
        # Only handle simple logger.<level>(f"...{x}...") patterns
        try:
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if func.value.id == "logger" and node.args:
                    first = node.args[0]
                    if isinstance(first, ast.JoinedStr):
                        # Build format string with %s placeholders
                        parts = []
                        exprs = []
                        for val in first.values:
                            if isinstance(val, ast.FormattedValue):
                                parts.append("%s")
                                exprs.append(val.value)
                            elif isinstance(val, ast.Constant):
                                parts.append(str(val.value))
                            else:
                                parts.append(ast.unparse(val))
                        new_msg = ast.Constant(value="".join(parts))
                        new_args = [new_msg] + exprs + node.args[1:]
                        node.args = new_args
        except Exception:
            return node
        return node


def transform_file(path: Path) -> bool:
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except Exception:
        return False
    transformer = LoggingFstringTransformer()
    new_tree = transformer.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_src = ast.unparse(new_tree)
    if new_src != src:
        path.write_text(new_src, encoding="utf-8")
        return True
    return False


def main(root: str):
    p = Path(root)
    changed = 0
    for path in p.rglob("*.py"):
        if ".venv" in path.parts:
            continue
        if path.match("*/alembic/*"):
            continue
        if path.match("scripts/*"):
            continue
        if path.name == Path(__file__).name:
            continue
        try:
            if transform_file(path):
                print(f"Transformed: {path}")
                changed += 1
        except Exception as e:
            print(f"Failed {path}: {e}")
    print(f"Total transformed files: {changed}")

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    main(root)
