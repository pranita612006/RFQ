import re

with open('inspect_db_utf8.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

keywords = ['tbl_bom_partdetails_master', 'tbl_bop_tool_measure', 'tbl_costing_internalconversion', 'tbl_bop_tab']
for kw in keywords:
    print(f"=== SEARCH FOR {kw} ===")
    pos = 0
    while True:
        idx = text.lower().find(kw.lower(), pos)
        if idx == -1:
            break
        print(text[max(0, idx-100):min(len(text), idx+500)])
        print("-" * 50)
        pos = idx + len(kw)
