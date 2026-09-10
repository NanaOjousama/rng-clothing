# Reference Corpus Inventory

## Scope and method

`ref_codex` was treated as immutable research input. The audit recursively enumerated direct files, inspected manifests and appearance JSON, expanded archive copies only under `/tmp`, grouped recolor-only families, and reviewed nearest-neighbor contact sheets of the available raster clothing. No source asset was copied into project output or modified.

The directory contains **19 top-level reference sources**: 16 archives and 3 already-expanded Fashion Sense packs. Eighteen sources were visually inspectable. One Content Patcher replacement pack is XNB-only and was limited to metadata/file-contract inspection.

At audit time the direct tree contained 103 files (45 JSON, 42 PNG, 16 ZIP). Read-only archive extraction exposed roughly 2,900 files, including about 765 Fashion Sense shirt textures. Across the corpus there are also pants, hats, accessories, presets, and a very small custom-sleeve subset. Counts describe assets, not independent designs: large packs contain many recolors and close variants.

## Source index

| # | Source | System | Scope and applicability | Direction/layer notes | Useful study value |
|---:|---|---|---|---|---|
| 1 | `(FS) 12 winter suits (male)` | Fashion Sense | Masculine winter outerwear; 12 shirts, pants, hats | Four shirt directions; native sleeve colors; companion winter pieces | Padded/boxy mass, thick collars, quilting, winter value grouping |
| 2 | `Grian Fashion` | Fashion Sense | Masculine/unisex character-themed tops | Four directions; shirt plus hats; mostly native sleeves | Graphic placement and bright/dark blocking only; character-specific layouts are excluded |
| 3 | `Court-style men's wear` | Fashion Sense | Masculine period/court uniform | Shirt plus pants; custom animation-oriented data | High collar, formal vertical rhythm, long-looking upper proportions; narrow coverage |
| 4 | `FS Gentlemen's Collection` | Fashion Sense | Masculine casual, knit, vest, cardigan, windbreaker, formal | 15 four-direction shirts; native sleeve colors | Strong primary masculine corpus: neckline, opening, knit, vest and cardigan differences |
| 5 | `Jjoripong's closet` | Fashion Sense | Broad masculine/unisex casual, formal, sport and themed tops | 75 four-direction shirts; overwhelmingly native sleeves | Large vocabulary and color range; group recolors and graphic families |
| 6 | `Luny's Cottagecore Shirts` | Fashion Sense | Masculine/unisex cottagecore casual shirts | Three shirts; one optional custom 3/4 sleeve; some shirt frames exceed 8×8 | Open shirt/overshirt layering and a controlled larger shirt footprint |
| 7 | `tracksuit outerwear` (expanded masculine pack) | Fashion Sense | Masculine/unisex athletic shells | Eight shirt variants plus companion pieces; native sleeve colors | Track-jacket collar, zipper, shoulder/sleeve block; mostly recolors of one topology |
| 8 | `12 winter suits (female)` | Fashion Sense | Feminine winter outerwear; secondary construction reference | Four directions; hats/pants; native sleeve colors | Padded silhouettes and collar/hood mass; not used as masculine silhouette authority |
| 9 | `Coii Girls Sets Pack` | Content Patcher/XNB replacement | Feminine shirts, pants, hair | XNB-only replacement assets | Contract and licensing metadata only; pixel art not decoded in this pass |
| 10 | `female_coats` | Fashion Sense | Feminine and some unisex coats, blazers, formal/fashion tops | 48 four-direction shirts; native sleeve behavior | High-value collar, lapel, opening, asymmetry and palette-topology research |
| 11 | `feminineclothing` | Fashion Sense | Very broad feminine fashion corpus | 478 shirts plus pants/hats; four-direction sheets | Neckline, shoulder exposure, wrap, sailor, corset, knit, jacket and pattern technique; not silently mapped to masculine grammar |
| 12 | `tracksuit outerwear` / Jedone jersey | Fashion Sense 7.5-era pack | Feminine/unisex sport and jersey tops | 16 shirts; three custom sleeves with large animation maps | Coordinated sleeve stripes and the cost/fragility of custom sleeves |
| 13 | `Katy's Closet No.2` | Fashion Sense | Feminine/unisex one-piece and themed clothing | 16 shirts, pants and hats; accessories | Multi-article coordination, large thematic blocks, costume/one-piece assembly; exact themes excluded |
| 14 | `Harry Potter 20 Uniforms` | Fashion Sense | Mixed school-uniform reference, copyrighted character source | 20 shirts; repeated open/closed/summer/sweater/winter structures | Abstract uniform layering and open/closed variants only; no logos, house marks, or costume layouts |
| 15 | `Butlers & Maids` | Fashion Sense presets | Mixed formal service clothing | Shirt, custom sleeves, pants, shoes, hat and accessories assembled into two presets | Best architecture example for coordinated formal layers; demonstrates complexity and fragility of custom animated sleeves |
| 16 | `FS Shire Collection` | Fashion Sense | Mixed period/fantasy layers, many masculine-suitable vests | Six shirts, pants and accessories | Waistcoats, suspenders, open vest layering and period color discipline; character-derived specifics excluded |
| 17 | `Daily Clothes Pack` | Fashion Sense | Mixed everyday casual/workwear | 47 shirts and hats | Broad practical collar, sweater, vest and workwear examples; good charm/clarity baseline |
| 18 | `Goldenfields Closet` | Fashion Sense | Unisex/feminine casual and themed garments | Seven shirts, hats and accessories | Crop, flannel, cardigan and companion-layer ideas; selective unisex use |
| 19 | `Rino's Clothes #1` | Fashion Sense | Unisex casual/themed pack | Ten 8×8×4 shirt sheets; native sleeve colors | Strong high-contrast pixel economy, graphic/topology examples and directional simplification |

## Framework and asset observations

- Fashion Sense is the dominant framework. Its common shirt contract is four explicit directional frames in `Front`, `Right`, `Left`, and `Back` order in data, usually stored as a vertical 8×32 sheet.
- Raster sizes vary. The dominant shirt sheet is 8×32; some packs use 10–20 pixel-wide/larger logical shirt frames, and custom animated article atlases can be much larger.
- Of 767 parseable shirt models, most use native sleeve recoloring. Sleeve-color arrays were present in the great majority: 641 had three colors, 45 had two, 64 had one, and 17 had none.
- Only **six** custom Sleeves appearances were found across the full direct-plus-archive corpus: two in Butlers & Maids, three in the jersey pack, and one in Luny's pack. The fully animated examples require explicit Farmer-state maps.
- Butlers & Maids demonstrates coordinated presets across Shirt, Sleeves, Pants, Shoes, Hat, and Accessory. Its coat tails are back accessories with explicit draw ordering, not proof that long geometry is safe as shirt art.
- Some manifests/configs use comments, trailing commas, BOMs, or older model field names. Their assets remain useful visually, but they are not safe templates to copy mechanically into a current pack.

## Duplication and reference safety

Recolors were grouped rather than counted as new grammar. The winter, tracksuit, school-uniform, graphic, and very large feminine packs contain substantial variant families. Copyrighted or character-specific sources were used only for broad construction lessons. Their insignia, characters, recognizable costume arrangements, and exact pixel placement are excluded from the semantic library.

## Inspection limitation

The Coii pack contains only compiled XNB clothing/hairstyle replacements plus documentation. The readme was inspected, including its redistribution restrictions, but the raster clothing was not decoded. It is therefore not counted among visually assessed sources and contributes no pixel-art claims to the findings.
