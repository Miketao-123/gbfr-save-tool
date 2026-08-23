import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch_text(url):
    data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40).read().decode('utf-8','replace')
    m = re.search(r'<article[^>]*>(.*?)</article>', data, re.S)
    body = m.group(1) if m else data
    t = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    t = re.sub(r'<style.*?</style>', '', t, flags=re.S)
    t = re.sub(r'</(tr|td|th|p|li|h\d|div|table|section|pre)>', '\n', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n\s*\n+', '\n', t)
    return t
t = fetch_text('https://nenkai.github.io/relink-modding/resources/file_extensions/')
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_fileext.txt','w',encoding='utf-8').write(t)
print(t[:6000])
