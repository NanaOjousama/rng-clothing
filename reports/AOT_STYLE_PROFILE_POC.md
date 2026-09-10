# AoT-Inspired External Style-Profile POC

Status: technical pipeline and three-garment style coherence pass. Immediate unlabeled Attack-on-Titan recognition is **provisional**, not proven by static review.

## Frozen architecture boundary

The experiment did not modify:

- the Generator V2 recipe shape or construction order;
- rarity budgets;
- the Fashion Sense permanent structural masks;
- edge, lighting, gesture, termination, coverage, or side-view grammar;
- Fashion Sense anchor/scale/sleeve behavior;
- the vanilla renderer;
- TFWR.

The only shared-data extensions are new legal style-profile/reference-trait identifiers and five authored palette-family records. Recipes remain the same coordinate-free V2 objects. `styleStrength`, corpus branch, and style evidence are external selection context and do not enter the renderer.

No final texture contains a manually painted style-specific pixel. The permanent renderer source contains no `AoTInspired` or profile-specific branch.

## Reference use

All eight supplied images were inspected. The profile is derived from repeated corpus-level traits:

- compact tan/brown field jackets;
- high or folded collars and lapels;
- dark olive/charcoal/neutral inner layers;
- fitted uniform and vest-like shirt construction;
- yokes, disciplined panels, and strong waist terminations;
- dark leather-like value accents;
- secondary civilian and formal branches.

No logo, insignia, exact character palette, exact pocket arrangement, or exact harness map was encoded. Reference PNG/JPEG pixels are never read by the generator or renderer.

Formal profile: `style-profiles/AoTInspired/profile.json`.

Detailed corpus analysis: `reports/AOT_STYLE_PROFILE_ANALYSIS.md`.

## Five semantic recipes

Exactly five original recipes were generated deterministically.

| ID | Name | Strength | Branch | Archetype | Rarity | Main construction | Palette | Rendered |
|---|---|---|---|---|---|---|---|---|
| 01 | Rampart Field Jacket | Strong | military core | Jacket | Rare | wide collar, open split panels, visible inner layer, structured waist | field tan / olive | yes |
| 02 | Mosswatch Utility Jacket | Strong | military core | Jacket | Rare | folded collar, open split panels, visible inner layer, contrast lower band | olive / warm beige | no |
| 03 | Cadence Yoke Shirt | Moderate | civilian utility | Button shirt | Rare | fitted folded collar, vest-like yoke overlay, buttons, structured lower band | ivory / black-brown | yes |
| 04 | Citadel Dress Shirt | Moderate | civilian utility | Button shirt | Uncommon | fitted single layer, folded collar, center placket, plain hem | dusty khaki / deep gray | no |
| 05 | Nightwatch Collar Knit | Strong | dark formal | Sweater | Rare | shallow V, broad collar, solid heavy body, structured waist | burgundy / charcoal | yes |

All five pass V2 compatibility and rarity validation. There are no exact structural duplicates. After gameplay-scale review, Mosswatch was removed from the final set because two split-panel jackets still converged despite semantic differences. The corrected selected set uses three different archetypes and three different side templates.

Recipe batch: `output/recipes/aot_style_profile_poc.json`.

Human and automatic pre-render review: `reports/AOT_RECIPE_REVIEW.md`.

## Three selected garments

### Rampart Field Jacket

This is the corrected close-adaptation candidate.

Preserved major language:

- compact waist-length jacket impression within the Farmer torso slot;
- warm tan/brown outer panels;
- wide structured collar/lapel recess;
- visibly darker olive inner shirt;
- panel-led shoulder/upper torso organization;
- strong dark outline and crease anchors;
- structured lower termination acting as a simplified waist/belt rhythm;
- `lapel_led` side reconstruction.

Omitted rather than faked:

- insignia and logos;
- exact chest-pocket flaps;
- epaulets;
- multiple harness straps or buckles.

At static gameplay footprint, this is clearly the iconic member of the set. The tan-over-olive, cropped/structured, wide-lapel formula is recognizable as AoT-adjacent. It is not uniquely franchise-specific: without an explicit label, some players may still read it as a general anime field jacket. The corrected “immediate recognition” criterion therefore needs an unlabeled in-game player judgment.

### Cadence Yoke Shirt

Cadence carries the fitted uniform/vest language through a high-value ivory body, dark black-brown shoulder yoke, small folded collar, tailored placket organization, and structured waist. The lighter, fitted torso removes the bulky outer-shell read. Its `yoke_tailored` side retains a collar/yoke/closure rhythm without the jacket's visible inner stripe.

### Nightwatch Collar Knit

Nightwatch is the corrected alternate branch. It uses a dark burgundy uninterrupted sweater mass, broad charcoal collar rhythm, and firm structured waist. It has no center opening, split shell, or yoke. The `heavy_mass` side is fuller and simpler than either the lapel-led jacket or tailored shirt side. Two substantial features and Rare construction keep it designed rather than filler.

## Critical evaluation

### 1. Did one style profile generate three visibly related garments?

