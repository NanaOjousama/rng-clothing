"""The pre-authored path: assets, the mirror rule, and style coherence.

These are asset-integrity tests.  They do not judge whether the art is good —
that is an in-game question — but they do catch every way an authored library
can be wrong without anyone noticing: a colour that is not in the index, a
decal that hangs off its base, a palette whose ramp has no ladder, a style tag
that lets a neon palette onto a cottagecore shirt.
"""

from __future__ import annotations

import unittest

from v5 import authored, grammar
from v5.grammar import luminance

STYLES = ("work", "casual", "smart", "formal", "cottagecore", "festival")


class AuthoredLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()

    def test_every_base_has_three_authored_views(self):
        for b in self.lib.bases:
            for view in authored.VIEWS:
                self.assertTrue(b.cells[view], f"{b.name}: {view} is empty")

    def test_every_pixel_decodes_to_a_role_and_step(self):
        """`load` raises on an off-index colour; assert the decode is complete."""
        for b in self.lib.bases:
            for view, cells in b.cells.items():
                for cell, (role, step) in cells.items():
                    self.assertIn(role, ("body", "trim", "accent"))
                    self.assertTrue(0 <= step < 6, f"{b.name} {view} {cell}")

    def test_right_is_the_mirror_of_left(self):
        """RIGHT is never drawn.  If it ever diverges, this is how we find out."""
        for slot in ("HEAD", "TOP"):
            g = authored.compose(0, slot, self.lib)
            left = g.directions["left"]
            right = g.directions["right"]
            self.assertEqual(right, [list(reversed(r)) for r in left])

    def test_anchors_land_on_the_base(self):
        """Every declared anchor is a cell the base actually draws."""
        for b in self.lib.bases:
            for name, per_view in b.anchors.items():
                for view, point in per_view.items():
                    if point is None:
                        continue
                    self.assertIn(tuple(point), b.cells[view],
                                  f"{b.name}: anchor {name} in {view} is off the garment")

    def test_no_decal_hangs_off_its_base(self):
        """A decal may not change the silhouette; dropped cells mean bad art."""
        bad = []
        for slot in ("HEAD", "TOP"):
            for seed in range(48):
                g = authored.compose(seed, slot, self.lib)
                for name, view, cell in g.dropped:
                    bad.append(f"seed {seed}: {name} spills at {cell} in {view}")
        self.assertEqual(bad, [], "\n".join(bad[:10]))

    def test_style_tags_are_honoured(self):
        """Every component of a garment carries the garment's own style tag."""
        for slot in ("HEAD", "TOP"):
            for seed in range(48):
                g = authored.compose(seed, slot, self.lib)
                self.assertIn(g.style, g.base.style)
                self.assertIn(g.style, g.palette.style)
                for d in g.decals:
                    self.assertIn(g.style, d.style,
                                  f"{d.name} is not {g.style}")

    def test_one_anchor_carries_one_decal(self):
        # The occupancy unit is the ZONE where a motif declares one, and the
        # anchor otherwise: zone motifs all carry an empty `attach`, so keying
        # on `attach` alone read two legal motifs as a collision.
        for slot in ("HEAD", "TOP"):
            for seed in range(48):
                g = authored.compose(seed, slot, self.lib)
                attaches = [d.zone or d.attach for d in g.decals]
                self.assertEqual(len(attaches), len(set(attaches)))
                self.assertLessEqual(len(attaches), authored.MAX_DECALS)

    def test_composition_is_deterministic(self):
        for seed in (0, 7, 23):
            a = authored.compose(seed, "HEAD", self.lib)
            b = authored.compose(seed, "HEAD", self.lib)
            self.assertEqual(a.directions, b.directions)
            self.assertEqual([d.name for d in a.decals], [d.name for d in b.decals])

    def test_curated_ramps_carry_a_value_ladder(self):
        """A palette whose steps sit together renders as one flat mass."""
        for p in self.lib.palettes:
            for role, ramp in p.ramps.items():
                lums = [luminance((*c, 255)) for c in ramp]
                self.assertEqual(lums, sorted(lums),
                                 f"{p.id}/{role}: ramp is not monotonic")
                self.assertGreaterEqual(lums[-1] - lums[0], 120,
                                        f"{p.id}/{role}: span too narrow to read")

    def test_a_style_can_be_requested(self):
        g = authored.compose(0, "HEAD", self.lib, style="formal")
        self.assertEqual(g.style, "formal")

    def test_atlas_is_four_stacked_frames(self):
        g = authored.compose(1, "HEAD", self.lib)
        w, h = g.base.size
        atlas = authored.atlas(g)
        self.assertEqual(len(atlas), h * 4)
        self.assertEqual(len(atlas[0]), w)

    def test_every_style_tag_can_be_built(self):
        """A tag with no palette or no base is a dead tag; catch it here."""
        for style in STYLES:
            bases = [b for b in self.lib.bases if style in b.style]
            pals = [p for p in self.lib.palettes if style in p.style]
            self.assertTrue(pals, f"no curated palette carries {style}")
            if bases:
                g = authored.compose(3, bases[0].slot, self.lib, style=style)
                self.assertEqual(g.style, style)


