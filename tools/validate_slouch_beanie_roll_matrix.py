#!/usr/bin/env python3
import json
from pathlib import Path

PATH=Path('generator/data/headwear/slouch_beanie_roll_matrix.json')
required_axes=['presentationLean','slouchDepth','bandType','drapeDirection','crownShape','openingFit','knitStructure','pattern','motif','carrierStyle','decorationStyle','motifPlacement','attachment','hardwareAccent']

def main():
    data=json.loads(PATH.read_text())
    assert data['id']=='slouch_beanie_v1'
    axes=data['axes']
    for name in required_axes:
        assert name in axes, f'missing axis {name}'
        vals=axes[name]
        assert vals and all(isinstance(v,int) and v>0 for v in vals.values()), f'bad weights in {name}'
    assert data['reference']['role']=='CONSTRUCTION_ONLY'
    assert data['reference']['cardinalFrames']=={'front':0,'right':2,'back':4,'left':6}
    assert data['exclusions'], 'no exclusions defined'
    asset_path=Path(data['assetLibrary'])
    assert asset_path.exists(), f'missing asset library {asset_path}'
    lib=json.loads(asset_path.read_text())
    assets=lib['assets']
    for key,asset in assets.items():
        ap=Path(asset['path']); assert ap.exists(), f'missing asset {key}: {ap}'
    for roll_key,asset_key in data.get('assetBindings',{}).items():
        assert asset_key in assets, f'asset binding {roll_key} -> {asset_key} missing'
    assert {'pom_small','pom_large'}.issubset(assets), 'pom attachments missing'
    assert {'patch_rect','side_label','stitched_badge'}.issubset(assets), 'carrier assets missing'
    # Hard guard: no-band results may not use cuff-only placements.
    no_band=next(r for r in data['exclusions'] if r.get('when')=={'bandType':'none'})
    cuff_places={'cuff_front_center','cuff_front_offset_left','cuff_front_offset_right','cuff_side_left','cuff_side_right','cuff_back_center'}
    assert cuff_places.issubset(set(no_band['disallow']['motifPlacement']))
    # Presentation is a soft preference only, never a gender lock.
    assert all(v.get('avoidHardLocks') is True for v in data['presentationModifiers'].values())
    print('PASS slouch beanie roll matrix')
    print(f"axes={len(required_axes)} exclusions={len(data['exclusions'])}")

if __name__=='__main__':
    main()
