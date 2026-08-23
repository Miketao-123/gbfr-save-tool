import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sig = json.load(open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\sigils.json', encoding='utf-8-sig'))
json.dump(sig, open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\catalog_sigils_full.json','w',encoding='utf-8'), ensure_ascii=False)
print('catalog_sigils_full.json:', len(sig['sigils']), 'entries')
