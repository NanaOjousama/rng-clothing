# Generator V5B — Sleeve and Upper-Garment Expansion

## Outcome

V5B is statically complete as a bounded upper-garment experiment. V5C2 subsequently corrected its sleeveless arm contract: Duskline now uses a generated skin-tone-masked animated arm companion instead of `HideSleeves`.

The output status is **EXPERIMENTAL**, not runtime pass. Fashion Sense can load the generated contracts in principle, but walking, tools, sitting, horse poses, and recolor behavior still require the supplied in-game checklist.

## Fashion Sense 7.5.0 sleeve capability audit

The installed/current 7.5.0 source is authoritative for this audit:

- `SleevesContentPack.GetSleevesFromFacingDirection` maps Farmer facing `0 → Back`, `1 → Right`, `2 → Front`, and `3 → Left`.
- Custom sleeves are drawn through `DrawSleevesCustom`, which applies `who.armOffset`, direction/state animation selection, subframes, and special slingshot handling.
- `SleevesModel` supports `SleevesSize`, `Scale`, `BodyPosition`, `DrawBeforeShirt`, `DrawBehindHead`, `UseShirtColors`, color masks, skin-tone masks, and the shared animation properties.
- `DrawBeforeShirt` is the correct native layer rule for arms under the garment torso.
- `HideSleeves` is global across collected appearance metadata; using it on a shirt also hides a selected custom Sleeves layer. V5C2 therefore no longer uses it for sleeveless garments.
- The official Default Short and Default Tall atlases are `192×672`, arranged as 12×21 `16×32` frames (252 addressable frames). Their contracts provide 62 Front, 28 Back, and 42 each Right/Left uniform animation records. Left uses the same side topology with `Flipped: true`.
- `UseShirtColors: true` allows custom sleeve mask pixels to use the equipped Shirt model's three `SleeveColors`. Skin-tone masks remain framework-owned.

The available community benchmark Sleeves packs confirm the same practical full-atlas pattern: the inspected Bonestealer sleeve textures are generally `192×672` with `16×32` pose cells and animation-conditioned JSON. Their art, pixels, motifs, and layouts were not copied.

An exhaustive project filename and archive-entry scan did **not** find a Peach Body or seasonal-sleeve reference pack. The only `peach` material found is a footwear color folder under the pants benchmark. V5B therefore used the installed FS 7.5.0 Default Short/Default Tall contracts, the official example contract, and the available benchmark Sleeves folders for technical research. Peach Body is not a dependency.

## Sleeve support classification

| Sleeve intent | Classification | V5B implementation |
|---|---|---|
| Sleeveless | NEEDS_FS_SLEEVES_LAYER | Conservative Shirt sleeve-region removal plus a generated skin-tone-masked full arm atlas; `HideSleeves` remains false |
| Short sleeve | SUPPORTED_NOW | Existing native animated sleeve path plus Shirt `SleeveColors`; paired preset selects FS `Default (Short)` |
| Fitted long sleeve | NEEDS_FS_SLEEVES_LAYER | Generated full 252-frame custom Sleeves atlas |
| Loose long sleeve | EXPERIMENTAL | FS can draw it, but pose-safe outward volume is not proven; not generated |
| Oversized long sleeve | EXPERIMENTAL | Tool/hand occlusion and extreme-pose mass are unresolved; not generated |
| Puff/volume sleeve | EXPERIMENTAL | Standing shape is plausible, full motion silhouette is not proven; not generated |
| Off-shoulder | EXPERIMENTAL | Needs an exposed-skin coverage envelope and broader body compatibility tests; not generated |
| One-shoulder/asymmetric | NOT_VIABLE in V5B | Direction flipping and tool subframes need a dedicated asymmetric contract |
| Rolled/cuffed sleeve | NEEDS_FS_SLEEVES_LAYER | Generated Short-topology atlas with a target-resolution cuff termination |
| Layered inner + outer sleeve | NEEDS_FS_SLEEVES_LAYER | Generated Tall-topology atlas with coordinated multi-cell cuff/layer treatment |

`NEEDS_FS_SLEEVES_LAYER` means Fashion Sense provides the correct native mechanism; it does not mean the generated artwork has passed runtime testing.

## Architecture

The semantic path is:

`V3 DesignConcept → V3 rarity/surface plan → frozen V4 article recipe → V5B article construction → SleeveIntent → shoulder/neckline/collar/layering/opening intent → Shirt + optional Sleeves export`

V5B recipes contain no sprite coordinates or frame indices. Renderer-owned masks and the FS animation contract remain under `generator/renderers/fashionsense/`.

