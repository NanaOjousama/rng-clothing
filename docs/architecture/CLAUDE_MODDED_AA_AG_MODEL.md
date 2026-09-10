# Stardew-compatible clothing: revised AA/AG model from the modded corpus

Author: Claude (Opus 5), 2026-09-03.
Extends the vanilla model derived in `CLAUDE_INDEPENDENT_ARCHITECTURE.md` and
`CLAUDE_V5_ADVERSARIAL_REVIEW.md`. Vanilla is treated as the baseline, not the ceiling.
No code written.

---

## 0. Corpus and method

Everything below is measured from `references/`, including the archives unpacked
for this study.

| Asset | Count |
|---|---:|
| `shirt.json` parsed | 1,669 |
| shirts with readable art | 1,146 |
| `pants.json` | 447 |
| `sleeves.json` | 95 |
| Fashion Sense packs | ~35 distinct |

Measured programmatically: frame size, scale, anchor, colour counts, alpha
discipline, ramp depth, hue drift, per-direction complexity, mirror discipline,
and construction idioms. Then read pixel-by-pixel and viewed on the Farmer at
gameplay scale for the strongest packs (Gentleman's Collection, Layicn's
Sino-Western, SubabyTvanZ's Sailor Suit, Harry Potter Uniforms, Butlers & Maids,
Frogwares Sherlock, Bonestealer, Daily Clothes, Jjoripong's Closet, Adventurer's
Armour).

---

## 1. The headline finding: mods did not raise the resolution

This is the single most important result and it contradicts an assumption the
project has been carrying.

| Strategy | Shirts | Colours (median) | Any partial alpha |
|---|---:|---:|---:|
| Vanilla density, 8x8 at Scale 4 | 983 | 10 | 3% |
| Extended frame, still Scale 4 | 122 | 8 | 1% |
| High resolution, Scale under 4 | 41 | 47 | 68% |

**1,472 of 1,669 shirts (88%) use exactly vanilla's 8x8 logical frame at Scale 4.**
One logical pixel equals one vanilla pixel.

**Not a single pack in the corpus uses 16x16 at Scale 2** — the same display box
at double density, which is what this project adopted in V3 onward. Scale 2
appears only on 96x96 full-body canvases. The project's format is mechanically
valid and was runtime-confirmed, but it is unprecedented in shipping work.

The 41 high-resolution garments are the tell: median 47 colours and 68% carrying
partial alpha means they are **resampled artwork**, not logical pixel art. That is
precisely the failure mode `README.md` forbids. They are also the least
Stardew-looking items in the corpus.

**Where the extra room actually goes: frame extent, not pixel density.**

| Frame | n | Anchor | Used for |
|---|---:|---|---|
| 8x7 | 67 | BP (0,0) | crop tops, tanks, suspender tops — one row *removed* to bare the midriff |
| 8x9 – 8x11 | 49 | BP (0,0)/(0,1) | raincoats, cloaks, aprons, suits — rows added *downward* over the pants |
| 8x16 | 3 | BP (0,0) | oversized layered tops reaching the knee |
| 10x8 – 10x11 | ~15 | BP (1,0) | shoulder and sleeve volume — pauldrons, puffed sleeves, gambeson |

The anchor compensates so the shoulders still land correctly: a 10-wide frame
uses `BodyPosition X:1` to re-centre. This is a mature, safe idiom, and it is the
mechanism that unlocks the garment lengths this project repeatedly failed to
reach (V5A long outerwear, V4.5/V4.6 lower body).

---

## 2. What mods do that vanilla does less of

Same frame, same density, measurably richer.

| Measure | Vanilla | Modded 8x8 |
|---|---:|---:|
| Colours per garment (4 directions) | median 6, max 12 | median 10, p90 17, max 115 |
| Colours, front view | ~6 | median 10 |
| Colours, back view | fewer than front | median 7 |
| Ramp depth, dominant fabric | 3–6 steps | median 6 steps |
| Occupied cells per direction | 53–64 of 64 | median 50 front, 43 side |
| Contains near-black | common as "deepest local colour" | 11.6% |

