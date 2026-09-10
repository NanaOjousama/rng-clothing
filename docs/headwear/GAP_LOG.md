# Headwear V5 — gap log

Every difficulty from the Vanilla Hat Reconstruction exercise, classified once.
Rule applied: **do not rewrite pipeline code to solve an authoring limitation,
and do not add a one-off motif where a reusable Architecture rule belongs.**

## PIPELINE LIMITATION
*(AA / AG / projection / placement / export cannot express it)*

1. **No palette-from-reference path.** V5 resolves colour from a rolled Color
   Architecture. Reconstructing a *specific* hat's palette has no entry point,
   so every reconstruction wears a borrowed palette. Silhouette reconstruction
   is unaffected; a true "remaster" would need one.
   *Not fixed — out of scope, and it would touch the deterministic resolution
   model.*

2. **Side view cannot carry features the front lacks.** The crown is anchored
   to identical columns in all views (a deliberate placement rule that fixed a
   real in-game bug). The Trucker Hat's visor is a side-view feature, so it is
   unreachable while that rule stands.
   *Not fixed — the anchoring rule is load-bearing.*

## ARCHITECTURE LIMITATION
*(the pipeline could do it; contracts/variables cannot represent it cleanly)*

3. **Odd-width rows are impossible.** `span()` emits only even widths so the
   mass centres exactly on a 20-wide frame. Vanilla uses 3/5/7/9/11 freely and
   accepts sub-pixel asymmetry (Witch 0.95, Santa 0.94). Blocks Witch and Santa.
   *Fix path: a declared per-Architecture exception, not a global change.*

4. **Detached mass and enclosed holes are forbidden.** Correct for BRIMMED and
   BRIMLESS. Cat Ears (6 components, 4 holes) needs an Architecture that
   declares them legal.
   *Do not weaken the existing contracts.*

5. **No one-sided Architecture.** Butterfly Bow is symmetry 0.11. Our contract
   enforces exact mirror symmetry outside declared motifs, and no motif of that
   magnitude should exist within BRIMMED.

6. **`TIP_LEAN` is a fixed column shift.** Santa's droop leans progressively
   with depth. A different variable, not a bigger lean.

## AUTHORING LIMITATION
*(supported already; our vocabulary was weak or missing)*

7. **Crown insets stopped at 4.** Vanilla reaches 5 (Bowler's 4-cell apex on a
   14 base). **FIXED** — `ROUND` deepened to `(5,4,3,2,2,1,0,0)`; Bowler went
   8% → 2%.

8. **No crease motif.** **FIXED** — `CROWN_CREASE` added, reproduces Cowboy's
   apex exactly; Cowboy went 12% → 10%.

9. **Brim-anchored side wings.** Cowboy's wings rest on the *brim's* widest
   row; `EARS_SIDE` anchors to the *crown's*. A distinct anchor, reusable for
   any wide-brimmed hat. *Logged, not built — one example so far.*

10. **No fast-shoulder cap dome.** Cap domes all taper gradually, so no cap can
    hold a constant-width column; the Trucker's best match was BRIMMED.
    *Logged — needs a second corpus example before authoring.*

11. **No cuff or pom motif.** Both are real recurring construction (Santa, knit
    hats). *Logged.*

## QC LIMITATION
*(the generator can produce the defect; no gate catches it)*

12. **A rolled motif could render nothing.** `EARS_SIDE` was silently reverted
    when the geometry could not support it — the spec claimed an ear that never
    drew. **FIXED** — legality now checks the actual shoulder/apex, and a test
    asserts every declared motif renders.

13. **Detached ear clusters were undetectable.** An ear could float with a gap
    below it without tripping the enclosed-hole rule (the gap was open at the
    side). **FIXED** — a connected-component test now runs over every view.

14. **No gate on reconstruction fidelity.** Corpus bounds pass happily on
    shapes that look nothing like a hat at gameplay scale. This exercise is the
    gate; there is no automated substitute.

---

# Phase 2 update

Classification is diagnostic, not a prohibition. Gaps re-examined with
permission to change Architecture or pipeline where evidence justified it.

## CLOSED

* **#3 Odd-width rows** — ADOPTED. Half-integer profile insets +
  `span(width, env, odd_bias)` + a per-hat `odd_bias` variable. Scoped by
  `has_odd_rows(profile)`, which the symmetry and side-brim contracts consult
  as a declared exception. Integer-inset profiles are bit-identical to before.
  *Witch 15% → 3%, Santa 15% → 8%.*
