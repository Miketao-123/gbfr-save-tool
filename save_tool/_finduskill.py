import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
fl = open(r'GBFRDataTools_filelist.txt', encoding='utf-8', errors='replace').read().splitlines()
for line in fl:
    if 'text_uskill' in line or ('text' in line and line.count('/') < 6):
        if 'text_uskill' in line or 'text_stage' in line:
            print(line)
