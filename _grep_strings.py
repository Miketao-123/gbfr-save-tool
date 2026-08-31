# -*- coding: utf-8 -*-
"""Grep exe ascii strings file for identifier-like tokens matching a regex.
Usage: python _grep_strings.py <pattern> [context]
"""
import re, sys

pat = re.compile(sys.argv[1], re.IGNORECASE)
tok_re = re.compile(r'[A-Za-z_][A-Za-z0-9_]{2,}')
show_ctx = len(sys.argv) > 2

hits = set()
with open(r'extracted\_ascii_strings.txt', encoding='utf-8', errors='replace') as f:
    for line in f:
        for m in tok_re.finditer(line):
            t = m.group(0)
            if pat.search(t):
                hits.add(t)

for t in sorted(hits):
    print(t)
print('---', len(hits), 'unique tokens', file=sys.stderr)
