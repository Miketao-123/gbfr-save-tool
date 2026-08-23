# -*- coding: utf-8 -*-
"""从 exe 字符串按词条块提取祝福词条目录(绕过被截断的长字符串)"""
import sys, json, re

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

LINES = open(r'C:\Users\Windows\Downloads\GBFR自用修改器\extracted\_ascii_strings.txt', encoding='utf-8', errors='replace').read().splitlines()
chunk = '\n'.join(LINES[19684:22318])

# 按 internalId 块切分
blocks = re.split(r'(?=^\s*"internalId":)', chunk, flags=re.M)
traits = []
for b in blocks:
    m_id = re.search(r'"internalId":\s*"([^"]+)"', b)
    m_h = re.search(r'"hash":\s*"0x([0-9A-Fa-f]+)"', b)
    m_name = re.search(r'"displayName":\s*"([^"]+)"', b)
    m_cat = re.search(r'"category":\s*(null|"[^"]*")', b)
    m_max = re.search(r'"maxLevel":\s*(\d+|null)', b)
    if m_id and m_h:
        entry = {
            'internalId': m_id.group(1),
            'hash': '0x' + m_h.group(1),
            'displayName': m_name.group(1) if m_name else m_id.group(1),
            'category': None if (m_cat and m_cat.group(1) == 'null') else (m_cat.group(1).strip('"') if m_cat else None),
            'maxLevel': int(m_max.group(1)) if (m_max and m_max.group(1) != 'null') else None,
        }
        traits.append(entry)

print('提取到词条总数:', len(traits))
wc = [t for t in traits if t.get('category') == 'wrightstone_trait']
print('wrightstone_trait 类:', len(wc))
json.dump({'schemaVersion': 1, 'traits': traits}, open(r'C:\Users\Windows\Downloads\GBFR自用修改器\save_tool\wrightstone_traits.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for t in wc[:40]:
    print('  %-32s %-12s max=%s' % (t['internalId'], t['hash'], t.get('maxLevel')))