* **#7 Crown insets stopped at 4** — closed in phase 1.
* **#8 No crease motif** — closed in phase 1.
* **#10 No fast-shoulder cap dome** — ADOPTED as `FAST (3,1,0)`, but the real
  blocker was #15 below.
* **#12, #13** — closed in phase 1.

## NEW, and closed

15. **`HEM_TAPER` was hardcoded to a single shape** — and it was among the
    *rarest* in the corpus. Measured over 59 brimless hats: `(1,)` 8 hats,
    `(3,6)` 7, `(3,)` 6, `(1,2,3)` only 2 — and `(1,2,3)` is what we had.
    Now a four-member closed set (`TIGHT`/`DROP`/`FLARE`/`SOFT`).
    *Trucker 14% → 11%; brimless distinct silhouettes 35/61 → 51/66.*

16. **Dome and hem taper fail as a PAIRING, not individually.** A fast dome
    with a tight hem leaves nothing shaped and the cap renders as a rectangle
    (fill 0.96 against a corpus median of 0.78). Neither choice is wrong alone.
    Guarded by `estimate_fill` at resolution time.

17. **A defect-prevention rule will eventually exclude a legitimate shape.**
    The 0.55 crown-proportion rule (added to stop chess-piece hats) blocked
    cones outright — a cone is *supposed* to be narrow. Fixed with a declared
    `NARROW_BY_DESIGN` exemption, not by deleting the rule.

## STILL OPEN

18. **`BRIM_WINGS` is unreachable** (KEEP EXPERIMENTAL). The anchor concept is
    implemented and correct, but a wing needs the crown to still be narrow at
    the brim row and every current profile has opened to full width by then.
    Needs a crown profile that stays narrow to the brim line.

