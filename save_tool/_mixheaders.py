import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = 'https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/GBFRDataTools.Database/Headers/'
for f in ['gem_mix.headers', 'gem_mix_success.headers', 'gem_mix_rupi.headers', 'skill_type_lot.headers', 'gem_mix_ticket.headers']:
    try:
        d = urllib.request.urlopen(urllib.request.Request(base+f, headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
        print('==========', f, '==========')
        print(d[:2000])
        print()
    except Exception as e:
        print(f, 'ERR', repr(e))
