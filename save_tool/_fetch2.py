import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=60).read().decode('utf-8','replace')
def text_of(data):
    m = re.search(r'<article[^>]*>(.*?)</article>', data, re.S)
    body = m.group(1) if m else data
    t = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    t = re.sub(r'</(tr|td|th|p|li|h\d|div|table|section)>', '\n', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n', t)
    return t
base = 'https://nenkai.github.io/relink-modding/'
pages = {
    'item_ids': 'resources/item_ids/',
    'quest_ids': 'resources/quest_ids/',
    'hashes': 'resources/re/hashes/',
    'obj_id': 'resources/re/obj_id/',
}
for name, path in pages.items():
    try:
        d = fetch(base + path)
        t = text_of(d)
        open(rf'C:\Users\MikeT\Downloads\1.8.5\save_tool\_{name}.txt','w',encoding='utf-8').write(t)
        print(name, 'saved', len(t), 'chars')
    except Exception as e:
        print(name, 'ERR', repr(e))
