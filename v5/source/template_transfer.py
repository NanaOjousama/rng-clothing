"""Source-backed template generator contracts and transfer planner.

The construction template owns geometry.  Approved source families donate
vocabulary, tone, materials, patterns and proven components, but are never
allowed to silently rewrite a template silhouette.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from v5.pngio import read_rgba_png

PROJECT = Path(__file__).resolve().parents[2]

TRANSFERABLE = {"STYLE_PROFILE", "PALETTE_TONE", "MATERIAL_PATTERN", "MOTIF", "ATTACHMENT", "HARDWARE"}
NEVER_CROSS_TEMPLATE = {"BASE_SPECIFIC", "ALTERNATE_CONSTRUCTION", "REFERENCE_ONLY"}


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class TemplateContract:
    id: str
    slot: str
    category: str
    family: str
    frame_size: tuple[int, int]
    frames: dict
    geometry_lock: dict
    zones: dict
    anchors: dict
    allowed_part_kinds: frozenset[str]
    incompatibilities: tuple[dict, ...]
    source_identity: dict

    @property
    def views(self):
        return tuple(self.frames)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alpha_cells(rows):
    return {(x, y) for y, row in enumerate(rows) for x, p in enumerate(row) if p[3]}


def load_contract(path) -> TemplateContract:
    p = Path(path)
    if not p.is_absolute():
        p = PROJECT / p
    d = json.loads(p.read_text())
    if d.get("schema") != "source-backed-template/v1":
        raise ContractError(f"{p}: unsupported schema {d.get('schema')!r}")
    return TemplateContract(
        d["id"], d["slot"], d["category"], d["family"], tuple(d["frameSize"]),
        d["frames"], d["geometryLock"], d.get("zones", {}), d.get("anchors", {}),
        frozenset(d.get("allowedPartKinds", [])), tuple(d.get("incompatibilities", [])),
        d.get("sourceIdentity", {}),
    )


def verify_contract(contract: TemplateContract) -> dict:
    w, h = contract.frame_size
    report = {"template": contract.id, "views": {}, "ok": True}
    expected_views = set(contract.geometry_lock.get("requiredViews", ()))
    if expected_views and expected_views != set(contract.frames):
        raise ContractError(f"{contract.id}: required views {sorted(expected_views)} != frames {sorted(contract.frames)}")
    for view, spec in contract.frames.items():
        p = PROJECT / spec["path"]
        if not p.exists():
            raise ContractError(f"{contract.id}/{view}: missing frame {p}")
        got_hash = _sha256(p)
        if got_hash != spec["sha256"]:
            raise ContractError(f"{contract.id}/{view}: frame hash drift {got_hash} != {spec['sha256']}")
        rows = read_rgba_png(p)
        if len(rows) != h or len(rows[0]) != w:
            raise ContractError(f"{contract.id}/{view}: size {(len(rows[0]), len(rows))} != {(w,h)}")
        cells = alpha_cells(rows)
        got_alpha = hashlib.sha256(";".join(f"{x},{y}" for x,y in sorted(cells)).encode()).hexdigest()
        if spec.get("alphaSha256") and got_alpha != spec["alphaSha256"]:
            raise ContractError(f"{contract.id}/{view}: alpha geometry drift")
        report["views"][view] = {"sha256": got_hash, "alphaSha256": got_alpha, "opaque": len(cells)}
    if contract.geometry_lock.get("forbidResample") is not True:
        raise ContractError(f"{contract.id}: geometry lock must forbid resampling")
    if contract.geometry_lock.get("forbidGenericNormalization") is not True:
        raise ContractError(f"{contract.id}: geometry lock must forbid generic normalization")
    return report


def assert_geometry_preserved(before, after, *, allow_added=False):
    """Reject any accidental silhouette rewrite.

    Base styling must keep alpha byte-for-byte. Attachments may add alpha only
    when their contract explicitly allows it; removing/replacing base alpha is
    never accepted here.
    """
    a, b = alpha_cells(before), alpha_cells(after)
    if allow_added:
        if not a.issubset(b):
            raise ContractError(f"geometry removed {len(a-b)} locked cells")
    elif a != b:
        raise ContractError(f"geometry changed: -{len(a-b)} +{len(b-a)} alpha cells")


def decision(part: dict, template: TemplateContract) -> dict:
    """Return an explicit ALLOW/DENY transfer decision for one catalog part."""
    kind = part.get("partKind")
    scope = part.get("transferScope")
    out = {"part": part.get("name"), "kind": kind, "scope": scope, "decision": "DENY", "reason": ""}
    if scope in NEVER_CROSS_TEMPLATE:
        out["reason"] = f"{scope} may not cross onto another construction template"
        return out
    if kind not in template.allowed_part_kinds:
        out["reason"] = f"template does not allow part kind {kind}"
        return out
    if scope == "SAME_BASE_ONLY":
        src = part.get("sourceBaseIdentity") or {}
        if src != template.source_identity:
            out["reason"] = "base-specific part does not match template source identity"
            return out
    need = part.get("requiresZone")
    if need and need not in template.zones:
        out["reason"] = f"required semantic zone {need!r} is absent"
        return out
    for rule in template.incompatibilities:
        if rule.get("partKind") == kind and rule.get("deny") is True:
            out["reason"] = rule.get("reason", "template incompatibility")
            return out
    out["decision"] = "ALLOW"
    out["reason"] = "explicit template contract permits this transfer"
    return out


def plan(template: TemplateContract, parts: list[dict]) -> dict:
    verify_contract(template)
    choices = [decision(p, template) for p in parts]
    return {
        "template": template.id,
        "allowed": [x for x in choices if x["decision"] == "ALLOW"],
        "denied": [x for x in choices if x["decision"] == "DENY"],
    }


def template_frames(template: TemplateContract) -> dict:
    """Load the locked construction frames without transforming a pixel."""
    verify_contract(template)
    return {view: read_rgba_png(PROJECT / spec['path'])
            for view, spec in template.frames.items()}


def compile_recipe(template: TemplateContract, style_profile: dict, parts=()) -> dict:
    """Validate a source-backed mix-and-match recipe before rendering.

    This is deliberately pixel-agnostic: it proves the donor/part combination
    is permitted by the target contract. A renderer may then apply only the
    operations named in this recipe and must retain the geometry guard.
    """
    verify_contract(template)
    sd = decision(style_profile, template)
    if sd['decision'] != 'ALLOW':
        raise ContractError(f"style donor denied: {sd['reason']}")
    chosen, credits = [], []
    for part in parts:
        d = decision(part, template)
        if d['decision'] != 'ALLOW':
            raise ContractError(f"{part.get('name')}: {d['reason']}")
        chosen.append({
            'name': part.get('name'), 'kind': part.get('partKind'),
            'pack': part.get('pack'), 'family': part.get('family'),
            'requiresZone': part.get('requiresZone')})
        if part.get('author') or part.get('pack'):
            credits.append({'author': part.get('author'), 'pack': part.get('pack'),
                            'asset': part.get('name')})
    spid = style_profile.get('id') or style_profile.get('name')
    credit = style_profile.get('credit') or {}
    if credit:
        credits.insert(0, {'author': credit.get('author'), 'pack': credit.get('pack'),
                           'asset': style_profile.get('name')})
    return {
        'schema': 'source-backed-generation-recipe/v1',
        'template': template.id,
        'styleDonor': spid,
        'parts': chosen,
        'credits': credits,
        'geometryPolicy': 'LOCKED_TEMPLATE_ALPHA',
        'neutralSource': {v: s['path'] for v,s in template.frames.items()},
    }
