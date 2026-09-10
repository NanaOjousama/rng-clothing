"""Component handlers translating approved projections into V5/HD pixel signals.

These handlers never decide which components exist. They realize only the
canonical instances and visibility states supplied by Phase 1.
"""

from __future__ import annotations

from typing import Any

from generator.controlled_test.reference_guided import _bounds, _clear, _paint
from generator.renderers.fashionsense.hd_garment_v2 import DIRECTION_ORDER

from .semantic_regions import SemanticRegionLedger

VISIBLE = {"FULL", "COMPRESSED", "DEPTH_ONLY", "EDGE_ONLY"}
SAILOR_TECHNICAL_PROFILE = "V4_2_SAILOR_TECHNICAL_EXPERIMENT"
SAILOR_OUTLINE_PROFILE = "V4_2_SAILOR_OUTLINE_REFINEMENT"
VANILLA_PLUS_PROFILE = "V4_VANILLA_PLUS_PROOF"


def _draw(base, frames, defaults, ledger, instance, system, direction, x, y, shade, fabric="PrimaryFabric"):
    before = frames[direction][y][x][3] if 0 <= x < 16 and 0 <= y < 16 else 0
    _paint(base, frames, defaults, ledger.systems, ledger.fabrics, system, direction, x, y, shade, fabric)
    if before:
        ledger.record(instance, system, direction, (x, y), fabric)
        return True
    return False


def _erase(frames, defaults, ledger, instance, direction, x, y):
    if not (0 <= x < 16 and 0 <= y < 16 and frames[direction][y][x][3]):
        return
    ledger.record_clear(instance, direction, (x, y))
    _clear(frames, defaults, ledger.systems, ledger.fabrics, direction, x, y)
    for views in ledger.component_cells.values():
        views.get(direction, set()).discard((x, y))


def _components(frame):
    cells = {(x, y) for y, row in enumerate(frame) for x, pixel in enumerate(row) if pixel[3]}
    found = []
    while cells:
        root = cells.pop(); group = {root}; todo = [root]
        while todo:
            x, y = todo.pop()
            for nxt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if nxt in cells:
                    cells.remove(nxt); group.add(nxt); todo.append(nxt)
        found.append(group)
    return sorted(found, key=len, reverse=True)


def _body(component, projections, base, frames, defaults, ledger, *, shape_profile=None, **_):
    family = component["definitionId"]
    for direction in DIRECTION_ORDER:
        # BODY_KNIT_VEST's physical side body is the torso-connected mass.
        # Detached carrier caps are outside the canonical BODY/ARMHOLE graph
        # and are excluded here, before construction, polish, or coloring.
        if family == "BODY_KNIT_VEST" and direction in {"right", "left"}:
            groups = _components(frames[direction])
            for group in groups[1:]:
                for x, y in sorted(group):
                    _erase(frames, defaults, ledger, component["instanceId"], direction, x, y)
            # The canonical cut-in shoulder cannot cantilever sideways across
            # the atlas top. Require direct cloth support in row 1; this is a
            # BODY topology rule, not a final-sprite island cleanup.
            unsupported_top = [x for x, pixel in enumerate(frames[direction][0]) if pixel[3] and not frames[direction][1][x][3]]
            for x in unsupported_top:
                _erase(frames, defaults, ledger, component["instanceId"], direction, x, 0)
        for y, row in enumerate(frames[direction]):
            for x, pixel in enumerate(row):
                if pixel[3]:
                    ledger.record(component["instanceId"], "silhouette", direction, (x, y), "PrimaryFabric")
        # A few connected plane anchors preserve the proven HD light field and
        # make fit differences visible without changing the safe envelope.
        volume = component["parameters"].get("volume", "regular")
        if shape_profile == VANILLA_PLUS_PROFILE:
            continue
        for y in (6, 10):
            bounds = _bounds(frames[direction], y)
            if not bounds:
                continue
            lo, hi = bounds
            inset = 2 if volume in {"fitted", "regular"} else 1
            _draw(base, frames, defaults, ledger, component["instanceId"], "silhouette", direction, lo+inset, y, "LIGHT")
            _draw(base, frames, defaults, ledger, component["instanceId"], "silhouette", direction, hi-inset, y, "SHADOW")