class DecorationLayer(unittest.TestCase):
    """Zones, motifs and the fourth role.

    Decoration is anchored, not scattered: every motif declares the bases it
    fits, the views it supports and the zone it belongs in, and a zone is a
    region of the base's own drawn cells.  These assert that the rules hold
    rather than that the art is good.
    """

    @classmethod
    def setUpClass(cls):
        cls.lib = authored.load()

    def test_zones_are_made_of_drawn_cells(self):
        """A zone is legal BY CONSTRUCTION — no corner hanging in space."""
        for b in self.lib.bases:
            for view, zones in b.zones.items():
                for name, (x0, y0, x1, y1) in zones.items():
                    holes = [(x, y) for y in range(y0, y1 + 1)
                             for x in range(x0, x1 + 1) if (x, y) not in b.cells[view]]
                    self.assertEqual(holes, [],
                                     f"{b.name}/{view}/{name} covers empty cells {holes[:4]}")

    def test_every_motif_has_a_home(self):
        """A motif that fits nowhere is dead weight in the library."""
        for d in self.lib.decals:
            homes = [b.name for b in self.lib.bases
                     if b.slot == d.slot and d.fits_base(b)
                     and any(authored._placement(b, d, v) for v in d.views)]
            self.assertTrue(homes, f"{d.name} has no legal placement on any base")

    def test_declared_fits_are_real(self):
        """If a motif says it fits a base, it must actually place there."""
        by_name = {b.name: b for b in self.lib.bases}
        for d in self.lib.decals:
            for base_name in d.fits:
                b = by_name.get(base_name)
                self.assertIsNotNone(b, f"{d.name} declares unknown base {base_name}")
                self.assertTrue(any(authored._placement(b, d, v) for v in d.views),
                                f"{d.name} declares {base_name} but does not fit it")

    def test_decoration_never_leaves_the_base(self):
        for slot in ("HEAD", "TOP"):
            for seed in range(120):
                g = authored.compose(seed, slot, self.lib)
                self.assertEqual(list(g.dropped), [],
                                 f"seed {seed}: {g.base.name} dropped {g.dropped}")

    def test_no_two_motifs_share_a_region(self):
        """Semantic occupancy: the eye resolves a REGION, not a zone.

        crown_top, crown_face and side are all the upper crown, and two motifs
        there read as speckle — which is exactly what the in-game pass showed
        for a buckle beside a pin.
        """
        for slot in ("HEAD", "TOP"):
            for seed in range(160):
                g = authored.compose(seed, slot, self.lib)
                regions = [authored.region_of(d) for d in g.decals]
                self.assertEqual(len(regions), len(set(regions)),
                                 f"seed {seed}: {regions} compete for one region")

    def test_attachments_are_bounded_and_anchored(self):
        """An attachment may leave the silhouette; it may not float or sprawl."""
        by_name = {b.name: b for b in self.lib.bases}
        for d in self.lib.decals:
            if d.kind != "attachment":
                continue
            self.assertGreater(d.max_extent, 0, f"{d.name} has no bound")
            for base_name in d.fits:
                base = by_name[base_name]
                for view in d.views:
                    origin = authored._placement(base, d, view)
                    self.assertIsNotNone(origin, f"{d.name} cannot place on {base_name}")
                    ax, ay = origin
                    placed = {(ax + x, ay + y) for (x, y) in d.view_cells(view)}
                    why = authored._attachment_ok(
                        {c: None for c in placed}, set(base.cells[view]), d, base.size)
                    self.assertIsNone(why, f"{d.name} on {base_name}/{view}: {why}")
                    outside = placed - set(base.cells[view])
                    self.assertLessEqual(len(outside), d.max_extent)

    def test_surface_motifs_stay_inside_the_base(self):
        """Only attachments may extend the silhouette."""
        by_name = {b.name: b for b in self.lib.bases}
        for d in self.lib.decals:
            if d.kind == "attachment":
                continue
            for base_name in d.fits or [b.name for b in self.lib.bases]:
                base = by_name.get(base_name)
                if base is None or base.slot != d.slot:
                    continue
                for view in d.views:
                    origin = authored._placement(base, d, view)
                    if origin is None:
                        continue
                    ax, ay = origin
                    placed = {(ax + x, ay + y) for (x, y) in d.view_cells(view)}
                    self.assertTrue(placed <= set(base.cells[view]),
                                    f"{d.name} leaves {base_name}/{view} but is not "
                                    f"declared an attachment")

    def test_declared_fits_are_style_reachable(self):
        """A base a motif can never legally meet is a lie in the manifest."""
        by_name = {b.name: b for b in self.lib.bases}
        for d in self.lib.decals:
            for base_name in d.fits:
                base = by_name[base_name]
                shared = set(base.style) & set(d.style)
                self.assertTrue(shared,
                                f"{d.name} declares {base_name} but shares no style tag")

    def test_one_motif_per_zone(self):
        for slot in ("HEAD", "TOP"):
            for seed in range(120):
                g = authored.compose(seed, slot, self.lib)
                keys = [d.zone or d.attach for d in g.decals]
                self.assertEqual(len(keys), len(set(keys)),
                                 f"seed {seed}: two motifs in one zone")

    def test_hardware_is_its_own_role(self):
        """HARDWARE resolves from the palette's metal, not the garment's cloth."""
        for p in self.lib.palettes:
            self.assertIn("hardware", p.ramps, f"{p.id} has no hardware ramp")
        metal = [d for d in self.lib.decals
                 for view in d.views
                 if any(role == "hardware"
                        for role, _ in d.view_cells(view).values())]
        self.assertTrue(metal, "no motif uses the hardware role")

    def test_tone_profiles_leave_decoration_alone(self):
        """Tone governs the body; trim/accent/hardware keep the palette's own
        contrast, or a band flattens onto the cloth it crosses."""
        tone = next(iter(self.lib.tones.values()))
        pal = self.lib.palettes[0]
        toned = tone.apply(pal)
        self.assertNotEqual(toned.ramps["body"], pal.ramps["body"])
        for role in ("trim", "accent", "hardware"):
            self.assertEqual(toned.ramps[role], pal.ramps[role])


