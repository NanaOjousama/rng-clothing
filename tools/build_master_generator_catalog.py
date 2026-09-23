import json, hashlib, re, sys
from pathlib import Path
from collections import defaultdict, Counter
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.pngio import read_rgba_png

cat = json.load(open(ROOT / "source_catalog/catalog.json"))
fam = json.load(open(ROOT / "source_catalog/families.json"))
apps = cat["appearances"]
families = fam["families"]

membership = defaultdict(list)
base_lookup = {}
for f in families:
    base_lookup[(f["pack"], f["base"])] = f
    for v in f.get("variants", []):
        membership[(f["pack"], v["variant"])].append({
            "family": f["family"], "category": f["category"], "pack": f["pack"],
            "class": v.get("class"), "base": f.get("base"),
            "modelled": v.get("modelled"), "exact": v.get("exact"),
            "reason": v.get("reason")
        })

def generic_role(a):
    key = (a["pack"], a["name"])
    if key in base_lookup:
        return "FAMILY_BASE"
    classes = {m.get("class") for m in membership.get(key, [])}
    if "REUSABLE" in classes: return "REUSABLE_COMPONENT"
    if "BASE-SPECIFIC" in classes: return "BASE_SPECIFIC_VARIANT"
    if "REFERENCE-ONLY" in classes: return "ALTERNATE_CONSTRUCTION"
    return "UNGROUPED_SOURCE"
def alpha_sig(path):
    rows = read_rgba_png(Path(path))
    alpha = bytes(1 if p[3] else 0 for row in rows for p in row)
    return hashlib.sha256(alpha).hexdigest()

hat_apps = [a for a in apps if a["category"] == "Hats"]
alpha_groups = defaultdict(list)
for a in hat_apps:
    p = Path(a["png_path"])
    if p.exists():
        alpha_groups[(tuple(a.get("png_size") or []), alpha_sig(p))].append((a["pack"], a["name"]))

same_group = {}
gid = 0
for _, vals in sorted(alpha_groups.items(), key=lambda kv: (-len(kv[1]), str(kv[0]))):
    if len(vals) > 1:
        gid += 1
        label = f"SHAPE-{gid:02d}"
        for k in vals:
            same_group[k] = {"group": label, "members": [{"pack": p, "name": n} for p, n in vals]}

head_accessory = [r"^Bow", r"^Bows", r"^Earmuffs", r"^Headband", r"^Barrette$", r"^Clip",
                  r"^Crown", r"^Decorative Bells", r"^Flower Dance Crown$", r"^Garland",
                  r"^Goggles", r"^Hair ", r"^Leaf$", r"^Sleeping Mask", r"^Sunglasses",
                  r"^Tiara", r"^Veil"]
full_hat = [r"^Beanie", r"^Beret", r"^Boater Hat", r"^Cap ", r"^Cap \(", r"^Cowboy Hat",
            r"^Headscarf", r"^Hood", r"^Mushroom Hat", r"^Paperboy Hat", r"^Party Hat",
            r"^Straw Hat", r"^Sun Hat", r"^Tulip Hat"]

def anymatch(name, pats):
    return any(re.search(p, name) for p in pats)
