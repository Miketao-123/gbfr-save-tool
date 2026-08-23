import urllib.request, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
# search repo code for tier map / ItemTierId / SkillTypeLot usage
r = json.loads(fetch('https://api.github.com/repos/Nenkai/GBFRDataTools/git/trees/master?recursive=1'))
paths = [t['path'] for t in r.get('tree',[]) if t['type']=='blob' and t['path'].endswith('.cs')]
print('cs files:', len(paths))
hits = []
for p in paths:
    try:
        d = urllib.request.urlopen(urllib.request.Request('https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/'+p, headers={'User-Agent':'Mozilla/5.0'}), timeout=20).read().decode('utf-8','replace')
        low = d.lower()
        if 'tier' in low and ('gem' in low or 'mix' in low or 'lot' in low) or 'itemtierid' in low or 'skilltypelotid' in low:
            hits.append((p, len(d)))
    except: pass
for p, n in hits:
    print(' ', p, n)
