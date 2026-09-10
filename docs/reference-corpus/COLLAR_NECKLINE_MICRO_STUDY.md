# Collar / Neckline Micro-Study

## Scope and evidence

This study treats the following files as read-only visual references:

- `references/collar/collarshirts-female.png`
- `references/collar/collarshirts-male.png`

Both files are 129×8 RGBA strips containing sixteen compact 8×8 front-facing shirt studies plus one trailing column. They are byte-identical (the same SHA-256 hash), and a pixel comparison finds no differences in any of the sixteen cells. The supplied material therefore does **not** demonstrate male/female construction differences, side views, or back views. It directly supports front-neckline and pixel-economy findings; side/back guidance below is a project-facing abstraction informed by those observations and the existing directional garment research. No source pixels or coordinates are reused.

## What the front studies demonstrate

The strip obtains visibly different neck reads with a small number of high-information value groups rather than detailed outlines. Across the studies, the useful families include:

- compact crew and bound neck openings;
- wide rounded or shallow scoop openings;
- shallow and deeper V openings;
- folded/open shirt-collar relationships with a visible inner field;
- square or broad horizontal neck fields;
- high bands and close neck treatments;
- broad sailor-like overlays;
- layered diagonal/scarf-like neck constructions;
- collarless garments whose neck is defined mostly by body/fabric separation.

The clearest examples do not rely on a single isolated dark pixel. They use a short, coherent opening edge, then let the torso fabric or inner layer explain the space below it. A neckline reads faster when its width, depth, and relation to the shoulders agree.

## Generalized front-neck principles

### Width before detail

At this scale, the opening's width is often more important than a literal collar outline. Narrow openings read close, sporty, or high; medium openings read like everyday crew or shirt necks; broad openings read softer, layered, sailor-like, or deliberately open.

### Depth must have a floor

A V may end in a point because the point is the construction. Rounded openings should not. A rounded or shallow opening needs a short horizontal or gently stepped lower floor. If its center terminates in one darkest cell, the viewer reads an arrow, notch, tie, or emblem rather than cloth.

### Separate inner layer from collar edge

Open shirts and folded collars need three distinguishable ideas: outer fabric, collar/opening edge, and inner shirt or skin field. Compressing all three into one bright center strip destroys the construction.

### Use darks at recesses, not everywhere

The most useful structural darks sit beneath the chin, under a folded edge, or at the two lateral points where a collar turns. A uniformly dark necklace-like loop looks pasted on. Highlights should describe the upper fold or one lit collar plane, not trace the entire opening.

## Rear-neck and rear-collar grammar

The rear treatment should be chosen independently from the front opening. A front V does not imply a rear V. In most ordinary garments, the back opening is shallower and broader than the front.

### Soft rear scoop

- Use for tees, crewnecks, sweatshirts, light knits, and collarless woven tops.
- Keep the opening broad enough to read as a neck boundary but shallow enough to remain at the upper back.
- Use a two-sided curve with a short, flat or softly stepped center floor.
- Prefer dark anchors at the lateral recess/turns plus a quieter center shadow.
- At the project's 16×16 logical resolution, one to two rows of depth is normally enough; the center floor should occupy multiple cells rather than terminate at one point.

### Rear collar band

- Use for folded shirts, work jackets, blazers, high collars, and structured outerwear.
- Treat it as a shallow horizontal or gently curved band wrapping behind the neck.
- Let the lower edge transition into a yoke, rear seam, or quiet fabric field.
- The band may be firmer or taller than a tee binding, but it should not descend as a narrow triangle.

### Rear feature ownership

- Tee: quiet binding or soft scoop.
- Cardigan: soft rear knit/shawl band over a coherent knit back.
- Folded shirt/work jacket: rear collar band followed by a broad yoke.
- Blazer: rear collar band plus shoulder seam/center seam, never rear lapels.
- Sailor top: the front collar reconstructs into a broad rear sailor panel rather than a small neckline mark.
- High collar: a close band with side/profile height; the rear lower edge remains broad.

## Evaluation of the project's sharp rear ▼

The current failure is a narrow inherited crease that continues downward beneath otherwise valid rear collar/yoke construction. Its single-point lower termination has the visual weight of a symbol. It can be misread as an upside-down badge, tie, opening, or cutout, and it makes unrelated garments share the same stamped rear identity.

Recommended replacement:

1. Treat the long central V as an invalid rear carrier for ordinary tees, cardigans, and work jackets.
2. End the rear opening within a shallow upper-neck zone.
3. Give the center a short horizontal/softly stepped floor, never a one-cell point.
4. Preserve garment-owned collar or yoke cells above and beside the opening.
5. Restore removed lower-point cells from adjacent existing fabric light/shadow planes so material shading remains continuous.
6. Choose `SOFT_REAR_SCOOP` for collarless/soft garments and `REAR_COLLAR_BAND` for folded or structured collars.

The desired read is a broad, low-depth neck transition. It should be visible at gameplay size but subordinate to the garment's collar, opening, yoke, or back mass.

## Male / female / unisex construction

The supplied male and female sheets offer no evidence of gender-specific geometry because they are identical. The project should not invent a gender rule from their filenames.

A safer semantic model is unisex and construction-led:

- neckline width follows article, fit, and desired openness;
- collar scale follows fabric weight and garment family;
- shoulder-to-collar spacing follows shoulder intent and torso mass;
- softer, broader, narrower, or more decorative neck treatments remain style choices rather than gender locks;
- any future body-branch differences should be learned from genuinely distinct worn references and represented as bounded fit/body translations, not “male = narrow/dark” or “female = wide/decorative.”

## Pixel economy

- One compact dark cluster can establish the under-chin recess.
- Two lateral dark anchors can show where a collar turns around the neck.
- A short light edge can communicate the top plane of a folded collar.
- A broad inner field is more useful than extra buttons when showing an open collar.
- One or two logical rows are sufficient for most rear neck bindings at 16×16.
- Deep V shapes require deliberate stepped descent; rounded shapes require a multi-cell floor.
- Avoid full black loops, uniform outlines, isolated center points, and collars whose dark mass is larger than the neckline they explain.
- Extra Fashion Sense resolution should clarify fold depth, band thickness, and layer separation—not make the neck busier.

## Directional collar grammar

### Front

Show the defining topology: bound opening, V descent, folded leaves, open inner field, high band, or sailor overlay. The opening may be the dominant construction cue, but it should connect to the torso rather than float.

### Right and left

Compress the front width into depth. Preserve one collar turn, fold thickness, band height, or outer/inner separation. A side collar normally needs fewer pixels than the front, but its neck-to-shoulder attachment must remain visible. Asymmetric/open collars may legitimately differ left-to-right.

### Back

Replace front opening logic with the correct rear carrier: soft scoop, binding, collar band, sailor panel, hood junction, or yoke. Front plackets, lapels, ties, and deep V points should disappear. Rear depth should generally be shallower than front depth.

## Proposed semantic collar library

Relative width and depth are torso-relative categories, not source coordinates.

| Semantic type | Front read | Side read | Back read | Relative width | Relative depth | Common failure mode |
|---|---|---|---|---|---|---|
| `ROUND_CREW` | Compact bound rounded opening | Thin binding with minimal projection | `SOFT_REAR_SCOOP` or quiet binding | Narrow–medium | Shallow | Becomes a dark necklace or square notch |
| `SHALLOW_V` | Broad, short V with an intentional two-plane meeting | One small diagonal edge; no center stripe | Soft scoop, not a rear V | Medium | Shallow | Single dark center pixel reads as badge/tie |
| `DEEP_V` | Deliberate stepped V exposing an inner field | Outer edge and inner layer remain distinct | Shallow scoop or tailored band | Medium | Deep front only | Copied to back; collapses into bright center stripe |
| `FOLDED_COLLAR` | Two readable collar leaves around placket/inner field | One projecting fold and under-collar shadow | `REAR_COLLAR_BAND` above yoke | Medium–broad | Moderate | Leaves become tiny triangles detached from shoulders |
| `OPEN_COLLAR` | Folded/open neck with a broad inner field and no forced full placket | One outer leaf plus visible inner neck | Rear collar band or quiet yoke | Broad | Moderate | Inner field narrows into a universal center stripe |
| `HIGH_BAND_COLLAR` | Close upright band framing a small opening | Height and neck attachment are primary | Continuous close rear band | Narrow–medium | Shallow opening; taller band | Oversized block covers face or reads as scarf |
| `SAILOR_COLLAR` | Broad V/opening with shoulder-spanning collar mass | Collar wraps over shoulder as a distinct layer | Wide rear sailor panel | Broad | Moderate | Reduced to an ordinary V or copied front motif |
| `COLLARLESS` | Neck defined by clean body/skin or inner-layer boundary | Minimal edge with no false projection | Very quiet soft scoop | Narrow–broad by article | Very shallow | Accidental dark collar is added by polish |
| `SOFT_REAR_SCOOP` | Not a front type; paired with soft/closed necks | Terminates gently before shoulder turn | Broad shallow curve with multi-cell floor | Medium–broad | Very shallow | Sharp single-point bottom recreates ▼ |
| `REAR_COLLAR_BAND` | Not a front type; paired with folded/high/structured collars | Band thickness remains visible | Shallow wrap band leading into yoke/back field | Medium–broad | Shallow | Becomes a thick horizontal bar or narrow V |

## Recommended semantic model

Do not store one `collar` value and reuse its geometry in every direction. Use at least:

- `frontNecklineIntent`
- `frontCollarConstruction`
- `sideCollarDepth`
- `rearNeckCarrier` (`SOFT_REAR_SCOOP`, `REAR_COLLAR_BAND`, `SAILOR_REAR_PANEL`, `HOOD_JUNCTION`, or quiet none)
- `rearNeckWidth`
- `rearNeckDepth`

This separation preserves family identity and prevents a front V/opening carrier from leaking into unrelated backs.

## Study conclusion

The references strongly support compact, width-led front neckline grammar and disciplined use of dark recess pixels. They do not directly support directional or gender comparisons. The project's pointed rear-neck problem should be corrected through a shallow, multi-cell rear floor and garment-specific rear carrier selection—not by adding shading, trim, or a universal rounded stamp.

No renderer, grammar data, palette, garment, or test pack was modified during this study.
