import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
# list GBFRDataTools repo tree
for repo in ['Nenkai/GBFRDataTools','relink-org/GBFRDataTools']:
    try:
        r = json.loads(fetch(f'https://api.github.com/repos/{repo}/git/trees/main?recursive=1'))
        paths = [t['path'] for t in r.get('tree',[]) if t['type']=='blob']
        print(f'=== {repo}: {len(paths)} files ===')
        for p in paths:
            if 'save' in p.lower() or 'Save' in p or 'checksum' in p.lower():
                print('  SAVE?', p)
        # print top-level dirs
        dirs = sorted(set(p.split('/')[0] for p in paths if '/' in p))
        print('  dirs:', dirs[:40])
    except Exception as e:
        print(repo, 'ERR', repr(e))