19. **Direction-specific features** (Trucker's visor). The crown is anchored to
    identical columns in all views — the rule that fixed a real in-game bug.
    A visor is a side-view feature. *Not attempted: the anchoring rule is
    load-bearing and the payoff is one hat.* Requires an Architecture-declared
    "this piece differs by direction" concept.

20. **Santa's split lower hem** — `......#......#......`, a row reduced to its
    two outer cells. Our brim insets remove symmetrically from both sides and
    cannot leave only corners. One example so far; not authored.

21. **#1 palette-from-reference, #4 detached mass, #5 one-sided Architecture,
    #6 progressive droop** — unchanged from phase 1.

---

# PHASE 3

## Metric correction (applies to every number above)

**0. The phase-2 metric scored the FRONT frame only, and swept undeclared
values.** Both flattered the result. A front-only score cannot see a
directional feature at all — vanilla's Trucker draws its visor in the two side
frames and nowhere else, so a missing visor and a perfect visor score
identically. And a sweep over values outside the declared domain measures an
Architecture we do not have.

Phase 3 scores front + side + back (side weighted double, since it serves two
runtime directions) and takes domains, `validate` and `activation` from each
Architecture's own schema. **Phase-2 and phase-3 numbers are not comparable**;
the phase-3 report restates both under the new metric.

## CLOSED in phase 3

18. **`BRIM_WINGS` unreachable** — CLOSED. The missing piece was the crown, not
    the motif: `COLUMN (0,0,0,0)` stays narrow to the brim line, which is the
    clearance a wing needs. Reachability is now a test
    (`test_brim_wings_are_now_reachable`) and the Cowboy reconstruction selects
    it. Supported by `crown_width` 8/10, `brim_line` 8 and `ROLLED`, all
    declared for `WIDE_BRIM_CROWNS` only.

19. **Direction-specific features** — CLOSED as a *concept*, partially as a
    reconstruction. `allows_directional_pieces` + `DIRECTIONAL_PIECES`
    (`VISOR`, `TAIL`). Decided once at Construction time, declared per frame,
    anchored to the already-anchored crown, and provably additive:
    `test_directional_piece_never_moves_the_hat` re-realizes with the piece off
    and requires the undeclared frames to be bit-identical. The anchoring rule
    was **not** weakened — see #23 for what that costs.

20. **Santa's split lower construction** — CLOSED as a general capability,
    `allows_split_rows`, though not via the two-corner form. The corpus shows
    47 of 112 hats splitting at the base, and the reusable case is geometric:
    a curled brim seen edge-on opens between its front and back ends
    (`SIDE_CURL_BRIMS`). Guarded so the gap cannot close underneath — the
    unguarded version produced an **enclosed hole**, caught only by a 400-seed
    sweep, now a permanent test.

21. **#6 progressive droop** — CLOSED. `TIP_DROOP` with `DROOP_STEPS (2,1,1)`,
    authored from two corpus examples, scoped to pointed crowns.

    **#4 detached mass** and **#5 one-sided Architecture** remain deliberately
    closed: flags exist (`allows_detached_mass`, `allows_extreme_asymmetry`),
    nothing declares them, and a test asserts they stay off. Only 3 of 112
    vanilla hats have a second component.

    **#1 palette-from-reference** unchanged and still out of scope.

## NEW, and closed

22. **The back frame was authored, and wrong.** It reused the front crown plus
    two full-crown-width rows under the brim line — a shape 1 of 112 vanilla
    hats draws. The corpus rule is *the same hat one row lower, lowest row
    repeated*: median prediction error 24.4% against the old rule's 28.8%,
    better on 75 of 114. The back is now a **function of the front**, computed
    after every motif, so the two frames cannot disagree.

23. **`crown_width` was validated against the wrong corpus.** The brimless
    validator ran the *brimmed* profile table against the *brimmed* bound
    (5–12). Correcting the table exposed the bound: against a ceiling meant for
    crowns that taper, **no cap wider than 12 was admissible at all**, while
    the brimless corpus median is 14. Two-thirds of the intended cap width
    range had been silently unreachable. Same class of error as #15 — a
    constant that passed every statistical check because nothing ever asked
    whether the *right* constant was being checked.

24. **Cap height was a module constant.** Every cap was eleven rows whatever
    dome it wore; the baseball family is nine. Height now belongs to the
    authored dome, as a brimmed crown's height belongs to its profile.

25. **22% of vanilla hats flare at the base and we could not.** `allows_base_
    flare` + `CUFF`, +2 columns on the bottom two rows, gated to crown widths
    where the result still classifies as brimless.

## STILL OPEN

26. **The side frame is anchored to the front's columns, and vanilla's is not.**
    Vanilla shifts the whole cap ~1 column backward in profile (Trucker), and
    the Top Hat's lower brim likewise. Correcting it would recover roughly a
    fifth of the remaining side-frame error on those hats — and would
    reintroduce the "hat shifts while turning" defect the anchoring rule was
    added to fix. **Deliberately not attempted.** A safe version would need a
    declared per-Architecture *constant* offset applied identically to every
    hat of that Architecture, which is a different change from letting the
    views drift.

27. **`HAT_SIDE_BRIM_RISE` has no corpus rule.** Re-measured: the side frame's
    widest row sits at the same row as the front's (median 0; −1: 24, 0: 32,
    +1: 23). Our frozen 1 is not the median — but flipping to 0 trades Top Hat
    and Witch for Bowler and Santa, and the distribution correlates with
    nothing measurable. The corpus supplies no replacement rule, only a per-hat
    property. **Rejected rather than tuned.**

28. **A hat may carry only one motif.** `protrusion` is a single variable, so
    Cowboy's crown crease and its brim wings are mutually exclusive even though
    the reference has both, and `asymmetry` is additionally locked out whenever
    a protrusion is present. The exclusivity was added for a good reason — a
    lean displaces the crown a protrusion is anchored to — but the correct fix
    is ordering and re-anchoring, not exclusion.

29. **A world-space feature cannot flip between frames.** Vanilla's Witch tip
    points one way in the front and left frames and the other way in the right
    and back frames — it is fixed in world space while the head turns. Our back
    frame is derived from the front, so a lean points the same way in both.
    This is most of the Witch's remaining back-frame error. It is the *mirror*
    variant of the directional-piece concept and would fit the same declaration.

30. **A brim deeper than four rows.** Cowboy's brim is six rows under a
    four-row crown. `WIDE_BRIM_MAX_DEPTH` stops at 4 because past that the
    goblet read returns for every crown that is not `COLUMN`. Needs the depth
    limit to be a property of the *pair*, as `estimate_fill` already is for
    caps.

