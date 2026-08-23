import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = 'https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/'
files = ['GBFRDataTools.Database/GameTable.cs']
for f in files:
    try:
        d = urllib.request.urlopen(urllib.request.Request(base+f, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
        open(rf'C:\Users\MikeT\Downloads\1.8.5\save_tool\_GameTable.cs','w',encoding='utf-8').write(d)
        print(f, 'saved', len(d))
    except Exception as e:
        print(f, 'ERR', repr(e))
# also get the file extraction portion of Archive.cs (search for OpenFile/Extract)
d = urllib.request.urlopen(urllib.request.Request(base+'GBFRDataTools.Archive/Archive.cs', headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_Archive.cs','w',encoding='utf-8').write(d)
print('Archive.cs saved', len(d))
