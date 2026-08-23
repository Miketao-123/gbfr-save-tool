import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
d = urllib.request.urlopen(urllib.request.Request('https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/GBFRDataTools.Database/Headers/gem.headers', headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
print(d[-3500:])
