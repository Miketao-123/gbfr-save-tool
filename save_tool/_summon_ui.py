import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
js = open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\app.js', encoding='utf-8').read()
# decode unicode
def dec(s):
    sb = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i+5 < len(s) and s[i+1] == 'u':
            try: sb.append(chr(int(s[i+2:i+6],16))); i += 6; continue
            except: pass
        sb.append(s[i]); i += 1
    return ''.join(sb)
d = dec(js)
# find summon-related section
i = d.find('SummonEditor')
print('SummonEditor at:', i)
if i > 0:
    snip = d[i:i+3000]
    # find type names / hashes
    m = re.findall(r'"([^"]{2,40})"\s*:\s*"([^"]{2,60})"', snip)
    for k,v in m[:40]:
        print(f'  {k} => {v}')
