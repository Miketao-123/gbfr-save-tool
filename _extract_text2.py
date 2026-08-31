# -*- coding: utf-8 -*-
"""Properly extract id_hash_/text_ pairs from raw msg text dump using msgpack str decoding."""
import re, sys

skill = sys.argv[1]
path = sys.argv[2] if len(sys.argv) > 2 else r'save_tool\_en_text.msg'
raw = open(path, 'rb').read()

def read_str(buf, i):
    b = buf[i]
    if 0xA0 <= b <= 0xBF:  # fixstr
        ln = b & 0x1F; i += 1
    elif b == 0xD9:  # str8
        ln = buf[i+1]; i += 2
    elif b == 0xDA:  # str16
        ln = (buf[i+1] << 8) | buf[i+2]; i += 3
    elif b == 0xDB:  # str32
        ln = int.from_bytes(buf[i+1:i+5], 'big'); i += 5
    else:
        return None, i
    return buf[i:i+ln].decode('utf-8', errors='replace'), i + ln

results = []
for m in re.finditer(rb'id_hash_', raw):
    i = m.end()
    idv, i = read_str(raw, i)
    if idv is None:
        continue
    # expect subid_hash_ then text_
    tm = re.match(rb'.{0,40}?text_', raw[i:i+60], re.DOTALL)
    if not tm:
        continue
    j = i + tm.end()
    tv, j = read_str(raw, j)
    if tv is None:
        continue
    results.append((idv, tv))

for k, v in results:
    if skill in k:
        print(k, '=>', v)
