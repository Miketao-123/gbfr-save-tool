import json
d = json.load(open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_GBFR_tables.json', encoding='utf-8'))
print('top keys:', list(d.keys())[:20] if isinstance(d, dict) else type(d))
