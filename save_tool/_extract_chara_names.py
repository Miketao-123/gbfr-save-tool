# -*- coding: utf-8 -*-
"""纯 Python(零依赖)从 data.i 提取角色名表 text_chara.msg(中/英),生成 PL->名字 映射。
用法: python _extract_chara_names.py <data.i 路径>
输出: _chara_names.json  (PLxxxx -> {"cn": ..., "en": ...})
"""
import io, os, struct, sys, json, bisect

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbfr_datai import parse_index, gbfr_file_hash

# ---------------- 纯 Python lz4 block 解压 ----------------
def _lz4_block(src, uncompressed_size):
    dst = bytearray()
    i = 0
    n = len(src)
    while i < n and len(dst) < uncompressed_size:
        token = src[i]; i += 1
        lit_len = token >> 4
        if lit_len == 15:
            while True:
                b = src[i]; i += 1
                lit_len += b
                if b != 255: break
        end = i + lit_len
        if end > n: end = n
        dst += src[i:end]; i = end
        if i >= n: break
        off = src[i] | (src[i+1] << 8); i += 2
        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while True:
                b = src[i]; i += 1
                match_len += b
                if b != 255: break
        start = len(dst) - off
        for _ in range(match_len):
            dst.append(dst[start]); start += 1
    return bytes(dst[:uncompressed_size])

def lz4_decompress(raw, uncompressed_size):
    # 兼容带 4 字节小端大小前缀与不带前缀两种形式
    if len(raw) >= 4 and struct.unpack_from('<I', raw, 0)[0] == uncompressed_size:
        raw = raw[4:]
    try:
        out = _lz4_block(raw, uncompressed_size)
        if len(out) == uncompressed_size:
            return out
    except Exception:
        pass
    # 尝试不带前缀(已经是)
    out = _lz4_block(raw, uncompressed_size)
    return out

# ---------------- 纯 Python msgpack 解码 ----------------
class Unpacker:
    def __init__(self, buf):
        self.b = buf; self.i = 0; self.depth = 0
    def _take(self, n):
        v = self.b[self.i:self.i+n]; self.i += n; return v
    def unpack(self):
        self.depth += 1
        if self.depth > 300:
            raise ValueError('nesting too deep at offset %d (byte 0x%02X)' % (self.i - 1, self.b[self.i-1]))
        try:
            return self._unpack1()
        finally:
            self.depth -= 1
    def _unpack1(self):
        c = self.b[self.i]; self.i += 1
        if c <= 0x7f: return c
        if c >= 0xe0: return c - 0x100
        if 0x80 <= c <= 0x8f:
            return {self.unpack(): self.unpack() for _ in range(c & 0x0f)}
        if 0x90 <= c <= 0x9f:
            return [self.unpack() for _ in range(c & 0x0f)]
        if 0xa0 <= c <= 0xbf:
            return self._take(c & 0x1f).decode('utf-8', 'replace')
        if c == 0xc0: return None
        if c == 0xc2: return False
        if c == 0xc3: return True
        if c == 0xc4: return self._take(self._u(1))
        if c == 0xc5: return self._take(self._u(2))
        if c == 0xc6: return self._take(self._u(4))
        if c == 0xca: return struct.unpack('>f', self._take(4))[0]
        if c == 0xcb: return struct.unpack('>d', self._take(8))[0]
        if c == 0xcc: return self._u(1)
        if c == 0xcd: return self._u(2)
        if c == 0xce: return self._u(4)
        if c == 0xcf: return self._u(8)
        if c == 0xd0: return self._s(1)
        if c == 0xd1: return self._s(2)
        if c == 0xd2: return self._s(4)
        if c == 0xd3: return self._s(8)
        if c == 0xd9: return self._take(self._u(1)).decode('utf-8', 'replace')
        if c == 0xda: return self._take(self._u(2)).decode('utf-8', 'replace')
        if c == 0xdb: return self._take(self._u(4)).decode('utf-8', 'replace')
        if c == 0xdc: return [self.unpack() for _ in range(self._u(2))]
        if c == 0xdd: return [self.unpack() for _ in range(self._u(4))]
        if c == 0xde: return {self.unpack(): self.unpack() for _ in range(self._u(2))}
        if c == 0xdf: return {self.unpack(): self.unpack() for _ in range(self._u(4))}
        raise ValueError('unknown msgpack byte 0x%02X at %d' % (c, self.i - 1))
    def _u(self, n): return int.from_bytes(self._take(n), 'big')
    def _s(self, n): return int.from_bytes(self._take(n), 'big', signed=True)

def msgpack_load(raw):
    u = Unpacker(raw)
    obj = u.unpack()
    return obj

# ---------------- 主流程 ----------------
def extract_file(idx, path):
    h = gbfr_file_hash(path)
    hashes = idx['archive_file_hashes']
    i = bisect.bisect_left(hashes, h)
    if i >= len(hashes) or hashes[i] != h:
        return None
    f2c = idx['file_to_chunk'][i]
    chunk = idx['chunks'][f2c[0]]
    with open(os.path.join(os.path.dirname(data_i), 'data.%d' % chunk[4]), 'rb') as f:
        f.seek(chunk[0]); raw = f.read(chunk[1])
    if chunk[2] != chunk[1]:
        raw = lz4_decompress(raw, chunk[2])
    return raw[f2c[2]:f2c[2]+f2c[1]]

def dump_rows(obj):
    rows = obj.get('rows_', [])
    out = []
    for r in rows:
        col = r.get('column_', {})
        kid = col.get('id_hash_', '')
        sub = col.get('subid_hash_', '')
        txt = col.get('text_', '')
        if isinstance(txt, (bytes, bytearray)):
            try: txt = txt.decode('utf-8', 'replace')
            except Exception: txt = repr(txt)
        out.append((kid, sub, txt))
    return out

def main(data_i):
    idx = parse_index(data_i)
    print('index ok, files:', len(idx['archive_file_hashes']))
    cn_raw = extract_file(idx, 'system/table/text/cs/text_chara.msg')
    en_raw = extract_file(idx, 'system/table/text/en/text_chara.msg')
    print('cs/text_chara.msg bytes:', len(cn_raw) if cn_raw else None)
    print('en/text_chara.msg bytes:', len(en_raw) if en_raw else None)
    if cn_raw is None or en_raw is None:
        print('[错误] 提取失败'); return
    cn_rows = dump_rows(msgpack_load(cn_raw))
    en_rows = dump_rows(msgpack_load(en_raw))
    print('cs rows:', len(cn_rows), ' en rows:', len(en_rows))
    # 打印前 60 行看结构
    for kid, sub, txt in cn_rows[:60]:
        print('CN %-28s sub=%s  %s' % (kid[:28], sub, txt))
    print('...')
    for kid, sub, txt in en_rows[:60]:
        print('EN %-28s sub=%s  %s' % (kid[:28], sub, txt))

if __name__ == '__main__':
    data_i = sys.argv[1] if len(sys.argv) > 1 else r'I:\STEAM\steamapps\common\Granblue Fantasy Relink\data.i'
    main(data_i)
