"""TIER 1 — Roll Context, and the Style Context bias system.

One player roll creates one hidden Roll Context.  Style Context may only
reweight options that Family or Architecture already declared (INV-02); it can
never introduce content.  That invariant is enforced structurally: hooks return
weights over the variable's own domain and the resolver rejects any new key.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .rng import StreamBank

# --- Formality: the one Style Context axis implemented first ----------------
FORMALITY = ("work", "casual", "smart", "formal")
FORMALITY_WEIGHTS = {"work": 0.22, "casual": 0.40, "smart": 0.26, "formal": 0.12}

# --- chromatic temperament --------------------------------------------------
TEMPERAMENT = ("cool", "neutral", "warm")
TEMPERAMENT_WEIGHTS = {"cool": 0.40, "neutral": 0.32, "warm": 0.28}

# --- novelty ----------------------------------------------------------------
NOVELTY = ("conservative", "standard", "adventurous")
NOVELTY_WEIGHTS = {"conservative": 0.30, "standard": 0.50, "adventurous": 0.20}

# complexity pool: 1-5 skewed low (canonical section 18)
COMPLEXITY_WEIGHTS = {1: 0.20, 2: 0.31, 3: 0.26, 4: 0.16, 5: 0.07}

# Reserved future Style Context axes; deliberately not implemented.
RESERVED_STYLE_AXES = ("idiom", "condition")


@dataclass
class RollContext:
    seed: int
    complexity_budget: int
    formality: str
    chromatic_temperament: str
    novelty_tier: str
    streams: StreamBank
    _hooks: list = field(default_factory=list)
    # Resolution-time services, attached by the resolver.  Activation
    # predicates and validators reach the budget / occupancy ledger / partial
    # geometry through these, which is what keeps the resolver itself free of
    # any family-specific control flow.
    budget: object = None
    occupancy: object = None
    record: object = None
    geometry: object = None
    palette: object = None
    architecture_feature_limit: object = None

    # -- gates used by declared activation / validation predicates ----------

    def claim_layer(self, name: str) -> bool:
        from .ornament import ORNAMENTS  # noqa: F401  (kept symmetrical)
        from .schema import OVERLAY
        return self.occupancy.claim("collar:center", name, OVERLAY)

    def claim_ornament(self, name: str) -> bool:
        from .grammar import IDENTITY_CONTRAST_FLOOR
        from .ornament import ORNAMENTS
        orn = ORNAMENTS[name]
        condition = True
        if orn.zone == "chest:center":
            pal = self.palette
            condition = pal.contrast(pal.color(orn.role, "base"),
                                     pal.color("under_layer", "base")) >= IDENTITY_CONTRAST_FLOOR
        return self.occupancy.claim(orn.zone, name, orn.claim_mode, condition_met=condition)

    def feature_load(self) -> int:
        """Optional appearance features instantiated so far.

        Busyness that neither the budget nor semantic occupancy can see: these
        features are individually cheap and do not share a zone, but together
        they crowd the construction.
        """
        from .ornament import ORNAMENTS
        names = ("surface_family", "collar_trim", "yoke_trim", "tie_style")
        n = sum(1 for k in names if self.record.has(k)
                and self.record.opt(k) != "solid")
        return n + sum(1 for k in ORNAMENTS if self.record.has(k))

    def under_feature_limit(self, limit) -> bool:
        return limit is None or self.feature_load() < limit

    def material_permits_surface(self, value: str) -> bool:
        from .material import MATERIALS
        return value in MATERIALS[self.record.get("material")].patterns

    def surface_reads(self, domain: str) -> bool:
        from .surface import SURFACES, domain_cells, readable
        surface = SURFACES[self.record.get("surface_family")]
        cells = domain_cells(self.geometry, domain, "front")
        return readable(surface, cells, 2)

    def period_reads(self, period: int) -> bool:
        from .surface import SURFACES, domain_cells, readable
        surface = SURFACES[self.record.get("surface_family")]
        cells = domain_cells(self.geometry, self.record.get("surface_domain"), "front")
        return readable(surface, cells, period)

    # -- style context ------------------------------------------------------

    def register_hook(self, hook) -> None:
        """A Family/Architecture reweight hook: (var, weights, record, ctx) -> weights."""
        self._hooks.append(hook)

    def reweight(self, var, weights: dict, record) -> dict:
        out = dict(weights)
        for hook in self._hooks:
            proposed = hook(var, out, record, self)
            if proposed is None:
                continue
            new = set(proposed) - set(out)
            if new:
                raise ValueError(
                    f"hook introduced {sorted(new)} into {var.name!r} (INV-02)"
                )
            out = {k: max(0.0, float(v)) for k, v in proposed.items()}
        return out

    @property
    def formality_index(self) -> int:
        return FORMALITY.index(self.formality)

    def as_dict(self) -> dict:
        return {
            "complexity": self.complexity_budget,
            "formality": self.formality,
            "temperament": self.chromatic_temperament,
            "novelty": self.novelty_tier,
        }


def roll_context(seed: int) -> RollContext:
    """Pass 1 — resolve the hidden context for one player roll."""
    streams = StreamBank(seed)
    s = streams("context")
    return RollContext(
        seed=seed,
        complexity_budget=s.weighted(COMPLEXITY_WEIGHTS),
        formality=s.weighted(FORMALITY_WEIGHTS),
        chromatic_temperament=s.weighted(TEMPERAMENT_WEIGHTS),
        novelty_tier=s.weighted(NOVELTY_WEIGHTS),
        streams=streams,
    )
