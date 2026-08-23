# -*- coding: utf-8 -*-
"""本地 qwen 大模型调用助手(OpenAI 兼容接口, LM Studio @127.0.0.1:1234)。

用法:
    python _llm.py <输出文件> <提示文件> [--system <文件>] [--max-tokens N] [--append]

- 提示文件/系统提示文件均为 UTF-8 文本;提示文件里可用 {FILE:路径} 占位符
  把任意本地文件内容嵌入(用于喂代码上下文)。
- --append 追加写入输出文件(分块生成同一文件用)。
- 输出为 UTF-8;若模型返回被 ``` 围栏包裹的代码块则自动去除围栏。
- 失败自动重试,每次尝试前更换随机 nonce 并递增退避。
注意:不要用空字符串占位参数(会被命令行吞掉),用命名参数。
"""
import sys
import os
import json
import time
import urllib.request

API = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen3.8-27b"


def load_prompt(path):
    """支持 {FILE:path} 占位符嵌入文件内容。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    out = []
    i = 0
    while True:
        j = text.find("{FILE:", i)
        if j < 0:
            out.append(text[i:])
            break
        out.append(text[i:j])
        k = text.find("}", j)
        if k < 0:
            out.append(text[j:])
            break
        fpath = text[j + 6:k].strip()
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf-8") as fp:
                out.append(fp.read())
        else:
            out.append("<!-- FILE NOT FOUND: %s -->" % fpath)
        i = k + 1
    return "".join(out)


def strip_fence(s):
    s = s.strip()
    if s.startswith("```"):
        # 去掉第一行围栏(可能带语言标记)
        lines = s.split("\n")
        lines = lines[1:]
        # 去掉结尾围栏
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return s


def call(system, user, max_tokens):
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    # 随机 nonce 注释,避免服务器端对重复请求的短路/缓存
    user = user + "\n\n# [request-nonce: %s]\n" % os.urandom(6).hex()
    msgs.append({"role": "user", "content": user})
    body = json.dumps({
        "model": MODEL,
        "messages": msgs,
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=1800) as resp:
            r = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError("HTTP %s: %s" % (e.code, e.read()[:500]))
    msg = r["choices"][0]["message"]
    content = msg.get("content") or ""
    usage = r.get("usage", {})
    comp = usage.get("completion_tokens", 0)
    if comp >= max_tokens - 32:
        # 生成本次输出达到 token 预算上限,可能被截断(模型思考过长),视为失败重试
        raise RuntimeError("possibly truncated (completion=%d ~ max_tokens=%d)" % (comp, max_tokens))
    if not content.strip():
        raise RuntimeError("empty content; msg keys=%s usage=%s"
                           % (list(msg.keys()), usage))
    return content, usage


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    outfile = sys.argv[1]
    prompt_file = sys.argv[2]
    system_file = None
    max_tokens = 16000
    append = False
    rest = sys.argv[3:]
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == '--system' and i + 1 < len(rest):
            system_file = rest[i + 1]
            i += 2
        elif a == '--max-tokens' and i + 1 < len(rest):
            max_tokens = int(rest[i + 1])
            i += 2
        elif a == '--append':
            append = True
            i += 1
        else:
            i += 1

    user = load_prompt(prompt_file)
    system = load_prompt(system_file) if system_file else "你是资深 Python 桌面应用开发工程师,精通 tkinter/ttk 暗色主题设计与 Windows 打包。输出严格按要求,不要额外解释。"

    last_err = None
    for attempt in range(6):
        try:
            t0 = time.time()
            content, usage = call(system, user, max_tokens)
            dt = time.time() - t0
            n = usage.get("completion_tokens", 0)
            print(f"[llm] {n} tokens in {dt:.1f}s ({n/dt:.1f} tok/s) -> {outfile}", flush=True)
            content = strip_fence(content)
            if not content.strip():
                raise RuntimeError("empty content")
            with open(outfile, "a" if append else "w", encoding="utf-8") as f:
                if append:
                    # 确保与已有内容之间用换行分隔
                    if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
                        f.write("\n")
                f.write(content)
            print(f"[llm] written {len(content)} chars", flush=True)
            return
        except Exception as e:
            last_err = e
            print(f"[llm] attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(5 + attempt * 5)
    print(f"[llm] FAILED: {last_err}", flush=True)
    sys.exit(1)


if __name__ == "__main__":
    main()
