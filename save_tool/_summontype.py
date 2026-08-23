import re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
data = open(r'C:\Users\MikeT\Downloads\1.8.5\GBFR PE Patch Tool.exe','rb').read()
text = data.decode('utf-8','replace')
# find summon-related JSON content around 15.3MB
for probe in ['"types"', '"typeHash"', '"skills"', 'SUMMON_', 'SO_0']:
    idx = text.find(probe, 14_000_000)
    print(f'{probe} @ {idx}')
# dump the summon type region: find JSON with "hash" + "name" entries that look like summon types
m = re.search(r'\{[^\n]*"hash"\s*:\s*"0x[0-9A-F]{8}"[^\n]*"displayName"\s*:\s*"[^"]{2,40}"', text[14_000_000:14_500_000])
if m:
    print('sample entry:', m.group(0)[:300])
# look for a JSON array/object of summon types near subParams (15.3MB)
i = text.find('"subParams"', 15_000_000)
start = i - 3000
snip = text[start:start+4000].replace('\x00','.')
print('=== region before subParams ===')
print(snip[:3000])