The optional companion is generated from the same recipe as its Shirt. A test-only `preset_outfits.json` pairs both appearance IDs so the user does not need to remember combinations. Short-sleeve presets select FS's built-in Default Short appearance. The sleeveless preset selects a generated skin-tone-masked animated arm companion.

## Custom framed sleeves

V5B uses `32×64` logical sleeve frames at `Scale 2`, with a `384×1344` atlas. `BodyPosition` is `(0,0)`, `DisableNativeOffset` is true, and the Sleeves layer draws before the Shirt. This preserves the same display footprint as the official `16×32`/Scale-4 motion topology while allowing target-resolution one-cell cuff, layer, and optical-edge work.

The official atlas is used only as the authoritative Farmer pose/skin/tool topology. V5B authors binary-alpha target cells, selective right/bottom optical shadow edges, and cuff/layer regions directly at the target logical resolution. It does not downsample, antialias, or generate conventional high-resolution art.

This remains a conservative first adapter: fitted and cuffed sleeves improve construction vocabulary, but it does not yet produce dramatically loose or puffed silhouettes. Claiming those from a template-shaped atlas would be dishonest.

## Article/sleeve compatibility

| Article | Bounded V5B sleeve options |
|---|---|
| Fitted Shirt | sleeveless, short, fitted long, rolled/cuffed |
| Sweater | fitted long, layered inner/outer |
| Vest Top | sleeveless, fitted long inner shirt, rolled inner shirt |
| Cropped Jacket | fitted long, rolled/cuffed, layered inner/outer |
| Standard Jacket | fitted long, rolled/cuffed, layered inner/outer |
| Blouse | sleeveless, short, fitted long, rolled/cuffed, layered inner/outer |

The matrix rejects unsupported combinations instead of silently coercing them. Dropped shoulders are currently a restrained shoulder-plane treatment, not an excuse to stretch Shirt pixels over moving arms.

## Coverage and animation assumptions

- Shirt frames remain `16×16`, Scale 2, BodyPosition `(0,32)`.
- Preview order is explicitly `FRONT | RIGHT | BACK | LEFT`; packed Shirt rows remain FS-correct at Front 0, Right 16, Left 32, Back 48.
- Sleeveless only removes cells classified as Shirt-owned `SLEEVE`; shoulder-cap/torso coverage remains present. Its companion converts cloth-mask cells to skin-tone masks so the animated arm remains present.
- Custom sleeves preserve FS skin-tone masks and full animation condition tables.
- The framework owns state selection and `armOffset`; V5B owns mask, cuff, and palette coordination.
- Static previews intentionally do not fake a Farmer composite because Shirt BodyPosition and full-body Sleeves source space use different draw origins. In-game review is the reliable junction test.

## Twelve prototypes

| # | Garment | Rarity | Article | Sleeve | Design role |
|---|---|---|---|---|---|
| 1 | Saltair Fitted Tee | Common | Fitted Shirt | Short/native | Simple fitted casual tee with deliberately subdued surface rhythm |
| 2 | Signalwork Rolled Shirt | Uncommon | Fitted Shirt | Rolled/cuffed custom | Narrow technical shirt, high utility neckline, strong center treatment |
| 3 | Maple Loom Knit | Common | Sweater | Fitted-long custom | Continuous warm knit mass with simple termination |
| 4 | Mosslight Familiar Knit | Rare | Sweater | Layered custom | Dropped shoulder plane, high neckline, motif/pattern/hem coordination |
| 5 | Duskline Waistcoat | Common | Vest | Sleeveless | Clear sleeveless waistcoat frame and narrow formal center opening |
| 6 | Relay Utility Vest | Uncommon | Vest over inner shirt | Fitted-long custom | Bright inner sleeves against a technical vest frame |
| 7 | Cinderstep Moto Jacket | Uncommon | Cropped Jacket | Rolled/cuffed custom | Cropped shell, opening, lapel cadence, and contrasting cuff |
| 8 | Rookwing Cropped Field Jacket | Rare | Cropped Jacket | Layered custom | AoT/fieldwear stress item with crop, shell/inner relationship, crest, and layered cuffs |
| 9 | Juniper Rain Cardigan | Common | Standard Jacket | Fitted-long custom | Full safe upper-body footprint with calmer open-front cardigan logic |
| 10 | Gilded Evening Blazer | Rare | Standard Jacket | Layered custom | Formal lapel/inner plane with controlled celestial focal treatment |
| 11 | Rose Circuit Sailor Blouse | Uncommon | Blouse | Short/native | Square/sailor collar treatment over a rose technical color block |
| 12 | Ribbonstar Bow Blouse | Rare | Blouse | Rolled/cuffed custom | Rounded/V neckline, bow focal cluster, ribbon surface network, and cuff echo |

