import re

with open('inspect_db_utf8.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

m = re.search(r'class TblCostingInternalconversion[\s\S]*?class ', text)
if m:
    print(m.group(0))
else:
    print("Class not found")