class SoftCapFoundation(unittest.TestCase):
    """The two things the cap rework had to fix, kept fixed.

    Both were found by eye and then measured; without a test the next redraw
    silently loses them, which is exactly what happened to the anchors.
    """

    def setUp(self):
        self.lib = authored.load()
        self.cap = next(b for b in self.lib.bases if b.name == "soft_cap")
        self.felt = next(b for b in self.lib.bases if b.name == "felt_hat")

    def test_cap_keeps_its_approved_proportions(self):
        """The shipped cap's own geometry, plus the one authorised change.

        The cap that passed visual review is 10 crown cells wide; it was
        widened by exactly one cell per side to give front-panel motifs room.
        It then gained ONE crown row, because the in-game capture showed 288 px
        of hair drawn above it — two full sprite rows across its whole width,
        against the felt control's 128 px over a narrower span.  The cap was a
        row short of covering the head dome, so the head sat on top of it.

        Its envelope now matches felt_hat's in every view, which is the hat
        that demonstrably wears correctly.  Pinned so a later "improvement"
        cannot re-inflate it past the control or shrink it back under the head.
        """
        front = grammar.crown_metrics(set(self.cap.cells["front"]))
        self.assertEqual(front["crown_width"], 12, "front crown width drifted")
        for view in ("front", "left", "back"):
            cap = {y for _, y in self.cap.cells[view]}
            felt = {y for _, y in self.felt.cells[view]}
            self.assertEqual((min(cap), max(cap)), (min(felt), max(felt)),
                             f"{view}: envelope no longer matches the control")

    def test_cap_is_still_a_cap(self):
        """The aperture reaches the head; the peak still projects forward.

        This replaces an earlier brim_ratio check that required the front
        visor to be no wider than the crown (the vanilla cap cluster measures
        exactly 1.00).  That rule came from sprites judged in isolation, and it
        is wrong for this head: measured off the worn capture, the farmer's
        head + hairstyle is 14 cells wide from the hat's fourth row down, and a
        12-wide cap leaves a 1-cell strip of hair on each side running to the
        bottom of the hat — which reads as the cap buried under the hair rather
        than worn on the head.  felt_hat, which reads correctly, meets the head
        exactly at its brim (14) while its crown is only 8.

        So the crown may stay narrow; the APERTURE is what has to reach.
        """
        rows = {}
        for (x, y) in self.cap.cells["front"]:
            rows.setdefault(y, []).append(x)
        ys = sorted(rows)
        widths = [max(rows[y]) - min(rows[y]) + 1 for y in ys]
        self.assertGreaterEqual(max(widths), 14,
                                "the aperture never reaches the head's width")
        # ...and it has to be at the BOTTOM, where the hat seats, not up in the
        # crown where it terminates nothing.
        widest = max(ys, key=lambda y: (max(rows[y]) - min(rows[y]), y))
        self.assertGreaterEqual(widest, ys[-1] - 2,
                                "the widest row is up in the crown, so the hat "
                                "flares above its own opening")
        # The peak's ABSOLUTE column, not a ratio and not a difference against
        # another part of the sprite.  Both derived forms proved unstable:
        # brim_ratio swung 1.50 -> 1.07 when a body row was added, and the
        # difference against the front silhouette swung 3 -> 2 when the
        # aperture was flared -- in both cases while the peak tip sat exactly
        # where it was authored.  "Preserve the projection" means this cell
        # does not move, so that is what is asserted.
        self.assertEqual(min(x for x, _ in self.cap.cells["left"]), 1,
                         "the profile peak tip moved")

    def test_visor_is_darker_than_the_crown_above_it(self):
        """17 of 29 corpus caps darken at the seam; only 2 lighten.

        Median break is -12 and the canonical cluster runs -19 to -60.  The
        visor is a plane turning down and away, so it takes the bottom of the
        ramp while the crown holds the top; that value break is what makes a
        peak read at gameplay scale, not its outline.
        """
        for view in ("front", "left"):
            cells = self.cap.cells[view]
            zones = self.cap.zones[view]
            if "visor" not in zones:
                continue      # in profile the peak rises into the crown rows
            vy = zones["visor"][1]
            rows = {}
            for (x, y), (_, step) in cells.items():
                rows.setdefault(y, []).append(step)
            crown = sum(rows[vy - 1]) / len(rows[vy - 1])
            visor = sum(rows[vy]) / len(rows[vy])
            # A real break, not a fixed magnitude.  The approved art breaks by
            # 0.83 of a step, and the corpus median (-12 luminance on these
            # levels) is under one step too — a 1.0-step gate would have failed
            # both.  What matters is the direction and that it is visible.
            self.assertLess(visor, crown,
                            f"{view}: visor does not break dark from the crown")

    def test_front_emblem_keeps_clear_of_the_visor(self):
        z = self.cap.zones["front"]
        self.assertIn("front_panel", z)
        self.assertIn("visor", z)
        self.assertGreaterEqual(z["visor"][1] - z["front_panel"][3], 2,
                                "no plain cloth between emblem and visor")

    def test_back_carries_no_front_emblem(self):
        self.assertNotIn("front_panel", self.cap.zones["back"])

    def test_front_emblems_sit_centred_on_the_panel(self):
        z = self.cap.zones["front"]["front_panel"]
        for d in self.lib.decals:
            if d.zone != "front_panel" or "soft_cap" not in (d.fits or ()):
                continue
            place = authored._placement(self.cap, d, "front")
            self.assertIsNotNone(place, d.name)
            w, _ = d.view_size("front")
            left_gap = place[0] - z[0]
            right_gap = z[2] - (place[0] + w - 1)
            self.assertLessEqual(abs(left_gap - right_gap), 1,
                                 f"{d.name} is not centred on the panel")