def hat_semantic(a):
    name, pack, role = a["name"], a["pack"], generic_role(a)
    if pack == "More Accessories and Stuff" and name == "Cap 2":
        return "CONSTRUCTION_BASE", "LIVE_APPROVED", "Baseball", "Current source-backed Baseball construction; live QC approved."
    if pack == "More Accessories and Stuff" and name == "Cap (Snapback)":
        return "CONSTRUCTION_BASE", "LIVE_APPROVED", "Snapback", "Current source-backed Snapback construction; live QC approved."
    if pack == "More Accessories and Stuff" and name == "Cap 1":
        return "RENDER_MATERIAL_VARIANT", "REVIEWED", "Baseball", "Exact alpha silhouette match to Cap 2; render/material variant, not a new shape."
    if pack == "More Accessories and Stuff" and name == "Paperboy Hat":
        return "REJECTED_CONSTRUCTION", "REJECTED_LIVE", "Paperboy", "Live worn test failed identity/readability."
    if name == "Plague Doctor Mask":
        return "MASK_FACE_HEADWEAR", "AVAILABLE", None, "Head-slot face/mask item, not a hat construction base."
    if anymatch(name, head_accessory):
        state = {"FAMILY_BASE":"AVAILABLE_FAMILY_BASE","REUSABLE_COMPONENT":"REUSABLE_COMPONENT",
                 "BASE_SPECIFIC_VARIANT":"BASE_SPECIFIC_VARIANT",
                 "ALTERNATE_CONSTRUCTION":"ALTERNATE_ACCESSORY_CONSTRUCTION"}.get(role, "AVAILABLE_UNGROUPED")
        return "HEAD_ACCESSORY", state, None, "Head-slot accessory; keep separate from full hat construction families."
    if anymatch(name, full_hat):
        if role == "FAMILY_BASE":
            return "CONSTRUCTION_BASE", "AVAILABLE_FAMILY_BASE", re.sub(r"\s*\(.*", "", name), "Detected family base; source construction candidate."
        if role == "REUSABLE_COMPONENT":
            return "SAME_CONSTRUCTION_VARIANT", "REUSABLE_COMPONENT", None, "Composable reusable variant of its family base."
        if role == "BASE_SPECIFIC_VARIANT":
            return "SAME_CONSTRUCTION_VARIANT", "BASE_SPECIFIC_VARIANT", None, "Variant usable only on its own base."
        if role == "ALTERNATE_CONSTRUCTION":
            return "ALTERNATE_CONSTRUCTION", "REVIEW_AS_OWN_BASE", None, "Diff reshapes/removes base cells; review as a separate construction."
        return "CONSTRUCTION_CANDIDATE", "REVIEW_NEEDED", re.sub(r"\s*\(.*", "", name), "Standalone full headwear construction; review visually before integration."
    return "OTHER_HEAD_SLOT", "REVIEW_NEEDED", None, "Unclassified head-slot source; inspect before generator use."

hat_rows = []
for a in sorted(hat_apps, key=lambda x: (x["pack"].lower(), x["name"].lower())):
    kind, state, hint, note = hat_semantic(a)
    key = (a["pack"], a["name"])
    hat_rows.append({
        "pack": a["pack"], "author": a.get("pack_author"), "name": a["name"], "folder": a["folder"],
        "png_size": a.get("png_size"), "generic_role": generic_role(a), "hat_kind": kind,
        "review_state": state, "family_hint": hint, "note": note,
        "family_memberships": membership.get(key, []), "exact_silhouette_group": same_group.get(key),
        "png_path": a.get("png_path"), "json_path": a.get("json_path")
    })
summary = {
    "source_root": cat.get("source_root"),
    "counts_by_category": dict(Counter(a["category"] for a in apps)),
    "packs": cat["packs"], "family_count": len(families),
    "approval_counts": dict(Counter(v.get("class") for f in families for v in f.get("variants", []))),
    "generic_role_counts": dict(Counter(generic_role(a) for a in apps)),
    "failed_family_ingests": fam.get("failed", []), "standalone_assets": [], "categories": {}
}
motif = ROOT / "generator content/motif"
if motif.exists():
    for p in sorted(motif.rglob("*")):
        if p.is_file():
            summary["standalone_assets"].append({"path": str(p), "name": p.name, "kind": "standalone_motif_asset"})

for a in apps:
    key = (a["pack"], a["name"])
    row = {"name":a["name"],"folder":a["folder"],"author":a.get("pack_author"),
           "png_size":a.get("png_size"),"animated":a.get("animated"),
           "color_masks":a.get("color_masks"),"hide_hair":a.get("hide_hair"),
           "generator_role":generic_role(a),"memberships":membership.get(key,[]),
           "png_path":a.get("png_path"),"json_path":a.get("json_path")}
    summary["categories"].setdefault(a["category"],{}).setdefault(a["pack"],[]).append(row)
