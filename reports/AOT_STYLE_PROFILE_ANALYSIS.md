# AoT-Inspired Style Profile Analysis

Status: corpus inspected and coordinate-free style profile defined. This report describes aggregate fashion language, not individual costume-copy instructions.

## Corpus inspection

All eight files in `references/style-profiles/AoTInspired/` were visually inspected before the profile was authored.

### Primary evidence

- `06a6c87d45d9159710cc6d1e466f5b7b.jpg`: cropped brown side jackets, high folded collar, angled lapel, shoulder and upper-sleeve paneling.
- `36af5584c94ab46f564e4750b5f13de8.jpg`: waist-length tan jacket, dark inner shirt, strong front opening, defined waist, utility pockets and harness/belt repetition.
- `901bcdb7968fc2d1dc816e6d9f87371c.jpg`: a family ranging from the core brown jacket to fitted dark tops, civilian dresses, and muted red/black outerwear.
- `aot.png`: multi-outfit sheet connecting tan cropped jackets, olive inner shirts, fitted vests, white shirts, dark harness-heavy combat wear, and practical brown trousers.
- `aotfront.jpeg`: front-view outer jacket, vest, fitted shirt, dark formal coat, olive outer layer, and white/charcoal military tailoring.

### Secondary evidence

- `a0tside.jpeg`: long black formal outerwear and a broad side silhouette.
- `images (1).jpeg`: alternate field uniform/cloak family and practical fitted silhouettes.
- `images.jpeg`: modern civilian reinterpretations using gray, black, cream, skirts, fitted shirts, and restrained layers.

The low-resolution secondary images are useful only for branch-level silhouette and palette tendencies. They are not reliable sources for construction detail.

## Recurring style language

### Core military branch

The strongest repeated identity is a compact, waist-emphasized field jacket:

- warm tan or brown outer cloth;
- structured folded or high collar;
- angled lapel/front-opening rhythm;
- visibly separate olive, charcoal, cream, or muted dark inner shirt;
- upper-chest and shoulder segmentation;
- sharply terminated waist/hem;
- dark leather-like lines used at construction points;
- practical fitted-to-regular mass rather than oversized cloth.

The recognizable identity comes from the combination of compact outer panels, collar mass, inner-layer contrast, and waist termination. Brown alone is insufficient.

### Tailored shirt and vest branch

Repeated related garments include:

- fitted white/cream shirts;
- small folded collars;
- dark or olive vest-like upper overlays;
- disciplined center closures;
- dark waist structures;
- restrained formal/workwear construction.

This branch is useful for proving that the profile can generate related clothing without producing three copies of the field jacket.

### Civilian and dark-formal branch

The secondary language includes:

- long dark coats;
- muted burgundy or black civilian outerwear;
- gray/black modern layering;
- simpler fitted shirts and pullovers;
- the same controlled collar and waist emphasis with fewer explicit military cues.

The frozen shirt renderer cannot produce a genuinely long coat. This POC therefore treats long-coat influence as palette/formality input and does not falsely claim a long silhouette.

## Stardew/Fashion Sense translation

### Preserve first

1. compact structured garment identity;
2. strong collar or yoke construction;
3. outer/inner layer relationship;
4. deliberate major panels;
5. waist or lower-band termination;
6. high-value palette separation;
7. at most one subordinate utility rhythm.

### Simplify

- Pocket maps become the existing panel hierarchy; unsupported pockets are not painted on manually.
- Harness systems become one placket, yoke, or waist-band gesture.
- Multiple belts and buckles are omitted.
- Shoulder epaulets are absorbed into collar/yoke construction.
- Vest styling becomes a fitted button-shirt overlay because native animated sleeves remain enabled.
- Long coats become standard torso outerwear with dark formal color blocking.

### Exclude

- logos, faction insignia, and emblems;
- exact pocket, belt, or harness arrangements from any one character;
- exact character palettes and costume layouts;
- tiny decorative buckles;
- realistic fabric noise;
- freehand pixels outside the frozen renderer grammar.

## Formal profile decisions

The profile prefers JACKET, BUTTON_SHIRT, and selectively SWEATER. JACKET carries the core style; BUTTON_SHIRT carries the vest/uniform relation; SWEATER is permitted only for the civilian branch.

Preferred construction:

- fit: regular or fitted where the archetype supports it;
- neckline: open for tailored garments, shallow V for civilian knitwear;
- collar: wide or small folded;
- closure: center-open or buttons;
- layering: visible inner layer or overlay panel;
- panels: split outer panels, center placket, or yoke;
- hems: structured, contrast band, or a deliberately plain tailored termination.

Style strength is bounded:

- `SUBTLE`: one fieldwear cue on ordinary Stardew clothing;
- `MODERATE`: two or more coordinated construction cues;
- `STRONG`: the strongest legal compact field-jacket grammar, still without insignia or exact costume replication.

The test deliberately emphasizes `MODERATE` and `STRONG`.

## Original palette families

The following families were authored from the corpus's broad relationships without sampling image colors:

- `field_tan_olive`;
- `olive_warm_beige`;
- `ivory_black_brown`;
- `dusty_khaki_deep_gray`;
- `civilian_burgundy_charcoal`.

Each retains a dark-to-light main-fabric mask through the frozen FS grammar and one coherent fixed secondary region. Their values are authored, not extracted from reference pixels.

## Frozen-renderer limitation relevant to the corrected target

The strongest requested field-jacket candidate can preserve tan/brown outer cloth, wide collar/lapel, split panels, dark inner shirt, body coverage, and a structured waist. The frozen semantic vocabulary has no `cropped_length`, `pocket_flap`, `epaulet`, `harness_line`, or leather-trim region. The permanent renderer likewise has no renderer-owned masks for those concepts.

This POC will not smuggle those traits in as hand-painted exceptions. The closest candidate will be rendered honestly. If the major supported construction is not enough for immediate AoT recognition, that is a meaningful stress-test failure and evidence that the future semantic vocabulary needs a bounded construction extension before production—not evidence that the current renderer should be hacked.
