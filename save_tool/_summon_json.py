import re, io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
data = open(r'C:\Users\MikeT\Downloads\1.8.5\GBFR PE Patch Tool.exe','rb').read()
text = data.decode('utf-8', 'replace')
# dump region around "subParams" (5073916) and "typeHash" (5065231) to find JSON files
for label, idx in [('typeHash', 5065231), ('subParams', 5073916)]:
    start = max(0, idx-400)
    snip = text[start:idx+800].replace('\x00','.')
    print(f'===== {label} @ {idx} =====')
    print(snip[:1100])
    print()
