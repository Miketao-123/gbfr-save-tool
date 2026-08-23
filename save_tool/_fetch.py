import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
url = 'https://nenkai.github.io/relink-modding/resources/re/save_units/'
data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
m = re.search(r'<article[^>]*>(.*?)</article>', data, re.S)
body = m.group(1) if m else data
text = re.sub(r'<script.*?</script>', '', body, flags=re.S)
text = re.sub(r'<style.*?</style>', '', text, flags=re.S)
# keep table structure readable
text = re.sub(r'</(tr|td|th|p|li|h\d|div)>', '\n', text)
text = re.sub(r'<[^>]+>', ' ', text)
text = html.unescape(text)
text = re.sub(r'[ \t]+', ' ', text)
text = re.sub(r'\n\s*\n+', '\n', text)
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_save_units.txt','w',encoding='utf-8').write(text)
print('saved', len(text))
