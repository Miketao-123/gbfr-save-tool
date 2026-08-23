import msgpack, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def load(fn):
    return msgpack.unpackb(open(fn,'rb').read(), raw=False)
for fn in ['_en_text_uskill.msg','_en_text.msg']:
    obj = load(fn)
    rows = obj.get('rows_', [])
    print(f'=== {fn}: {len(rows)} rows ===')
    hits = []
    for r in rows:
        col = r.get('column_', {})
        t = str(col.get('text_',''))
        if 'Crab' in t or 'Pincer' in t or 'crab' in t:
            hits.append((col.get('id_hash_',''), col.get('subid_hash_',''), t))
    for h in hits:
        print('  HIT:', h)
    if not hits:
        print('  (no crab hits)')
