import urllib.request, re, html, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
urls = [
    'https://news.17173.com/content/07232026/110302561.shtml',
    'https://www.9game.cn/news/11978394.html',
]
for url in urls:
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
        # extract title + main text
        t = re.sub(r'<script.*?</script>', ' ', data, flags=re.S)
        t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S)
        title = re.search(r'<title>(.*?)</title>', t, re.S)
        t = re.sub(r'<[^>]+>', '\n', t)
        t = html.unescape(t)
        t = re.sub(r'[ \t]+', ' ', t)
        t = re.sub(r'\n\s*\n+', '\n', t)
        print('=====', url)
        print('TITLE:', title.group(1).strip() if title else '?')
        # find sections about reward/奖励/因子/共鸣
        lines = t.splitlines()
        for i, line in enumerate(lines):
            if any(k in line for k in ['奖励','因子','共鸣','蟹之','报恩','全收集','报酬']):
                print(' >', line.strip()[:300])
    except Exception as e:
        print(url, 'ERR', repr(e))