Three real behavioural differences:

1. **The colour budget was under-used by vanilla, not capped by the format.** At
   identical resolution, mods carry roughly 1.7x the colours. Vanilla's ~6 was a
   house style, not a limit.
2. **Mods carve the silhouette; vanilla fills the box.** Median coverage drops from
   ~60 to ~50 cells front and ~43 side. Sleeveless, off-shoulder, cropped and
   open-front garments leave cells transparent so skin and arms read.
3. **Mods break symmetry deliberately.** Only 41.8% of modded fronts are near
   mirror-symmetric (median symmetry 0.938) — the remainder carry a chest pocket,
   badge, brooch or offset closure on one side only.

---

## 3. Construction idioms, measured

Across 983 modded 8x8 fronts:

| Idiom | Share | Reading |
|---|---:|---|
| Collar / neck band distinct from torso | **90.5%** | rows 0–1(–2) are a separate system in almost every garment |
| One- or two-pixel accent colour | **86.0%** | buttons, clasps, badges, tie knots |
| Torso not a flat field | **85.8%** | some structural value variation |
| Contrasting centre column | **77.6%** | the layering idiom |
| …strongly contrasting (ΔL > 40) | 36.9% | open jacket, cardigan, cloak, waistcoat |
| Hem band | 37.6% | |
| Near-symmetric front | 41.8% | |
| Near-black present | 11.6% | |

**The centre-column idiom is the dominant construction device in modded
clothing.** An open garment is rendered as: dark outer field, two dark opening
edges at roughly x=2 and x=5, and a light inner-layer column at x=3–4. Butler
Vest, Blue Cardigan, Gryffindor cloak, Sherlock coat, Watson's coat and Mycroft's
suit all use exactly this. It is the same two-slot region partition I measured in
vanilla's vest and overalls, used far more often and more confidently.

---

## 4. Technique study

### 4.1 Construction and layering

Read from Butler Vest (Open), 5 colours, greyscale so it stays recolourable:

```
00033000     0 = vest / darkest      3 = inner shirt
22444422     2 = vest midtone        4 = inner shirt light
22044022     col 2 and col 5 hold the opening edges
12244221     cols 3–4 hold the inner shirt
02044020
01344310
03444430
04000040     hem
```

Five colours produce a complete, recolourable, legible waistcoat. Construction is
carried by **region assignment**, not by detail.

### 4.2 Restraint at the low end

SubabyTvanZ Shirt 1, a complete sailor top in **three colours**: navy, periwinkle,
white. The collar is the navy V, the body is white, and the mid tone does all the
form work. The back flap is the mid tone with a navy border. Proof that identity
is a structural decision, not a budget.

### 4.3 Length and the extended frame

Sherlock's coat, 8x10 frame, 10 colours:

```
front rows 0–3   white collar points against near-black coat
front rows 4–7   coat body with 3 subtle fold values
front rows 8–9   only the outer columns occupied  <- coat tails hanging past the torso
back  rows 1–5   two flat fields, no closure detail at all
```

The tails are the whole point of the extended frame: rows 8–9 hold nothing but
the two outer columns, so the coat reads as hanging open over the legs.

### 4.4 Shading and folds

- **Ramp depth median 6** in the dominant fabric family, versus the 4 roles
  (deep/shadow/base/light) this project's model provides. **4 is under-provisioned.**
- **Hue drift dark→light is small: median 3.3°, p75 9.6°.** Modded Stardew clothing
  does *not* use the aggressive 30–40° hue-shifted ramps of other pixel-art
  schools. Saturation does not systematically rise in shadow. Restrained,
  near-neutral ramps are part of what keeps the work Stardew-like.
- Folds are **structural, not textural**: one or two darker cells marking a panel
  break, a sleeve junction or a hanging edge. Never noise, never dithering.