def _inner(component, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_events=None, shape_profile=None, **_):
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        if direction == "front":
            cells = ((7,1),(8,1),(7,2),(8,2)) if component["definitionId"] == "INNER_LAYER_WOVEN_SHIRT" and shape_library is not None else ((7,1),(8,1),(6,2),(7,2),(8,2),(9,2),(7,3),(8,3))
        elif direction == "right":
            if component["definitionId"] == "INNER_LAYER_WOVEN_SHIRT" and shape_library is not None:
                continue
            cells = ((8,1),(9,1),(9,2))
        elif direction == "left":
            if component["definitionId"] == "INNER_LAYER_WOVEN_SHIRT" and shape_library is not None:
                continue
            cells = ((6,1),(7,1),(6,2))
        else:
            cells = ()
        for x, y in cells:
            _draw(base, frames, defaults, ledger, component["instanceId"], "inner_layer", direction, x, y, "LIGHT" if y < 2 else "BASE", "SecondaryFabric")
    if component["definitionId"] == "INNER_LAYER_WOVEN_SHIRT" and shape_library is not None:
        variant="VEST_INNER_SHIRT_VANILLA_A" if shape_profile==VANILLA_PLUS_PROFILE else "INNER_SHIRT_EXPOSURE_SIDE_V1"
        event=shape_library.emit(variant,component,projections,topology=topology,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric),system="inner_layer")
        shape_events.append(event)


