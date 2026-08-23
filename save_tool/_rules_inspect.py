import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# check secondary-trait-rules.json content around the error point
raw = open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\secondary-trait-rules.json','rb').read()
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
s = raw.decode('utf-8','replace')
print('文件总长:', len(s))
print('=== 前 400 字符 ===')
print(s[:400])
print('=== 4962 附近(解析报错处) ===')
print(s[4800:5600])
print('=== 尾部 200 ===')
print(s[-200:])