- Layicn's Changshan is the exception that proves the rule: its darks are strongly
  hue-shifted purple (#200338) rather than neutral. It still reads, because the
  shift is in the *darkest* step only.

### 4.5 Edge treatment

Only 11.6% of modded garments contain a near-black, and only 29% contain any
colour below luminance 30. **There is no global outline convention.** Edges are
carried by value contrast between adjacent regions. Where a dark line does appear
it marks a *specific* construction event: an opening edge, a collar underside, a
belt, a hem.

This independently confirms the contrast-aware outline rule derived in the sailor
prototype: outline when contrast is low, let colour do the work when it is high.

### 4.6 Trim and decoration

- Trim is a line running parallel to a free edge, one cell in from it — sailor
  collar stripes, cuff bands, hem bands, placket edges.
- Decoration is **small and singular**: 86% carry a 1–2 pixel accent. A Gryffindor
  tie is a two-cell striped column. Frog fastenings on the Changshan are single
  bright cells. Buttons are single cells in a vertical rhythm.
- Whole-torso patterns exist (plaid sweater, knit texture on the cardigan back)
  but are a minority and always low contrast, two values within one hue family.

### 4.7 Front / side / back continuity

- **Front is +x in the right-facing view.** Confirmed again here: the Butler vest's
  light inner-shirt column appears at cols 4–5 in the side view, toward the front.
- **Wrap systems continue in every view**: collar band, hem band, yoke, sailor flap.
- **Front-only systems vanish behind**: plackets, buttons, ties, bibs.
- **The back is simplified but not empty**: median 7 colours versus 10 in front. It
  keeps the collar band, the yoke and the flap; it drops the closure.
- **Left mirrors right**: exact in 60.6%, alpha-identical in 90.4%, median zero
  differing cells. Vanilla was 70% exact. Mirror-by-default with an optional
  small patch is confirmed on both sides.

### 4.8 Sleeves and lower body

- Custom `Sleeves` are shipped by only 9 of ~35 packs, always **16x32 at Scale 4**,
  frame-aligned to the Farmer's own animation atlas, with `DisableNativeOffset`
  and per-frame Idle/Movement animation. This is the only route to cuffs, rolled
  sleeves and contrast sleeves, and it is a genuinely advanced technique.
- `Pants` at 16x32 or 16x16 Scale 4 (348 of 447), with 28x21 used for skirts that
  need extra width. Same principle: extend the frame, keep the density.

---

## 5. Stardew-like versus too far

**Still Stardew-like**

- 8x8 or extended frames at Scale 4; binary alpha; region-partition construction;
  a 4–6 step ramp; small hue drift; 1–2 pixel accents; a distinct collar band;
  simplified backs; mirrored sides; trim parallel to a free edge; deliberate
  silhouette carving.

**Pushing away from the style**

- Resampled high-resolution art. The 41 Scale-under-4 garments average 47 colours
  with 68% carrying partial alpha; they read as smooth illustrations pasted onto a
  pixel game.
- Colour counts above roughly 20 per garment. The corpus tail runs to 115, and
  those items look muddy at gameplay scale.
- Soft alpha gradients used for volume rather than for a deliberate sheer fabric.
- Whole-torso high-contrast pattern, which destroys the construction read.

**Genuine deliberate exceptions worth respecting**

- The Alt-Fashion Set's mesh tops use a *single* intermediate alpha (116) across
  the whole garment to render sheer fabric. That is a controlled material effect,
  not a resampling artifact. Distinguish "one intentional alpha value" from "a
  spread of alpha values".

---

## 6. Revised AA/AG model

### Tier 1 — Vanilla invariants (hold everywhere; never break)

| # | Invariant |
|---|---|
| V1 | One logical pixel is authored directly. No resampling, no anti-aliasing, no smoothing, ever. |
| V2 | Alpha is binary. 97% of the modded corpus and effectively all of vanilla. |
| V3 | Four directions: front, right, left, back. Left defaults to `mirror(right)` — but the mirror must be MATERIALISED into the sheet or declared with `Flipped`; Fashion Sense draws nothing for a facing whose model is absent. See AMENDMENT AG-1. |
| V4 | The garment anchors to a fixed torso point; the Farmer's proportions are not negotiable. |
| V5 | Shoulder coverage rows must stay opaque, or the Farmer shows skin at the shoulder line. |
| V6 | Sleeves are not shirt pixels. Native sleeve recolouring via `SleeveColors` is the default; 1,531 of 1,669 shirts use it. |
| V7 | Front is +x in the right-facing view. |
| V8 | The back drops closure detail but keeps construction. |
| V9 | Identity is carried by contrast times area. A one-pixel accent at high contrast beats a six-pixel shape at low contrast. |

### Tier 2 — Vanilla tendencies (house style, not law; mods safely revise these)

| # | Tendency | Vanilla | Revised for Fashion Sense |
|---|---|---|---|
| T1 | Colour budget | median 6, max 12 | **8–14 typical, 17 at p90, treat 20 as the ceiling** |
| T2 | Ramp depth | 3–6 steps | **4–6 steps in the dominant fabric; 4 roles is under-provisioned, provide 5–6** |
| T3 | Coverage | fills the box, 53–64 of 64 | **carving is legitimate: 43–55 is normal; sleeveless, cropped and open garments show skin** |
| T4 | Symmetry | mostly symmetric | **58% of modded fronts are asymmetric; one-sided pockets and badges are normal** |
| T5 | Deepest value | used as "deepest local colour" fairly freely | **near-black in only ~12%; prefer contrast over a dark line** |
| T6 | Two colour slots | forced by the base/dye-mask system | **an artifact of the vanilla shirt format. Fashion Sense allows fixed colour or an UNCAPPED list of `ColorMaskLayers`. Use as many as the construction has materials** — see AMENDMENT AG-3 |
| T7 | Frame | fixed 8x8 | **8x7 to 8x16 and 10xN are all safe at Scale 4 with anchor compensation** |

**T6 and T7 are the two rules that were purely artifacts of the old shirt system.**
Vanilla's two-slot limit and fixed frame were engine constraints, not aesthetics.

### Tier 3 — Safe modded extensions (adopt these; they are well-attested)

**Architecture (AA)**

| # | Rule |
|---|---|
| A1 | **Frame envelope selection.** Choose from crop (8x7), standard (8x8), long (8x9–8x11), full-length (8x16), wide (10xN). Always Scale 4. Compensate with `BodyPosition` (X:1 for a 10-wide frame). |
| A2 | **Region partition is the primary construction device.** A garment is 2–4 named regions over one torso, not a body plus small stamps. |
| A3 | **Centre-column layering.** An open garment renders as outer field + two opening edges + a 2-cell inner-layer column. Used by 77.6% of the corpus. |
| A4 | **Collar band.** Rows 0–1(–2) are a separate system from the torso in 90.5% of garments. Effectively mandatory. |
| A5 | **Attached versus free edges.** An attached edge is continuous with the body and takes no outline. A free edge terminates the fabric and occludes what is behind it. |
| A6 | **Silhouette carving.** Leaving cells transparent is a design act, not damage — subject to V5. |
| A7 | **Directional continuity classes.** `wrap` systems appear in all four views; `front_only` systems are forbidden behind; `back_only` systems (sailor flap, yoke) are forbidden in front. |
| A8 | **Extended-frame length semantics.** Rows below the torso box belong to the garment's hanging portion and must taper to the outer columns, or they read as a skirt rather than an open coat. |

**Art grammar (AG)**

| # | Rule |
|---|---|
| G1 | **Colour budget 8–14, hard ceiling ~20** across all four directions. |
| G2 | **Ramp of 4–6 steps** in the dominant fabric; secondary fabrics may carry 3. |
| G3 | **Small hue drift**: 3–10° dark to light. Do not adopt 30°+ hue-shifted ramps. |
| G4 | **No global outline.** A dark line marks a named construction event only. Where two adjacent regions already differ by more than ~45 luminance, the colour change *is* the edge. |
| G5 | **Free-edge termination plus occlusion.** A hanging edge takes the fabric's dark step; the body cell behind it takes a *shadow*, never the darkest step, or the pair reads as a two-pixel black bar. |
| G6 | **Accent economy.** One or two 1–2 pixel accents, high contrast, carrying identity. Present in 86% of the corpus. |
| G7 | **Trim runs parallel to a free edge**, inset one cell, and is skipped where the region is under three cells wide. |
| G8 | **Folds are structural.** One or two darker cells at a panel break or sleeve junction. Never dithering, never texture noise. |
| G9 | **Back simplification is a rule, not laziness.** Target roughly 70% of the front's colour count. |
| G10 | **Mirror by default, patch rarely.** Author left only when a genuine asymmetry exists, and then usually as a few cells. |

### Tier 4 — Keep authored or special-case; do not generalise

| Technique | Why it stays authored |
|---|---|
| Custom `Sleeves` atlases | 16x32 Scale 4, frame-aligned to the Farmer's animation, with per-frame Idle/Movement animation. Only 9 packs attempt it. High risk, high skill, and the only route to cuffs. |
| Animated shirts | 12 of 1,669 use Idle/Movement animation on the shirt itself. Genuinely rare. |
| Semi-transparent fabric | Legitimate only as a *single* deliberate alpha value across a whole region (mesh, veil). Never as a gradient. |
| Whole-torso pattern (plaid, knit texture) | Works only at low contrast within one hue family. Easy to get wrong, hard to parameterise. |
| Strongly hue-shifted darks | Layicn's purple-black works; it is a considered choice about one step of one ramp, not a rule. |
| Full-body high-resolution gowns | 96x96 at Scale 2. A different medium. Do not generalise. |
| Multi-layer `ColorMaskLayers` (2–3 layers) | 46 garments. Powerful for player recolouring but needs disjoint colour sets and careful validation. |

---

## 7. Consequences for this project

1. **The pending resolution decision now has evidence.** In 1,146 measured
   garments, nothing uses 16x16 at Scale 2. The community's entire quality
   distribution sits at vanilla density. The Phase 1 resolution sheet should be
   judged with that in mind; if 8x8 at Scale 4 reads as well, it aligns the project
   with the whole corpus and gains native vanilla shirt support as a by-product.
2. **Density was the wrong axis for "vanilla plus".** The corpus buys richness with
   colours (10 versus 6) and with frame extent, not with pixels per inch. This
   project has been spending its complexity budget on the one axis the community
   does not use.
3. **Frame extension solves a problem the project failed at three times.** Long
   coats, cloaks and aprons are routine at 8x10 and 8x11. V5A's "bounded long
   outerwear", V4.5 and V4.6's lower-body work were all attempts to reach garment
   lengths that this idiom reaches directly.
4. **The four-role model needs a fifth and sixth step.** Median modded ramp depth is
   6; the project provides 4.
5. **The slot model should grow from 2 to 3–4.** Vanilla's two-slot limit was a
   format artifact, and the centre-column layering idiom needs at least three.
6. **The prototype's contrast-aware outline rule is corpus-validated.** Only 11.6%
   of modded garments use near-black at all.
7. **Region partition beats small stamps as the primary device**, which matches the
   adversarial review's finding and is now confirmed at 77.6% across a much larger
   corpus.

---

## 8. Open questions this study did not settle

- Whether 8x8 at Scale 4 or 16x16 at Scale 2 reads better *for this project's
  output* is still a human judgement; the corpus shows what others chose, not what
  looks best on your sheets.
- How to parameterise whole-torso patterns without them reading as noise.
- Whether extended frames interact safely with the pants layer during animation.
  Every extended-frame garment in the corpus is static; none was tested here in
  motion.
- Custom sleeves remain unmeasured for quality; only their format was surveyed.


---

# AMENDMENTS FROM THE OFFICIAL FASHION SENSE REFERENCE

Added 2026-09-08 after ingesting the official Fashion Sense sources into
`references/fashion-sense-official/`. Each amendment cites the reference entry
it comes from. **Only assumptions contradicted or expanded by official
behaviour are touched; everything else in this document stands as measured.**

## What was checked and left unchanged

The corpus measurements are art observations and remain valid. In particular:

* **8x8 at Scale 4 as the primary density** (§1) is confirmed by the framework:
  `Scale` has a documented default of `4.0`, matching the game's own scale.
  The finding that 88% of shirts use 8x8/Scale 4 is a statement about what
  authors do, and nothing in the official docs contradicts it.
* Colour counts, ramp depth, region partition, accent size, edge treatment,
  front/side/back continuity, and the Tier 1–4 structure are unaffected.
* The extended-envelope list (8x7 … 10xN) stands; the framework's only stated
  limit is 16384x16384.

## AG-1. Mirroring is a framework feature, not only an art habit
* **Was:** "Left mirrors right … mirror-by-default with an optional override"
  (§4.7, and the V3 row of the Tier 1 table).
* **Now:** still true as art, and the framework supports it directly:
  `Flipped` (bool, all eight appearance types) draws a model mirrored, and the
  wiki names Left/Right as its purpose. So Right may point at the Left region
  with `Flipped: true` instead of duplicating pixels.
* **Hard constraint that was never stated:** a facing whose model is absent
  draws **nothing** — there is no implicit mirroring or fallback.
  `HatContentPack.GetHatFromFacingDirection` is a plain switch returning null
  (facing 0=Back, 1=Right, 2=Front, 3=Left).
* **Reference:** BEHAVIOR_MAP A2, A3.

## AG-2. Greyscale art is a tint mask, and that dictates recolour maths
* **Was:** §4 treats greyscale as "so it stays recolourable" without saying
  what the framework does with it.
* **Now:** with no masks declared, the player's colour choice targets the
  **whole sprite**, multiplicatively. Greyscale source art is therefore
  authored *as a tint mask*, which is why a recolour that pins each step to its
  authored absolute luminance washes these assets out, and why multiplying the
  chosen colour by the authored value is the faithful operation.
* **Consequence for the art grammar:** the value ramp an author draws is a
  *ratio* ladder, not a set of final colours. Ramp depth and contrast should be
  judged as ratios.
* **Reference:** BEHAVIOR_MAP D1; `Color-Masks-Property.md`.

## AG-3. Colour slots are uncapped, and mutually exclusive with baked colour
* **Was:** "Fashion Sense allows fixed colour or 1–3 mask layers. Use 3–4 slots."
* **Now:** `ColorMaskLayers` is an **uncapped list**. Each layer has `Name`,
  `Values` (RGB list), optional `DefaultColor` and `IgnoreUserColorChoice`.
  Layers should not share colours. Values need not be greyscale — a non-grey
  mask value is applied **additively**, producing a different hue than its grey
  counterpart.
* **The trap:** *all colour masks are ignored when `DisableGrayscale` is true.*
  Baked colour and player-recolourable layers are mutually exclusive per model.
  Our exporter currently sets `DisableGrayscale: true`, so adding
  `ColorMaskLayers` without removing it would silently do nothing.
* **Reference:** BEHAVIOR_MAP D2; `Color-Mask-Layers-Property.md`.

## AG-4. Skin is a separate masking channel
* `SkinToneMasks` takes exactly three RGB values, replaced by the player's
  three skin shades; `DisableSkinGrayscale` opts out. Relevant to any garment
  that exposes skin (off-shoulder, sandals, short sleeves), which the corpus
  study treated purely as drawn pixels.
* **Reference:** BEHAVIOR_MAP D3.

## AG-5. Sleeve/shirt colour coupling is declarative
* A shirt declares `SleeveColors`; sleeves set `UseShirtColors: true` to follow
  them. `DisableNativeOffset` (Sleeves only) turns off the framework's built-in
  arm offset. §4.8's observation that only 9 packs ship custom sleeves is
  unchanged, but the coupling mechanism is now known.
* **Reference:** BEHAVIOR_MAP H.

## AG-6. The corpus's own hair convention, measured
* Over the 116 hats in the authored source library: **114 declare nothing
  (hair kept), 2 declare `HideHair`, none use `UseBaldHead`.** Both exceptions
  (Headscarf, Plague Doctor Mask) enclose the whole head.
* **Consequence:** hiding hair is not the normal treatment even for
  close-fitting hats. It is an opt-in justified by construction.
* **Reference:** BEHAVIOR_MAP B1; `v5/hairpolicy.py`.