Yes. All three use compact practical mass, disciplined collar/upper construction, dark anchor values, muted tan/olive/khaki relationships, and firm lower termination. They read as one fieldwear family in the three-way sheet.

### 2. Are they related through construction as well as palette?

Yes. Rampart carries the open split-panel jacket; Cadence carries a fitted yoke/closure system; Nightwatch carries a solid dark formal mass with broad collar and structured waist. Their common family comes from disciplined collar and waist construction, not one repeated center stripe.

### 3. Do they remain visually distinct?

Yes at static gameplay footprint. Rampart has the only framed outer shell and visible inner layer. Cadence is visibly lighter, fitted, and upper-yoke-led. Nightwatch is dark, uninterrupted, collar-led, and fuller. Front, back, and side roles remain distinguishable without reading item names.

### 4. Do they blend into Stardew?

Yes in static review. They retain chunky connected clusters, restrained shade roles, selective dark anchors, no texture noise, and the same 32×32 displayed footprint as the accepted permanent backend.

### 5. Does the FS high-detail renderer provide enough vocabulary?

Enough for a coherent broad style family: collars, lapels, open layers, yokes, waist bands, value hierarchy, and reconstructed sides all survive.

Not enough to guarantee immediate iconic recognition under the corrected bar. The frozen vocabulary lacks semantic regions for cropped length, chest pocket flaps, epaulets, restrained harness lines, and leather trim. Those are precisely the features that would distinguish the iconic jacket from generic fieldwear after logos are removed.

### 6. Which thematic traits survived best?

- tan/olive outer-inner relationship;
- wide or folded collar identity;
- compact split-panel outerwear;
- upper yoke construction;
- fitted utility-shirt mass;
- dark waist/hem termination;
- rugged muted palette family;
- front/side layering continuity.

### 7. Which traits were simplified?

- a cropped jacket is conveyed by compact torso proportions and a strong structured waist, not a separate length mask;
- pocket flaps are absorbed into general panel hierarchy;
- harness/belt systems reduce to one waist or placket gesture;
- vest construction remains a fitted overlay shirt with native sleeves;
- long coats become standard-length dark formal torso clothing;
- multiple buckles, straps, and epaulets are omitted.

### 8. Did any design require a renderer-specific hack?

No. All three use the unchanged permanent renderer, existing archetype masks, existing side-template library, existing body coverage, and existing shade grammar. Unsupported requests were simplified semantically instead of painted by exception.

### 9. Would a player recognize the military/anime-inspired language without a label?

Likely yes for the general military/anime fieldwear language. Rampart is the only candidate likely to prompt a specific AoT association because of its tan cropped-jacket impression over a dark olive inner shirt with broad lapels.

Static judgment cannot honestly guarantee the stricter “immediately AoT” result. The output is suggestive and close at the major-construction level, but the missing pocket/harness vocabulary prevents a confident unique-franchise read. Status: **provisional; requires unlabeled in-game review**.

### 10. Are the garments plausible RNG rewards?

All three are plausible rewards rather than one hero plus fillers. Rampart is the iconic Rare jacket; Cadence is a crisp fitted Rare shirt/vest interpretation with high-contrast yoke construction; Nightwatch is a strong dark-formal Rare alternative with broad collar and structured waist. Nightwatch is intentionally quieter than Rampart, but not structurally plain.

## Success-condition verdict

- coherent three-garment style family: **PASS**;
- more than recolors: **PASS**;
- construction differences visible: **PASS_AFTER_CORRECTION** across Jacket, Button Shirt, and Sweater roles;
- Stardew compatibility: **PASS_STATIC**;
- no special-case pixel hacks: **PASS**;
- reference-to-semantic influence: **PASS**;
- immediate unique AoT recognition: **PROVISIONAL / NOT PROVEN**.

The style-profile mechanism succeeds at broad controlled transfer. The corrected iconic-recognition requirement is only partially demonstrated by the frozen vocabulary. If an unlabeled in-game review does not recognize Rampart, the appropriate next change is a future bounded semantic vocabulary addition for cropped hem, pocket panel, and one utility-line gesture—not manual sprite exceptions and not a renderer rewrite during this POC.

## Outputs and installation

- revised assets: `output/fashionsense/style-profile-aot/revised/`;
- equal-footprint sheet: `output/comparisons/AOT_STYLE_PROFILE_3WAY.png`;
- previous-vs-revised sheet: `output/comparisons/AOT_STYLE_PROFILE_PREVIOUS_VS_REVISED.png`;
- isolated pack: `test-packs/fashionsense/RNG-Clothing-AoT-Style-POC/`;
- machine validation: `output/fashionsense/style-profile-aot/revised/validation.json`.

Copy the whole `RNG-Clothing-AoT-Style-POC` directory into `Stardew Valley/Mods/`, with Fashion Sense 7.5.0 installed separately, then restart SMAPI. Use `fs_add_mirror` if a Hand Mirror is needed and select the three original entries under Shirts.

Nothing was installed automatically.
