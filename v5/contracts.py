"""Family and Architecture contracts, plus their registries.

INV-01: Family defines possibility; Architecture commits construction.

The resolver never imports a Family or an Architecture by name.  It walks
whatever contracts the registry holds, which is what makes "adding a Family is
authoring, not engine programming" (section 48) testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .grammar import HAT_ENVELOPE, STANDARD_ENVELOPE

SLOTS = ("TOP", "BOTTOM", "ONE_PIECE")


@dataclass(frozen=True)
class IdentitySeparation:
    """One perceptual separation an Architecture needs in order to read.

    `floor_scale` multiplies the Architecture's identity_floor, so a pair that
    only needs to be noticeable can say so without inventing a second constant.
    `needs` names an optional feature: the separation is only required when that
    feature was actually instantiated, which keeps a rule about ties from firing
    on a garment that has no tie (INV-03).
    """
    role: str
    against: str
    floor_scale: float = 1.0
    required: bool = True
    needs: str | None = None
    # How load-bearing this cue is when identity is judged as a whole.
    weight: float = 1.0

    @property
    def key(self) -> str:
        return f"{self.role}_vs_{self.against}"


def separations(pairs) -> tuple:
    """Accept bare (role, against) tuples as well as full declarations."""
    return tuple(p if isinstance(p, IdentitySeparation) else IdentitySeparation(*p)
                 for p in pairs)


@dataclass(frozen=True)
class SlotContract:
    """Slot resolves first because it determines representation capabilities."""
    name: str
    render_class: str
    dye_mask: bool
    coverage_axis: str
    envelope: object = STANDARD_ENVELOPE
    # Whether failing to cover the Grammar's required rows shows Farmer skin.
    # True for a torso garment; FALSE for a hat, which has no obligation to
    # cover anything — a small hat simply leaves the head visible, and 120
    # vanilla hats occupy a median of 27% of their frame.
    requires_coverage: bool = True
    # Deepest ramp this slot's art needs, regardless of what the material asks
    # for.  A shirt is 8x8 and reads fine on four steps; a hat is 20x20, is
    # OUTLINED, and carries a form rather than a flat panel.  Measured against
    # the four hats the user picked as good and 116 vanilla hats, our headwear
    # ran 5 distinct colours against their 10.5 and a luminance span of 120
    # against 155-182 — with wool and canvas hats capped at FOUR steps, the
    # highlight step and the light step collapse into one another and the
    # "small hard highlight" the shading asks for cannot be drawn at all.
    min_ramp_depth: int = 4
    # Multiplier on the ramp's LIGHTNESS spread for this slot.  Vanilla hats run
    # a luminance span of 182 and the four reference hats about 155; our
    # headwear ran 120 on the same step table that serves an 8x8 shirt.  A hat
    # is a lit object with a top, a side and an underside, and it needs the
    # range to say so.  Slot-scoped so clothing is untouched — a headwear
    # finding must not restyle every shirt.
    ramp_spread: float = 1.0


SLOT_LIBRARY = {
    "TOP": SlotContract("TOP", "torso_8x8", True, "torso_length"),
    "HEAD": SlotContract("HEAD", "head_20x20", True, "crown_height",
                         envelope=HAT_ENVELOPE, requires_coverage=False,
                         min_ramp_depth=6, ramp_spread=1.5),
}


@dataclass(frozen=True)
class FamilyContract:
    """What is *conceivable* for a kind of garment."""
    name: str
    slot: str
    architectures: dict                 # architecture name -> base weight
    closure_vocabulary: tuple
    aperture_vocabulary: tuple
    limb_vocabulary: tuple
    layer_slot_vocabulary: tuple        # slots that MAY exist
    material_vocabulary: tuple
    coverage_domain: tuple
    color_architecture_vocabulary: tuple
    surface_capabilities: tuple
    style_hook: Callable | None = None


@dataclass(frozen=True)
class ArchitectureContract:
    """How one specific construction tradition is built."""
    name: str
    family: str
    # --- commitments ---
    closure: str
    aperture: str
    limb: str
    topology: tuple                     # required structural pieces
    silhouettes: dict                   # authored closed set -> weight
    layer_slots_opened: tuple
    coverage_range: tuple
    surface_domains: tuple              # regions Surface is allowed to occupy
    occupancy: tuple                    # (zone, feature, mode) claimed by construction
    base_cost: int
    color_architectures: dict           # narrowed from Family, with weights
    materials: dict                     # narrowed from Family, with weights
    # --- behaviour ---
    declare_schema: Callable            # (family, ctx, record) -> [Variable]
    realize: Callable                   # (spec, env) -> Construction
    # (variable name, pieces that carry it) — lets AA place trim without
    # knowing what a collar or a yoke is.
    trim: tuple = ()
    # Role pairs that must visibly separate or the family stops reading.
    # Declared here so AA and the quality gate stop hardcoding sailor landmarks.
    identity_pairs: tuple = ()
    # Minimum luminance separation the FIRST identity pair needs from a palette
    # before that palette is admissible here.  The grammar floor (38) is the
    # point at which a feature stops being visible at all; an Architecture whose
    # identity rides on a one- or two-pixel band needs far more than that, and
    # says so here rather than leaving it to taste.
    identity_floor: float = 38.0
    # Minimum fraction of an identity-carrying piece that must still be painted
    # in its OWN role after composition.  Trim, surface and ornament all write
    # over construction; without a floor a braid can repaint most of a thin
    # collar and the garment silently loses the feature that identifies it.
    identity_retention: float = 1.0
    # Identity is judged compositionally.  A single weak role pair is fatal only
    # when the Architecture's identity, taken together, also falls below this
    # floor — a garment whose other cues are strong still reads even if one
    # relationship went flat.  Expressed as a weighted mean of each cue's
    # measured/required ratio, so a strong cue can carry a weak one.
    identity_composite_floor: float = 0.0
    # How many optional appearance features may coexist before further detail is
    # suppressed.  Busyness control that occupancy and budget cannot express,
    # because these features do not share a zone and are individually cheap.
    max_appearance_features: int | None = None
    # HEAD slot only.  Fashion Sense exposes exactly one lever over the
    # player's hair — HideHair, a boolean — and custom hats never receive the
    # per-hairstyle offset the vanilla path applies (hairstyleHatOffset is only
    # read in the vanilla hat draw).  So there is nothing hairstyle-specific to
    # accommodate: the policy is binary and declared once per Architecture.
    hair_policy: str = "PRESERVE"
    # Authored INTERIORS this Architecture may build its pieces with, by name
    # and IN PRIORITY ORDER (see `library/hat_templates.py`).  The Architecture
    # still owns legality, topology and silhouette; a template owns planes,
    # landmarks, seams and occlusion inside pieces this Architecture has
    # already built, and is invoked from its own `realize`.
    #
    # Which one applies is DERIVED from the geometry already resolved, never
    # rolled — `hat_templates.select` takes the first whose predicate matches,
    # and the family's fallback closes the set.  So a template adds no entropy
    # and needs no variable of its own.  It is a declaration, not a stage:
    # nothing in the pipeline reads this field, only the Architecture that
    # declares it.
    construction_templates: tuple = ()
    # --- declarative QC legality (HEAD slot) ---------------------------------
    # Rules that are load-bearing for one Architecture and wrong for another are
    # declared here rather than relaxed globally.  Every one of these defaults
    # to the strict behaviour, so an Architecture that says nothing keeps the
    # invariant it has today; an Architecture that needs the exception has to
    # name it, and the tests read the declaration rather than a hardcoded list.
    #
    #   allows_directional_pieces  a piece may be present in some frames and
    #                              absent in others (cap visor, hanging tail).
    #                              It may only ADD mass — never move the hat.
    #   allows_split_rows          a row may carry more than one run BELOW the
    #                              widest row.  69% of vanilla hats split a row
    #                              somewhere and 42% split at the base, but a
    #                              split base is a different topology from an
    #                              ear pair and is off unless declared.
    #   allows_base_flare          the lowest rows may be WIDER than the crown
    #                              — a knitted cuff.  22% of the corpus.
    #   allows_detached_mass       the silhouette may have more than one
    #                              connected component.  3 of 112 vanilla hats
    #                              do this; nothing here declares it, and the
    #                              flag exists to mark the boundary rather than
    #                              to be switched on.
    #   allows_extreme_asymmetry   mirror symmetry may fall below the corpus
    #                              floor of 0.80.
    allows_directional_pieces: bool = False
    allows_split_rows: bool = False
    allows_base_flare: bool = False
    allows_detached_mass: bool = False
    allows_extreme_asymmetry: bool = False
    style_hook: Callable | None = None

    @property
    def separation_rules(self) -> tuple:
        return separations(self.identity_pairs)

    def check_against(self, family: FamilyContract) -> None:
        """An Architecture may only narrow, never extend, its Family (INV-01)."""
        def subset(child, parent, what):
            extra = set(child) - set(parent)
            if extra:
                raise ValueError(
                    f"{self.name}: {what} {sorted(extra)} not legal for family "
                    f"{family.name} (INV-01)"
                )
        if self.family != family.name:
            raise ValueError(f"{self.name} belongs to {self.family}, not {family.name}")
        subset([self.closure], family.closure_vocabulary, "closure")
        subset([self.aperture], family.aperture_vocabulary, "aperture")
        subset([self.limb], family.limb_vocabulary, "limb")
        subset(self.layer_slots_opened, family.layer_slot_vocabulary, "layer slots")
        subset(self.coverage_range, family.coverage_domain, "coverage")
        subset(self.materials, family.material_vocabulary, "materials")
        subset(self.color_architectures, family.color_architecture_vocabulary,
               "color architectures")
        subset(self.surface_domains, family.surface_capabilities, "surface domains")


FAMILY_LIBRARY: dict[str, FamilyContract] = {}
ARCHITECTURE_LIBRARY: dict[str, ArchitectureContract] = {}


def register_family(f: FamilyContract) -> FamilyContract:
    FAMILY_LIBRARY[f.name] = f
    return f


def register_architecture(a: ArchitectureContract) -> ArchitectureContract:
    ARCHITECTURE_LIBRARY[a.name] = a
    a.check_against(FAMILY_LIBRARY[a.family])
    return a


def families_for_slot(slot: str) -> dict:
    return {n: f for n, f in FAMILY_LIBRARY.items() if f.slot == slot}
