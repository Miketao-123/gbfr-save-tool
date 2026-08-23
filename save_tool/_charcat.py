import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
c = json.load(open(r'catalog_chars.json', encoding='utf-8'))
print('chars:', len(c))
for k, v in list(c.items())[:5]:
    print('  ', k, '->', v)
# test find
print('PL0000 in values:', 'PL0000' in c.values())
