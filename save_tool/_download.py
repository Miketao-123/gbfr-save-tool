import urllib.request, tarfile, io, sys, os, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
url = 'https://github.com/xcier/GBFR-Save-Editor/archive/refs/heads/main.tar.gz'
dst = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_gbfr-save-editor.tar.gz'
print('downloading...')
urllib.request.urlretrieve(url, dst)
print('downloaded', os.path.getsize(dst))
# extract
outdir = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor'
if os.path.exists(outdir): shutil.rmtree(outdir)
with tarfile.open(dst) as tf:
    tf.extractall(outdir)
print('extracted to', outdir)
for root, dirs, files in os.walk(outdir):
    for f in files:
        if f.endswith('.py'):
            print(os.path.relpath(os.path.join(root,f), outdir))
