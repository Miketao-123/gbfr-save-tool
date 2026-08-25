# -*- coding: utf-8 -*-
"""Extract embedded JSON from GBFR PE Patch Tool.exe by brace scanning."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

exe = r'C:\Users\MikeT\Downloads\1.8.5\GBFR PE Patch Tool.exe'
data = open(exe, 'rb').read()
print('exe size:', len(data))

def extract_json(data, key_needle, min_ctx=200):
    """Find '{...}' object containing key_needle; brace-balanced extract."""
    found = []
    start = 0
    while True:
        i = data.find(key_needle, start)
        if i < 0:
            break
        # find the '{' that starts the object: search backwards, skip strings
        j = i
        while j > max(0, i - min_ctx):
            if data[j:j+1] == b'{':
                # brace-balance forward
                depth = 0
                k = j
                in_str = False
                esc = False
                while k < len(data):
                    c = data[k:k+1]
                    if in_str:
                        if esc:
                            esc = False
                        elif c == b'\\':
                            esc = True
                        elif c == b'"':
                            in_str = False
                    else:
                        if c == b'"':
                            in_str = True
                        elif c == b'{':
                            depth += 1
                        elif c == b'}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    obj = json.loads(data[j:k+1].decode('utf-8'))
                                    found.append((j, k + 1, obj))
                                except Exception as e:
                                    found.append((j, k + 1, None))
                                start = i + 1
                                break
                    k += 1
                break
            j -= 1
        else:
            start = i + 1
    return found

out_dir = r'C:\Users\MikeT\gbfr-save-tool\save_tool'
for name, needle in [('summons', b'"summons"'), ('skills', b'"skills"'), ('subParams', b'"subParams"'), ('baseParams', b'"baseParams"')]:
    objs = extract_json(data, needle)
    print(f'=== {name}: {len(objs)} objects ===')
    for j, k, obj in objs:
        if obj is None:
            print(f'  @0x{j:x}..0x{k:x} (len {k-j}) JSON parse FAILED')
            continue
        keys = list(obj.keys()) if isinstance(obj, dict) else '?'
        print(f'  @0x{j:x}..0x{k:x} (len {k-j}): keys={keys}')
        if isinstance(obj, dict) and name in obj:
            arr = obj[name]
            print(f'    {name} count = {len(arr)}')
            if arr:
                print(f'    sample: {json.dumps(arr[0], ensure_ascii=False)[:220]}')
            fn = os.path.join(out_dir, f'_patch_summon_{name}.json')
            with open(fn, 'w', encoding='utf-8') as f:
                json.dump(obj, f, ensure_ascii=False, indent=1)
            print(f'    saved -> {fn}')
