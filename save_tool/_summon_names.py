import msgpack, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
obj = msgpack.unpackb(open('_en_text.msg','rb').read(), raw=False)
rows = obj.get('rows_', [])
hits = [r.get('column_',{}) for r in rows if str(r.get('column_',{}).get('id_hash_','')).startswith('TXT_SUMMON') or str(r.get('column_',{}).get('id_hash_','')).startswith('TXT_SO_')]
print('summon text keys:', len(hits))
for c in hits[:30]:
    print('  ', c.get('id_hash_',''), '=>', str(c.get('text_',''))[:50])
