import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = 'https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/'
files = [
    'GBFRDataTools.Database/Headers/skill.headers',
    'GBFRDataTools.Database/Headers/gem.headers',
    'GBFRDataTools.Database/Headers/skill_status.headers',
]
for f in files:
    try:
        d = urllib.request.urlopen(urllib.request.Request(base+f, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
        print('==========', f, '==========')
        print(d[:3000])
        print()
    except Exception as e:
        print(f, 'ERR', repr(e))
