import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
for repo in ['xcier/GBFR-Save-Editor','LonelyThic/GBFRSaveEditor']:
    try:
        meta = json.loads(fetch(f'https://api.github.com/repos/{repo}'))
        br = meta['default_branch']
        print(f'=== {repo} (branch {br}) ===')
        r = json.loads(fetch(f'https://api.github.com/repos/{repo}/git/trees/{br}?recursive=1'))
        for t in r.get('tree',[]):
            if t['type']=='blob' and t.get('path','').endswith(('.cs','.py','.js','.ts','.go','.md')):
                print(' ', t['path'])
    except Exception as e:
        print(repo, 'ERR', repr(e))
