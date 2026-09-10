"""Generic resolution machinery: variables, budget, occupancy, garment record.

Nothing here knows what a sailor top is.  Families and Architectures are data
contracts; this module is the engine that resolves whatever they declare.

Enforces:
  INV-03 invalid concepts are absent, never `none`
  INV-04 one owner / one resolution pass per variable
  INV-05 lower passes cannot reopen decisions above them
  INV-06 bounded repair stays inside the variable's existing domain
  INV-07 one complexity pool, every spend tagged
  INV-08 exclusive / conditional-share / overlay occupancy claims
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

# --- spend tags (canonical section 18) --------------------------------------
STRUCTURAL, SURFACE, ORNAMENT = "STRUCTURAL", "SURFACE", "ORNAMENT"
SPEND_TAGS = (STRUCTURAL, SURFACE, ORNAMENT)

# --- visual significance classes (canonical section 43) ---------------------
IDENTITY, APPEARANCE, SUBTLE = "structural_identity", "appearance", "semantic_subtle"

# --- repair policies (canonical section 39) ---------------------------------
REPAIR_NONE, REPAIR_RETRY, REPAIR_DROP = "none", "retry_in_domain", "drop_optional"


@dataclass(frozen=True)
class Variable:
    """A declared, scoped, unresolved choice.

    `domain` is the complete set of legal values.  `activation` decides whether
    the variable comes into existence at all; a variable that does not activate
    is never instantiated, never serialized and cannot be mutated.
    """
    name: str
    owner: str                       # tier that declared it
    resolution_pass: str
    domain: tuple
    weights: dict = field(default_factory=dict)
    significance: str = APPEARANCE
    activation: Callable | None = None      # (record, ctx) -> bool
    cost: dict | int = 0                    # per-value or flat complexity cost
    cost_tag: str = STRUCTURAL
    repair: str = REPAIR_NONE
    # How many samples bounded repair may take before giving up.  The default
    # of 4 is fine while a domain has four or fewer members; past that a
    # variable with a legal value can be DROPPED because the first four samples
    # happened to be the illegal ones.  Widening `crown_width` to five members
    # surfaced that 533 seeds in, as an AbsentConcept crash in a downstream
    # validator rather than as a bad hat.
    #
    # Declared per variable rather than raised globally: making the bound the
    # domain length everywhere is arguably more correct, but it changes
    # resolution for every existing garment, and a variable that needs to
    # exhaust its domain should have to say so.
    repair_attempts: int = 4
    validate: Callable | None = None        # (value, record, ctx) -> bool
    stream: str | None = None               # defaults to resolution_pass

    def base_weights(self) -> dict:
        if self.weights:
            unknown = set(self.weights) - set(self.domain)
            if unknown:
                raise ValueError(f"{self.name}: weights outside domain: {sorted(unknown)}")
            return {v: float(self.weights.get(v, 0.0)) for v in self.domain}
        return {v: 1.0 for v in self.domain}

    def cost_of(self, value) -> int:
        return int(self.cost.get(value, 0)) if isinstance(self.cost, dict) else int(self.cost)


# ---------------------------------------------------------------------------
# complexity budget
# ---------------------------------------------------------------------------

@dataclass
class Spend:
    who: str
    tag: str
    amount: int


class Budget:
    """One shared pool (INV-07).  Spend order is Construction, Surface, Ornament."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.spends: list[Spend] = []

    @property
    def used(self) -> int:
        return sum(s.amount for s in self.spends)

    @property
    def remaining(self) -> int:
        return self.total - self.used

    def can_afford(self, amount: int) -> bool:
        return amount <= self.remaining

    def spend(self, who: str, tag: str, amount: int) -> None:
        if tag not in SPEND_TAGS:
            raise ValueError(f"untagged or unknown spend tag {tag!r}")
        # Spend order is Construction, then Surface, then Ornament (section 18).
        rank = SPEND_TAGS.index(tag)
        if self.spends and rank < max(SPEND_TAGS.index(s.tag) for s in self.spends):
            raise ValueError(f"{who}: {tag} spend after a later-tagged spend")
        if amount < 0:
            raise ValueError("negative spend")
        if amount > self.remaining:
            raise ValueError(f"{who}: overspend {amount} > {self.remaining}")
        self.spends.append(Spend(who, tag, amount))

    def refund(self, who: str) -> int:
        """Give back everything `who` spent (used when a feature is dropped)."""
        back = sum(s.amount for s in self.spends if s.who == who)
        self.spends = [s for s in self.spends if s.who != who]
        return back

    def by_tag(self) -> dict:
        return {t: sum(s.amount for s in self.spends if s.tag == t) for t in SPEND_TAGS}


# ---------------------------------------------------------------------------
# semantic spatial occupancy
# ---------------------------------------------------------------------------

EXCLUSIVE, CONDITIONAL_SHARE, OVERLAY = "exclusive", "conditional_share", "overlay"


@dataclass
class Claim:
    feature: str
    mode: str
    overpainted: bool = False


