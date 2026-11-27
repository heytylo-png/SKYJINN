#!/usr/bin/env python3
"""Embed art/sfx/sfx_<category>_<n>.mp3 into index.html as SFX_DATA = {category: [base64, ...]}.

Run from the repo root:  python3 tools/sfx.py
Re-running replaces the existing SFX_DATA line.
"""
import base64, glob, json, os, re

files = sorted(glob.glob('art/sfx/sfx_*.mp3'))
data = {}
for f in files:
    m = re.match(r'sfx_(.+)_(\d+)\.mp3$', os.path.basename(f))
    if not m:
        continue
    data.setdefault(m.group(1), []).append((int(m.group(2)), base64.b64encode(open(f, 'rb').read()).decode()))
data = {k: [b for _, b in sorted(v)] for k, v in data.items()}
line = 'const SFX_DATA=' + json.dumps(data, separators=(',', ':')) + ';\n'
p = 'index.html'
s = open(p).read()
if 'const SFX_DATA=' in s:
    s = re.sub(r'const SFX_DATA=.*?;\n', lambda _: line, s, count=1, flags=re.S)
else:
    i = s.index('const TOWER_DATA=')
    s = s[:i] + line + s[i:]
open(p, 'w').write(s)
print({k: len(v) for k, v in data.items()}, f'{len(line)/1024:.0f} KB')
