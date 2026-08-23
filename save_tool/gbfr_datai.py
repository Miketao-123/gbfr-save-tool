# -*- coding: utf-8 -*-
"""Parse GBFR data.i (IndexFile FlatBuffers) and locate/extract table files."""
import io, os, struct, sys

MASK64 = 0xFFFFFFFFFFFFFFFF
XXH_PRIME64_1 = 11400714785074694791
XXH_PRIME64_2 = 14029467366897019727
XXH_PRIME64_3 = 1609587929392839161
XXH_PRIME64_4 = 9650029242287828579
XXH_PRIME64_5 = 2870177450012600261

def _rol64(v, b): return ((v << b) & MASK64) | (v >> (64 - b))
def _round(acc, val):
    acc = (acc + val * XXH_PRIME64_2) & MASK64
    acc = _rol64(acc, 31)
    acc = (acc * XXH_PRIME64_1) & MASK64
    return acc
def _merge(acc, val):
    val = _round(0, val)
    acc ^= val
    acc = (acc * XXH_PRIME64_1 + XXH_PRIME64_4) & MASK64
    return acc
def _avalanche(v):
    v ^= v >> 33; v = (v * XXH_PRIME64_2) & MASK64
    v ^= v >> 29; v = (v * XXH_PRIME64_3) & MASK64
    v ^= v >> 32
    return v & MASK64
def xxh64(data, seed=0):
    view = memoryview(data); length = len(view); pos = 0
    if length >= 32:
        v1 = (seed + XXH_PRIME64_1 + XXH_PRIME64_2) & MASK64
        v2 = (seed + XXH_PRIME64_2) & MASK64
        v3 = seed & MASK64
        v4 = (seed - XXH_PRIME64_1) & MASK64
        limit = length - 32
        while pos <= limit:
            v1 = _round(v1, struct.unpack_from("<Q", view, pos)[0]); pos += 8
            v2 = _round(v2, struct.unpack_from("<Q", view, pos)[0]); pos += 8
            v3 = _round(v3, struct.unpack_from("<Q", view, pos)[0]); pos += 8
            v4 = _round(v4, struct.unpack_from("<Q", view, pos)[0]); pos += 8
        h64 = (_rol64(v1,1)+_rol64(v2,7)+_rol64(v3,12)+_rol64(v4,18)) & MASK64
        h64 = _merge(h64, v1); h64 = _merge(h64, v2); h64 = _merge(h64, v3); h64 = _merge(h64, v4)
    else:
        h64 = (seed + XXH_PRIME64_5) & MASK64
    h64 = (h64 + length) & MASK64
    while pos + 8 <= length:
        k1 = _round(0, struct.unpack_from("<Q", view, pos)[0])
        h64 ^= k1; h64 = (_rol64(h64,27) * XXH_PRIME64_1 + XXH_PRIME64_4) & MASK64; pos += 8
    if pos + 4 <= length:
        h64 ^= (struct.unpack_from("<I", view, pos)[0] * XXH_PRIME64_1) & MASK64
        h64 = (_rol64(h64,23) * XXH_PRIME64_2 + XXH_PRIME64_3) & MASK64; pos += 4
    while pos < length:
        h64 ^= (view[pos] * XXH_PRIME64_5) & MASK64
        h64 = (_rol64(h64,11) * XXH_PRIME64_1) & MASK64; pos += 1
    return _avalanche(h64)

def gbfr_file_hash(path: str) -> int:
    """GBFR archive file hash: XXHash64(lowercased path, seed 0), big-endian u64."""
    return xxh64(path.lower().encode('ascii'), 0)