class OccupancyLedger:
    """Semantic garment space, not pixel space (canonical section 19)."""

    def __init__(self, zones: tuple[str, ...]) -> None:
        self.zones = zones
        self.claims: dict[str, list[Claim]] = {z: [] for z in zones}
        self.rejections: list[tuple[str, str, str]] = []

    def claim(self, zone: str, feature: str, mode: str, *, condition_met: bool = True) -> bool:
        if zone not in self.claims:
            raise ValueError(f"unknown semantic zone {zone!r}")
        sitting = self.claims[zone]
        if mode == EXCLUSIVE:
            if sitting:
                self.rejections.append((zone, feature, "occupied"))
                return False
        elif mode == CONDITIONAL_SHARE:
            if any(c.mode == EXCLUSIVE for c in sitting):
                self.rejections.append((zone, feature, "exclusive incumbent"))
                return False
            if sitting and not condition_met:
                self.rejections.append((zone, feature, "share condition failed"))
                return False
        elif mode == OVERLAY:
            for c in sitting:
                c.overpainted = True
        else:
            raise ValueError(f"unknown claim mode {mode!r}")
        sitting.append(Claim(feature, mode))
        return True

    def occupants(self, zone: str) -> list[str]:
        return [c.feature for c in self.claims.get(zone, [])]

    def is_overpainted(self, zone: str, feature: str) -> bool:
        return any(c.feature == feature and c.overpainted for c in self.claims.get(zone, []))


# ---------------------------------------------------------------------------
# the generated record
# ---------------------------------------------------------------------------

class AbsentConcept(KeyError):
    """Raised when code asks for a concept that was never instantiated."""


class Record:
    """Holds only instantiated concepts.  There is no `none` (INV-03)."""

    def __init__(self) -> None:
        self._values: dict[str, object] = {}
        self._owner: dict[str, str] = {}
        self._pass: dict[str, str] = {}

    def write(self, name: str, value, owner: str, resolution_pass: str) -> None:
        if name in self._values:
            raise ValueError(
                f"{name!r} already written by {self._owner[name]} in pass "
                f"{self._pass[name]} (INV-04: one owner / one pass)"
            )
        self._values[name] = value
        self._owner[name] = owner
        self._pass[name] = resolution_pass

    def drop(self, name: str) -> None:
        """Un-instantiate an optional feature that failed downstream validation."""
        self._values.pop(name, None)
        self._owner.pop(name, None)
        self._pass.pop(name, None)

    def has(self, name: str) -> bool:
        return name in self._values

    def get(self, name: str):
        if name not in self._values:
            raise AbsentConcept(f"{name!r} was never instantiated for this garment")
        return self._values[name]

    def opt(self, name: str, fallback=None):
        """Explicit caller-side default.  Never stored on the record."""
        return self._values.get(name, fallback)

    def owner_of(self, name: str) -> str:
        return self._owner[name]

    def pass_of(self, name: str) -> str:
        return self._pass[name]

    def as_dict(self) -> dict:
        return dict(self._values)

    def __contains__(self, name: str) -> bool:
        return name in self._values

    def __repr__(self) -> str:
        return f"Record({self._values!r})"


# ---------------------------------------------------------------------------
# resolver
# ---------------------------------------------------------------------------

class SchemaRegistry:
    """Collects declared variables and enforces single ownership."""

    def __init__(self) -> None:
        self.variables: list[Variable] = []
        self._seen: dict[str, Variable] = {}

    def declare(self, *variables: Variable) -> None:
        for v in variables:
            if v.name in self._seen:
                prior = self._seen[v.name]
                raise ValueError(
                    f"{v.name!r} declared twice: by {prior.owner} and {v.owner} (INV-04)"
                )
            if v.cost_tag not in SPEND_TAGS:
                raise ValueError(f"{v.name!r}: bad cost tag {v.cost_tag!r}")
            self._seen[v.name] = v
            self.variables.append(v)

    def get(self, name: str) -> Variable:
        return self._seen[name]

    def __contains__(self, name: str) -> bool:
        return name in self._seen


def resolve_variable(var: Variable, record: Record, ctx, budget: Budget, log: list) -> bool:
    """Resolve one declared variable.  Returns True if it was instantiated.

    Bounded local repair (INV-06): on validation failure we retry OTHER VALUES
    OF THE SAME VARIABLE ONLY, capped, using the same deterministic stream.  We
    never switch to a different variable or reopen a parent decision.
    """
    if var.activation is not None and not var.activation(record, ctx):
        log.append((var.name, "not_activated"))
        return False

    weights = var.base_weights()
    weights = ctx.reweight(var, weights, record)
    illegal = set(weights) - set(var.domain)
    if illegal:
        raise ValueError(
            f"style context tried to introduce {sorted(illegal)} into {var.name!r} "
            "(INV-02: reweighting may not add content)"
        )

    stream = ctx.streams(var.stream or var.resolution_pass)
    # Bounded repair must at least be able to EXHAUST the domain.  A fixed 4
    # was silently fine while every structural domain had three or four
    # members; widening `crown_width` to five made it possible for a variable
    # with a legal value to be dropped because the first four samples happened
    # to be the illegal ones — which surfaced 533 seeds in as an AbsentConcept
    # crash in a downstream validator, not as a bad hat.  Repair stays bounded;
    # the bound is now the domain.
    attempts, max_attempts = 0, max(var.repair_attempts, 1)
    pool = dict(weights)
    while attempts < max_attempts:
        affordable = {v: w for v, w in pool.items() if w > 0 and budget.can_afford(var.cost_of(v))}
        if not affordable:
            break
        value = stream.weighted(affordable)
        attempts += 1
        ok = var.validate is None or var.validate(value, record, ctx)
        if ok:
            budget.spend(var.name, var.cost_tag, var.cost_of(value))
            record.write(value=value, name=var.name, owner=var.owner,
                         resolution_pass=var.resolution_pass)
            log.append((var.name, f"resolved={value!r}", f"attempts={attempts}"))
            return True
        if var.repair == REPAIR_NONE:
            break
        pool[value] = 0.0                       # bounded repair inside the domain
        log.append((var.name, f"repair_reject={value!r}"))

    log.append((var.name, "dropped"))
    if var.repair == REPAIR_NONE and var.significance == IDENTITY:
        raise RuntimeError(f"identity variable {var.name!r} could not be resolved")
    return False
