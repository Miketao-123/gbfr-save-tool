import msgpack, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
for fn in ['_cs_text.msg','_en_text.msg']:
    obj = msgpack.unpackb(open(fn,'rb').read(), raw=False)
    rows = obj.get('rows_', [])
    hits = []
    for r in rows:
        col = r.get('column_', {})
        t = str(col.get('text_',''))
        if any(k in t for k in ['配装','方案','套装','预设','Loadout','loadout','Preset','preset','Set','套装']):
            hits.append((col.get('id_hash_',''), t[:80]))
    print(f'=== {fn}: {len(hits)} hits ===')
    for h in hits[:25]:
        print('  ', h)
