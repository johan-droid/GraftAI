import ast, os, sys

errors = []
for root, dirs, files in os.walk("backend"):
    # Skip virtual envs, node_modules, pycache
    dirs[:] = [d for d in dirs if d not in (".venv", "node_modules", "__pycache__", ".pytest_cache")]
    for f in files:
        if not f.endswith(".py"):
            continue
        path = os.path.join(root, f)
        try:
            with open(path, encoding="utf-8") as fh:
                ast.parse(fh.read(), filename=path)
        except SyntaxError as e:
            errors.append(f"SYNTAX ERROR in {path}: line {e.lineno}: {e.msg}")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print(f"All Python files parsed OK")