for c in summary["categories"].values():
    for rows in c.values(): rows.sort(key=lambda r:r["name"].lower())

(ROOT/"source_catalog/MASTER_CATALOG.json").write_text(json.dumps(summary,indent=2)+"\n")
(ROOT/"source_catalog/HAT_WORKING_CATALOG.json").write_text(json.dumps({
    "count":len(hat_rows),
    "kind_counts":dict(Counter(r["hat_kind"] for r in hat_rows)),
    "review_state_counts":dict(Counter(r["review_state"] for r in hat_rows)),
    "rows":hat_rows
},indent=2)+"\n")
lines = ["# Generator Content Master Catalog","",
         "Read-only derived inventory of generator content/. Source assets are not modified.","",
         "## Summary","",f"- Total Fashion Sense appearances: **{len(apps)}**"]
for k,v in sorted(summary["counts_by_category"].items()): lines.append(f"- {k}: **{v}**")
lines += [f"- Modelled source families: **{len(families)}**",
          f"- Failed family ingests: **{len(summary['failed_family_ingests'])}**",
          f"- Standalone non-FS assets: **{len(summary['standalone_assets'])}**","",
          "### Generator roles",""]
for k,v in sorted(summary["generic_role_counts"].items()): lines.append(f"- **{k}**: {v}")
lines += ["","## Full inventory",""]
for catname in sorted(summary["categories"]):
    lines += [f"### {catname}",""]
    for pack in sorted(summary["categories"][catname]):
        rows = summary["categories"][catname][pack]
        lines += [f"#### {pack} ({len(rows)})",""]
        for r in rows:
            size = "x".join(map(str,r["png_size"] or [])) or "?"
            lines.append(f"- **{r['name']}** — {r['folder']} — {size} — {r['generator_role']}")
        lines.append("")
if summary["standalone_assets"]:
    lines += ["### Standalone assets",""]
    for x in summary["standalone_assets"]: lines.append(f"- {x['path']}")
    lines.append("")
(ROOT/"source_catalog/MASTER_CATALOG.md").write_text("\n".join(lines)+"\n")

hc=Counter(r["hat_kind"] for r in hat_rows); rs=Counter(r["review_state"] for r in hat_rows)
hl=["# Hat Working Catalog","",
    "Semantic working inventory for all 116 hat-slot appearances in generator content/.","",
    "## Counts",""]
for k,v in sorted(hc.items()): hl.append(f"- **{k}**: {v}")
hl += ["","### Review state",""]
for k,v in sorted(rs.items()): hl.append(f"- **{k}**: {v}")
hl += ["","## Exact same-silhouette groups",""]
seen=set()
for r in hat_rows:
    g=r["exact_silhouette_group"]
    if g and g["group"] not in seen:
        seen.add(g["group"])
        members="; ".join(f"{m['pack']} / {m['name']}" for m in g["members"])
        hl.append(f"- **{g['group']}** — {members}")
hl.append("")
for kind in sorted(hc):
    hl += [f"## {kind}",""]
    for r in [x for x in hat_rows if x["hat_kind"]==kind]:
        size="x".join(map(str,r["png_size"] or [])) or "?"
        shape=f" — {r['exact_silhouette_group']['group']}" if r["exact_silhouette_group"] else ""
        hl.append(f"- **{r['name']}** ({r['pack']}) — {size} — {r['review_state']}{shape}")
        hl.append(f"  - {r['note']}")
    hl.append("")
(ROOT/"source_catalog/HAT_WORKING_CATALOG.md").write_text("\n".join(hl)+"\n")

print("MASTER roles", summary["generic_role_counts"])
print("HAT kinds", dict(hc))
print("HAT states", dict(rs))
print("wrote MASTER_CATALOG.md/json + HAT_WORKING_CATALOG.md/json")
