import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read()
r = json.loads(fetch('https://api.github.com/repos/Nenkai/GBFRDataTools/git/trees/master?recursive=1'))
paths = [t['path'] for t in r.get('tree',[]) if t['type']=='blob']
for p in paths:
    low = p.lower()
    if 'filelist' in low or 'hash_to_folder' in low or p.endswith('.txt'):
        print(p)