## Static validation

PASS:

- deterministic Shirt and Sleeves output;
- 12 recipes and appearances, with two of every article family;
- balanced 4 Common / 4 Uncommon / 4 Rare;
- all five bounded V5B sleeve paths represented;
- ten custom Sleeves companions after the Duskline missing-arm correction;
- `16×64` Shirt textures containing four `16×16` direction frames;
- `384×1344` Sleeves textures containing 252 `32×64` frames;
- binary alpha;
- current FS dimensions, offsets, direction mapping, animation counts, and layer flags;
- body coverage and neck/shoulder construction guards;
- twelve unique semantic signatures and eight distinct Shirt silhouette masks;
- no Pants/Shoes output and no V3/V4 mutation;
- test-pack appearance IDs and presets resolve consistently.

One pre-existing V3 diagnostic warning remains on Ribbonstar Bow Blouse: four isolated front surface cells need human visual review. It is not a structural or alpha failure.

## Critical quality assessment

### Strongest article families

**Cropped Jacket** remains the clearest high-value family. Crop termination, outer/inner split, collar structure, and coordinated sleeves all survive gameplay footprint. Rookwing also provides the required AoT/fieldwear stress check without changing the renderer.

**Vest Top** remains structurally strong. Duskline and Relay read differently because sleeveless arm exposure and contrasting generated inner sleeves change the article relationship, not merely the palette.

### Weakest article family

**Blouse** is improved but remains the least structurally independent. Sailor/bow collar geometry and sleeve choices create a fashion-top read, yet the safe torso envelope is still derived from a fitted V4 shirt. Runtime-safe puff/off-shoulder sleeves are the missing silhouette multiplier.

### Strongest sleeve implementation

The fitted-long contract is the safest mechanical design because it follows the complete official Tall topology. Rolled/cuffed is the strongest static visual differentiator because its boundary is visible as an intentional garment termination.

### Weakest sleeve implementation

Layered inner/outer sleeves currently express layering mainly at the cuff. They are coordinated and target-resolution, but the arm shaft does not yet have a proven independent loose/outer silhouette. They must not be described as oversized sleeves.

### Art-quality caveats

- The standalone Shirt previews cannot show the final Shirt/Sleeves junction. Runtime screenshots are necessary.
- Several sleeve cuff accents are intentionally high-contrast for diagnosis and may be too bright after real dye choices.
- The native short-sleeve garments are reliable but provide less silhouette novelty than custom companions.
- Common garments remain intentionally quiet. Saltair is the most plain and should be judged as a baseline, not a chase reward.
- The 32×64 full-motion atlas costs far more texture memory than a Shirt. One RGBA atlas is about 1.97 MiB uncompressed; nine simultaneously loaded unique atlases are about 17.7 MiB before framework/runtime overhead. The PNG pack is only about 816 KiB on disk. A future production pass should investigate sharing recolorable sleeve-family atlases when fixed cuff accents are not required.

## Runtime risks

1. Tool and slingshot subframes are mapped but untested in this pack.
2. Horse and sitting poses may expose a shirt/sleeve junction not visible in isolated previews.
3. `UseShirtColors` should coordinate dye masks, but fixed cuff accents intentionally do not recolor and need aesthetic review across dye choices.
4. Preset outfits can clear unrelated Fashion Sense slots. This is acceptable for a test pack, not ideal production UX.
5. Default-body compatibility is the target. Body mods with altered shoulder/arm topology remain unverified.
6. Multiplayer equipment/color sync remains unverified.

## Files and commands

- Generator: `tools/generate_v5b_upper_garments.py`
- Validator: `tools/validate_generator_v5b.py`
- Semantic data: `generator/data/v5b/`
- Renderer grammar: `generator/data/fashionsense/v5b_upper_grammar.json`
- Renderer: `generator/renderers/fashionsense/upper_v5b.py`
- Recipes: `output/recipes/v5b_upper_garment_benchmark.json`
- Assets/previews: `output/fashionsense/v5b-upper-garments/`
- Comparison: `output/comparisons/V5B_UPPER_ARTICLE_FRONTS_8X.png`
- Test pack: `test-packs/fashionsense/RNG-Clothing-V5B-Upper-Garments/`

Regenerate and validate with:

```bash
python3 tools/generate_v5b_upper_garments.py
python3 tools/validate_generator_v5b.py
```

## Recommendation

Install and test this pack before expanding the sleeve vocabulary. If fitted-long and rolled/cuffed pass the full action matrix, promote those templates first. Keep puff, oversized, off-shoulder, and asymmetric sleeves out of production until each has a genuinely pose-safe full atlas. V5B should stop here pending runtime and visual feedback, as requested.
