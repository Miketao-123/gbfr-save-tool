import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = 'https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/'
for f in ['GBFRDataTools.FlatBuffers/IndexFile.fbs', 'GBFRDataTools.Archive/Archive.cs']:
    try:
        d = urllib.request.urlopen(urllib.request.Request(base+f, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
        print('==========', f, '==========')
        print(d[:8000])
        print()
    except Exception as e:
        print(f, 'ERR', repr(e))
