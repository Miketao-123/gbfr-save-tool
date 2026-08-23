import msgpack, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
obj = msgpack.unpackb(open('_en_text.msg','rb').read(), raw=False)
rows = obj.get('rows_', [])
targets = ['TXT_SKILL_300','TXT_SKILL_301','TXT_SKILL_302','TXT_SKILL_303','TXT_GEEN_300','TXT_GEEN_301','TXT_GEEN_302','TXT_GEEN_303']
for r in rows:
    col = r.get('column_', {})
    kid = col.get('id_hash_','')
    if any(kid.startswith(t) for t in targets) and col.get('subid_hash_','') == '':
        print(f"{kid}: {col.get('text_','')}")
