"""Prototype test suite — canonical section 59."""

from __future__ import annotations

import unittest

from v5 import ag, quality
from v5.color import COLOR_ARCHITECTURES, HARMONIES, resolve_palette
from v5.construction import Piece
from v5.context import roll_context
from v5.contracts import ARCHITECTURE_LIBRARY, FAMILY_LIBRARY
from v5.grammar import (ATTACHED, FABRIC_ROLES, FREE, STANDARD_ENVELOPE, Envelope,
                        compose_occlusion, landmarks, luminance, required_coverage)
from v5.construction import parse_shading
from v5.library import sailor_top
from v5.library.sailor_motifs import SLEEVE_CAPS
from v5.library.sailor_top import INSERT_STENCILS
from v5.material import MATERIALS
from v5.pipeline import generate, generate_batch
from v5.projection import check_continuity, check_coverage, project
from v5.resolver import generate_spec
from v5.rng import Stream
from v5.schema import (CONDITIONAL_SHARE, EXCLUSIVE, OVERLAY, AbsentConcept, Budget,
                       OccupancyLedger, Record, SchemaRegistry, Variable)

SEEDS = range(120)


def _first_with(architecture: str):
    for seed in SEEDS:
        g = generate(seed)
        if g.spec.architecture == architecture:
            return g
    raise AssertionError(f"no {architecture} in the sample")


FAMILY = FAMILY_LIBRARY["SAILOR_TOP"]
ARCH = ARCHITECTURE_LIBRARY["CLASSIC_SQUARE_FLAP"]
MIDDY = ARCHITECTURE_LIBRARY["MIDDY_YOKE"]


class Schema(unittest.TestCase):
    def test_absent_is_not_none(self):
        """A concept that never activated is absent — not `none`, `null` or False."""
        untrimmed = [s for s in (generate_spec(i) for i in SEEDS)
                     if "collar_trim" not in s.parameters]
        self.assertTrue(untrimmed, "expected at least one garment without collar trim")
        spec = untrimmed[0]
        blob = spec.as_dict()
        self.assertNotIn("collar_trim", blob["parameters"])
        self.assertNotIn("collar_trim", repr(blob))
        for s in (generate_spec(i) for i in SEEDS):
            if not s.layers:
                self.assertNotIn("layers", s.as_dict())
            if not s.surface:
                self.assertNotIn("surface", s.as_dict())
            self.assertNotIn(None, s.parameters.values())
            self.assertNotIn(False, s.parameters.values())

    def test_record_raises_for_absent_concept(self):
        record = Record()
        record.write("a", 1, "owner", "pass")
        self.assertEqual(record.get("a"), 1)
        with self.assertRaises(AbsentConcept):
            record.get("lapel_style")
        self.assertFalse(record.has("lapel_style"))

    def test_one_owner_one_pass(self):
        registry = SchemaRegistry()
        v = Variable("collar_width", "A", "structural", (1, 2))
        registry.declare(v)
        with self.assertRaises(ValueError):
            registry.declare(Variable("collar_width", "B", "structural", (1, 2)))
        record = Record()
        record.write("collar_width", 1, "A", "structural")
        with self.assertRaises(ValueError):
            record.write("collar_width", 2, "B", "surface")

    def test_declared_schema_has_unique_owners(self):
        ctx = roll_context(1)
        ctx.budget, ctx.occupancy, ctx.record = Budget(5), OccupancyLedger(()), Record()
        registry = SchemaRegistry()
        registry.declare(*ARCH.declare_schema(FAMILY, ARCH, ctx, ctx.record))
        names = [v.name for v in registry.variables]
        self.assertEqual(len(names), len(set(names)))
        for v in registry.variables:
            self.assertEqual(v.owner, ARCH.name)

    def test_architecture_cannot_introduce_family_illegal_options(self):
        rogue = ARCH.__class__(**{**ARCH.__dict__, "materials": {"denim_twill": 1.0}})
        with self.assertRaises(ValueError):
            rogue.check_against(FAMILY)
        rogue = ARCH.__class__(**{**ARCH.__dict__, "closure": "OPEN_FRONT"})
        with self.assertRaises(ValueError):
            rogue.check_against(FAMILY)

    def test_style_context_cannot_resurrect_illegal_options(self):
        ctx = roll_context(1)
        ctx.register_hook(lambda var, w, rec, c: {**w, "OPEN_FRONT": 5.0})
        var = Variable("closure", "A", "structural", ("PULLOVER",))
        with self.assertRaises(ValueError):
            ctx.reweight(var, var.base_weights(), Record())

    def test_child_variables_only_when_declared(self):
        """surface_period exists only when the surface family is periodic."""
        for spec in (generate_spec(i) for i in SEEDS):
            periodic = spec.surface.get("family") in ("horizontal_stripe", "vertical_stripe")
            self.assertEqual("period" in spec.surface, periodic)
            self.assertEqual("domain" in spec.surface, bool(spec.surface))


