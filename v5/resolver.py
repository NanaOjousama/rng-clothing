"""The generic resolver — canonical passes 1 through 9.

There is no Family- or Architecture-specific control flow in this file.  It
walks whatever child schema the selected Architecture publishes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .color import resolve_palette
from .grammar import MIN_RAMP_DEPTH
from .context import RollContext, roll_context
from .contracts import (ARCHITECTURE_LIBRARY, FAMILY_LIBRARY, SLOT_LIBRARY,
                        families_for_slot)
from .grammar import STANDARD_ENVELOPE, ZONES, Envelope
from .material import MATERIALS
from .ornament import ORNAMENTS
from .schema import (Budget, OccupancyLedger, Record, SchemaRegistry,
                     resolve_variable)


@dataclass(frozen=True)
class GarmentSpec:
    """Pass 9 — one immutable semantic specification.

    Contains only concepts that were actually instantiated (INV-03).
    """
    seed: int
    slot: str
    family: str
    architecture: str
    roll_context: dict
    parameters: dict
    layers: dict
    material: str
    color_architecture: str
    palette: object
    ornaments: tuple
    silhouette_ref: str
    construction_refs: tuple
    envelope: Envelope
    surface: dict = field(default_factory=dict)
    budget_ledger: dict = field(default_factory=dict)
    occupancy_ledger: dict = field(default_factory=dict)
    trace: tuple = ()
    context: object = None

    def as_dict(self) -> dict:
        out = {
            "seed": self.seed, "slot": self.slot, "family": self.family,
            "architecture": self.architecture, "roll_context": self.roll_context,
            "parameters": self.parameters, "material": self.material,
            "color_architecture": self.color_architecture,
            "silhouette_ref": self.silhouette_ref,
            "construction_refs": list(self.construction_refs),
            "envelope": [self.envelope.width, self.envelope.height, self.envelope.scale],
            "budget": self.budget_ledger,
        }
        if self.layers:
            out["layers"] = self.layers
        if self.surface:
            out["surface"] = self.surface
        if self.ornaments:
            out["ornaments"] = list(self.ornaments)
        return out


# variable name -> which serialized section it belongs to
_LAYER_VARS = ("tie_style",)
_SURFACE_VARS = ("surface_family", "surface_domain", "surface_period", "surface_phase")


def generate_spec(seed: int, *, slot: str = "TOP",
                  envelope: Envelope = STANDARD_ENVELOPE) -> GarmentSpec:
    ctx = roll_context(seed)                                     # Pass 1
    trace: list = []

    # --- Pass 2: Slot ------------------------------------------------------
    slot_contract = SLOT_LIBRARY[slot]
    # The slot travels with the context so later passes can consult it without
    # threading it through every signature — the ramp depth a slot's art needs
    # is a slot capability, not a material one.
    ctx.slot = slot
    trace.append(("slot", slot_contract.name))

    # --- Pass 3: Family ----------------------------------------------------
    eligible = families_for_slot(slot)
    if not eligible:
        raise ValueError(f"no family registered for slot {slot!r}")
    family_name = ctx.streams("family").weighted({n: 1.0 for n in eligible})
    family = FAMILY_LIBRARY[family_name]
    trace.append(("family", family_name))

    # --- Pass 4: Architecture ---------------------------------------------
    arch_name = ctx.streams("architecture").weighted(dict(family.architectures))
    arch = ARCHITECTURE_LIBRARY[arch_name]
    arch.check_against(family)
    trace.append(("architecture", arch_name))

    if family.style_hook:
        ctx.register_hook(family.style_hook)
    if arch.style_hook:
        ctx.register_hook(arch.style_hook)

    # One shared pool.  base_cost buys the Architecture's own construction;
    # the remainder is the design budget for trim, surface and ornament.
    ctx.budget = Budget(ctx.complexity_budget + 2)
    ctx.budget.spend(arch.name, "STRUCTURAL", arch.base_cost)
    ctx.occupancy = OccupancyLedger(ZONES)
    ctx.architecture_feature_limit = arch.max_appearance_features
    for zone, feature, mode in arch.occupancy:
        ctx.occupancy.claim(zone, feature, mode)

    record = Record()
    ctx.record = record

    registry = SchemaRegistry()
    registry.declare(*arch.declare_schema(family, arch, ctx, record))

    # --- Passes 5-8: walk the published schema in declared order -----------
    for var in registry.variables:
        # Provisional geometry becomes available as soon as every structural
        # variable is resolved; Surface gating needs real region areas.
        if var.resolution_pass == "surface" and ctx.geometry is None:
            ctx.geometry = arch.realize(_PartialSpec(record.as_dict()), envelope)
        if var.resolution_pass == "ornament" and ctx.palette is None:
            ctx.palette = _palette_for(ctx, record)
        resolve_variable(var, record, ctx, ctx.budget, trace)

    if ctx.geometry is None:
        ctx.geometry = arch.realize(_PartialSpec(record.as_dict()), envelope)
    if ctx.palette is None:
        ctx.palette = _palette_for(ctx, record)

    # --- Pass 9: finalize ---------------------------------------------------
    values = record.as_dict()
    parameters = {k: v for k, v in values.items()
                  if k not in _LAYER_VARS and k not in _SURFACE_VARS
                  and k not in ORNAMENTS and k != "detail_package"}
    layers = {k: values[k] for k in _LAYER_VARS if k in values}
    surface = {k.removeprefix("surface_"): values[k] for k in _SURFACE_VARS if k in values}
    if surface.get("family") == "solid":
        surface = {}                     # solid is the absence of a Surface feature
    elif "domain" not in surface:
        # Pass 7 rule (section 39): when bounded repair cannot place a Surface
        # anywhere it would read, the whole feature is dropped and refunded —
        # it is never half-instantiated.
        ctx.budget.refund("surface_family")
        record.drop("surface_family")
        trace.append(("surface_family", "dropped: no readable domain"))
        surface = {}
    ornaments = tuple(n for n in ORNAMENTS if n in values)
    if "detail_package" in values:
        parameters["detail_package"] = values["detail_package"]

    spec = GarmentSpec(
        seed=seed, slot=slot, family=family_name, architecture=arch_name,
        roll_context=ctx.as_dict(), parameters=parameters, layers=layers,
        material=record.get("material"), color_architecture=record.get("color_architecture"),
        palette=ctx.palette, ornaments=ornaments,
        silhouette_ref=record.get("silhouette"), construction_refs=arch.topology,
        envelope=envelope, surface=surface,
        budget_ledger={"total": ctx.budget.total, "used": ctx.budget.used,
                       "by_tag": ctx.budget.by_tag(),
                       "spends": [(s.who, s.tag, s.amount) for s in ctx.budget.spends]},
        occupancy_ledger={z: ctx.occupancy.occupants(z)
                          for z in ZONES if ctx.occupancy.occupants(z)},
        trace=tuple(trace), context=ctx,
    )
    ctx.streams.freeze()          # INV-11: no design entropy past this line
    return spec


def _palette_for(ctx, record):
    from .contracts import SLOT_LIBRARY
    slot = SLOT_LIBRARY.get(getattr(ctx, "slot", None) or "TOP")
    return resolve_palette(
        record.get("color_architecture"), record.get("harmony"),
        ctx.chromatic_temperament, MATERIALS[record.get("material")],
        ctx.streams("chroma"),
        min_depth=slot.min_ramp_depth if slot else MIN_RAMP_DEPTH,
        ramp_spread=slot.ramp_spread if slot else 1.0,
    )


class _PartialSpec:
    """The shape `realize` expects, built from a partially-resolved record.

    The record is flat, so `parameters` and `layers` are the same mapping here;
    the split only happens at finalization.  Construction must read a layer-slot
    value from `layers` so that provisional geometry and the final render agree.
    """

    def __init__(self, values: dict) -> None:
        self.parameters = values
        self.layers = values
