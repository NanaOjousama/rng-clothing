"""HAT V5 — corpus-derived contracts.

The constants in `v5.grammar` were produced by measuring the 120 vanilla hats
in `Characters/Farmer/hats.png`.  `VanillaHatCorpus` re-derives them at test
time from that file, so a constant can never silently drift away from the
corpus it claims to describe.  Everything else asserts that generated hats sit
inside the measured ranges.

Deliberately NOT asserted here (shirt-only rules that must not leak):
  * required_coverage — a hat owes no coverage; the slot declares this.
  * one-span-per-row — 82 of 120 vanilla hats legitimately break it
    (brim gaps, ear flaps), unlike shirts where a split reads as a hole.
"""

from __future__ import annotations

import os
import statistics as st
import unittest

from v5.grammar import (HAT_BRIMLESS_BOUNDS, HAT_BRIMMED_BOUNDS, HAT_DIRECTION_PROFILE, HAT_ENVELOPE,
                        HEAD_BOX, RENDER_CLASS_OUTLINE, brim_line, crown_metrics,
                        enclosed_holes, head_box, mirror_symmetry, occupied_bbox,
                        outline_delta, overhang, row_widths)
from v5.contracts import ARCHITECTURE_LIBRARY, SLOT_LIBRARY
from v5.library import brimmed_hat, brimless_hat  # noqa: F401  (registers contracts)
from v5.library import hat_templates
from v5.pipeline import generate, generate_batch
from v5.pngio import read_rgba_png

VANILLA_HATS = ("/run/media/deck/USD00/steamapps/common/Stardew Valley/"
                "Content (unpacked)/Characters/Farmer/hats.png")
SEEDS = range(48)