class Determinism(unittest.TestCase):
    def test_same_seed_same_spec(self):
        for seed in (0, 7, 41, 99):
            self.assertEqual(generate_spec(seed).as_dict(), generate_spec(seed).as_dict())

    def test_same_spec_same_views(self):
        for seed in (0, 7, 41, 99):
            a, b = generate(seed), generate(seed)
            self.assertEqual(a.projection.directions, b.projection.directions)
            self.assertEqual(a.projection.dye_mask, b.projection.dye_mask)

    def test_streams_are_independent(self):
        """A draw on one stream must not shift another stream's sequence."""
        a = Stream(5, "surface")
        first = [a.unit() for _ in range(3)]
        b = Stream(5, "ornament")
        [b.unit() for _ in range(9)]
        c = Stream(5, "surface")
        self.assertEqual(first, [c.unit() for _ in range(3)])


class Repair(unittest.TestCase):
    def test_repair_stays_inside_the_variable_domain(self):
        """A rejected value is replaced from the SAME domain, never by another variable."""
        log, record = [], Record()
        ctx = roll_context(3)
        ctx.budget, ctx.occupancy, ctx.record = Budget(9), OccupancyLedger(()), record
        from v5.schema import REPAIR_DROP, resolve_variable
        seen = []

        def validate(value, rec, c):
            seen.append(value)
            return value == 3

        var = Variable("surface_period", "A", "surface", (2, 3, 4),
                       repair=REPAIR_DROP, validate=validate)
        self.assertTrue(resolve_variable(var, record, ctx, ctx.budget, log))
        self.assertEqual(record.get("surface_period"), 3)
        self.assertTrue(set(seen) <= {2, 3, 4})

    def test_double_stripe_repairs_rather_than_switching_variable(self):
        """DOUBLE_STRIPE is illegal on a 1px collar; repair picks another trim."""
        for spec in (generate_spec(i) for i in SEEDS):
            if spec.parameters.get("collar_trim") == "DOUBLE_STRIPE":
                self.assertEqual(spec.parameters["collar_width"], 2)


class BudgetRules(unittest.TestCase):
    def test_all_spends_tagged_and_within_pool(self):
        for spec in (generate_spec(i) for i in SEEDS):
            ledger = spec.budget_ledger
            self.assertLessEqual(ledger["used"], ledger["total"])
            for who, tag, amount in ledger["spends"]:
                self.assertIn(tag, ("STRUCTURAL", "SURFACE", "ORNAMENT"))
                self.assertGreaterEqual(amount, 0)
            self.assertEqual(sum(ledger["by_tag"].values()), ledger["used"])

    def test_spend_order_is_construction_surface_ornament(self):
        order = ("STRUCTURAL", "SURFACE", "ORNAMENT")
        for spec in (generate_spec(i) for i in SEEDS):
            ranks = [order.index(t) for _, t, _ in spec.budget_ledger["spends"]]
            self.assertEqual(ranks, sorted(ranks))

    def test_overspend_is_refused(self):
        b = Budget(2)
        b.spend("x", "STRUCTURAL", 2)
        with self.assertRaises(ValueError):
            b.spend("y", "ORNAMENT", 1)

    def test_untagged_spend_is_refused(self):
        with self.assertRaises(ValueError):
            Budget(3).spend("x", "MISC", 1)

    def test_higher_complexity_buys_more_features(self):
        low, high = [], []
        for spec in (generate_spec(i) for i in range(400)):
            n = len(spec.ornaments) + bool(spec.surface) + len(spec.layers)
            (low if spec.roll_context["complexity"] <= 2 else high).append(n)
        self.assertLess(sum(low) / len(low), sum(high) / len(high))


class Occupancy(unittest.TestCase):
    def setUp(self):
        self.ledger = OccupancyLedger(("chest:center", "hem:girth"))

    def test_exclusive_conflict(self):
        self.assertTrue(self.ledger.claim("hem:girth", "hem_band", EXCLUSIVE))
        self.assertFalse(self.ledger.claim("hem:girth", "peplum", EXCLUSIVE))
        self.assertEqual(self.ledger.occupants("hem:girth"), ["hem_band"])

    def test_conditional_share(self):
        self.ledger.claim("chest:center", "front_insert", CONDITIONAL_SHARE)
        self.assertFalse(self.ledger.claim("chest:center", "emblem", CONDITIONAL_SHARE,
                                           condition_met=False))
        self.assertTrue(self.ledger.claim("chest:center", "emblem", CONDITIONAL_SHARE,
                                          condition_met=True))

    def test_overlay(self):
        self.ledger.claim("chest:center", "front_insert", CONDITIONAL_SHARE)
        self.assertTrue(self.ledger.claim("chest:center", "bib", OVERLAY))
        self.assertTrue(self.ledger.is_overpainted("chest:center", "front_insert"))

    def test_exclusive_blocks_conditional_share(self):
        self.ledger.claim("chest:center", "armour_plate", EXCLUSIVE)
        self.assertFalse(self.ledger.claim("chest:center", "emblem", CONDITIONAL_SHARE))


