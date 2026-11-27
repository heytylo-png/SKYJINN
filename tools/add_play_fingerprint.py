# Add Google Play's app signing key fingerprint to .well-known/assetlinks.json (keeps the upload key's).
#   python3 tools/add_play_fingerprint.py AB:CD:...   (Play Console > Test and release > App integrity > App signing)
import json, re, sys
fp = sys.argv[1].strip().upper()
assert re.fullmatch(r'([0-9A-F]{2}:){31}[0-9A-F]{2}', fp), 'expected a SHA-256 fingerprint like AB:CD:...(32 pairs)'
p = '.well-known/assetlinks.json'; d = json.load(open(p))
fps = d[0]['target']['sha256_cert_fingerprints']
if fp not in fps: fps.append(fp)
json.dump(d, open(p, 'w'), indent=2); print('fingerprints:', fps)