def _load_vanilla():
    """120 vanilla hats as {direction: cells}, or None if the game is absent."""
    if not os.path.exists(VANILLA_HATS):
        return None
    im = read_rgba_png(VANILLA_HATS)
    w, h = len(im[0]), len(im)
    dirs = ("front", "right", "left", "back")
    out, idx = [], 0
    while True:
        x0, y0 = (idx * 20) % w, (idx * 20 // w) * 80
        if y0 + 80 > h:
            break
        frames = {d: {(x, y) for y in range(20) for x in range(20)
                      if im[y0 + di * 20 + y][x0 + x][3] > 0}
                  for di, d in enumerate(dirs)}
        if len(frames["front"]) >= 12:
            out.append(frames)
        idx += 1
    return out


def _is_brimmed(cells):
    return crown_metrics(cells)["brim_ratio"] > 1.15


class VanillaHatCorpus(unittest.TestCase):
    """The frozen constants must still describe the corpus they came from."""

    @classmethod
    def setUpClass(cls):
        cls.hats = _load_vanilla()
        if cls.hats is None:
            raise unittest.SkipTest("vanilla hats.png not available")
        cls.brimmed = [h for h in cls.hats if _is_brimmed(h["front"])]

    def test_corpus_shape(self):
        self.assertEqual(len(self.hats), 120)
        self.assertEqual(len(self.brimmed), 74)

    def test_head_box_is_where_the_hats_are(self):
        """Every column/row of HEAD_BOX is covered by most of the corpus."""
        x0, x1, y0, y1 = HEAD_BOX
        n = len(self.hats)
        for x in range(x0, x1 + 1):
            hit = sum(1 for h in self.hats if any(c[0] == x for c in h["front"]))
            self.assertGreaterEqual(hit / n, 0.95, f"col {x} only {hit}/{n}")
        for y in range(y0, y1 + 1):
            hit = sum(1 for h in self.hats if any(c[1] == y for c in h["front"]))
            self.assertGreaterEqual(hit / n, 0.79, f"row {y} only {hit}/{n}")

    def test_head_box_is_tight(self):
        """The rows/cols just outside HEAD_BOX are markedly less occupied."""
        x0, x1, _, y1 = HEAD_BOX
        n = len(self.hats)
        for x in (x0 - 2, x1 + 2):
            hit = sum(1 for h in self.hats if any(c[0] == x for c in h["front"]))
            self.assertLess(hit / n, 0.7, f"col {x} at {hit}/{n} — box too tight")
        hit = sum(1 for h in self.hats if any(c[1] == y1 + 2 for c in h["front"]))
        self.assertLess(hit / n, 0.5)

    def test_frozen_bounds_match_the_corpus(self):
        f = [h["front"] for h in self.brimmed]
        measured = {
            "cells": [len(c) for c in f],
            "bbox_w": [occupied_bbox(c)[1] - occupied_bbox(c)[0] + 1 for c in f],
            "bbox_h": [occupied_bbox(c)[3] - occupied_bbox(c)[2] + 1 for c in f],
            "crown_top": [crown_metrics(c)["crown_top"] for c in f],
            "brim_line": [brim_line(c) for c in f],
            "brim_width": [crown_metrics(c)["brim_width"] for c in f],
            "crown_height": [crown_metrics(c)["crown_height"] for c in f],
            "crown_width": [crown_metrics(c)["crown_width"] for c in f],
        }
        for key, values in measured.items():
            lo, hi = HAT_BRIMMED_BOUNDS[key]
            v = sorted(values)
            p05, p95 = v[int(0.05 * (len(v) - 1))], v[int(0.95 * (len(v) - 1))]
            self.assertEqual((p05, p95), (lo, hi),
                             f"{key} drifted: corpus says {(p05, p95)}, "
                             f"HAT_BRIMMED_BOUNDS says {(lo, hi)}")

    def test_corpus_is_outlined(self):
        """117/120 — this is why hats get RENDER_CLASS_OUTLINE and shirts do not."""
        im = read_rgba_png(VANILLA_HATS)
        w, h = len(im[0]), len(im)
        outlined = total = 0
        idx = 0
        while True:
            x0, y0 = (idx * 20) % w, (idx * 20 // w) * 80
            if y0 + 80 > h:
                break
            raster = {(x, y): im[y0 + y][x0 + x][:3]
                      for y in range(20) for x in range(20)
                      if im[y0 + y][x0 + x][3] > 0}
            if len(raster) >= 12:
                total += 1
                if outline_delta(raster) < -10:
                    outlined += 1
            idx += 1
        self.assertEqual(total, 120)
        self.assertGreaterEqual(outlined / total, 0.95,
                                f"only {outlined}/{total} vanilla hats outlined")
        self.assertTrue(RENDER_CLASS_OUTLINE["head_20x20"])
        self.assertFalse(RENDER_CLASS_OUTLINE["torso_8x8"])

    def test_corpus_has_no_enclosed_holes(self):
        clean = sum(1 for h in self.hats
                    if not enclosed_holes(h["front"], HAT_ENVELOPE))
        self.assertGreaterEqual(clean / len(self.hats), 0.85)

    def test_corpus_is_horizontally_centred(self):
        off = []
        for h in self.hats:
            x0, x1, _, _ = occupied_bbox(h["front"])
            off.append((x0 + x1) / 2 - (HAT_ENVELOPE.width - 1) / 2)
        self.assertEqual(st.median(off), 0.0)
        v = sorted(off)
        self.assertEqual((v[int(.1 * (len(v) - 1))], v[int(.9 * (len(v) - 1))]),
                         (0.0, 0.0), "centring is absolute in the corpus")

    def test_split_rows_are_normal_for_hats(self):
        """The shirt one-span-per-row rule must NOT be ported."""
        split = 0
        for h in self.hats:
            rows: dict[int, list[int]] = {}
            for (x, y) in h["front"]:
                rows.setdefault(y, []).append(x)
            if any(1 + sum(1 for a, b in zip(sorted(xs), sorted(xs)[1:]) if b - a > 1) > 1
                   for xs in rows.values()):
                split += 1
        self.assertGreater(split / len(self.hats), 0.5,
                           "majority of vanilla hats have split rows")

    def test_left_mirrors_right(self):
        mirrored = sum(1 for h in self.hats
                       if h["left"] == {(19 - x, y) for x, y in h["right"]})
        self.assertGreaterEqual(mirrored / len(self.hats), 0.75)

    def test_back_carries_more_mass_than_front(self):
        self.assertGreater(st.median([len(h["back"]) for h in self.brimmed]),
                           st.median([len(h["front"]) for h in self.brimmed]))


class HatSlot(unittest.TestCase):
    def test_slot_declares_its_own_envelope_and_render_class(self):
        slot = SLOT_LIBRARY["HEAD"]
        self.assertEqual((slot.envelope.width, slot.envelope.height), (20, 20))
        self.assertEqual(slot.envelope.scale, 4.0)
        self.assertEqual(slot.render_class, "head_20x20")

    def test_hats_owe_no_coverage(self):
        self.assertFalse(SLOT_LIBRARY["HEAD"].requires_coverage)
        self.assertTrue(SLOT_LIBRARY["TOP"].requires_coverage)

    def test_no_shirt_coverage_problems_are_raised(self):
        for g in generate_batch(SEEDS, slot="HEAD"):
            self.assertEqual(
                [p for p in g.problems if "uncovered" in p], [],
                f"seed {g.spec.seed}: shirt coverage rule leaked into hats")


class HatPlacement(unittest.TestCase):
    """Placement is invisible to shirt-style metrics, so it gets its own gate."""

    @classmethod
    def setUpClass(cls):
        cls.batch = generate_batch(SEEDS, slot="HEAD")

    def test_envelope(self):
        for g in self.batch:
            self.assertEqual((g.spec.envelope.width, g.spec.envelope.height),
                             (20, 20))

    def test_mass_registers_to_the_head_box(self):
        x0, x1, y0, y1 = head_box(HAT_ENVELOPE)
        for g in self.batch:
            cells = set(g.raster["front"])
            for x in range(x0, x1 + 1):
                self.assertTrue(any(c[0] == x for c in cells),
                                f"seed {g.spec.seed}: head column {x} uncovered")
            bx0, bx1, by0, by1 = occupied_bbox(cells)
            self.assertLessEqual(by0, y0 + 2, f"seed {g.spec.seed}: sits too low")
            self.assertGreaterEqual(by1, y1 - 3, f"seed {g.spec.seed}: sits too high")

    def test_horizontal_centring_is_exact(self):
        """Symmetry is the DEFAULT; only a declared motif may break it.

        72% of vanilla brimmed hats are exact mirrors, and the ones that are
        not sit at median 0.94 / min 0.80.  So a hat with no asymmetry motif
        must be perfectly symmetric and perfectly centred, and one carrying a
        motif must stay inside the corpus band rather than drifting freely.
        """
        for g in self.batch:
            from v5.library.brimmed_hat import has_odd_rows
            motif = g.spec.parameters.get("asymmetry", "NONE")
            if has_odd_rows(g.spec.parameters["crown_profile"],
                            g.spec.architecture):
                continue      # declared exception: odd rows are half a pixel off
            for view in ("front", "back"):
                cells = set(g.raster[view])
                score = mirror_symmetry(cells, HAT_ENVELOPE)
                x0, x1, _, _ = occupied_bbox(cells)
                centre = (x0 + x1) / 2
                if motif == "NONE":
                    self.assertEqual(score, 1.0,
                                     f"seed {g.spec.seed} {view}: asymmetric "
                                     f"without a declared motif")
                    self.assertEqual(centre, (HAT_ENVELOPE.width - 1) / 2,
                                     f"seed {g.spec.seed} {view} off-centre")
                else:
                    self.assertGreaterEqual(
                        score, 0.80,
                        f"seed {g.spec.seed} {view}: {motif} is wilder than "
                        f"anything in the corpus")
                    self.assertLessEqual(
                        abs(centre - (HAT_ENVELOPE.width - 1) / 2), 1.0,
                        f"seed {g.spec.seed} {view}: {motif} unbalanced the hat")

    def test_asymmetry_is_closed_set_and_profile_scoped(self):
        from v5.library.brimmed_hat import asymmetry_options
        for g in self.batch:
            p = g.spec.parameters
            motif = p.get("asymmetry", "NONE")
            self.assertIn(motif, asymmetry_options(p["crown_profile"],
                                                   p.get("brim_profile", "TAPERED")),
                          f"seed {g.spec.seed}: {motif} not legal for "
                          f"{p['crown_profile']}/{p.get('brim_profile', '-')}")

    def test_asymmetry_magnitude_matches_the_corpus(self):
        """Vanilla: median 6 unmirrored cells, p90 13, max 36."""
        for g in self.batch:
            if g.spec.parameters.get("asymmetry", "NONE") == "NONE":
                continue
            cells = set(g.raster["front"])
            odd = {c for c in cells if (19 - c[0], c[1]) not in cells}
            self.assertLessEqual(len(odd), 20,
                                 f"seed {g.spec.seed}: {len(odd)} odd cells")

    def test_side_views_are_not_leaned_twice(self):
        """A profile already shows one side; motifs apply to front/back only."""
        import v5.library.brimmed_hat as bh
        for g in self.batch:
            if g.spec.parameters.get("asymmetry", "NONE") == "NONE":
                continue
            side = set(g.raster["side"])
            bl = brim_line(side)
            crown = {c for c in side if c[1] < bl}
            if not crown:
                continue
            cl, cr = min(x for x, _ in crown), max(x for x, _ in crown)
            self.assertEqual((cl + cr) / 2, (HAT_ENVELOPE.width - 1) / 2,
                             f"seed {g.spec.seed}: side crown displaced")

    def test_no_enclosed_holes(self):
        for g in self.batch:
            for view in ("front", "side", "back"):
                self.assertEqual(
                    enclosed_holes(set(g.raster[view]), HAT_ENVELOPE), set(),
                    f"seed {g.spec.seed} {view} has an enclosed hole")

    def test_overhang_within_corpus_range(self):
        lo, hi = HAT_BRIMMED_BOUNDS["overhang"]
        for g in self.batch:
            left, right = overhang(set(g.raster["front"]), HEAD_BOX)
            self.assertTrue(lo <= left <= hi and lo <= right <= hi,
                            f"seed {g.spec.seed}: overhang {(left, right)}")

    def test_brim_sits_on_the_head_not_the_face(self):
        """The brim line is what decides hat-on-head vs hat-over-eyes.

        Vanilla: median 10, p90 12.  The frame is anchored to the head, so a
        brim two rows below that lands on the brow — reported in game as hats
        covering the Farmer's face.  Nothing else catches this: such a hat
        passes occupancy, bbox, colour, symmetry and every corpus bound.
        """
        lo, hi = HAT_BRIMMED_BOUNDS["brim_line"]
        bottoms = []
        for g in self.batch:
            if g.spec.architecture != "BRIMMED_HAT":
                continue
            cells = set(g.raster["front"])
            bl = brim_line(cells)
            self.assertTrue(lo <= bl <= hi,
                            f"seed {g.spec.seed}: brim line {bl} outside {(lo, hi)}")
            self.assertLessEqual(bl, 12,
                                 f"seed {g.spec.seed}: brim line {bl} is on the face")
            bottoms.append(max(y for _, y in cells))
        self.assertLessEqual(max(bottoms), 14,
                             "a hat reaches below the corpus range for this family")

    def test_tall_crowns_grow_upward_not_downward(self):
        """A tall crown must use rows 0-3, not push its brim onto the face."""
        from v5.library.brimmed_hat import CROWN_PROFILES
        for g in self.batch:
            profile = g.spec.parameters["crown_profile"]
            if g.spec.architecture != "BRIMMED_HAT":
                continue
            if len(CROWN_PROFILES[profile]) < 9:
                continue
            top = min(y for _, y in set(g.raster["front"]))
            self.assertLessEqual(top, 4,
                                 f"seed {g.spec.seed}: {profile} starts at row "
                                 f"{top} instead of reaching upward")

    def test_head_position_x_is_zero_at_20x20(self):
        """(w - 20*(4/Scale))/2 == 0, so the pack needs no horizontal offset."""
        env = HAT_ENVELOPE
        self.assertEqual((env.width - 20 * (4 / env.scale)) / 2, 0)


class HatSilhouette(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = generate_batch(SEEDS, slot="HEAD")

    def test_each_architecture_is_what_it_claims(self):
        """The 1.15x flare is what separates the two Architectures."""
        for g in self.batch:
            m = crown_metrics(set(g.raster["front"]))
            if g.spec.architecture == "BRIMMED_HAT":
                self.assertGreater(m["brim_ratio"], 1.15,
                                   f"seed {g.spec.seed}: brim not wider than crown")
            else:
                self.assertLessEqual(m["brim_ratio"], 1.15,
                                     f"seed {g.spec.seed}: BRIMLESS has a brim")

    def test_within_corpus_bounds(self):
        checks = {
            "cells": lambda c: len(c),
            "bbox_w": lambda c: occupied_bbox(c)[1] - occupied_bbox(c)[0] + 1,
            "bbox_h": lambda c: occupied_bbox(c)[3] - occupied_bbox(c)[2] + 1,
            "crown_top": lambda c: crown_metrics(c)["crown_top"],
            "brim_line": lambda c: brim_line(c),
            "brim_width": lambda c: crown_metrics(c)["brim_width"],
            "crown_height": lambda c: crown_metrics(c)["crown_height"],
            "crown_width": lambda c: crown_metrics(c)["crown_width"],
        }
        for g in self.batch:
            cells = set(g.raster["front"])
            bounds = (HAT_BRIMMED_BOUNDS if g.spec.architecture == "BRIMMED_HAT"
                      else HAT_BRIMLESS_BOUNDS)
            for key, fn in checks.items():
                if key not in bounds:
                    continue
                lo, hi = bounds[key]
                self.assertTrue(lo <= fn(cells) <= hi,
                                f"seed {g.spec.seed}: {key}={fn(cells)} "
                                f"outside corpus {(lo, hi)}")

    def test_is_outlined(self):
        """117/120 vanilla hats are outlined; every hat we SHIP must be too.

        Scoped to accepted rolls, and the threshold is unchanged.  A roll the
        gate rejects for flatness (one or two value levels) cannot carry an
        outline for exactly the reason it is being rejected — asserting the
        property on output we discard would only push us to weaken the bar for
        everything else.
        """
        for g in self.batch:
            if g.verdict.classification != "ACCEPT":
                continue
            self.assertLess(outline_delta(g.raster["front"]), -10,
                            f"seed {g.spec.seed}: no darker border")

    def test_colour_count_matches_corpus(self):
        lo, hi = HAT_BRIMMED_BOUNDS["colors"]
        for g in self.batch:
            n = len({tuple(v) for v in g.raster["front"].values()})
            self.assertLessEqual(n, hi + 4, f"seed {g.spec.seed}: {n} colours")

    def test_back_carries_more_mass_than_front(self):
        for g in self.batch:
            self.assertGreaterEqual(len(g.raster["back"]), len(g.raster["front"]),
                                    f"seed {g.spec.seed}: thin back")

    def test_side_brim_is_balanced_about_the_crown(self):
        """Vanilla side brims are symmetric about the crown, not swept back.

        Measured on 74 vanilla brimmed hats: front:back reach ratio median
        1.00, 45 of 73 exactly equal, 65 of 73 within one cell.  A wider skew
        reads as one side of the brim having been cut short, and belongs to an
        Architecture that explicitly justifies it — not to ordinary hats.
        """
        from v5.grammar import HAT_SIDE_BRIM_SKEW
        for g in self.batch:
            if g.spec.architecture != "BRIMMED_HAT":
                continue
            side = set(g.raster["side"])
            bl = brim_line(side)
            crown = {c for c in side if c[1] < bl}
            if not crown:
                continue
            cl = min(x for x, _ in crown)
            cr = max(x for x, _ in crown)
            centre = (cl + cr) / 2
            row = [x for (x, y) in side if y == bl]
            from v5.library.brimmed_hat import has_odd_rows
            skew = HAT_SIDE_BRIM_SKEW + (
                1 if has_odd_rows(g.spec.parameters["crown_profile"]) else 0)
            back, front = centre - min(row), max(row) - centre
            self.assertLessEqual(
                abs(front - back), skew,
                f"seed {g.spec.seed}: side brim reaches {back} back / "
                f"{front} front — skewed, not projected")

    def test_side_brim_matches_the_front_brim_width(self):
        """The corpus draws the same brim head-on and in profile (both 14)."""
        from v5.grammar import HAT_SIDE_BRIM_SKEW
        for g in self.batch:
            if g.spec.architecture != "BRIMMED_HAT":
                continue
            fw = crown_metrics(set(g.raster["front"]))["brim_width"]
            side = set(g.raster["side"])
            row = [x for (x, y) in side if y == brim_line(side)]
            # BRIM_FLICK deliberately kicks the front brim out one cell on one
            # side and does not touch the profile, so it is allowed that much.
            from v5.library.brimmed_hat import has_odd_rows
            tol = HAT_SIDE_BRIM_SKEW + (
                1 if g.spec.parameters.get("asymmetry") == "BRIM_FLICK" else 0)
            if has_odd_rows(g.spec.parameters["crown_profile"],
                            g.spec.architecture):
                tol += 1      # an odd row is half a pixel off by construction
            self.assertLessEqual(
                abs((max(row) - min(row) + 1) - fw), tol,
                f"seed {g.spec.seed}: side brim width disagrees with the front")


class HatHairPolicy(unittest.TestCase):
    """Hair is preserved unless the Architecture declares AND earns otherwise.

    The first version of this asked whether each head-box column had any cell
    within the top five rows — true of any crown — so 78 of 89 rolls hid the
    Farmer's hair and a brimmed hat made them look bald from behind.
    """

    def test_architecture_declares_a_hair_policy(self):
        arch = ARCHITECTURE_LIBRARY["BRIMMED_HAT"]
        self.assertIn(arch.hair_policy, ("HIDE", "PRESERVE"))

    def test_brimmed_hats_preserve_hair(self):
        """A brim sits ON the head; hair falls below and behind it."""
        from v5.library.brimmed_hat import hair_policy_for
        self.assertEqual(ARCHITECTURE_LIBRARY["BRIMMED_HAT"].hair_policy,
                         "PRESERVE")
        for g in generate_batch(SEEDS, slot="HEAD"):
            self.assertEqual(hair_policy_for(g.construction), "PRESERVE",
                             f"seed {g.spec.seed} hides hair")

    def test_hide_requires_the_architecture_to_declare_it(self):
        """Geometry alone may never opt into hiding hair."""
        from dataclasses import replace
        from v5.library.brimmed_hat import covers_whole_head, hair_policy_for
        arch = ARCHITECTURE_LIBRARY["BRIMMED_HAT"]
        hiding = replace(arch, hair_policy="HIDE")
        for g in generate_batch(SEEDS, slot="HEAD"):
            # declared PRESERVE -> always preserved, whatever the shape
            self.assertEqual(hair_policy_for(g.construction, arch), "PRESERVE")
            # declared HIDE -> only when the head box is genuinely covered
            self.assertEqual(
                hair_policy_for(g.construction, hiding) == "HIDE",
                covers_whole_head(g.construction),
                f"seed {g.spec.seed}: declaration and geometry disagree")

    def test_covering_the_head_means_every_cell_of_the_head_box(self):
        from v5.library.brimmed_hat import covers_whole_head
        x0, x1, y0, y1 = HEAD_BOX
        for g in generate_batch(SEEDS, slot="HEAD"):
            cells = g.construction.silhouette["front"]
            expected = all((x, y) in cells for x in range(x0, x1 + 1)
                           for y in range(y0, y1 + 1))
            self.assertEqual(covers_whole_head(g.construction), expected)

    def test_export_writes_one_policy_to_all_four_directions(self):
        """FS reads HideHair per facing direction, so it must not vary.

        `IsHatHidingHair` is fed `GetCurrentlyEquippedModels(who, facing)`, so a
        per-direction policy would make hair appear and vanish as the Farmer
        turns.  One decision per garment, written four times.
        """
        from v5.library.brimmed_hat import hair_policy_for
        from v5.projection import fs_hat_metadata
        for g in generate_batch(SEEDS, slot="HEAD"):
            hide = hair_policy_for(g.construction) == "HIDE"
            meta = fs_hat_metadata(g.spec, hide)
            flags = {m["HideHair"] for m in meta.values()}
            self.assertEqual(flags, {hide},
                             f"seed {g.spec.seed}: HideHair varies by direction")
            self.assertEqual(len(meta), 4)


class HatProtrusions(unittest.TestCase):
    """Ears and the like: authored, closed-set, profile-scoped, ATTACHED.

    74% of shipping hats have at least one split row against our previous
    1.00 runs-per-row, and that flatness is most of why our output read as
    primitives rather than hats.
    """

    @classmethod
    def setUpClass(cls):
        cls.batch = generate_batch(SEEDS, slot="HEAD")

    def test_closed_set_and_profile_scoped(self):
        from v5.library.hat_motifs import protrusion_options
        for g in self.batch:
            m = g.spec.parameters.get("protrusion", "NONE")
            p = g.spec.parameters
            self.assertIn(m, protrusion_options(p["crown_profile"],
                                                g.spec.architecture,
                                                p["crown_width"],
                                                p.get("brim_width")),
                          f"seed {g.spec.seed}: {m} not legal for "
                          f"{g.spec.architecture}/{p['crown_profile']}")

    def test_a_declared_motif_always_renders(self):
        """A rolled protrusion must actually draw.  Silently rendering nothing
        meant the spec claimed an ear the geometry could not produce."""
        from v5.library.hat_motifs import runs_per_row
        for g in self.batch:
            if g.spec.parameters.get("protrusion", "NONE") == "NONE":
                continue
            self.assertTrue(
                any(n > 1 for n in runs_per_row(set(g.raster["front"])).values()),
                f"seed {g.spec.seed}: {g.spec.parameters['protrusion']} rendered nothing")

    def test_protrusion_and_asymmetry_are_exclusive(self):
        """One shape decision per hat: asymmetry displaces the crown a
        protrusion is anchored to."""
        for g in self.batch:
            p = g.spec.parameters
            self.assertFalse(
                p.get("protrusion", "NONE") != "NONE"
                and p.get("asymmetry", "NONE") != "NONE",
                f"seed {g.spec.seed} carries both")

    def test_apex_pairs_appear_in_profile(self):
        """The corpus draws an apex pair in the side view; side pairs it does not."""
        from v5.library.hat_motifs import runs_per_row
        for g in self.batch:
            if g.spec.parameters.get("protrusion") != "EARS_TOP":
                continue
            self.assertTrue(
                any(n > 1 for n in runs_per_row(set(g.raster["side"])).values()),
                f"seed {g.spec.seed}: apex pair missing from the profile")

    def test_ears_rest_on_fabric(self):
        """Every ear cell must touch the hat; a floating cluster is the bug
        that made seed 11 read as a nub rather than an appendage."""
        for g in self.batch:
            if g.spec.parameters.get("protrusion", "NONE") == "NONE":
                continue
            for view in ("front", "side", "back"):
                cells = set(g.raster[view])
                if not cells:
                    continue
                seen, stack = set(), [next(iter(cells))]
                while stack:
                    k = stack.pop()
                    if k in seen or k not in cells:
                        continue
                    seen.add(k)
                    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((k[0] + d[0], k[1] + d[1]))
                self.assertEqual(len(seen), len(cells),
                                 f"seed {g.spec.seed} {view}: detached cluster")

    def test_protrusions_actually_split_a_row(self):
        from v5.library.hat_motifs import runs_per_row
        split = [g for g in self.batch
                 if any(n > 1 for n in runs_per_row(set(g.raster["front"])).values())]
        self.assertTrue(split, "no hat has a split row — protrusions are inert")
        for g in split:
            p = g.spec.parameters
            self.assertTrue(
                p.get("protrusion", "NONE") != "NONE"
                or p.get("asymmetry", "NONE") != "NONE",
                f"seed {g.spec.seed} splits a row with no motif at all")

    def test_runs_per_row_stays_within_the_corpus(self):
        """Corpus max runs on a row is 5; we stay at or under 3."""
        from v5.library.hat_motifs import MAX_RUNS_PER_ROW, runs_per_row
        for g in self.batch:
            for view in ("front", "side", "back"):
                worst = max(runs_per_row(set(g.raster[view])).values())
                self.assertLessEqual(worst, MAX_RUNS_PER_ROW,
                                     f"seed {g.spec.seed} {view}: {worst} runs")

    def test_protrusions_never_open_an_enclosed_hole(self):
        """Attached motifs keep the gap open upward; a closed one is reverted."""
        for g in self.batch:
            for view in ("front", "side", "back"):
                self.assertEqual(
                    enclosed_holes(set(g.raster[view]), HAT_ENVELOPE), set(),
                    f"seed {g.spec.seed} {view}: protrusion closed a hole")

    def test_symmetric_motifs_stay_symmetric(self):
        for g in self.batch:
            if g.spec.parameters.get("protrusion", "NONE") == "NONE":
                continue
            if g.spec.parameters.get("asymmetry", "NONE") != "NONE":
                continue
            for view in ("front", "back"):
                self.assertEqual(
                    mirror_symmetry(set(g.raster[view]), HAT_ENVELOPE), 1.0,
                    f"seed {g.spec.seed} {view}: ear pair is not symmetric")


class BrimlessArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch = [g for g in generate_batch(SEEDS, slot="HEAD")
                     if g.spec.architecture == "BRIMLESS_HAT"]

    def test_the_family_offers_both(self):
        from v5.library.brimmed_hat import HAT
        self.assertEqual(set(HAT.architectures), {"BRIMMED_HAT", "BRIMLESS_HAT"})

    def test_brimless_rolls_exist(self):
        self.assertTrue(self.batch, "BRIMLESS_HAT never rolled")

    def test_shares_the_placement_model(self):
        x0, x1, y0, y1 = head_box(HAT_ENVELOPE)
        for g in self.batch:
            cells = set(g.raster["front"])
            for x in range(x0, x1 + 1):
                self.assertTrue(any(c[0] == x for c in cells),
                                f"seed {g.spec.seed}: head column {x} uncovered")
            if g.spec.parameters.get("asymmetry", "NONE") == "NONE":
                self.assertEqual(mirror_symmetry(cells, HAT_ENVELOPE), 1.0)

    def test_within_brimless_corpus_bounds(self):
        for g in self.batch:
            cells = set(g.raster["front"])
            x0, x1, y0, y1 = occupied_bbox(cells)
            for key, val in (("cells", len(cells)),
                             ("bbox_w", x1 - x0 + 1),
                             ("bbox_h", y1 - y0 + 1),
                             ("crown_top", y0),
                             ("bottom_row", y1)):
                lo, hi = HAT_BRIMLESS_BOUNDS[key]
                self.assertTrue(lo <= val <= hi,
                                f"seed {g.spec.seed}: {key}={val} outside {(lo, hi)}")

    def test_is_not_a_solid_block(self):
        """Corpus fill ratio is 0.78; a cap curves in where it meets the head."""
        for g in self.batch:
            cells = set(g.raster["front"])
            x0, x1, y0, y1 = occupied_bbox(cells)
            fill = len(cells) / ((x1 - x0 + 1) * (y1 - y0 + 1))
            self.assertLess(fill, 0.92, f"seed {g.spec.seed}: fill {fill:.2f}")


class _Params:
    """A spec-shaped shim so a construction can be re-realized with one
    parameter changed, without going back through the resolver."""
    def __init__(self, spec, **over):
        self.parameters = dict(spec.parameters); self.parameters.update(over)
        self.layers = {}


class DeclaredCapabilities(unittest.TestCase):
    """QC legality is DECLARED per Architecture, never relaxed globally.

    Each capability defaults to the strict behaviour.  These tests assert two
    things about every one of them: that an Architecture which does not declare
    it cannot reach it at all, and that an Architecture which does declare it
    still keeps the invariant the declaration was carved out of.
    """

    @classmethod
    def setUpClass(cls):
        cls.batch = generate_batch(SEEDS, slot="HEAD")

    # --- directional pieces -------------------------------------------------

    def test_directional_pieces_need_the_declaration(self):
        from v5.library.hat_motifs import directional_options

        class Silent:                      # declares nothing
            pass
        for arch in ("BRIMMED_HAT", "BRIMLESS_HAT"):
            for profile in ("CONE", "ROUND", "FAST"):
                self.assertEqual(
                    directional_options(arch, profile, Silent()), ("NONE",),
                    "an Architecture that declares nothing must not be "
                    "offered a directional piece")

    def test_declared_directional_pieces_are_reachable(self):
        """A capability nothing can roll is not a capability."""
        seen = {g.spec.parameters.get("directional", "NONE")
                for g in self.batch}
        self.assertTrue(seen - {"NONE"},
                        "no hat in the batch carries a directional piece")

    def test_directional_piece_never_moves_the_hat(self):
        """The guard against the bug this Architecture was built to avoid.

        A directional piece may ADD mass to the frames it declares.  It may
        never move a cell the crown, brim or hem already owns — otherwise the
        hat visibly shifts as the Farmer turns, which is exactly the defect
        that made the crown anchoring rule load-bearing in the first place.
        """
        for g in self.batch:
            motif = g.spec.parameters.get("directional", "NONE")
            if motif == "NONE":
                continue
            arch = ARCHITECTURE_LIBRARY[g.spec.architecture]
            plain = arch.realize(_Params(g.spec, directional="NONE"),
                                 HAT_ENVELOPE)
            withit = arch.realize(_Params(g.spec), HAT_ENVELOPE)
            for view in ("front", "side", "back"):
                self.assertTrue(
                    plain.silhouette[view] <= withit.silhouette[view],
                    f"seed {g.spec.seed} {view}: {motif} removed hat cells")
            # and the frames it does NOT declare are bit-identical
            from v5.library.hat_motifs import DIRECTIONAL_PIECES
            declared = DIRECTIONAL_PIECES[motif]["views"]
            for view in ("front", "side", "back"):
                if view in declared:
                    continue
                self.assertEqual(
                    plain.silhouette[view], withit.silhouette[view],
                    f"seed {g.spec.seed}: {motif} leaked into {view}")

    def test_directional_piece_stays_attached(self):
        for g in self.batch:
            if g.spec.parameters.get("directional", "NONE") == "NONE":
                continue
            for view in ("front", "side", "back"):
                cells = set(g.raster[view])
                if not cells:
                    continue
                seen, stack = set(), [next(iter(cells))]
                while stack:
                    k = stack.pop()
                    if k in seen or k not in cells:
                        continue
                    seen.add(k)
                    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        stack.append((k[0] + d[0], k[1] + d[1]))
                self.assertEqual(len(seen), len(cells),
                                 f"seed {g.spec.seed} {view}: detached piece")

    # --- base flare ---------------------------------------------------------

    def test_base_flare_needs_the_declaration(self):
        from v5.library.brimless_hat import cuff_options

        class Silent:
            pass
        self.assertEqual(cuff_options(16, Silent()), ("NONE",))

    def test_a_cuffed_cap_is_still_a_cap(self):
        """The flare must not push the shape over the 1.15 that separates the
        two Architectures — a cap with a brim is a brimmed hat."""
        for g in self.batch:
            if g.spec.parameters.get("cuff", "NONE") != "CUFF":
                continue
            m = crown_metrics(set(g.raster["front"]))
            self.assertLessEqual(m["brim_ratio"], 1.15,
                                 f"seed {g.spec.seed}: the cuff made a brim")

    # --- split rows ---------------------------------------------------------

    def test_a_split_row_never_closes_underneath(self):
        """A curl opens a row; a gap that closes again below it is an enclosed
        hole, which is the one thing every hat may not have.  Caught in a
        400-seed sweep, not in the 48 the rest of this file uses."""
        for g in generate_batch(range(400), slot="HEAD"):
            for view in ("front", "side", "back"):
                self.assertEqual(
                    enclosed_holes(set(g.raster[view]), HAT_ENVELOPE), set(),
                    f"seed {g.spec.seed} {view}: a split row closed underneath")

    def test_split_rows_need_the_declaration(self):
        from v5.library.brimmed_hat import SIDE_CURL_BRIMS
        self.assertTrue(ARCHITECTURE_LIBRARY["BRIMMED_HAT"].allows_split_rows)
        self.assertFalse(
            ARCHITECTURE_LIBRARY["BRIMLESS_HAT"].allows_split_rows,
            "BRIMLESS has no curled brim to open, so it must not declare it")
        # SIDE_CURL is parked (see the note beside SIDE_CURL_BRIMS): the
        # declaration and the machinery stand, the scope is empty.
        from v5.library.brimmed_hat import SIDE_CURL_CANDIDATES
        self.assertEqual(SIDE_CURL_BRIMS, ())
        self.assertTrue(SIDE_CURL_CANDIDATES)

    # --- detached mass stays shut ------------------------------------------

    def test_nothing_declares_detached_mass(self):
        """3 of 112 vanilla hats have a second component.  The flag exists to
        mark the boundary, not to be switched on."""
        for name, c in ARCHITECTURE_LIBRARY.items():
            self.assertFalse(getattr(c, "allows_detached_mass", False),
                             f"{name} declares detached mass")

    # --- the derived back frame --------------------------------------------

    def test_back_frame_is_derived_from_the_front(self):
        """Vanilla puts the back frame one row lower than the front (median +1
        on the top row, +2 on the bottom).  Ours is a function of the front, so
        the two frames cannot disagree about the hat."""
        for g in self.batch:
            front, back = set(g.raster["front"]), set(g.raster["back"])
            if not front or not back:
                continue
            self.assertEqual(min(y for _, y in back),
                             min(y for _, y in front) + 1,
                             f"seed {g.spec.seed}: back top row")
            self.assertGreaterEqual(max(y for _, y in back),
                                    max(y for _, y in front) + 1,
                                    f"seed {g.spec.seed}: back does not reach lower")

    # --- capabilities the phase-2 log listed as unreachable ----------------

    def test_brim_wings_are_now_reachable(self):
        """Phase 2 shipped BRIM_WINGS with no crown that could carry it.  A
        motif no legal combination can produce is a dead entry in the table."""
        from v5.library.hat_motifs import protrusion_options
        self.assertIn("BRIM_WINGS",
                      protrusion_options("COLUMN", "BRIMMED_HAT", 8, 18))

    def test_cap_height_belongs_to_the_dome(self):
        from v5.library.brimless_hat import CAP_DOMES, cap_height
        heights = {cap_height(n) for n in CAP_DOMES}
        self.assertGreater(len(heights), 1,
                           "every cap is still the same height")


if __name__ == "__main__":
    unittest.main()

class ConstructionTemplates(unittest.TestCase):
    """The authored interiors, and the properties they promise.

    Structural promises are asserted (a template may not move a cell; a band
    must land on its declared seat).  Rendering promises are NOT asserted as
    pass/fail here — they are reported by `hat_templates.verify` per seed,
    because a family's interior is a range and a hard bar on a median would be
    the same mistake as the alpha-mask gate.
    """

    @classmethod
    def setUpClass(cls):
        cls.batch = generate_batch(range(96), slot="HEAD")

    def test_every_hat_selects_a_template(self):
        for g in self.batch:
            self.assertIsNotNone(g.construction.meta.get("template"),
                                 f"seed {g.spec.seed}: no template selected")
            self.assertIn(g.construction.meta["template"], hat_templates.TEMPLATES)

    def test_selection_is_derived_not_rolled(self):
        """Same spec, same template — the interior follows the geometry."""
        for g in self.batch[:24]:
            again = generate(g.spec.seed, slot="HEAD")
            self.assertEqual(g.construction.meta["template"],
                             again.construction.meta["template"])
            meta = again.construction.meta
            arch = ARCHITECTURE_LIBRARY[again.spec.architecture]
            self.assertEqual(hat_templates.select(arch.construction_templates, meta).name,
                             meta["template"])

    def test_a_template_may_not_move_a_cell(self):
        """`apply` is the one-owner guarantee; prove the assertion fires."""
        from v5.construction import Piece

        class Vandal(hat_templates.ConstructionTemplate):
            pass

        g = self.batch[0]
        crown = g.construction.by_name("crown")
        pieces = {"crown": Piece("crown", "body", z=0,
                                 cells={v: set(c) for v, c in crown.cells.items()})}
        tpl = hat_templates.TEMPLATES[g.construction.meta["template"]]
        hat_templates.apply(tpl, pieces)          # clean
        pieces["crown"].cells["front"].add((0, 0))
        with self.assertRaises(AssertionError):
            hat_templates._assert_unchanged(tpl, pieces, {
                "crown": {v: set(c) - {(0, 0)} for v, c in pieces["crown"].cells.items()}})

    def test_structural_landmarks_hold(self):
        """Band seat and base flare are structural: zero tolerance."""
        structural = {"band_off_crown", "band_unseated", "base_flare",
                      "crown_missing", "crown_empty"}
        bad = []
        for g in self.batch:
            tpl = hat_templates.TEMPLATES[g.construction.meta["template"]]
            arch = ARCHITECTURE_LIBRARY[g.spec.architecture]
            for name, msg in hat_templates.verify(tpl, g.construction, g.raster,
                                                  art=g.art, architecture=arch):
                if name in structural:
                    bad.append(f"seed {g.spec.seed} [{tpl.name}] {name}: {msg}")
        self.assertEqual(bad, [], "\n".join(bad))
