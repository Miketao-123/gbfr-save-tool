import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
r = json.loads(fetch('https://api.github.com/repos/Nenkai/GBFRDataTools/git/trees/master?recursive=1'))
paths = [t['path'] for t in r.get('tree',[]) if t['type']=='blob']
print('total files:', len(paths))
# find archive/data reading files
for p in paths:
    low = p.lower()
    if any(k in low for k in ['archive','dataid','dataindex','data.i','reader','index']) and ('data' in low or 'archive' in low):
        print(' ', p)
