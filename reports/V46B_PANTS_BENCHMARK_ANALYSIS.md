# V4.6B Lower-Body Benchmark Analysis

## Scope and authority

The requested `references/benchmark/pants.zip` corpus was already extracted at
`references/benchmark/pants/`; the ZIP itself is not present. Every supplied
lower-body PNG and its available Fashion Sense JSON was inspected. Shoe-only
material was inventoried but excluded from V4.6B.

The corpus includes four compact 16×32 Pants packs, several HD jeans/trouser
packs, three 16×16 lower-body templates, skirt palettes/reference sheets, and
accessory examples. Some community JSON uses older conventions or invalid
trailing commas. It is useful as an art and pose benchmark, not as the runtime
contract. Installed Fashion Sense 7.5.0 and Stardew 1.6.15 behavior remain
authoritative.

No benchmark pixels, palettes, motifs, garment layouts, or texture coordinates
are consumed by the V4.6B generator.

## Pants findings

- Strong pants readability comes from two long vertical leg channels, not one
  lower-body color block.
- The waist and hips may connect, but the center front/back construction must
  develop into an inseam before the lower termination.
- Each leg needs an independent cuff or ankle termination. A continuous
  full-width lower border reads as a skirt hem.
- Knee articulation and side seams work as subordinate construction cues. They
  cannot substitute for two-leg geometry.
- Fitted, tapered, straight, and relaxed trousers alter the outer leg path and
  lower width; they do not merely change color.
- Side poses need one coherent trouser mass with a visible outer seam and a
  deliberate cuff. A cropped front silhouette is insufficient.
- Back stride poses often create the widest native leg separation, so they need
  frame-specific construction rather than a static mirrored front.

## Shorts findings

- Shorts need two separate high hems and an exposed native lower leg below each
  hem.
- The center split begins below the hip/crotch. A split carried to the waistband
  becomes an exposed-body hole.
- Rolled/cuffed shorts use a paired termination band; the band must not bridge
  both legs.
- Wide or relaxed shorts widen the two leg openings independently. A single
  wide trapezoid reads as a mini skirt.
- Side shorts are shorter and lighter than pants, with a high side hem and one
  structural seam.

## Skirt findings

- A skirt is a deliberately connected mass. It must not inherit the pants
  inseam or independent cuff vocabulary.
- A-line and soft-flare identities come from controlled widening between the
  waistband and hem.
- Pleats are value/structural lines inside one garment mass; they are not alpha
  splits.
- The hem remains continuous through the center while the native legs remain
  visible below it.
- Side volume is narrower than the front/back flare but must remain a unified
  garment with an intentional lower edge.

## Motion and high-density implications

The installed Farmer base uses a six-column, 126-frame 16×32 topology that
matches the Fashion Sense Pants animation contract. V4.6 decorated only a
narrow portion of that envelope, which made its trousers resemble shorts or a
generic lower-body slab.

V4.6B therefore uses a full 32×64 logical Farmer frame at Scale 2. This has the
same approximate 64×128 display footprint as a 16×32 Scale-4 frame but provides
four times as many logical cells. The 16×32 source envelope is used only to map
coverage and motion. Finished silhouettes, seams, cuffs, pleats, panels, and
shading are resolved directly at 32×64; no finished 16×32 or 8×8 art is
upscaled.

The extra resolution is spent in this order: coverage, article identity,
silhouette, construction, surface structure, color blocking, small details,
then shading. It is not a license for texture noise.

## Reusable grammar extracted

1. Pants: connected hips, paired long channels, center construction, independent
   terminations.
2. Shorts: connected hips, paired short channels, high independent hems,
   exposed lower legs.
3. Skirts: connected waistband-to-hem mass, no inseam, continuous lower edge,
   optional flare/pleat rhythm.
4. All articles: direction-aware reconstruction from one semantic recipe.
5. Surface detail may reinforce an article, but the alpha/major-region geometry
   must identify it without shading.

