# -*- coding: utf-8 -*-
"""手动从 PyPI 下载 wheel(绕过 pip 的沙箱问题),解压到 _pylibs。"""
import json, os, sys, urllib.request, zipfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = r'C:\Users\Windows\Downloads\GBFR自用修改器'
WHEELS = os.path.join(BASE, '_wheels')
LIBS = os.path.join(BASE, '_pylibs')
os.makedirs(WHEELS, exist_ok=True)
os.makedirs(LIBS, exist_ok=True)

PKGS = ['pyinstaller-hooks-contrib', 'altgraph', 'packaging',
        'pefile', 'pywin32-ctypes', 'setuptools']


def pick_wheel(pkg):
    with urllib.request.urlopen('https://pypi.org/pypi/%s/json' % pkg, timeout=60) as r:
        data = json.load(r)
    files = data.get('urls', [])
    cands = []
    for f in files:
        fn = f['filename']
        if not fn.endswith('.whl'):
            continue
        # {name}-{ver}-{pytag}-{abitag}-{plat}.whl
        parts = fn[:-4].split('-')
        if len(parts) < 5:
            continue
        pytag, plat = parts[-3], parts[-1]
        if 'win_amd64' not in plat and 'any' not in plat:
            continue
        cands.append((fn, f['url'], pytag))
    def score(item):
        fn, _, pytag = item
        if 'cp314' in pytag: return 0
        if 'abi3' in pytag: return 1
        if pytag.startswith('py3') or pytag == 'py3': return 2
        return 3
    cands.sort(key=score)
    if not cands:
        print('  [跳过] %s: 无可用 wheel' % pkg)
        return None
    return cands[0][0], cands[0][1]


def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print('  [已有]', os.path.basename(dest))
        return
    print('  [下载]', url.split('/')[-1])
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)


for pkg in PKGS:
    print(pkg)
    picked = pick_wheel(pkg)
    if not picked:
        continue
    fn, url = picked
    wpath = os.path.join(WHEELS, fn)
    download(url, wpath)
    print('  [解压]', fn)
    with zipfile.ZipFile(wpath) as z:
        z.extractall(LIBS)

print('done. _pylibs contents:')
for n in sorted(os.listdir(LIBS)):
    print('  ', n)
