# Garment Grammar Library

Status: curated foundation, generation disabled. Machine-readable authority: [`generator/data/reference_engine/garment_grammar_library.json`](generator/data/reference_engine/garment_grammar_library.json).

## Result

The library contains **22 named grammars across 20 topology groups**. The lower topology count is intentional: fitted/relaxed tees and crewneck/textured knits each share a broad topology while differing in shoulder, mass, hem, and Farmer read. Shared topology is never hidden behind a new name.

| Grammar | Topology | Primary worn cue |
|---|---|---|
| FITTED_TEE | BASIC_CLOSED | compact clean field, crew landmark, short taper |
| RELAXED_TEE | BASIC_CLOSED | dropped shoulder, broad body, loose hem |
| HENLEY | BASIC_SHORT_OPEN | short placket that does not become a full split |
| BUTTON_WORK_SHIRT | COLLARED_FULL_OPEN | work collar, full placket, pockets, back yoke |
| SAILOR_TOP | BROAD_YOKE | broad collar/tie and dominant back yoke |
| CREWNECK_KNIT | KNIT_CLOSED | continuous knit plus ribbed terminations |
| TEXTURED_SWEATER | KNIT_CLOSED | heavier dropped mass and connected knit rhythm |
| OPEN_CARDIGAN | SOFT_OPEN_FRAME | wide inner field framed by knitted edges |
| FORMAL_WAISTCOAT | SLEEVELESS_V_FRAME | deep V, inner sleeves, pointed hem, welt pockets |
| UTILITY_VEST | SLEEVELESS_BLOCK_FRAME | broad vest frame, block pockets, structured waist |
| CROPPED_BOMBER | SHORT_ROUNDED_SHELL | rounded short shell and thick gathered band |
| MOTO_JACKET | ASYMMETRIC_SHORT_SHELL | diagonal zip, broad asymmetric lapel, angular crop |
| CROPPED_STRUCTURED_JACKET | CROPPED_PANEL_SHELL | outer/inner shell, cropped waist, yoke/pockets |
| FIELD_JACKET | UTILITY_SHELL | field collar, ordered pockets, waist, strong back yoke |
| FITTED_BLAZER | FORMAL_LAPEL_FRAME | lapel hierarchy, inset shirt/tie, tailored waist |
| PERIOD_COAT_TOP | ELONGATED_PERIOD_FRAME | offset closure and bounded elongated rhythm |
| TRUE_HOODIE | HOODED_SOFT_SHELL | real hood silhouette plus pouch/zip and ribbing |
| ASYMMETRIC_WRAP_TOP | DIAGONAL_WRAP | diagonal closure and unequal shoulder emphasis |
| BELTED_TUNIC | BELTED_LAYERED_CLOTH | belt/sash, split neck, non-shirt hem |
| TABARD_ADVENTURE_TOP | CENTER_OVERPANEL | center over-panel and belt/material hierarchy |
| CEREMONIAL_TOP | CEREMONIAL_HIERARCHY | signature collar/lapel and coordinated back cue |
| STREETWEAR_STATEMENT | BLOCKED_ASYMMETRIC_STREET | shape-led block, strong cuff/hem, one signature cue |

## Construction contract

Every grammar fully defines silhouette, shoulder, neckline, collar, lapel, opening, torso mass, waist, hem, sleeve, cuff, pockets, layering, asymmetry, side reconstruction, and back reconstruction. Decorative sockets are permissions, not requirements.

Recipes choose a grammar ID and semantic variants within that grammar. Recipes do not contain coordinates. The article adapter owns geometry; the stable renderer owns pixels and runtime fields.

## Shared-topology rule

Two grammars sharing a topology must differ in at least three high-salience structural axes, including at least one of silhouette/shoulder/torso mass/hem and one of neckline/collar/opening/layering. They must then pass the Farmer-composite pairwise gate. If the worn result still converges, merge, revise, or retire a grammar—the name does not win.

## Directional reconstruction

- Front owns the full opening and focal hierarchy.
- Right/left compress depth, move closures to the physical forward edge, and terminate front-only features at seams.
- Back removes front ornament but retains the topology carrier: yoke, hood mass, collar, band, belt, panel, vent, or material hierarchy.
- Mirroring is allowed only where the construction is actually symmetric.

## Known runtime boundaries

- The proven Fashion Sense high-detail Shirt contract is 16×16 logical frames, Scale 2, BodyPosition `(0,32)`, with native Farmer sleeves as the safe default.
- True hoodie head silhouette can use the frozen coordinated hoodie contract; it is not a Shirt-only illusion.
- “Period coat-top” is bounded upper-body proportion, not true long coat geometry.
- Oversized/volume language is optical within the Farmer envelope unless a separately proven native layer exists.
- Exposed shoulder/asymmetric sleeve concepts remain conditional on correct skin/arm coverage.

No garment can be approved from this document alone. The Farmer gate decides whether a semantic difference survives.
