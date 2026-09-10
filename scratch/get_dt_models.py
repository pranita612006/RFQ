import re

with open('inspect_db_utf8.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

models_to_find = [
    'tbl_dtassigmentyeardata',
    'tbl_dtcategorylist'
]

for m in models_to_find:
    pattern = r"class\s+\w+\(models\.Model\):[\s\S]*?db_table = '" + m + "'"
    match = re.search(pattern, text)
    if match:
        print(f"================ {m} ================")
        print(match.group(0))
    else:
        print(f"NOT FOUND EXACT MATCH FOR {m}")
        idx = text.lower().find(m.lower())
        if idx != -1:
            print("Found nearby text:")
            print(text[max(0, idx-200):min(len(text), idx+500)])
