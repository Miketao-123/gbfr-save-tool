import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
# sitemap
try:
    s = fetch('https://nenkai.github.io/relink-modding/sitemap.xml')
    urls = re.findall(r'<loc>(.*?)</loc>', s)
    print("=== sitemap URLs ===")
    for u in urls:
        print(u)
except Exception as e:
    print('sitemap ERR', e)
    # fallback: robots/nav
    s = fetch('https://nenkai.github.io/relink-modding/')
    print(s[:2000])
