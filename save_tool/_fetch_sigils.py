import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
url = 'https://nenkai.github.io/relink-modding/resources/sigil_gem_ids/'
data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read().decode('utf-8','replace')
m = re.search(r'<article[^>]*>(.*?)</article>', data, re.S)
body = m.group(1) if m else data
t = re.sub(r'<script.*?</script>', '', body, flags=re.S)
t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
t = re.sub(r'</(tr|td|th|p|li|h\d|div|table|section)>', '\n', t)
t = re.sub(r'<[^>]+>', ' ', t)
t = html.unescape(t)
t = re.sub(r'[ \t]+', ' ', t)
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_sigils_wiki.txt','w',encoding='utf-8').write(t)
print('saved', len(t))
# search for crab
for pat in ['Crab','crab','Pincer','pincer']:
    for i, line in enumerate(t.splitlines()):
        if pat in line:
            print(f'[{pat}] {line.strip()}')
