import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
data = open(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\granblue_fantasy_relink.exe','rb').read()
strs = re.findall(rb'[\x20-\x7e]{4,}', data)
print('total strings:', len(strs))
seen = set()
for s in strs:
    t = s.decode('latin1')
    if ('.msg' in t or 'text_' in t or '/text/' in t) and t not in seen:
        seen.add(t)
        print(t[:200])
    if len(seen) > 60: break
