# Fashion Sense Architecture Findings

## Dominant reliable pattern

The corpus strongly favors a **Shirt appearance plus native Farmer sleeves colored through the shirt model**. This keeps Stardew's animated arm topology while allowing body art to describe shoulders, armholes, cuffs and outer-layer transitions. In 767 inspected shirt models, native sleeve colors were overwhelmingly common; only a tiny minority omitted them.

This supports the project's existing rule: prefer native animated Farmer sleeves unless a compelling, runtime-tested silhouette requires custom Sleeves. Nothing in this study changes that rule.

## Directional shirt contract

- Successful packs provide explicit front, right, left and back shirt models.
- The common texture is a vertical four-frame sheet, often 8×32 at default Fashion Sense scale.
- Direction models can specify independent body position and source size. Some sources use slightly larger logical frames for clearer shoulders/open layers.
- Source atlas order must not be treated as preview label order. Project review remains Front | Right | Back | Left after semantic mapping.
- Many older/hand-authored packs use JSON comments, trailing commas, BOMs, and version-specific fields. They are observations, not drop-in schemas.

## Native SleeveColors

Native sleeves are sufficient for most tees, shirts, knits, cardigans, vests, jackets, hoodies and formal tops when:

- shoulder/body pixels establish the garment-to-arm transition;
- sleeve ramps coordinate with the garment material;
- cuffs are communicated through safe shirt-edge treatment or native color boundaries;
- sleeveless layers deliberately expose an inner shirt sleeve rather than blanking the arm.

This is the lowest-risk runtime architecture for generated upper garments.

## Custom Sleeves

Only six custom Sleeves appearances were found across three sources. Fully animated examples use 16×32 frames and extensive `UniformAnimation` mappings for idle, horse, sitting, tools and special Farmer states. They also carry fields such as `DisableNativeOffset`, body position, skin-tone masks and custom color masks.

General conclusion: custom Sleeves can add frills, cuffs, three-quarter cuts, or continuous sport stripes, but they increase state coverage and anchor risk substantially. They should be opt-in, inherit a proven current-runtime contract, and never be created just to make a garment appear more detailed.

## Coordinated presets and companion layers

Butlers & Maids demonstrates a true coordinated preset containing Shirt, custom Sleeves, Pants, Shoes, Hat and multiple Accessories. Separate accessories carry a bow and coat-tail shapes; the latter use explicit back-accessory draw ordering. This architecture can create identity unavailable to Shirt alone, but every layer has a category-specific anchor and animation contract.

Use a companion layer only when the feature is materially separate:

- a true head/hood silhouette;
- a bow, scarf, or back feature that cannot live safely in shirt art;
- a tested animated sleeve silhouette;
- an intentionally coordinated preset whose parts have independent runtime meaning.

Do not split buttons, drawstrings, trim or tiny torso details into accessories when they can safely live on Shirt. More layers are not higher quality.

## Pants, hats, accessories and one-piece illusion

Several packs coordinate Shirt with Pants/Hat/Accessory to create one-piece or costume reads. They demonstrate semantic coordination, not proof that arbitrary long Shirt geometry is safe. Back accessories can imply coat tails, but runtime draw order and animation behavior remain an explicit experimental contract. Lower-body and long-layer findings from prior project runtime tests remain authoritative.

## Architecture risk table

| Architecture | Research assessment | Generator policy |
|---|---|---|
| Shirt + native SleeveColors | Broadly represented, simplest animated contract | Default |
| Shirt + native sleeves + Hat/Hood | Useful for true head silhouette | Use only proven hood contract |
| Shirt + small Accessory | Effective for genuinely separate bow/back feature | Conservative, category-specific anchors |
| Shirt + custom Sleeves | Rare and animation-heavy | Experimental/proven-template only |
| Full multi-piece preset | Strong identity, highest coordination burden | Reserved for complex garments with material payoff |
| Long Shirt art over legs | Not validated by this corpus and contradicted by project runtime findings | Do not infer safety |

## Machine-readable data caution

The corpus spans multiple Fashion Sense versions. Exact fields, positions and animation mappings should be verified against installed Fashion Sense 7.5.0 before any future implementation. This research extracts semantic architecture only and does not promote any source model to a production template.
