import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
txt = open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\traits.json', encoding='utf-8').read()
# find entries for SKILL_563/564/565 (highest, likely DLC)
for sid in ['SKILL_563','SKILL_564','SKILL_565']:
    for m in re.finditer(r'\{[^{}]*?"internalId"\s*:\s*"' + sid + r'[^{}]*?\}', txt):
        print('=== ' + sid + ' ===')
        print(m.group(0)[:800])
        print()