# ---- minimal FlatBuffers reader ----
class FB:
    def __init__(self, buf):
        self.buf = buf
        self.root = struct.unpack_from('<I', buf, 0)[0]
    def _u16(self, o): return struct.unpack_from('<H', self.buf, o)[0]
    def _i32(self, o): return struct.unpack_from('<i', self.buf, o)[0]
    def _u32(self, o): return struct.unpack_from('<I', self.buf, o)[0]
    def _u64(self, o): return struct.unpack_from('<Q', self.buf, o)[0]
    def table_field(self, table, idx):
        vtable = table - self._i32(table)
        vsize = self._u16(vtable)
        entry = 4 + idx*2
        if entry + 2 > vsize: return None
        rel = self._u16(vtable + entry)
        if rel == 0: return None
        return table + rel
    def string_at(self, off):
        o = off + self._u32(off)
        n = self._u32(o)
        return self.buf[o+4:o+4+n].decode('utf-8', 'replace')
    def vector(self, table, idx, elem_size=4):
        fp = self.table_field(table, idx)
        if fp is None: return None
        o = fp + self._u32(fp)
        n = self._u32(o)
        return o + 4, n
    def struct_vector_data(self, table, idx, elem_size):
        r = self.vector(table, idx, elem_size)
        if r is None: return None, 0
        off, n = r
        return off, n

def parse_index(path):
    buf = open(path, 'rb').read()
    fb = FB(buf)
    root = fb.root
    out = {}
    out['codename'] = fb.string_at(fb.table_field(root, 0)) if fb.table_field(root,0) is not None else None
    f1 = fb.table_field(root, 1); out['num_archives'] = fb._u16(f1) if f1 else 0
    f2 = fb.table_field(root, 2); out['xxhash_seed'] = fb._u16(f2) if f2 else 0
    # vectors
    out['archive_file_hashes'] = []
    off, n = fb.struct_vector_data(root, 3, 8)
    if off: out['archive_file_hashes'] = [struct.unpack_from('<Q', buf, off+i*8)[0] for i in range(n)]
    out['file_to_chunk'] = []  # (chunk_index, file_size, offset_in_chunk)
    off, n = fb.struct_vector_data(root, 4, 12)
    if off:
        for i in range(n):
            b = off + i*12
            out['file_to_chunk'].append((fb._i32(b), fb._u32(b+4), fb._u32(b+8)))
    out['chunks'] = []  # (file_offset, size, uncomp_size, align, data_file_number)
    off, n = fb.struct_vector_data(root, 5, 24)
    if off:
        for i in range(n):
            b = off + i*24
            out['chunks'].append((fb._u64(b), fb._u32(b+8), fb._u32(b+12), fb._u32(b+16), fb.buf[b+22]))
    out['external_file_hashes'] = []
    off, n = fb.struct_vector_data(root, 6, 8)
    if off: out['external_file_hashes'] = [struct.unpack_from('<Q', buf, off+i*8)[0] for i in range(n)]
    return out

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    idx = parse_index(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i')
    print('codename:', idx['codename'])
    print('num_archives:', idx['num_archives'], 'xxhash_seed:', idx['xxhash_seed'])
    print('archive file hashes:', len(idx['archive_file_hashes']))
    print('file_to_chunk:', len(idx['file_to_chunk']))
    print('chunks:', len(idx['chunks']))
    print('external file hashes:', len(idx['external_file_hashes']))
    # find table files
    import bisect
    table_paths = [
        'system/table/skill.tbl','system/table/skill_status.tbl','system/table/gem.tbl',
        'system/table/chara_gem.tbl','system/table/skill_level_lot.tbl','system/table/skill_lot.tbl',
        'system/table/skill_type_lot.tbl','system/table/weapon_skill_level.tbl',
        'system/table/gem_rare.tbl','system/table/gem_ticket.tbl','system/table/gem_sell.tbl',
        'system/table/gem_mix.tbl','system/table/gem_mix_rupi.tbl','system/table/gem_mix_success.tbl',
        'system/table/ability.tbl','system/table/constant.tbl','system/table/gem_mix_ticket.tbl',
        'system/table/gem_type.tbl',
    ]
    hashes = idx['archive_file_hashes']
    print()
    for p in table_paths:
        h = gbfr_file_hash(p)
        i = bisect.bisect_left(hashes, h)
        if i < len(hashes) and hashes[i] == h:
            f2c = idx['file_to_chunk'][i]
            print(f'FOUND {p} hash={h:016X} chunk={f2c[0]} size={f2c[1]} off_in_chunk={f2c[2]}')
        else:
            print(f'miss  {p} hash={h:016X}')
    # dump a few unknown hashes to see the range / try common prefixes
    print()
    print('first 10 archive hashes:', ['%016X' % h for h in hashes[:10]])
