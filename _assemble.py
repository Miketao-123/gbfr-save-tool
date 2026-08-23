# -*- coding: utf-8 -*-
"""把 qwen 生成的各分块方法拼接进 gbfr_gui_new.py 骨架,输出最终 gbfr_gui.py。

用法: python _assemble.py <chunk1> [chunk2] ...
"""
import re
import sys

SKELETON = "save_tool/gbfr_gui_new.py"
OUT = "save_tool/gbfr_gui.py"


def parse_methods(text):
    """从分块文本提取 {方法名: 方法块行列表}。方法以 4 空格缩进或 0 缩进的 def 开头,
    到下一个同级别 def 或文件结束为止。"""
    methods = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r'^(?:    )?def (\w+)\(', lines[i])
        if m:
            name = m.group(1)
            block = [lines[i]]
            i += 1
            while i < len(lines):
                if re.match(r'^(?:    )?def \w+\(', lines[i]):
                    break
                block.append(lines[i])
                i += 1
            methods[name] = block
        else:
            i += 1
    return methods


def main():
    skel = open(SKELETON, encoding='utf-8').read().split("\n")
    merged = {}
    for cf in sys.argv[1:]:
        with open(cf, encoding='utf-8') as f:
            merged.update(parse_methods(f.read()))
    out = []
    i = 0
    replaced = set()
    while i < len(skel):
        m = re.match(r'^    def (\w+)\(', skel[i])
        if m and m.group(1) in merged:
            name = m.group(1)
            j = i
            while j < len(skel) and 'raise NotImplementedError' not in skel[j]:
                j += 1
            if j >= len(skel):
                print(f"WARN: no stub end for {name}")
                out.append(skel[i])
                i += 1
                continue
            block = merged[name]
            # 去掉块尾多余空行,保留一个
            while block and block[-1].strip() == '':
                block.pop()
            # 归一化缩进:让 def 行落在 4 空格(类方法),其余行按相对缩进平移
            def_indent = len(block[0]) - len(block[0].lstrip(' '))
            shift = 4 - def_indent
            if shift:
                block = [(' ' * shift + ln) if ln.strip() else '' for ln in block]
            out.extend(block)
            out.append('')
            i = j + 1
            replaced.add(name)
        else:
            out.append(skel[i])
            i += 1
    missing = [n for n in merged if n not in replaced]
    if missing:
        print("NOT REPLACED:", missing)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write("\n".join(out))
    print(f"replaced {len(replaced)} methods -> {OUT}")


if __name__ == '__main__':
    main()
