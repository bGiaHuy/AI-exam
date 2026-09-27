import os
import re
import json

py_imports = set()
for root, dirs, files in os.walk('backend'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                for line in fp:
                    m = re.match(r'^(?:from|import)\s+([a-zA-Z0-9_]+)', line.strip())
                    if m:
                        py_imports.add(m.group(1))

print("Python imports in backend:", sorted(list(py_imports)))

# Read package.json
with open('package.json', 'r', encoding='utf-8') as fp:
    pkg = json.load(fp)

print("\nFrontend dependencies:")
for k, v in pkg.get('dependencies', {}).items():
    print(f"  {k}: {v}")
print("\nFrontend devDependencies:")
for k, v in pkg.get('devDependencies', {}).items():
    print(f"  {k}: {v}")
