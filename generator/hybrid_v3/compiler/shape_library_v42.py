"""Executable V4.2 component-local shape library for the three-family proof."""
from __future__ import annotations

import json
from pathlib import Path

from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER

ROOT = Path(__file__).resolve().parents[3]
SHAPES = ROOT / "specs/garment_grammar_v4/component_shape_variants.json"
VANILLA_PLUS_SHAPES = ROOT / "specs/garment_grammar_v4/vanilla_plus_micro_shapes.json"
ENVELOPES = ROOT / "specs/garment_grammar_v4/safe_envelopes.json"
VISIBLE = {"FULL", "COMPRESSED", "DEPTH_ONLY", "EDGE_ONLY"}


class ShapeLibraryV42:
    def __init__(self, *, document_path=SHAPES):
        self.document_path = Path(document_path)
        self.document = json.loads(self.document_path.read_text(encoding="utf-8"))
        required = set(self.document["variantContract"]["required"])
        self.variants = {}
        for variant in self.document["variants"]:
            missing = required - set(variant)
            if missing:
                raise ValueError(f"shape variant {variant.get('variantId')} missing {sorted(missing)}")
            self.variants[variant["variantId"]] = variant
        self.envelope_document = json.loads(ENVELOPES.read_text(encoding="utf-8"))

    @property
    def schema_version(self):
        return self.document["schemaVersion"]

    def safe_envelope(self, family):
        matches = [v for v in self.envelope_document["proofEnvelopes"].values() if v["family"] == family]
        if not matches:
            return {d: set() for d in DIRECTION_ORDER}
        result = {d:set() for d in DIRECTION_ORDER}
        for direction, spans in matches[0]["directions"].items():
            for y, lo, hi in spans:
                result[direction].update((x,y) for x in range(lo,hi+1))
        return result

    def emit(self, variant_id, component, projections, *, topology, draw, system):
        variant = self.variants[variant_id]
        component_owner = variant.get("ownership", {}).get("componentOwner", component["instanceId"])
        family_ok = component["definitionId"] in variant["compatibleComponentIds"]
        if not family_ok:
            raise ValueError(f"{variant_id} incompatible with {component['definitionId']}")
        emitted = {d:set() for d in DIRECTION_ORDER}
        for direction in variant["allowedDirections"]:
            if projections[direction]["visibility"] not in VISIBLE:
                continue
            geometry = variant["directionGeometry"].get(direction, {})
            anchor = geometry.get("anchor")
            if anchor is None:
                continue
            ax, ay = anchor
            for op, dx, dy in variant["alphaOperations"].get(direction, []) if isinstance(variant["alphaOperations"], dict) else ():
                x,y=ax+dx,ay+dy
                kwargs=dict(component_owner=component_owner, variant_id=variant_id, system=system, semantic_region=system)
                if op == "ADD": topology.add(direction,x,y,shade="BASE",**kwargs)
                elif op == "REMOVE": topology.remove(direction,x,y,**kwargs)
                else: raise ValueError(f"unsupported topology operation {op}")
            for dx,dy,shade,fabric in geometry.get("semanticCells", []):
                x,y=ax+dx,ay+dy
                if draw(component_owner,system,direction,x,y,shade,fabric):
                    emitted[direction].add((x,y))
        return {"variantId":variant_id,"emitted":{d:len(c) for d,c in emitted.items()},"minimumIdentityCells":variant["minimumIdentityCells"]}

    def emit_knit_hem(self, variant_id, component, projections, *, frames, bounds, draw):
        variant=self.variants[variant_id]; emitted={d:0 for d in DIRECTION_ORDER}
        for direction in variant["allowedDirections"]:
            if projections[direction]["visibility"] not in VISIBLE: continue
            occupied=[y for y,row in enumerate(frames[direction]) if any(p[3] for p in row)]
            if not occupied: continue
            y=max(occupied); edge=bounds(frames[direction],y)
            if not edge: continue
            lo,hi=edge
            for x in range(lo+1,hi):
                draw(component["instanceId"],"hem",direction,x,y,"SHADOW" if (x-lo)%4==0 else "BASE","PrimaryFabric"); emitted[direction]+=1
        return {"variantId":variant_id,"emitted":emitted,"minimumIdentityCells":variant["minimumIdentityCells"]}

    def emit_vanilla_hem(self, variant_id, component, projections, *, frames, bounds, draw):
        """Emit two tiny local-color termination cues, never a waistband."""
        variant=self.variants[variant_id]; emitted={d:0 for d in DIRECTION_ORDER}
        owner=variant.get("ownership",{}).get("componentOwner",component["instanceId"])
        for direction in variant["allowedDirections"]:
            if projections[direction]["visibility"] not in VISIBLE: continue
            occupied=[y for y,row in enumerate(frames[direction]) if any(p[3] for p in row)]
            if not occupied: continue
            y=max(occupied); edge=bounds(frames[direction],y)
            if not edge or edge[1]-edge[0] < 5: continue
            lo,hi=edge
            for x,shade in ((lo+1,"SHADOW"),(lo+2,"BASE"),(hi-2,"BASE"),(hi-1,"SHADOW")):
                if draw(owner,"hem",direction,x,y,shade,"PrimaryFabric"):
                    emitted[direction]+=1
        return {"variantId":variant_id,"emitted":emitted,"minimumIdentityCells":variant["minimumIdentityCells"]}

    def emit_sailor_rear(self, variant_id, component, projections, *, draw):
        variant=self.variants[variant_id]; result=self.emit(variant_id,component,projections,topology=_NoTopology(),draw=draw,system="rear_panel")
        if projections["back"]["visibility"] in VISIBLE:
            shape=component["parameters"].get("shape","square")
            geometry=variant["directionGeometry"]["back"]; ax,ay=geometry["anchor"]
            widths=[(ax+lo,ax+hi) for lo,hi in geometry["rowProfiles"][shape]]
            count=0
            for row,(lo,hi) in enumerate(widths,ay):
                for x in range(lo,hi+1):
                    shade="STRUCTURAL_EDGE" if row==ay or x in {lo,hi} else ("BASE" if x<ax else "SHADOW")
                    draw(component["instanceId"],"rear_panel","back",x,row,shade,"Trim"); count+=1
            result["emitted"]["back"]=count
        return result


class _NoTopology:
    def add(self,*args,**kwargs): raise AssertionError("unexpected topology")
    def remove(self,*args,**kwargs): raise AssertionError("unexpected topology")