def _collar(component, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_events=None, shape_profile=None, **_):
    """Render construction-first neckline grammar.

    V4 Pass 2 keeps collars shallow and readable at 16x16.  The shapes below
    are directional construction clusters, not arbitrary visibility tokens.
    They deliberately avoid long central Vs and full-width dark bands.
    """
    definition = component["definitionId"]
    params = component["parameters"]
    if shape_library is not None and shape_profile == VANILLA_PLUS_PROFILE:
        variants={
            "COLLAR_BOUND_CREW":(("TEE_CREW_BINDING_VANILLA_A","collar"),),
            "COLLAR_FOLDED_POLO":(("POLO_COLLAR_VANILLA_A","collar"),),
            "COLLAR_VEST_DEEP_V":(("VEST_V_BINDING_VANILLA_A","collar"),),
            "COLLAR_SAILOR_BROAD":(("SAILOR_COLLAR_VANILLA_A","collar"),("SAILOR_BOW_SMALL_A","tie")),
        }.get(definition)
        if variants is not None:
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric)
            for variant,system in variants:
                shape_events.append(shape_library.emit(variant,component,projections,topology=topology,draw=draw,system=system))
            if definition=="COLLAR_SAILOR_BROAD":
                ledger.record_runtime(component["instanceId"],"back","V4_VANILLA_PLUS_REAR_FLAP_COLLAR_HANDOFF")
            return
    if shape_library is not None and definition == "COLLAR_SAILOR_BROAD" and shape_profile in {SAILOR_TECHNICAL_PROFILE, SAILOR_OUTLINE_PROFILE}:
        draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric)
        variants = [
            ("SAILOR_COLLAR_FRONT_TECHNICAL_V1","collar"),
            ("SAILOR_COLLAR_SIDE_TECHNICAL_V1","collar"),
        ]
        if shape_profile == SAILOR_OUTLINE_PROFILE:
            variants += [
                ("SAILOR_COLLAR_FLAP_OUTLINE_REFINED_V1","collar_border"),
                ("SAILOR_FRONT_BOW_TIE_OUTLINE_REFINED_V1","tie"),
            ]
        else:
            variants += [
                ("SAILOR_COLLAR_BORDER_TECHNICAL_V1","collar_border"),
                ("SAILOR_FRONT_OPENING_OR_INSERT_V1","inner_layer"),
            ]
        for variant,system in variants:
            shape_events.append(shape_library.emit(variant,component,projections,topology=topology,draw=draw,system=system))
        ledger.record_runtime(component["instanceId"],"back","V4_2_TECHNICAL_REAR_FLAP_COLLAR_HANDOFF")
        return
    if shape_library is not None and definition in {"COLLAR_FOLDED_POLO","COLLAR_VEST_DEEP_V","COLLAR_SAILOR_BROAD"}:
        variants={
            "COLLAR_FOLDED_POLO":("FOLDED_POLO_COLLAR_FRONT_V1","FOLDED_POLO_COLLAR_SIDE_V1","FOLDED_POLO_COLLAR_BACK_V1"),
            "COLLAR_VEST_DEEP_V":("V_BINDING_FRONT_V1","V_BINDING_SIDE_V1","V_BINDING_BACK_V1"),
            "COLLAR_SAILOR_BROAD":("SAILOR_COLLAR_FRONT_V1","SAILOR_COLLAR_SIDE_V1","SAILOR_FRONT_OPENING_OR_INSERT_V1"),
        }[definition]
        draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric)
        for variant in variants:
            system="inner_layer" if variant=="SAILOR_FRONT_OPENING_OR_INSERT_V1" else "collar"
            shape_events.append(shape_library.emit(variant,component,projections,topology=topology,draw=draw,system=system))
        if definition == "COLLAR_SAILOR_BROAD" and projections["back"]["visibility"] in VISIBLE:
            ledger.record_runtime(component["instanceId"],"back","V4_2_SAILOR_REAR_PANEL_COLLAR_HANDOFF")
        return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        cells: list[tuple[int,int,str,str]] = []
        if definition == "COLLAR_BOUND_CREW":
            width = params.get("width", "medium")
            if direction == "front":
                cells = [(6,1,"LIGHT","Trim"),(7,1,"BASE","Trim"),(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim")]
                if width == "wide":
                    cells += [(5,2,"BASE","Trim"),(10,2,"SHADOW","Trim")]
            elif direction == "back":
                cells = [(6,1,"BASE","Trim"),(7,1,"BASE","Trim"),(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim")]
            elif direction == "right":
                cells = [(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim")]
            else:
                cells = [(6,1,"LIGHT","Trim"),(7,1,"BASE","Trim")]

        elif definition == "COLLAR_FOLDED_POLO":
            # Two compact leaves in front; a shallow rear band; a 2x2-ish
            # side fold.  No deep V and no vertical side stripe.
            if direction == "front":
                cells = [
                    (5,1,"LIGHT","Trim"),(6,1,"BASE","Trim"),(5,2,"STRUCTURAL_EDGE","Trim"),(6,2,"BASE","Trim"),
                    (10,1,"SHADOW","Trim"),(9,1,"BASE","Trim"),(10,2,"DEEP_CREASE","Trim"),(9,2,"SHADOW","Trim"),
                ]
            elif direction == "back":
                cells = [(6,1,"LIGHT","Trim"),(7,1,"BASE","Trim"),(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim"),
                         (7,2,"SHADOW","PrimaryFabric"),(8,2,"SHADOW","PrimaryFabric")]
            elif direction == "right":
                cells = [(8,1,"LIGHT","Trim"),(9,1,"BASE","Trim"),(8,2,"BASE","Trim"),(9,2,"SHADOW","Trim")]
            else:
                cells = [(6,1,"LIGHT","Trim"),(7,1,"BASE","Trim"),(6,2,"STRUCTURAL_EDGE","Trim"),(7,2,"BASE","Trim")]

        elif definition == "COLLAR_VEST_DEEP_V":
            # Readable V binding, but bounded to the upper chest.  The old
            # mapping descended too far and made every vest look deeply cut.
            if direction == "front":
                cells = [(5,1,"STRUCTURAL_EDGE","Trim"),(10,1,"STRUCTURAL_EDGE","Trim"),
                         (6,2,"BASE","Trim"),(9,2,"SHADOW","Trim"),
                         (7,3,"BASE","Trim"),(8,3,"SHADOW","Trim")]
            elif direction == "back":
                cells = [(6,1,"BASE","Trim"),(7,1,"LIGHT","Trim"),(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim")]
            elif direction == "right":
                cells = [(8,1,"BASE","Trim"),(9,1,"SHADOW","Trim"),(9,2,"BASE","Trim")]
            else:
                cells = [(6,1,"LIGHT","Trim"),(7,1,"BASE","Trim"),(6,2,"BASE","Trim")]

        elif definition == "COLLAR_SAILOR_BROAD":
            if direction == "front":
                cells = [(3,1,"LIGHT","Trim"),(4,1,"BASE","Trim"),(5,2,"BASE","Trim"),(6,3,"STRUCTURAL_EDGE","Trim"),
                         (12,1,"SHADOW","Trim"),(11,1,"BASE","Trim"),(10,2,"SHADOW","Trim"),(9,3,"STRUCTURAL_EDGE","Trim")]
            elif direction == "right":
                cells = [(9,1,"BASE","Trim"),(10,1,"SHADOW","Trim"),(10,2,"SHADOW","Trim")]
            elif direction == "left":
                cells = [(5,1,"LIGHT","Trim"),(6,1,"BASE","Trim"),(5,2,"BASE","Trim")]
            else:
                cells = [(5,1,"BASE","Trim"),(6,1,"LIGHT","Trim"),(7,2,"BASE","Trim"),(8,2,"BASE","Trim"),(9,1,"SHADOW","Trim"),(10,1,"BASE","Trim")]
        for x, y, shade, fabric in cells:
            _draw(base, frames, defaults, ledger, component["instanceId"], "collar", direction, x, y, shade, fabric)

def _sleeve(component, projections, base, frames, defaults, ledger, **_):
    for direction, item in projections.items():
        if item["visibility"] in VISIBLE:
            ledger.record_runtime(component["instanceId"], direction, "NATIVE_ANIMATED_SLEEVES_V1")
            bounds = _bounds(frames[direction], 4)
            if bounds:
                lo, hi = bounds
                _draw(base, frames, defaults, ledger, component["instanceId"], "sleeves", direction, lo+1, 4, "LIGHT")
                _draw(base, frames, defaults, ledger, component["instanceId"], "sleeves", direction, hi-1, 4, "SHADOW")


def _armhole(component, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_events=None, shape_profile=None, **_):
    """Narrow sleeveless binding; never a full-height dark side rail."""
    if component["definitionId"] == "ARMHOLE_BOUND_CUT_IN" and shape_library is not None:
        variant="VEST_CUTIN_ARMHOLE_VANILLA_A" if shape_profile==VANILLA_PLUS_PROFILE else "CUTIN_ARMHOLE_SIDE_V1"
        event=shape_library.emit(variant,component,projections,topology=topology,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric),system="armholes")
        shape_events.append(event)
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        if direction in {"front", "back"}:
            for y in range(2, 6):
                bounds = _bounds(frames[direction], y)
                if not bounds: continue
                lo, hi = bounds
                _draw(base, frames, defaults, ledger, component["instanceId"], "armholes", direction, lo, y, "BASE", "Trim")
                _draw(base, frames, defaults, ledger, component["instanceId"], "armholes", direction, hi, y, "SHADOW", "Trim")
        else:
            if component["definitionId"] == "ARMHOLE_BOUND_CUT_IN" and shape_library is not None:
                continue
            # A short upper binding cue only. Side torso below this belongs to
            # body form and must remain a clean fabric plane.
            for y in range(1, 5):
                bounds = _bounds(frames[direction], y)
                if not bounds: continue
                edge = bounds[0] if direction == "right" else bounds[1]
                shade = "SHADOW" if direction == "right" else "LIGHT"
                _draw(base, frames, defaults, ledger, component["instanceId"], "armholes", direction, edge, y, shade, "Trim")

def _opening(component, projections, base, frames, defaults, ledger, *, shape_library=None, **_):
    if component["definitionId"] == "OPENING_SHORT_POLO" and shape_library is not None:
        if projections["front"]["visibility"] in VISIBLE:
            ledger.record_runtime(component["instanceId"],"front","V4_2_SHORT_POLO_PLACKET_PARENT")
        return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        if component["definitionId"] == "OPENING_SHORT_POLO" and direction == "front":
            for x, y, shade in ((7,2,"STRUCTURAL_EDGE"),(8,2,"SHADOW"),(7,3,"BASE"),(8,3,"DEEP_CREASE")):
                _draw(base, frames, defaults, ledger, component["instanceId"], "opening", direction, x, y, shade, "Trim")


def _placket(component, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_events=None, shape_profile=None, **_):
    if component["definitionId"] == "PLACKET_POLO_SHORT" and shape_library is not None:
        variant="POLO_PLACKET_VANILLA_A" if shape_profile==VANILLA_PLUS_PROFILE else "SHORT_POLO_PLACKET_FRONT_V1"
        event=shape_library.emit(variant,component,projections,topology=topology,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric),system="placket")
        shape_events.append(event); return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        if direction == "front":
            for y in range(3, 6):
                _draw(base, frames, defaults, ledger, component["instanceId"], "placket", direction, 7, y, "STRUCTURAL_EDGE", "Trim")
                _draw(base, frames, defaults, ledger, component["instanceId"], "placket", direction, 8, y, "SHADOW", "Trim")
            for y in (3, 5)[:int(component["parameters"].get("buttons", 0))]:
                _draw(base, frames, defaults, ledger, component["instanceId"], "placket", direction, 8, y, "BASE", "Accent")


def _hem(component, projections, base, frames, defaults, ledger, *, shape_library=None, shape_events=None, shape_profile=None, **_):
    if component["definitionId"] == "HEM_KNIT_RIBBED" and shape_library is not None:
        draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric)
        if shape_profile==VANILLA_PLUS_PROFILE:
            event=shape_library.emit_vanilla_hem("VEST_HEM_VANILLA_A",component,projections,frames=frames,bounds=_bounds,draw=draw)
        else:
            event=shape_library.emit_knit_hem("KNIT_HEM_TERMINATION_V1",component,projections,frames=frames,bounds=_bounds,draw=draw)
        shape_events.append(event); return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        occupied = [y for y, row in enumerate(frames[direction]) if any(pixel[3] for pixel in row)]
        if not occupied: continue
        bottom = max(occupied)
        bounds = _bounds(frames[direction], bottom)
        if not bounds: continue
        lo, hi = bounds
        if component["definitionId"] == "HEM_KNIT_RIBBED":
            # Ribbed knit is the same garment fabric, not an arbitrary dark
            # contrast strip. Keep it one logical row at this scale.
            for x in range(lo+1, hi):
                shade = "SHADOW" if (x-lo) % 4 == 0 else "BASE"
                _draw(base, frames, defaults, ledger, component["instanceId"], "hem", direction, x, bottom, shade, "PrimaryFabric")
        else:
            # Light straight hem: only termination cues, never a full dark bar.
            for x in range(lo+2, hi-1):
                shade = "SHADOW" if x in {lo+2, hi-2} else "BASE"
                _draw(base, frames, defaults, ledger, component["instanceId"], "hem", direction, x, bottom, shade, "PrimaryFabric")

def _waistband(component, projections, base, frames, defaults, ledger, *, shape_profile=None, **_):
    if shape_profile==VANILLA_PLUS_PROFILE:
        for direction,item in projections.items():
            if item["visibility"] in VISIBLE:
                ledger.record_runtime(component["instanceId"],direction,"V4_VANILLA_PLUS_COMPRESSED_INTO_HEM")
        return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        # Waistband is a knit termination of the primary garment, not a
        # contrast belt. One row is enough at 16x16.
        occupied=[y for y,row in enumerate(frames[direction]) if any(p[3] for p in row)]
        if not occupied: continue
        y=max(occupied)-1
        bounds=_bounds(frames[direction],y)
        if bounds:
            for x in range(bounds[0]+1,bounds[1]):
                shade="BASE" if (x-bounds[0])%3 else "SHADOW"
                _draw(base,frames,defaults,ledger,component["instanceId"],"waistband",direction,x,y,shade,"PrimaryFabric")

def _ribbing(component, projections, base, frames, defaults, ledger, *, shape_library=None, shape_profile=None, **_):
    if shape_profile==VANILLA_PLUS_PROFILE:
        for direction,item in projections.items():
            if item["visibility"] in VISIBLE:
                ledger.record_runtime(component["instanceId"],direction,"V4_VANILLA_PLUS_COMPRESSED_INTO_HEM")
        return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        occupied=[y for y,row in enumerate(frames[direction]) if any(p[3] for p in row)]
        if not occupied: continue
        # V4.2 allocates surface rib ticks one row above the waistband so the
        # two canonical components never compete for structural ownership.
        y=max(occupied)-(2 if shape_library is not None else 1)
        bounds=_bounds(frames[direction],y)
        if bounds:
            for x in range(bounds[0]+2,bounds[1]-1,3):
                _draw(base,frames,defaults,ledger,component["instanceId"],"ribbing",direction,x,y,"LIGHT" if x<8 else "SHADOW","PrimaryFabric")

def _rear_panel(component, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_events=None, shape_profile=None, **_):
    if component["definitionId"] == "REAR_PANEL_SAILOR_SQUARE" and shape_library is not None and shape_profile == VANILLA_PLUS_PROFILE:
        event=shape_library.emit("SAILOR_REAR_FLAP_VANILLA_A",component,projections,topology=topology,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric),system="rear_panel")
        shape_events.append(event); return
    if component["definitionId"] == "REAR_PANEL_SAILOR_SQUARE" and shape_library is not None and shape_profile in {SAILOR_TECHNICAL_PROFILE, SAILOR_OUTLINE_PROFILE}:
        event=shape_library.emit("SAILOR_REAR_FLAP_TECHNICAL_V1",component,projections,topology=topology,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric),system="rear_panel")
        shape_events.append(event); return
    if component["definitionId"] == "REAR_PANEL_SAILOR_SQUARE" and shape_library is not None:
        event=shape_library.emit_sailor_rear("SAILOR_REAR_PANEL_V1",component,projections,
            draw=lambda i,s,d,x,y,shade,fabric:_draw(base,frames,defaults,ledger,i,s,d,x,y,shade,fabric))
        shape_events.append(event); return
    for direction, item in projections.items():
        if item["visibility"] not in VISIBLE:
            continue
        if direction == "back":
            shape = component["parameters"].get("shape", "square")
            ranges = ((3,12),(3,12),(4,11),(5,10)) if shape == "tapered_square" else ((3,12),(3,12),(3,12),(4,11))
            for offset, (x0, x1) in enumerate(ranges):
                y = 2 + offset
                for x in range(x0, x1+1):
                    shade = "STRUCTURAL_EDGE" if offset == 0 or x in {x0,x1} else "BASE" if x < 8 else "SHADOW"
                    _draw(base, frames, defaults, ledger, component["instanceId"], "rear_panel", direction, x, y, shade, "Trim")
        elif direction in {"right", "left"}:
            x = 10 if direction == "right" else 5
            for y in range(2, 6):
                _draw(base, frames, defaults, ledger, component["instanceId"], "rear_panel", direction, x, y, "SHADOW" if direction == "right" else "LIGHT", "Trim")


HANDLERS = {
    "BODY": _body, "INNER_LAYER": _inner, "COLLAR": _collar, "SLEEVE": _sleeve,
    "ARMHOLE": _armhole, "OPENING": _opening, "PLACKET": _placket,
    "HEM": _hem, "WAISTBAND": _waistband, "RIBBING": _ribbing,
    "REAR_PANEL": _rear_panel,
}

ORDER = {name: index for index, name in enumerate(("BODY", "INNER_LAYER", "COLLAR", "SLEEVE", "ARMHOLE", "OPENING", "PLACKET", "REAR_PANEL", "HEM", "WAISTBAND", "RIBBING"))}


def compile_components(canonical, projections, base, frames, defaults, ledger, *, shape_library=None, topology=None, shape_profile=None):
    by_direction = {direction: {item["componentInstance"]: item for item in items} for direction, items in projections.items()}
    map_entries = []; shape_events=[]
    for component in sorted(canonical["components"], key=lambda item: (ORDER[item["componentType"]], item["pixelPriority"])):
        handler = HANDLERS.get(component["componentType"])
        if handler is None:
            raise ValueError(f"no V3 component compiler for {component['componentType']}")
        projected = {direction: by_direction[direction][component["instanceId"]] for direction in DIRECTION_ORDER}
        before=len(shape_events)
        handler(component, projected, base, frames, defaults, ledger, shape_library=shape_library, topology=topology, shape_events=shape_events, shape_profile=shape_profile)
        map_entries.append({
            "componentInstance": component["instanceId"], "definitionId": component["definitionId"],
            "componentType": component["componentType"], "handler": handler.__name__,
            "pixelPriority": component["pixelPriority"], "mandatory": component["mandatory"],
            "projectionVisibility": {d: projected[d]["visibility"] for d in DIRECTION_ORDER},
            "emittedCellCount": {d: len(ledger.component_cells.get(component["instanceId"], {}).get(d, set())) for d in DIRECTION_ORDER},
            "clearedCellCount": {d: len(ledger.cleared_cells.get(component["instanceId"], {}).get(d, set())) for d in DIRECTION_ORDER},
            "runtimeContract": ledger.runtime_components.get(component["instanceId"], {}),
            "shapeVariants": [event["variantId"] for event in shape_events[before:]],
        })
    return map_entries, shape_events
