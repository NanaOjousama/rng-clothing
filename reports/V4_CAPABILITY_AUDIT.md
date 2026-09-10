# Generator V4 Garment-Article Capability Audit

Scope: current RNG Clothing project, Fashion Sense 7.5.0, Stardew Valley 1.6.15, and the proven 16×16 Scale-2 shirt pipeline. This audit distinguishes framework possibility from an article type that the current generator can render reliably.

## Decision summary

| Article | Classification | Reason |
|---|---|---|
| fitted shirt / standard top | **SAFE NOW** | Existing button-shirt grammar, native animated sleeves, body envelope, anchors, four directions, and surface zones are proven. A lower-torso taper can be applied below required coverage rows. |
| sweater / pullover | **SAFE NOW** | Existing heavy-mass/yoke sweater grammar, ribbed termination, native sleeves, and four-direction templates are proven. |
| vest-led top | **SAFE NOW, bounded** | Reliable as a vest **over an inner shirt**: the shirt layer retains body coverage while article translation assigns sleeve/shoulder material to the under-shirt and body panels to the vest. A truly bare-arm vest would require more careful skin/sleeve behavior and is not included. |
| cropped jacket | **SAFE NOW, bounded** | A jacket can terminate two HD cells above the normal shirt bottom while retaining the existing upper-body coverage envelope, native sleeves, lapels, inner layer, and side grammar. The crop is visible without enlarging the frame. |
| short jacket / standard outerwear | **SAFE NOW** | Existing jacket grammar already has a fuller lower and side mass, split/open outer shell, inner layer, lapels, and native sleeves. It serves as the full-length comparison to cropped outerwear within the shirt footprint. |
| high-collar outerwear | **SAFE NOW as a short-outerwear variant** | Collar/cuff/yoke changes fit the proven frame. It is not a separate long garment and does not require new layer ownership. |
| long jacket / coat | **EXPERIMENTAL** | Fashion Sense supports arbitrary `ShirtSize`, but a rectangle extending below the proven torso footprint would remain a static per-direction shirt while the legs, horse pose, tools, sitting, swimming, and pants animate separately. A loadable PNG would not establish a believable coat. No V4 coat is shipped. |
| mantle / cape-like outerwear | **EXPERIMENTAL** | Fashion Sense accessories can be body-sized and drawn behind/after other layers, but a cape requires a separate appearance, draw-order contract, motion strategy, and likely presets. It is not a shirt-article adapter. |
| pants | **LATER** | Fashion Sense pants are supported, but leg motion, shirt overlap, sitting/swimming, color integration, and their own article templates need a dedicated lower-body audit and validation suite. |
| skirt | **LATER** | A fitted short skirt may be possible through Fashion Sense pants, but wide/long hems need animation-aware lower-body geometry. It must not be inferred from the top renderer. |
| boots / shoes | **LATER** | Fashion Sense shoes are supported and item-linkable, but they are a separate layer/type with leg-frame and pants-order concerns. They do not help prove upper-garment translation. |
| accessory-like upper additions | **EXPERIMENTAL** | Scarves, shoulder pieces, and capes are feasible framework types, but require accessory slot, draw order, preset/equip, and multiplayer UX decisions outside this first V4 article model. |

## Why true long outerwear is not in V4

Fashion Sense confirms arbitrary source rectangles; it does **not** provide a dedicated coat type. A long coat would need one or more of:

- a taller shirt frame extending into animated legs;
- coordinated pants/coat-tail art;
- separate custom sleeves;
- action/horse/sitting/swimming animation states;
- explicit layer and preset coordination.

The current shirt POC only proves a 16×16 logical frame at Scale 2 and `BodyPosition (0,32)`. Calling a same-footprint full-height top a “long coat” would be naming, not article translation. Calling an untested taller static rectangle successful would overpromise. V4 therefore records `LONG_OUTERWEAR` in the article vocabulary as unsupported/experimental and rejects it from generated collections.

## First practical V4 article set

V4 implements five adapters within four primary article families:

1. `FITTED_SHIRT` — tailored lower taper; shirt/placket/collar zones.
2. `SWEATER_TOP` — uninterrupted cloth mass and ribbed/structured termination.
3. `VEST_TOP` — vest-over-shirt material topology with under-shirt sleeves.
4. `CROPPED_JACKET` — true two-HD-cell shorter outer shell with relocated termination cues.
5. `SHORT_OUTERWEAR` — standard shirt-footprint outerwear retaining the full lower shell.

The first four create the requested visible article categories. `SHORT_OUTERWEAR` supplies the honest alternate when long outerwear is not yet runtime-proven and lets validation compare cropped versus full shirt-footprint jackets.

## Frozen contracts retained

- V3 concept, surface design, topology, palette, rarity, and diversity systems.
- Existing Fashion Sense 16×16 logical frames at Scale 2.
- `BodyPosition (0,32)` and direction starts at Y 0/16/32/48.
- Existing upper-body coverage envelope and outline/shading grammar.
- Native animated sleeve integration through `SleeveColors`.
- Vanilla renderer and all V1/V2/V3 outputs.

V4 adds an article selector and post-V3 translation adapter. It does not replace the V3 renderer and does not claim unsupported lower-body garments.
