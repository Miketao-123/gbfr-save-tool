import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
# find the correct repo
for repo in ['relink-org/GBFRDataTools','Nenkai/GBFRDataTools']:
    try:
        meta = json.loads(fetch(f'https://api.github.com/repos/{repo}'))
        print(repo, '| default_branch:', meta['default_branch'], '| updated:', meta.get('pushed_at'))
        br = meta['default_branch']
        r = json.loads(fetch(f'https://api.github.com/repos/{repo}/git/trees/{br}?recursive=1'))
        paths = [t['path'] for t in r.get('tree',[]) if t['type']=='blob']
        print('  files:', len(paths))
        for p in paths:
            low = p.lower()
            if any(k in low for k in ['dataarchive','data.i','tbl','table','skill','gem','save']):
                print('   ', p)
    except Exception as e:
        print(repo, 'ERR', repr(e))
