import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
# GitHub code/repo search for GBFR save
for q in ['Granblue+Fantasy+Relink+save+editor', 'GBFR+save+editor', 'relink+save+checksum']:
    try:
        r = json.loads(fetch(f'https://api.github.com/search/repositories?q={q}&per_page=10'))
        print(f'=== repos for "{q}" ===')
        for it in r.get('items', []):
            print(' ', it['full_name'], '|', (it.get('description') or '')[:80])
    except Exception as e:
        print(q, 'ERR', repr(e))
