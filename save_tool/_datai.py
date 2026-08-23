import sys, io, struct, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
path = r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i'
data = open(path,'rb').read()
print('data.i size:', len(data))
# ASCII strings in data.i
import re
strs = re.findall(rb'[\x20-\x7e]{5,}', data)
print('ascii strings:', len(strs))
for s in strs[:80]:
    print(' ', s.decode('latin1'))
