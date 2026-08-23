import msgpack, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def load(fn):
    d = open(fn,'rb').read()
    try:
        return msgpack.unpackb(d, raw=False)
    except Exception as e:
        print(fn, 'msgpack ERR', repr(e))
        # try raw
        try:
            return msgpack.unpackb(d, raw=True)
        except Exception as e2:
            print('  raw ERR', repr(e2)); return None
for fn in ['_en_text_uskill.msg','_cs_text_uskill.msg']:
    obj = load(fn)
    print('===', fn, 'type:', type(obj))
    if isinstance(obj, dict):
        print('  entries:', len(obj))
        hits = []
        for k,v in obj.items():
            s = str(v)
            if 'Pincer' in s or 'pincer' in s or 'Dread' in s:
                hits.append((k,v))
        for k,v in hits:
            print('  HIT:', repr(k), '=>', repr(v))
        if not hits:
            print('  (no pincer hits)')
            for k,v in list(obj.items())[:8]:
                print('   sample:', repr(k), '=>', repr(v)[:80])
    elif isinstance(obj, list):
        print('  len:', len(obj))
        print('  first:', str(obj[0])[:200])
