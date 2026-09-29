#!/usr/bin/env python3
from generator.content_source_policy import allowed_sources
from generator.production_router import pools,render

def main():
    assert set(allowed_sources('VanillaOnly'))=={'VANILLA'}
    assert set(allowed_sources('ModAuthorOnly'))=={'MOD_AUTHOR'}
    assert set(allowed_sources('Everything'))=={'VANILLA','MOD_AUTHOR','CONSTRUCTION_PRINTER'}
    v=pools('VanillaOnly');m=pools('ModAuthorOnly');e=pools('Everything')
    assert len(v['hat'])==8 and len(v['shirt'])==8
    assert all(x['provenance']=='VANILLA' for k in ('hat','shirt') for x in v[k])
    assert len(m['hat'])==20 and len(m['shirt'])==0
    assert all(x['provenance']=='MOD_AUTHOR' for k in ('hat','shirt') for x in m[k])
    assert len(e['hat'])==28 and len(e['shirt'])==8
    vr=render(v['hat'][0]); assert vr['provenance']=='VANILLA' and vr['productionAuthority']=='STARDEW_SOURCE_PIXELS_FIRST'
    mr=render(m['hat'][0]); assert mr['provenance']=='MOD_AUTHOR' and mr['productionAuthority']=='GOLDEN_SOURCE_RESPECTING_HYBRID_V1'
    print('PASS content-source routing: VanillaOnly=8 hats+8 shirts; ModAuthorOnly=20 hats; Everything=28 hats+8 shirts')
if __name__=='__main__':main()
