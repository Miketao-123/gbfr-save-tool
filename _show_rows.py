# -*- coding: utf-8 -*-
import re, sys
d = open(sys.argv[1], encoding='utf-8').read()
for m in re.finditer(r'<row r="(\d+)".*?</row>', d, re.DOTALL):
    s = m.group(0)
    print('ROW', m.group(1), ':', s[:300])
    print('---')
