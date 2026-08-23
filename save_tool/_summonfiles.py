import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
data = open(r'C:\Users\MikeT\Downloads\1.8.5\GBFR PE Patch Tool.exe','rb').read()
text = data.decode('utf-8', 'replace')
# find summon data file references
for probe in ['summonTypeFile','summonSkillFile','summonSubParamFile','data/summon']:
    idx = text.find(probe)
    print(f'{probe}: {idx}')
    if idx >= 0:
        print('  ctx:', text[max(0,idx-120):idx+200].replace('\x00','.'))
# search for summon JSON content: "subParams" / summon type entries
for probe in ['"subParams"', '"typeHash"', 'summon']:
    idx = text.find(probe)
    print(f'{probe}: {idx}')