class Projection(unittest.TestCase):
    def test_no_rng_after_spec_finalization(self):
        spec = generate_spec(11)
        for stream in spec.context.streams._streams.values():
            self.assertTrue(stream.frozen)
        with self.assertRaises(RuntimeError):
            spec.context.streams("surface").unit()

    def test_projection_adds_no_design_entropy(self):
        """Every projected pixel already exists in the authored view raster."""
        for seed in (2, 13, 44):
            g = generate(seed)
            authored = {v: set(g.raster[v].values()) for v in ("front", "side", "back")}
            for direction, rows in g.projection.directions.items():
                view = {"front": "front", "right": "side",
                        "left": "side", "back": "back"}[direction]
                for row in rows:
                    for px in row:
                        if px[3]:
                            self.assertIn(px, authored[view])

    def test_left_is_the_mirror_of_right(self):
        g = generate(5)
        mirrored = [list(reversed(r)) for r in g.projection.directions["right"]]
        self.assertEqual(g.projection.directions["left"], mirrored)

    def test_views_agree_across_the_batch(self):
        for seed in SEEDS:
            g = generate(seed)
            self.assertEqual(check_continuity(g.spec, g.construction, g.art), [])
            self.assertEqual(check_coverage(g.spec, g.projection), [])


class EnvelopeContract(unittest.TestCase):
    def test_standard_envelope(self):
        self.assertEqual((STANDARD_ENVELOPE.width, STANDARD_ENVELOPE.height), (8, 8))
        self.assertEqual(STANDARD_ENVELOPE.scale, 4.0)
        self.assertEqual(STANDARD_ENVELOPE.atlas, (8, 32))

    def test_extended_envelope_is_representable(self):
        """The data model carries 8x11 and wider shoulders without code changes."""
        coat = Envelope(width=10, height=11, scale=4.0,
                        direction_body_position=(("right", (1, 0)),))
        self.assertEqual(coat.atlas, (10, 44))
        self.assertEqual(coat.bp_for("right"), (1, 0))
        self.assertEqual(coat.bp_for("front"), (0, 0))
        marks = landmarks(coat)
        self.assertEqual(marks["hem_row"], 10)
        self.assertEqual(marks["center_left"], 4)
        self.assertTrue(all(len(r) == 10 for rs in required_coverage(coat).values() for r in rs))

    def test_architecture_declines_an_envelope_it_has_not_authored(self):
        spec = generate_spec(1)
        with self.assertRaises(ValueError):
            sailor_top.realize(spec, Envelope(width=8, height=11))


