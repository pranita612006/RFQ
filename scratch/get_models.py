import re

with open('inspect_db_utf8.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

models_to_find = [
    'tbl_bom_partdetails_master',
    'tbl_bop_tool_measure',
    'tbl_costing_internalconversion',
    'tbl_bop_tab'
]

for m in models_to_find:
    pattern = r"class\s+\w+\(models\.Model\):[\s\S]*?db_table = '" + m + "'"
    match = re.search(pattern, text)
    if match:
        print(f"================ {m} ================")
        print(match.group(0))
    else:
        print(f"NOT FOUND EXACT MATCH FOR {m}")
