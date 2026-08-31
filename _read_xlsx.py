# -*- coding: utf-8 -*-
"""Minimal xlsx reader (stdlib only). Usage: python _read_xlsx.py <file> [sheet_name_or_index]"""
import zipfile, re, sys, xml.etree.ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
RNS = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

def col_to_idx(col):
    n = 0
    for c in col:
        n = n * 26 + (ord(c) - 64)
    return n - 1

def load(path):
    z = zipfile.ZipFile(path)
    # shared strings
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        root = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in root.findall(f'{NS}si'):
            text = ''.join(t.text or '' for t in si.iter(f'{NS}t'))
            shared.append(text)
    # workbook sheets
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    relmap = {r.get('Id'): r.get('Target') for r in rels}
    sheets = []
    for s in wb.find(f'{NS}sheets'):
        rid = s.get(f'{RNS}id')
        target = relmap[rid].lstrip('/')
        if not target.startswith('xl/'):
            target = 'xl/' + target
        sheets.append((s.get('name'), target))
    return z, shared, sheets

def read_sheet(z, shared, target):
    root = ET.fromstring(z.read(target))
    rows = []
    for row in root.iter(f'{NS}row'):
        cells = {}
        maxc = -1
        for c in row.findall(f'{NS}c'):
            ref = c.get('r', 'A1')
            col = col_to_idx(re.match(r'([A-Z]+)', ref).group(1))
            maxc = max(maxc, col)
            t = c.get('t')
            v = c.find(f'{NS}v')
            is_ = c.find(f'{NS}is')
            f_ = c.find(f'{NS}f')
            if t == 's' and v is not None:
                val = shared[int(v.text)]
            elif t == 'inlineStr' and is_ is not None:
                val = ''.join(x.text or '' for x in is_.iter(f'{NS}t'))
            elif v is not None and v.text:
                val = v.text
            elif f_ is not None and f_.text:
                val = f_.text
            else:
                val = ''
            cells[col] = val
        if maxc >= 0:
            rows.append([cells.get(i, '') for i in range(maxc + 1)])
        else:
            rows.append([])
    return rows

if __name__ == '__main__':
    path = sys.argv[1]
    z, shared, sheets = load(path)
    if len(sys.argv) < 3:
        for i, (name, _) in enumerate(sheets):
            print(i, name)
    else:
        arg = sys.argv[1+1]
        idx = None
        for i, (name, _) in enumerate(sheets):
            if name == arg or str(i) == arg:
                idx = i; break
        if idx is None:
            print('sheet not found:', arg); sys.exit(1)
        name, target = sheets[idx]
        rows = read_sheet(z, shared, target)
        maxr = int(sys.argv[3]) if len(sys.argv) > 3 else len(rows)
        for r in rows[:maxr]:
            print('\t'.join(str(x) for x in r))