class Color(unittest.TestCase):
    def test_components_reference_semantic_roles(self):
        g = generate(9)
        for view in ("front", "side", "back"):
            for pc in g.art.paint[view].values():
                self.assertIn(pc.role, FABRIC_ROLES)

    def test_views_introduce_no_palette_decisions(self):
        for seed in SEEDS:
            g = generate(seed)
            authored = g.spec.palette.all_colors
            for view in ("front", "side", "back"):
                for px in g.raster[view].values():
                    self.assertIn(px, authored)

    def test_ramp_depth_is_material_driven(self):
        stream = Stream(1, "c")
        for name, material in MATERIALS.items():
            pal = resolve_palette("DARK_BODY_LIGHT_COLLAR", "analogous", "cool",
                                  material, Stream(1, "c"))
            self.assertEqual(len(pal.steps), max(4, material.ramp_depth), name)
        del stream

    def test_color_capacity_sits_in_the_corpus_band(self):
        counts = sorted(len(ag.distinct_colors(generate(s).raster)) for s in SEEDS)
        median = counts[len(counts) // 2]
        self.assertGreaterEqual(median, 8)
        self.assertLessEqual(counts[-1], 24)

    def test_declared_palettes_clear_their_architecture_identity_floor(self):
        """A palette is admissible only if it keeps the family reading.

        Sweeps the material x harmony x temperament grid for every palette each
        Architecture declares and checks the FIRST identity pair at p10.  This
        is what makes "incompatible palette" a checkable property rather than a
        matter of taste — and it is the check that retired
        MONOCHROME_CONTRAST_TRIM and LOW_CONTRAST_STRONG_ACCENT from CLASSIC.
        """
        # Scoped to Architectures whose identity is CHROMATIC.  A hat's
        # identity is geometric — brim wider than crown — so BRIMMED_HAT
        # declares no unconditional separation rule and there is nothing here
        # to sweep.  Selecting on the rule rather than on the slot keeps this
        # true for any future family of either kind.
        for name, arch in ARCHITECTURE_LIBRARY.items():
            rule = next((r for r in arch.separation_rules
                         if r.required and not r.needs), None)
            if rule is None:
                continue
            role, against, floor = rule.role, rule.against, (
                arch.identity_floor * rule.floor_scale)
            for ca in arch.color_architectures:
                separations = []
                for mi, material in enumerate(MATERIALS.values()):
                    for harmony in HARMONIES:
                        for temperament in ("cool", "neutral", "warm"):
                            for k in range(4):
                                pal = resolve_palette(ca, harmony, temperament, material,
                                                      Stream(k * 7 + mi, "c"))
                                separations.append(pal.contrast(pal.color(role, "base"),
                                                                pal.color(against, "base")))
                separations.sort()
                p10 = separations[len(separations) // 10]
                self.assertGreaterEqual(
                    p10, floor,
                    f"{name}: {ca} separates {role} from {against} by only {p10:.0f} "
                    f"at p10, under its declared floor of {floor:.0f}")

    def test_rejected_palettes_really_do_fail(self):
        """The two palettes retired from CLASSIC fail the floor they were held to."""
        arch = ARCH
        for ca in ("MONOCHROME_CONTRAST_TRIM", "LOW_CONTRAST_STRONG_ACCENT"):
            self.assertNotIn(ca, arch.color_architectures)
            separations = sorted(
                resolve_palette(ca, h, t, MATERIALS["cotton_drill"], Stream(k, "c"))
                .contrast(resolve_palette(ca, h, t, MATERIALS["cotton_drill"], Stream(k, "c"))
                          .color("trim", "base"),
                          resolve_palette(ca, h, t, MATERIALS["cotton_drill"], Stream(k, "c"))
                          .color("body", "base"))
                for h in HARMONIES for t in ("cool", "neutral", "warm") for k in range(4))
            self.assertLess(separations[len(separations) // 10], arch.identity_floor)

    def test_every_color_architecture_resolves(self):
        for name in COLOR_ARCHITECTURES:
            pal = resolve_palette(name, "complementary", "warm",
                                  MATERIALS["cotton_drill"], Stream(2, "c"))
            self.assertTrue(pal.all_colors)


class Edges(unittest.TestCase):
    def test_free_and_attached_are_distinguished(self):
        g = _first_with("CLASSIC_SQUARE_FLAP")
        collar = g.construction.by_name("collar")
        free = collar.free_edges["front"]
        self.assertTrue(free)
        # the collar's outermost row-0 cell.  It is no longer column 0 — the
        # frame's shoulder corners are body, never identity trim — so take the
        # leftmost cell the collar actually holds rather than a fixed column.
        shoulder = min((c for c in collar.view_cells("front") if c[1] == 0),
                       key=lambda c: c[0])
        self.assertEqual(collar.edge_kind("front", shoulder), ATTACHED)
        self.assertEqual(collar.edge_kind("front", next(iter(free))), FREE)

    def test_attached_edges_receive_no_termination(self):
        """The sleeve joins the body with an attached edge and is never outlined."""
        for seed in (1, 6, 22):
            g = generate(seed)
            sleeve = g.construction.by_name("sleeve")
            self.assertEqual(sleeve.free_edges, {})

    def test_no_global_dark_outline(self):
        """Selective outlining only: the silhouette border is not uniformly dark."""
        from v5.grammar import luminance
        g = generate(0)
        border = [luminance(g.raster["front"][c]) for c in g.construction.silhouette["front"]
                  if any((c[0] + dx, c[1] + dy) not in g.construction.silhouette["front"]
                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        self.assertGreater(max(border) - min(border), 20)


class Occlusion(unittest.TestCase):
    def test_stamps_compose_by_max(self):
        composed = compose_occlusion([{(1, 1): 1, (2, 2): 2}, {(1, 1): 3, (3, 3): 1}])
        self.assertEqual(composed, {(1, 1): 3, (2, 2): 2, (3, 3): 1})

    def test_shadow_lands_outside_the_piece_that_casts_it(self):
        """A declared shadow falls on the fabric the free edge terminates over."""
        for seed in SEEDS:
            g = generate(seed)
            for piece in g.construction.pieces:
                for view, stamp in piece.occlusion.items():
                    own = piece.view_cells(view)
                    for (x, y) in stamp:
                        self.assertNotIn((x, y), own)
                        self.assertTrue(
                            any((x + dx, y + dy) in own
                                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))),
                            f"{piece.name} {view} shadow at {(x, y)} touches no edge")

    def test_occlusion_only_moves_ramp_indices(self):
        for seed in (4, 18, 33):
            g = generate(seed)
            for px in g.raster["back"].values():
                self.assertIn(px, g.spec.palette.all_colors)


class QualityGate(unittest.TestCase):
    def test_gate_classifies_without_mutating_the_generator(self):
        batch = generate_batch(range(40))
        before = [generate_spec(s).as_dict() for s in range(40)]
        after = [g.spec.as_dict() for g in batch]
        self.assertEqual(before, after)
        for g in batch:
            self.assertIn(g.verdict.classification,
                          (quality.ACCEPT, quality.NEAR_DUPLICATE,
                           quality.IDENTITY_TOO_WEAK, quality.LEGIBILITY_FAILURE))

    def test_near_duplicate_interface_exists(self):
        g = generate(1)
        self.assertEqual(quality.distance(g.signature or _sig(g), _sig(g)), 0.0)

    def test_metadata_difference_is_not_visual_diversity(self):
        """Identical rasters must measure as identical, whatever the record says."""
        a, b = generate(7), generate(7)
        self.assertEqual(quality.distance(_sig(a), _sig(b)), 0.0)


def _sig(g):
    return quality.signature(g.spec, g.construction, g.art, g.raster)


class ConstructionRules(unittest.TestCase):
    def test_every_silhouette_cell_is_owned(self):
        for seed in SEEDS:
            generate(seed).construction.validate()

    def test_silhouettes_come_from_the_authored_set(self):
        for spec in (generate_spec(i) for i in SEEDS):
            authored = ARCHITECTURE_LIBRARY[spec.architecture].silhouettes
            self.assertIn(spec.silhouette_ref, authored)

    def test_pieces_never_paint_outside_the_silhouette(self):
        g = generate(12)
        rogue = Piece("rogue", "body", z=9, cells={"front": {(99, 99)}})
        g.construction.pieces.append(rogue)
        with self.assertRaises(ValueError):
            g.construction.validate()


class InGameValidation(unittest.TestCase):
    """Authored-geometry regressions found by in-game Fashion Sense testing.

    Each of these was a single shared motif that misread across a large slice of
    the pool, not a bad roll.  See docs/decisions/SAILOR_INGAME_VALIDATION_01.md
    for the pack, the seeds and the measurements.
    """

    BATCH = None

    @classmethod
    def setUpClass(cls):
        cls.BATCH = generate_batch(range(96))

    def test_back_articulation_is_a_shoulder_not_a_strap(self):
        """It is scoped to the sleeve cap, never to the flap depth.

        Run to the flap depth it put a 1px column of the lightest colour on the
        sheet down the outer edge of the back frame, over the Farmer's arm:
        "back straps too far outward" (003), "two white bars passing through the
        elbows/hands" (045), and a sleeve that looked detached (004).
        """
        for g in self.BATCH:
            cap = SLEEVE_CAPS[g.spec.parameters["sleeve_cap"]]
            shoulder = g.construction.by_name("shoulder")
            if shoulder is None:
                continue
            for x in (0, g.spec.envelope.width - 1):
                rows = sorted(y for (cx, y) in shoulder.view_cells("back") if cx == x)
                self.assertLessEqual(
                    len(rows), cap,
                    f"seed {g.spec.seed}: back articulation is {len(rows)} rows "
                    f"deep at column {x}, sleeve cap is {cap}")

    def test_the_shoulder_never_paints_over_the_collar_it_emerges_beside(self):
        """CLASSIC only: the articulation is OUTBOARD of the collar.

        Placed on the collar's first V row it rendered a two-wide collar one
        cell wide, so the collar mass dropped from full width to a single pixel
        in one row — read in game as a box under the chin (083) and a collar
        "too wide/flat relative to the centre insert" (040).
        """
        for g in self.BATCH:
            if g.spec.architecture != "CLASSIC_SQUARE_FLAP":
                continue
            shoulder = g.construction.by_name("shoulder")
            collar = g.construction.by_name("collar")
            if shoulder is None:
                continue
            overlap = shoulder.view_cells("front") & collar.view_cells("front")
            self.assertFalse(
                overlap,
                f"seed {g.spec.seed}: articulation eats collar at {sorted(overlap)}")

    def test_the_rear_flap_is_not_a_rectangle(self):
        """It leaves the neck narrow and only spans the frame over the shoulders.

        A constant six-of-eight span with a straight hem read as a horizontal
        bar laid across the shoulders (013, 025, 040).
        """
        for g in self.BATCH:
            flap = g.construction.by_name("rear_flap")
            cells = flap.view_cells("back")
            spans = {y: (min(x for (x, r) in cells if r == y),
                         max(x for (x, r) in cells if r == y))
                     for y in {r for (_, r) in cells}}
            self.assertGreater(
                len(set(spans.values())), 1,
                f"seed {g.spec.seed}: rear flap is a rectangle, spans {spans}")

    def test_the_collar_band_is_modelled_not_flat(self):
        """CLASSIC's rows above the V carry an authored interior.

        Filled with one flat value they gave every roll two or three rows of a
        single colour across the whole frame: "collapses into a flat horizontal
        band" (014), "front collar mass too wide/flat" (040).
        """
        for g in self.BATCH:
            if g.spec.architecture != "CLASSIC_SQUARE_FLAP":
                continue
            for y in range(g.construction.meta["notch_depth"]):
                row = [g.raster["front"][(x, y)] for x in range(g.spec.envelope.width)
                       if (x, y) in g.raster["front"]]
                if len(row) < 4:
                    continue
                self.assertGreater(
                    len(set(row)), 1,
                    f"seed {g.spec.seed}: collar row {y} is one flat colour")

    def test_the_dickey_has_a_neckline_not_a_lid(self):
        """The insert's top row models the neck opening instead of capping it.

        Authored `..MLLM..` the brightest cells on the panel sat directly under
        the chin and the dickey read as a rectangular box (083).  Two things are
        asserted, at the two layers that can each break it:

          * the AUTHORED stencil lights the outer pair and leaves the pair under
            the neck opening in shadow.  Written as dark-on-the-centre instead,
            it collapsed to one colour on every palette whose under layer already
            sits at the bottom of its ramp.
          * the RENDERED row is flat on only a small minority of rolls.  Neither
            the order nor a per-roll guarantee is asserted: where collar and
            dickey share a tone the AA edge pass darkens the dickey to separate
            them, and on a short ramp that consumes the one step the stencil had
            to work with.  Separation outranks modelling, correctly, so the
            residual is bounded rather than forbidden.
        """
        for depth, stencil in INSERT_STENCILS.items():
            shading = parse_shading(stencil)
            self.assertLess(
                min(shading[(2, 0)], shading[(5, 0)]),
                min(shading[(3, 0)], shading[(4, 0)]),
                f"insert stencil {depth}: the neck opening is not in shadow")
        flat, total = [], 0
        for g in self.BATCH:
            insert = g.construction.by_name("front_insert")
            if insert is None or not insert.view_cells("front"):
                continue
            cells = insert.view_cells("front")
            top = min(y for (_, y) in cells)
            row = [g.raster["front"][(x, y)] for (x, y) in cells
                   if y == top and (x, y) in g.raster["front"]]
            if len(row) < 4:
                continue
            total += 1
            if len(set(row)) == 1:
                flat.append(g.spec.seed)
        # Measured over the 96-seed pool.  Authored `..MLLM..`, 46 of the 47
        # CLASSIC rolls put the brightest cells of the panel directly under the
        # chin — the defect, and systemic, which is what made it a motif bug and
        # not a bad roll.  Authored `..HMMH..` that falls to 12, all of them
        # cases where the AA spent the ramp on collar-to-dickey separation, and
        # 6 rolls go flat for the same reason.  The bound is a ceiling on that
        # residual, not a target.
        self.assertLessEqual(
            len(flat), round(total * 0.15),
            f"{len(flat)}/{total} dickey top rows are flat: {flat}")


class SailorQCLock(unittest.TestCase):
    """LOCKED by human visual review, 2026-09-04.

    The Sailor pool's quality-control behaviour is fixed at these values.  It was
    arrived at by review of a 96-seed batch, not by fitting, and it is pinned
    here so a later change to the palette, AA or renderer cannot move acceptance
    without this failing loudly.

    The CONFIGURATION below — floors, retention, composite, separation rules —
    is what is locked, and it has not been touched.  The batch OUTCOME is a
    consequence of it and moves when the authored geometry moves.

    Original residual: seeds 24 and 30 were ACCEPTED though a reviewer would
    reject them, and seed 46 was REJECTED though a reviewer would accept it.

    2026-09-04, in-game validation pass.  In-game testing produced exactly the
    repeatable failure pattern this lock was waiting on: a back shoulder
    articulation scoped to the flap depth, a rectangular rear flap, a flat
    collar band and a flat-lidded dickey (see
    docs/decisions/SAILOR_INGAME_VALIDATION_01.md).  Those are authored
    geometry, so they were fixed in v5/library, and the outcome below is the
    re-measured consequence.  No QC number moved.

    Two of the three documented human-review discrepancies closed on their own
    when the geometry was corrected: seed 46 now ACCEPTs and seed 24 now
    REJECTs, both in the direction the reviewer called.  That is evidence the
    gate was reading real defects and the metric never needed retuning.

    Do not retune to close the remaining gap (seed 30).
    """

    QC = {
        "CLASSIC_SQUARE_FLAP": dict(
            identity_floor=80.0, identity_retention=0.80,
            identity_composite_floor=1.20, max_appearance_features=3,
            rules=(("trim_vs_body", 1.0, True, None),
                   ("under_layer_vs_trim", 0.5, True, None),
                   ("accent_vs_body", 0.7, True, "tie"),
                   ("accent_vs_trim", 0.8, True, "tie"))),
        "MIDDY_YOKE": dict(
            identity_floor=80.0, identity_retention=0.80,
            identity_composite_floor=1.20, max_appearance_features=3,
            rules=(("under_layer_vs_trim", 1.0, True, None),
                   ("accent_vs_body", 0.7, True, "tie"),
                   ("accent_vs_under_layer", 0.4, False, "tie"))),
    }

    def test_declared_qc_configuration_is_locked(self):
        for name, want in self.QC.items():
            arch = ARCHITECTURE_LIBRARY[name]
            for field in ("identity_floor", "identity_retention",
                          "identity_composite_floor", "max_appearance_features"):
                self.assertEqual(getattr(arch, field), want[field],
                                 f"{name}.{field} moved; see SailorQCLock")
            got = tuple((r.key, r.floor_scale, r.required, r.needs)
                        for r in arch.separation_rules)
            self.assertEqual(got, want["rules"], f"{name} separation rules moved")

    def test_locked_batch_outcome(self):
        batch = generate_batch(range(96))
        counts = {}
        for g in batch:
            counts[g.verdict.classification] = counts.get(g.verdict.classification, 0) + 1
        # Re-pinned after in-game validation pass 03.  The locked QC
        # CONFIGURATION above is untouched; the authored geometry it measures
        # moved again (shoulder articulation, hem/waistband inset, side tie),
        # so the measured outcome moved with it.  It moved UP: the articulation
        # that was painting a foreign light pixel at the armpit was also
        # costing identity separation, and removing it recovered four rolls.
        self.assertEqual(counts, {quality.ACCEPT: 93,
                                  quality.IDENTITY_TOO_WEAK: 1,
                                  quality.NEAR_DUPLICATE: 2})
        rejected = {g.spec.seed: g.verdict.classification
                    for g in batch if g.verdict.classification != quality.ACCEPT}
        # 13, 23, 54 and 76 all recovered in pass 03 — the shoulder
        # articulation had been consuming under_layer area that
        # under_layer_vs_trim is measured on.  Only 24 still fails identity.
        self.assertEqual(rejected, {21: quality.NEAR_DUPLICATE,
                                    24: quality.IDENTITY_TOO_WEAK,
                                    73: quality.NEAR_DUPLICATE})

    def test_accepted_residual_stays_accepted(self):
        """Seed 30 is the one remaining roll the reviewer would reject.

        Seed 24 was the other; correcting the authored geometry moved it onto
        the reviewer's side of the gate without any QC number changing, so it is
        no longer a residual and is asserted as REJECTED above.
        """
        batch = {g.spec.seed: g for g in generate_batch(range(96))}
        self.assertEqual(batch[30].verdict.classification, quality.ACCEPT,
                         "seed 30 is a known, accepted residual")
        self.assertEqual(batch[46].verdict.classification, quality.ACCEPT,
                         "seed 46 was rejected against reviewer judgement; the "
                         "geometry fix, not a retune, is what let it through")

    def test_retention_constraint_still_active(self):
        """Retention solved a real problem and must not be optimised away."""
        batch = generate_batch(range(96))
        acted = sum(1 for g in batch
                    if any(n.startswith("retention:") for n in g.art.notes))
        self.assertGreaterEqual(acted, 30, "the retention guard stopped firing")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class SilhouetteIntegrity(unittest.TestCase):
    """Pass 02: defects the eye caught that no existing metric did.

    Measured over the 68 frames of the shipping reference packs: ZERO contain a
    transparent cell with fabric directly above and below it.  Ours had one in
    every roll (side) and two more in every strap roll (back), which in game
    read as an armpit hole (002, 011) and a protruding side profile (000).
    """

    @staticmethod
    def _bites(cells):
        return {(x, y) for y in range(8) for x in range(8)
                if (x, y) not in cells
                and any((x, j) in cells for j in range(0, y))
                and any((x, j) in cells for j in range(y + 1, 8))}

    def test_no_frame_has_an_enclosed_bite(self):
        for g in generate_batch(range(96)):
            for view in ("front", "side", "back"):
                self.assertEqual(
                    self._bites(set(g.raster[view].keys())), set(),
                    f"seed {g.spec.seed} {view} has an enclosed gap")

    def test_neck_opening_is_one_span_per_row(self):
        """A row may open at the neck; it may not be split by a fabric bridge."""
        for g in generate_batch(range(96)):
            cells = set(g.raster["front"].keys())
            for y in range(8):
                row = sorted(x for x in range(8) if (x, y) in cells)
                if not row:
                    continue
                runs = 1 + sum(1 for a, b in zip(row, row[1:]) if b - a > 1)
                self.assertLessEqual(runs, 2, f"seed {g.spec.seed} row {y} split")

    def test_front_shoulder_corners_are_never_identity_trim(self):
        """The front frame's top corners are where the Farmer's arm reads.

        FRONT only.  003 reported the front collar edge as "lying on the arm";
        the back's own outward-reaching defect is the flap, and tapering its
        hem fixes that without costing the back band the area its
        collar-against-body separation is measured on.
        """
        for g in generate_batch(range(96)):
            for piece in g.construction.pieces:
                if piece.role != "trim":
                    continue
                held = piece.view_cells("front") & {(0, 0), (7, 0)}
                self.assertEqual(held, set(),
                                 f"seed {g.spec.seed} {piece.name} front "
                                 f"holds a shoulder corner")

    def test_flap_hem_ends_inboard_of_the_arm(self):
        """The flap's lowest row never reaches the outer body columns."""
        from v5.library.sailor_motifs import flap_outline
        for depth in (3, 4, 5):
            cells = flap_outline(depth)
            bottom = max(y for _, y in cells)
            xs = [x for (x, y) in cells if y == bottom]
            self.assertGreaterEqual(min(xs), 2)
            self.assertLessEqual(max(xs), 5)


class LineTermination(unittest.TestCase):
    """grammar.terminate_inboard — the shared decorative-line rule.

    Confirmed independently by hem_band, the MIDDY waistband and horizontal
    stripes: a decorative line that ENDS on the silhouette boundary reads as
    passing through the figure, because that is where the Farmer's arm and body
    edge are drawn.  Structural panels and seams are deliberately exempt.
    """

    def test_long_run_is_pulled_inboard(self):
        from v5.grammar import terminate_inboard
        row = {(x, 3) for x in range(8)}
        self.assertEqual(terminate_inboard(row, run_axis=0),
                         {(x, 3) for x in range(1, 7)})

    def test_vertical_run_uses_the_other_axis(self):
        from v5.grammar import terminate_inboard
        col = {(2, y) for y in range(6)}
        self.assertEqual(terminate_inboard(col, run_axis=1),
                         {(2, y) for y in range(1, 5)})

    def test_short_run_is_preserved_not_erased(self):
        """The guard is the point: insetting must not delete a pattern."""
        from v5.grammar import LINE_MIN_RUN, terminate_inboard
        for n in range(1, LINE_MIN_RUN):
            run = {(x, 3) for x in range(n)}
            self.assertEqual(terminate_inboard(run, run_axis=0), run,
                             f"a {n}-cell run must survive intact")

    def test_panel_is_not_terminated(self):
        """A panel is a structural block; its edges belong on the boundary."""
        from v5.surface import SURFACES, figure_cells
        cells = {(x, y) for x in range(8) for y in range(4)}
        got = figure_cells(SURFACES["panel"], cells, period=2, phase=0,
                           registration=0)
        self.assertTrue(got)
        self.assertEqual({y for _, y in got}, {0, 1, 2, 3})

    def test_no_line_endpoint_lands_on_the_boundary_unless_guarded(self):
        from v5.grammar import LINE_MIN_RUN
        vertical = {"vertical_stripe"}
        for g in generate_batch(range(96)):
            for view in ("front", "side", "back"):
                sil = set(g.raster[view].keys())
                if not sil:
                    continue
                runs = {}
                for cell, pc in g.art.paint[view].items():
                    parts = pc.feature.split(":")
                    kind = parts[1] if parts[0] == "surface" and len(parts) > 1 else parts[0]
                    if kind not in ("horizontal_stripe", "vertical_stripe",
                                    "cuff_band", "hem_band"):
                        continue
                    axis = 1 if kind in vertical else 0
                    runs.setdefault((kind, axis, cell[1 - axis]), set()).add(cell[axis])
                for (kind, axis, grp), vals in runs.items():
                    if len(vals) < LINE_MIN_RUN:
                        continue               # guarded: too short to inset
                    ext = [c[axis] for c in sil if c[1 - axis] == grp]
                    for end in (min(vals), max(vals)):
                        self.assertNotIn(
                            end, (min(ext), max(ext)),
                            f"seed {g.spec.seed} {view} {kind} ends on the boundary")


class SurfaceDropsSafely(unittest.TestCase):
    def test_periodic_surface_without_a_period_is_absent_not_defaulted(self):
        """A dropped period must drop the pattern, not invent one.

        aa.py read `spec.surface.get("period", 2)`, so an unresolved period
        painted anyway and check_continuity then crashed on the key that was
        never set.  Absent is not None (INV-04).
        """
        from v5 import aa, projection
        from v5.surface import SURFACES

        class _Spec:
            pass
        g = generate(0)
        spec = g.spec
        stripe = dict(family="horizontal_stripe", domain="shell")   # no period
        object.__setattr__(spec, "surface", stripe) if hasattr(spec, "__dataclass_fields__") \
            else setattr(spec, "surface", stripe)
        self.assertTrue(SURFACES[stripe["family"]].periodic)
        art = aa.plan(spec, g.construction,
                      ARCHITECTURE_LIBRARY[spec.architecture])
        painted = [c for v in ("front", "side", "back")
                   for c, pc in art.paint[v].items()
                   if pc.feature.startswith("surface:")]
        self.assertEqual(painted, [], "an unresolvable pattern must not paint")
        # and continuity must not raise
        projection.check_continuity(spec, g.construction, art)

