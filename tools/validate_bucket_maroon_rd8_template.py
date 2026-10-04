#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
manifest=json.loads((ROOT/'authored/templates/bucket_maroon_rd8/frame_manifest.json').read_text())
contract=json.loads((ROOT/'generator/data/templates/bucket_maroon_rd8.json').read_text())
assert manifest['id']=='bucket_maroon_rd8'
assert contract['id']=='bucket_maroon_rd8'
assert manifest['runtimeAuthority']==['front','right','back','left']
assert set(manifest['evidenceOnly'])=={'front_right','back_right','back_left','front_left'}
for name,rec in manifest['frames'].items():
 p=ROOT/rec['path']; im=Image.open(p).convert('RGBA')
 assert im.size==(24,24), (name,im.size)
 assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']
 assert hashlib.sha256(im.getchannel('A').tobytes()).hexdigest()==rec['alphaSha256']
 assert rec['nativeTightSize'][0]<=24 and rec['nativeTightSize'][1]<=24
reg=json.loads((ROOT/'generator/data/templates/index.json').read_text())['templates']['bucket_maroon_rd8']
assert reg['humanArtApprovalRequired'] is True and reg['esmWearApprovalRequired'] is True
print('PASS bucket_maroon_rd8: 8/8 pinned, pad-only 24x24, 4 cardinal runtime authority, 4 diagonal evidence views, promotion gates closed')