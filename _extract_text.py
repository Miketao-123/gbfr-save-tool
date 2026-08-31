# -*- coding: utf-8 -*-
"""Extract text entries near a skill id from the raw .msg text dump."""
import re, sys

skill = sys.argv[1] if len(sys.argv) > 1 else '324'
path = sys.argv[2] if len(sys.argv) > 2 else r'save_tool\_en_text.msg'

data = open(path, 'rb').read().decode('utf-8', errors='replace')

# msgpack-ish: find 'text_' followed by str marker then content
# Simpler: split on 'column_' markers, pair id_hash_ / text_
entries = []
# find all id_hash_ values (printable) and following text_ values
pat = re.compile(r'id_hash_.{0,4}?([A-Za-z0-9_]{4,60}).{0,30}?subid_hash_.{0,12}?text_.{0,4}?([ -~]{1,400})', re.DOTALL)
for m in pat.finditer(data):
    entries.append((m.group(1), m.group(2)))

for k, v in entries:
    if skill in k:
        print(k, '=>', v[:300])
