import re, sys

def extract_strings(path, minlen=4, ascii_only=True, start=0, end=None):
    with open(path, 'rb') as f:
        if end is None:
            f.seek(0, 2); end = f.tell()
        f.seek(start)
        data = f.read(end - start)
    if ascii_only:
        return re.findall(rb'[\x20-\x7e]{%d,}' % minlen, data)
    else:
        return re.findall(rb'[\x20-\x7e]{%d,}' % minlen, data)

if __name__ == '__main__':
    exe = r"D:\Steam\steamapps\common\Granblue Fantasy Relink\granblue_fantasy_relink.exe"
    # schema strings are near the end (chunk ~100MB+)
    strs = extract_strings(exe, minlen=4, start=90*1024*1024)
    text = b'\n'.join(strs).decode('latin1')
    # filter schema-like names
    keys = ['SaveData','PlayerInfo','Sigil','Wrightstone','Item','Quest','Collect','Trait','Weapon','Chara','Character','Rupie','MSP','Dabloon','Pendant','Crab','crab','Hash','hash','Count','count','Unit','unit','vtable','FlatBuffer','flatbuffer','Schema','schema','DataList','List']
    seen = set()
    for m in re.finditer(r'[\x20-\x7e]{4,}', text):
        s = m.group()
        for k in keys:
            if k.lower() in s.lower():
                if s not in seen:
                    seen.add(s)
                    print(s)
                break
