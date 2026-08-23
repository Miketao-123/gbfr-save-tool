import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
for fn in ['sigils.json', 'secondary-trait-rules.json']:
    p = rf'C:\Users\MikeT\Downloads\1.8.5\extracted\{fn}'
    raw = open(p, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    # check first non-space char
    s = raw.decode('utf-8', 'replace').lstrip()
    if not s.startswith('{'):
        raw = b'{' + raw
    # try parse
    try:
        obj = json.loads(raw.decode('utf-8-sig'))
        open(p, 'wb').write(raw)
        print(fn, 'fixed, keys:', list(obj.keys())[:5])
    except Exception as e:
        print(fn, 'still broken:', repr(e)[:120])
