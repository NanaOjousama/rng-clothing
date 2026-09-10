# V5E Rare+ Structured Outerwear Proof

## Result

V5E produced one original **Sunfield Pathfinder Jacket** as a semantic Rare recipe rendered through `RARE_PLUS_COMPLEX_LAYER_GARMENT_V1`. Static validation passes. A first live test rejected its experimental custom Sleeves atlas because the arms detached below the Farmer. Version 1.1 now uses the final hoodie branch's known-good native sleeve contract and requires live retesting.

This is a meaningful generalization beyond hoodies, but not yet a runtime promotion. The corrected contract coordinates a high-detail Shirt with Stardew/Fashion Sense's native animated sleeves through `SleeveColors`, without requiring a custom Sleeves appearance, hood, weather state, hair policy, or decorative accessory.

## Controlled scope

- One garment only.
- Semantic rarity: `Rare`.
- Renderer tier: `RARE_PLUS_COMPLEX_LAYER_GARMENT_V1`.
- Article: `STRUCTURED_FIELD_JACKET` / bounded short outerwear.
- Fashion Sense Shirt: 16×16 logical frames, Scale 2, BodyPosition `(0,32)`.
- Sleeves: native animated Farmer arm path, recolored through the Shirt's three `SleeveColors`.
- Coordinated runtime: Shirt + native sleeves + preset (`SleevesId: None`).
- Deliberately absent: Hat, Hood, Accessory, Pants, Shoes, weather behavior, and hair policy.

Rare+ is a renderer/layer capability tier here; it does not introduce a new semantic rarity or consume Legendary/Mythic design space.

## Recipe and construction

The recipe is coordinate-free and asks for:

- a reinforced sloped shoulder;
- folded field lapels;
- a bounded open front;
- a visible inner shirt;
- paired pocket flaps;
- side shell seams;
- layered long cuffs;
- a short structured hem;
- an intentional back yoke;
- one small original field tab as the controlled accent.

Renderer coordinates remain inside the Fashion Sense V5E adapter. Benchmark and vanilla pixels are never generator inputs.

## Why the custom Sleeves layer was removed

The initial V5E exporter reused V5B's 32×64 Scale-2 custom Sleeves atlas with `BodyPosition (0,0)` and `DisableNativeOffset: true`. Live gameplay showed the same detached-at-feet failure already diagnosed and removed from the final hoodie branch. That contract is now explicitly rejected.

The corrected pack uses `NATIVE_ANIMATED_SLEEVES_V1`: `HideSleeves: false`, three Shirt `SleeveColors`, native Shirt feature offsets, `SleevesId: None`, and no `Sleeves/` directory. This retains the jacket's sleeve palette and dark/light cuff value intent, but does not claim a custom cuff silhouette. Native attachment is more important than unsupported custom geometry.

An Accessory still adds no safe article identity. Lapels, pockets, yoke, seams, and the field tab all fit within the Shirt topology.

## What changed from Sunfield Scout Jacket

The old V5D Sunfield had three major weaknesses:

1. its cream inner layer continued almost the full torso height and read as a centered stripe;
2. its shell ended too high, weakening the short-outerwear mass;
3. its rolled/cuffed sleeve treatment could read as short or exposed arms.

V5E replaces those with:

- a bounded inner-shirt region that ends in the upper torso;
- a narrow lower panel-overlap seam rather than another pale stripe;
- a full short-outerwear hem through logical row 13;
- connected pocket flap/body clusters;
- broken shoulder panels that preserve the collar interruption;
- one dominant back yoke with a subordinate short center seam;
- independently reconstructed right and left collar/opening rhythms;
- a full Fashion Sense animated long-sleeve companion with a three-cell layered cuff treatment.

## Vanilla and human-reference quality gate

Installed Stardew Valley 1.6.15 jacket examples were used as a research-only readability baseline, especially Brown Jacket, Canvas Jacket, and Short Jacket. Their useful aggregate lesson is severe economy: one strong opening/collar cue, compact pocket or panel rhythm, and much quieter side/back views.

The equal-footprint comparison uses 32 displayed pixels for both systems:

- vanilla 8×8 × 4;
- Fashion Sense 16×16 × 2.

Static judgment: V5E now communicates a field jacket at least as quickly as those selected vanilla baselines while using its extra cells for lapel stairs, pocket clusters, yoke termination, side seams, and a bounded inner layer. It does not merely add texture. The front is substantially clearer and more attractive than the previous Sunfield output.

Critical limitation: the front remains the strongest view. The side construction is purposeful and no longer a cropped front, but it is necessarily quieter and should be judged over walking/tool animations in game. Static sheets cannot prove the long sleeves remain convincingly attached through every Farmer pose.

## Directional reconstruction

- **Front:** lapel/opening is primary; pockets and shoulder panels are subordinate; the olive field tab is the sole accent.
- **Right:** visible collar plane, short inner-shirt wedge, pocket edge, and shadow-side shell seam.
- **Back:** folded collar cue, one dominant yoke, short center seam, and restrained lower panel marks.
- **Left:** reconstructed counterpart with the world-light bias reversed optically rather than copying the front.

The Fashion Sense texture contract remains Front Y0, Right Y16, Left Y32, Back Y48. Preview sheets deliberately present Front | Right | Back | Left.

## Outputs

- Semantic recipe: `output/fashionsense/v5e-rareplus-field-jacket/recipe.json`
- Native Shirt: `output/fashionsense/v5e-rareplus-field-jacket/shirt.png`
- Gameplay-footprint diagnostic: `output/fashionsense/v5e-rareplus-field-jacket/gameplay-footprint.png`
- Direction diagnostic: `output/fashionsense/v5e-rareplus-field-jacket/directions-8x.png`
- Sleeve component diagnostic: `output/fashionsense/v5e-rareplus-field-jacket/sleeves-idle.png`
- Previous-vs-new: `output/comparisons/V5E_SUNFIELD_BEFORE_AFTER.png`
- Four-direction comparison: `output/comparisons/V5E_RAREPLUS_FIELD_JACKET.png`
- Equal-footprint vanilla baseline: `output/comparisons/V5E_VANILLA_FIELD_JACKET_BASELINE.png`
- Test pack: `test-packs/fashionsense/RNG-Clothing-V5E-RarePlus-Field-Jacket/`

## Validation

Static checks cover:

- deterministic semantic recipe and render;
- coordinate-free semantic V5E layer;
- inherited V3/V4/V5B recipe validity;
- body-coverage envelope;
- bounded inner layer;
- authored signals in every direction;
- Shirt 16×64 texture and correct direction rows;
- Scale 2 and BodyPosition `(0,32)`;
- known-good native animated sleeve contract;
- binary alpha and direct logical pixels;
- three Shirt `SleeveColors`, `HideSleeves: false`, and native feature offsets;
- exactly one Shirt and one preset with `SleevesId: None`;
- no custom `Sleeves/` directory;
- absence of Hat/Accessory/Pants/Shoes layers;
- no benchmark dependency inside the renderer;
- clean V5B/V5D regression validation.

Static status is `PASS_STATIC_EXPERIMENTAL_RUNTIME_NOT_TESTED`. Beauty and animation remain human/runtime gates.

## Conclusion

The Rare+ coordinated architecture generalizes cleanly to a structured jacket without dragging hoodie-specific machinery into the garment. The new jacket passes the static visual gate and is materially stronger than Sunfield V5D. It is ready for a focused in-game test, not production promotion. No other garment family was started.
