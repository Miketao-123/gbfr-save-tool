# -*- coding: utf-8 -*-
"""Extract skill.tbl / gem.tbl / skill_status.tbl from data.0 and parse them (GBFR 2.0.4)."""
import io, struct, sys, bisect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
from gbfr_datai import parse_index, gbfr_file_hash
import lz4.block

GAME = r'D:\Steam\steamapps\common\Granblue Fantasy Relink'

def extract_file_from_archive(idx, path):
    hashes = idx['archive_file_hashes']
    h = gbfr_file_hash(path)
    i = bisect.bisect_left(hashes, h)
    if i >= len(hashes) or hashes[i] != h:
        return None
    f2c = idx['file_to_chunk'][i]
    chunk = idx['chunks'][f2c[0]]
    data_file = f'{GAME}\\data.{chunk[4]}'
    with open(data_file, 'rb') as f:
        f.seek(chunk[0])
        raw = f.read(chunk[1])
    if chunk[2] != chunk[1]:
        raw = lz4.block.decompress(raw, uncompressed_size=chunk[2])
    return raw[f2c[2]:f2c[2]+f2c[1]]

# ---------- column definitions (v2.0.4) ----------
HASH = 'HASH'; UINT = 'UINT'; INT = 'INT'; FLOAT = 'FLOAT'; BYTE = 'BYTE'; RAW16 = 'RAW16'
SKILL_COLS = [RAW16, RAW16, RAW16, HASH, HASH, HASH, HASH, HASH, HASH, HASH, HASH, HASH,
              INT, INT, UINT, UINT, INT, INT, BYTE, BYTE, BYTE, BYTE]
SKILL_NAMES = ['IconId1','IconId2','SortOrderMaybe','Unk1','Unk2','Unk3','Unk4','Unk5',
               'Key','Name','Summary','Explain','Unk11','Unk12','GemCategory','QuestId',
               'SortOrder','InventorySortOrder','UnkBool11','IsResistance','pad1','pad2']
GEM_COLS = [HASH, HASH, HASH, HASH, HASH, HASH, HASH, UINT, UINT, INT, UINT, UINT, UINT, UINT,
            BYTE, BYTE, BYTE, BYTE, BYTE, BYTE, BYTE, BYTE]
GEM_NAMES = ['SkillId1','SkillId2','Key','Name','Description','PlayerReq','ItemTierId',
             'IsLuciliusGem','SortOrderForRewards','SkillTypeLotIdForRandom2ndSkill',
             'ItemMaterialCommonAnimaSpecialBossColIndex','Category','Rarity',
             'ItemMaterialCommonStageColIndex','CanGemMix','CantSell','HideLevelNumber',
             'CanOnlyHoldOne','CanUseAzurite','Unk20','Unk21','Unk22']
SKILLSTATUS_COLS = [FLOAT]*10 + [HASH, HASH, UINT]
SKILLSTATUS_NAMES = ['LevelValue'+str(i) for i in range(1,11)] + ['Key','LevelDescription','Level']

def parse_table(data, cols, names, row_size):
    n = struct.unpack_from('<q', data, 0)[0]
    rows = []
    for i in range(n):
        base = 8 + i*row_size
        row = {}
        off = base
        for ci, c in enumerate(cols):
            if c == RAW16:
                row[names[ci]] = data[off:off+16].rstrip(b'\x00').decode('utf-8','replace'); off += 16
            elif c == HASH:
                row[names[ci]] = struct.unpack_from('<I', data, off)[0]; off += 4
            elif c == UINT:
                row[names[ci]] = struct.unpack_from('<I', data, off)[0]; off += 4
            elif c == INT:
                row[names[ci]] = struct.unpack_from('<i', data, off)[0]; off += 4
            elif c == FLOAT:
                row[names[ci]] = struct.unpack_from('<f', data, off)[0]; off += 4
            elif c == BYTE:
                row[names[ci]] = data[off]; off += 1
        rows.append(row)
    return rows

if __name__ == '__main__':
    idx = parse_index(GAME + r'\data.i')
    for path, cols, names, rs in [
        ('system/table/skill.tbl', SKILL_COLS, SKILL_NAMES, 112),
        ('system/table/gem.tbl', GEM_COLS, GEM_NAMES, 64),
        ('system/table/skill_status.tbl', SKILLSTATUS_COLS, SKILLSTATUS_NAMES, 52),
    ]:
        data = extract_file_from_archive(idx, path)
        if data is None:
            print(f'{path}: NOT FOUND'); continue
        rows = parse_table(data, cols, names, rs)
        out = path.replace('/', '_') + '.json'
        import json
        json.dump(rows, open(rf'C:\Users\MikeT\Downloads\1.8.5\save_tool\{out}', 'w', encoding='utf-8'), indent=1)
        print(f'{path}: {len(rows)} rows -> {out}')
    print('done')
