import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

def vec(idt):
    r = save.find_first('uint', idt) or save.find_first('int', idt) or save.find_first('bool', idt)
    return (r, save.get_values(r)) if r else (None, [])

# crab quest IDs: 0x200001 and 0x290002..0x290015
crab = {0x200001:'Save the Crustaceans (base)'}
for i in range(0x290002, 0x290016):
    crab[i] = f'Part/chain 0x{i:06X}'

for name, idt in [('2505',2505),('2510',2510),('2550',2550),('2560',2560),('2570',2570),('2580',2580)]:
    r, vals = vec(idt)
    if not r: continue
    print(f'=== {idt} kind={r.kind} count={len(vals)} ===')
    hits = [(i,v) for i,v in enumerate(vals) if v in crab]
    for i,v in hits:
        print(f'   idx {i}: 0x{v:06X} = {crab[v]}')
    if not hits:
        print('   (no crab quest ids)')
    # show status/complete at those indices for known parallel vectors
    if idt == 2550:
        s2551 = vec(2551)[1]; b2554 = vec(2554)[1]; b2555 = vec(2555)[1]
        for i,v in hits:
            print(f'      -> 2551[{i}]={s2551[i] if i<len(s2551) else "?"}  2554[{i}]={b2554[i] if i<len(b2554) else "?"}  2555[{i}]={b2555[i] if i<len(b2555) else "?"}')
