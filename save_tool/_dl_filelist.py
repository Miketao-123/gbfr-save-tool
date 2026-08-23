import urllib.request, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = 'https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/'
for f in ['GBFRDataTools/filelist.txt', 'GBFRDataTools/unknown_hash_to_folder.txt', 'GBFRDataTools.Database/Data/ids.txt']:
    try:
        d = urllib.request.urlopen(urllib.request.Request(base+f, headers={'User-Agent':'Mozilla/5.0'}), timeout=60).read().decode('utf-8','replace')
        fn = f.replace('/','_')
        open(rf'C:\Users\MikeT\Downloads\1.8.5\save_tool\{fn}','w',encoding='utf-8').write(d)
        print(f, 'saved', len(d), 'chars, lines:', d.count(chr(10)))
    except Exception as e:
        print(f, 'ERR', repr(e))
# search filelist for text/skill paths
fl = open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\GBFRDataTools_filelist.txt', encoding='utf-8', errors='replace').read().splitlines()
print()
print('=== text/skill related paths in filelist ===')
for line in fl:
    low = line.lower()
    if 'text' in low and ('skill' in low or '.msg' in low) or 'text_uskill' in low or 'text_stage' in low:
        print(' ', line)
