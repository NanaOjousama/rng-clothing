# Cap Source Corpus Audit — 2026-09-25

## Scope

Searched the active RNG Clothing repo/reference corpus plus external cap material under:

- `/run/media/deck/USD00/RNG_clothing`
- `/home/deck/Downloads`
- `/run/media/deck/USD00`

The external sweep checked both paths and tolerant Fashion Sense `hat.json` metadata, then deduplicated repeated copies by sprite MD5/alpha shape so backups, installed mods, old projects, and repo copies do not count as separate constructions.

## External author/source findings

After filtering project-generated RNG outputs, the named-cap source pool contains these useful groups:

| Source | Author | Construction finding | Audit use |
|---|---|---|---|
| Cap 1 / Cap 2 | plurffle, More Accessories and Stuff | Cap 1 and Cap 2 have the same alpha silhouette; Cap 2 is already live-QC approved in the project | direct Baseball fallback/reference |
| Cap (Snapback) | plurffle | complete 4-direction structured-cap construction; already live-QC approved | direct/partial structured-cap donor |
| Paperboy Hat | plurffle | full construction but previously failed live identity/readability | reference only |
| Backwards Cap 01–05 | Jedone | five style variants share one identical alpha construction | partial donor / backwards-cap reference |
| Vintage Cap 01–03 | Jedone | three style variants share one identical alpha construction | strong low/soft-cap donor |
| Cap & Headphones 01–08 | Jedone | all eight share one alpha construction; this construction contains the Vintage Cap geometry plus 16–18 attachment pixels per view for the headphones | cap core reference; headphones excluded |
| Officer Cap | Jedone | complete peaked-cap construction | brim/crown reference only |
| Boys Cap | Seyph, Ragnarok Online Hats | complete 20×80 four-view cap source | strong Baseball/soft-cap donor |
| Maid Cap | PeacefulEnd, Butlers & Maids | complete off-type service cap | corpus completeness/reference only |

A standalone 16×16 Trucker front reference also exists in Downloads / the old `experiments/trucker_cap` work. It is useful for Trucker panel/material identity but is too frame-filling to splice directly with the 20×20 author sources without reintroducing front/side scale drift.

## Audit quality convention

The generated contact sheet scores construction-only readability:

- **3** = strong/readable construction
- **2** = usable/partial
- **1** = weak for the requested identity
- **0** = missing direction

Output:

- `experiments/cap_source_corpus_audit_01/CAP_SOURCE_AUDIT_CONTACT_X10.png`
- `experiments/cap_source_corpus_audit_01/cap_source_audit.json`

## Selected construction candidates

### Baseball

**Primary source geometry:** Seyph / Ragnarok Online Hats — `0_BoysCap.png`.

Why: among the source pool it gives the cleanest coherent front/right/left/back casual-cap silhouette. The selected template copies **alpha geometry only**; project-owned neutral shading and later generator style replace the source RGB/design.

Status: experimental candidate pending human approval. The existing plurffle Cap 2 source-backed Baseball remains the active live-approved fallback until this candidate passes worn QC.

### Dad Cap

**Primary source geometry:** Jedone — Vintage Cap construction.

Why: low/soft crown, short bill, rounded back, and a closure-like lower detail. The Cap & Headphones family confirms the Vintage Cap geometry is the reusable cap core: its alpha is exactly the Vintage construction plus headphone attachment pixels.

Status: experimental candidate pending human approval.

### Trucker Cap

**Primary construction geometry:** plurffle — Cap (Snapback).

**Identity references:** standalone 16px Trucker front reference + the existing vanilla #16 Trucker study in `docs/headwear/KNOWLEDGE_BASE.md`.

Why: the source pool does not contain a complete mod-author Trucker construction. Snapback is the strongest coherent structured-cap four-view donor. Trucker identity should therefore come from a **material/panel contract** (solid/foam front panel + mesh rear, side visor read) rather than forcing the incomplete 16px front reference into the geometry and breaking cross-view scale.

Status: experimental candidate pending human approval.

## Source-derived template rule

For all three selected templates:

- borrowed: exact alpha/silhouette geometry from the declared source construction;
- not borrowed: source RGB palette, artwork, motif, branding, or source shading;
- project owns the new neutral shading / semantic treatment / future generator styling;
- every candidate records source and template alpha hashes and asserts `alphaExact: true`.

Outputs:

- `experiments/cap_source_corpus_audit_01/selected_templates/baseball/`
- `experiments/cap_source_corpus_audit_01/selected_templates/dad/`
- `experiments/cap_source_corpus_audit_01/selected_templates/trucker/`
- `experiments/cap_source_corpus_audit_01/selected_templates/SELECTED_CAP_TEMPLATES_CONTACT_X10.png`
- QC pack: `test-packs/fashionsense/RNG-Cap-Source-Template-QC/`

No candidate is promoted into the production hat catalog until human visual approval + worn QC.