31. **Bounded repair could not exhaust a domain.** `resolve_variable` allowed 4
    samples; widening `crown_width` to five members made it possible to drop a
    variable that had a legal value. It failed 533 seeds later as an
    `AbsentConcept` crash in a *different* validator. Fixed declaratively
    (`Variable.repair_attempts`, default 4) so the shirt path stays
    bit-identical — the global version erases a shirt property the suite
    asserts, and that property was resting on a 0.015 margin either way.

32. **Two capabilities were legal but visually wrong, and only the contact
    sheet said so.** `COLUMN` at crown 12 under a brim of 16 passed every
    bound and rendered as a dish — the crown and brim came out nearly the same
    width. And a `TAIL` hung off a three-row 16-wide brim looks like the brim
    is dripping, because a tail belongs on a *cuff*. Both fixed by scoping
    (`WIDE_BRIM_MIN_FLARE = 6`; `TAIL` requires a brim of two rows or fewer),
    not by new geometry. Neither was visible in any metric — reconstruction
    included, since neither combination is what a reconstruction selects.

## STILL OPEN (continued)

33. **A hat carries one motif.** Vanilla #0 has both a crown crease and brim
    wings; `protrusion` is a single variable, so it can have one. See #28.

34. **`BRIM_WINGS` fires about 5 times in 1200 rolls** even after its weight
    was raised to 0.30 — it needs `crown_width` 10 or less AND a brim of 16+.
    Reachable, and now in the validation pack (seed 473), but rare. Whether
    that rate is right is a judgement for in-game review, not a metric.

---

# PHASE 4 — live in-game QC

## CLOSED / REFUTED

35. **"Our hats cover the face."** REFUTED by real capture. Vanilla puts
    594/788/1178 px (p10/med/p90) into a conservative face box and intrudes 30
    px deep at the median; ours put 760 px and intrude 19. We are *more*
    conservative than vanilla and identical to the four reference hats.

36. **"Our hats float / sit too high."** REFUTED. Like-for-like inside one
    session, floating columns are 0 for vanilla, references and ours alike, and
    the seating transform is -4.00 sprite px for both vanilla and ours. An
    earlier pass measured 8 floating columns and a 2 px offset, set
    `HAT_HEAD_POSITION_Y = -2`, and was wrong: the two groups had been captured
    in different game sessions, and a restart redraws the farmer's hair one
    pixel taller. The hat's own position was byte-identical between them.
    **Reverted to 0.**

37. **The synthetic composite.** Deprecated for placement, with numbers: -4
    sprite px vertical, footprint IoU 0.200 against the real render, scale
    identical. It flattered seating specifically.

## NEW

38. **A cross-session comparison measures the session.** Two confident, wrong
    root causes came from this in one sitting. Capture every group a comparison
    touches inside one game session, and make that a property of the capture
    plan rather than something checked afterwards.

39. **Fashion Sense caches content packs at load.** `HeadPosition.Y` was swept
    0/-2/-4/-6 in a live pack with no movement whatsoever; new packs and changed
    PNGs are equally invisible until restart. A placement fix therefore cannot
    be verified in the session that authors it.

40. **Headwear could not express a chromatic band, structurally.** Two roles
    (body, trim) and no permitted palette gave trim a distinct hue. Closed with
    `CHROMATIC_BAND` (hue-led) and `MUTED_BAND` (saturation-led); far-hue share
    reaches 0.059 where they apply, against a reference target of 0.156.

41. **The ramp was a clothing ramp.** HEAD now declares `min_ramp_depth = 6`
    and `ramp_spread = 1.5` on its SlotContract, which also relieves the value
    floor. That floor came from a clothing corpus where 11.6% of garments
    contain near-black; headwear is the opposite. Darkest luminance 47.5 -> 18
    (vanilla 15), contour -37 -> -60 (vanilla -59), acceptance 178 -> 200/200,
    shirts unchanged at 187/200.

## STILL OPEN

42. **Colour count 6 against a reference median of 10.5.** The deeper ramp
    helped the span, not the count: the sprite only uses the steps the shading
    asks for, and the shading asks for about six.

43. **The highlight is still 3-4x too broad** (0.16-0.21 of the sprite against
    0.052 in the references). The discrete top-plane / highlight-patch shading
    replaced the radial field, but "light" and "highlight" still merge under the
    ramp's upper compression on pale hats.

44. **Chromatic bands reach only ~31% of rolls** (palette AND band both have to
    come up). Vanilla carries a hue accent on 75%.
