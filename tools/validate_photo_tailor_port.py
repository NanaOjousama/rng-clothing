#!/usr/bin/env python3
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from generator.photo_tailor_port import canonical_u,view_u_from_canonical,build_shade_ramp
from generator.cap_photo_tailor_pipeline import render_cap_family

def main():
    assert abs(canonical_u('right',0.0)-0.45)<1e-9
    assert abs(canonical_u('left',0.0)-0.55)<1e-9
    assert abs(canonical_u('back',0.2)-0.8)<1e-9
    assert abs(view_u_from_canonical('right',0.45)-0.0)<1e-9
    assert view_u_from_canonical('right',0.2) is None
    assert len(build_shade_ramp((120,100,80)))==5
    out=Path('experiments/cap_photo_tailor_port_batch_01')
    assert (out/'CAP_PT_PORT_CONTACT_X10.png').exists()
    assert json.loads((out/'rejected.json').read_text())==[]
    print('PASS Photo Tailor direct-code port + cap QC batch')

if __name__=='__main__': main()
