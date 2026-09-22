# Sprite Fusion Workflow — Canonical Handoff

Use this file as the source of truth for GPT/Claude/Codex when working on the AI-assisted clothing pipeline.

## Core rule
- The generator plans, constrains, validates, records provenance, and promotes assets.
- Sprite Fusion may synthesize/edit/directionalize visual art.
- Do not let procedural fallback redraw a source-backed design when a good visual donor exists.
- Construction/template silhouette authority remains project-controlled unless Nana explicitly approves a silhouette change.
- Human visual approval remains mandatory before production promotion.

## Sprite Fusion operation roles
- style-reference = create a NEW asset guided by a curated reference set.
- edit = make a targeted change to a nearly-approved primary sprite; first input is the primary sprite.
- direction-set = exactly one finished/approved sprite; no prompt; returns N/NE/E/SE/S/SW/W/NW.
- Pixel Snapper is NOT a default post-process for native Sprite Fusion output.
- Pixel Snapper remains optional for imported/off-grid/non-SF art and always remains behind the silhouette guard.
## Reference preparation
- Prefer a small curated 4–8 image reference set for style work.
- Give each reference a declared role: construction, material, pattern, motif, trim, palette/value, or overall style.
- Do not dump a huge mixed corpus into one request.
- Use source-role metadata so later agents know why each reference was included.
- Style-reference prompts should mainly describe the new subject/design intent.
- Avoid redundant boilerplate such as "transparent background", "crisp pixel art", or "pixel-perfect pixel art".
- Put target size in the API size field, not in prompt prose when possible.
- Current project target: request 16; prefer 16–24; mechanically allow <=32 for candidate review.

## Candidate generation
- Generate candidate fronts first.
- Download outputs locally immediately; do not rely on hosted asset URLs.
- Record request ID, operation, prompt, source/reference IDs, output index, asset ID, native dimensions, local path, and timestamp.
- Never auto-promote API output.
- Never automatically retry an interrupted charged request; inspect saved/history state first.
## Candidate QC gate
- Reject >32 px on either dimension for the current Stardew candidate path.
- Reject obvious non-hat contamination: mannequin/person/head/face, extra object, background, UI/text, or disconnected junk.
- Mechanical checks may flag stray components/oversize/canvas issues, but semantic contamination still requires human review.
- Review/cleanup happens BEFORE any directional edit.
- Produce a zoomed front-candidate contact sheet; human marks ACCEPT / REWORK / REJECT.
- REWORK uses targeted edit or manual editor cleanup; do not regenerate blindly if the candidate is already close.

## Direction workflow
- **Headwear production uses EDIT-CARDINAL, not direction-set.**
- Front = approved candidate.
- Right = Sprite Fusion edit from the approved Front; choose the compact hat-only result.
- Back = Sprite Fusion edit from the approved Front; choose the compact hat-only result.
- Left base = deterministic horizontal mirror of the approved Right base for mirror-safe hat construction.
- Do not spend a separate AI edit on Left unless construction explicitly forbids mirroring and Nana approves that exception.
- LOCALIZED motifs/tags/patches are applied after the base cardinal views by the generator using declared placement/visibility rules.
- direction-set is retained only for legacy research/evidence because repeated hat-only tests hallucinated wearer/body contamination.
- Do not project the Front into side/back as production art.
## Direction consistency QC
- WHOLE_HAT: all-over material/pattern identity must remain consistent across Front/Right/Back/Left.
- WRAPAROUND_REGION: continuous cuff/headband/crown treatment must remain on that semantic region in every visible view.
- LOCALIZED: motif/emblem/tag/patch appears only where physically/intentionally visible; it does NOT need to appear in every view.
- Edge labels stay attached to the physical edge/side; never duplicate as a fixed screen-space sticker.
- Reject a cardinal set if a whole-hat/wraparound feature disappears, changes category, jumps regions, or contamination appears.
- Produce a 4-cardinal contact sheet before ESM.

## ESM / promotion
- ESM QC Preview is the wearability gate after art approval; no ingredient crafting should be required for QC.
- Check normalized presentation size, head contact, clipping/hair overlap, and per-direction fit.
- Promotion lifecycle:
  - GENERATED_UNREVIEWED
  - CANDIDATE_FRONT_APPROVED
  - CANDIDATE_DIRECTIONAL
  - QC_APPROVED
  - PRODUCTION_APPROVED
  - REWORK
  - REJECTED
- Only PRODUCTION_APPROVED enters the live generator production pool.
## What is retained
- Template contracts and silhouette authority.
- Source catalogs/deconstruction/provenance.
- Roll matrices, rarity guidance, exclusions, placement rules, and view-consistency semantics.
- Existing trusted source-backed rendering paths.
- ESM garment runtime/fitting/QC preview.
- QC metrics, contact sheets, and accepted/rejected history.

## What is deprecated for finished SF-backed art
- Generic procedural redraw of trim/micro-accent/source design.
- Blind tiling of tiny swatches as a substitute for donor structure.
- Front-only projection into fake side/back production views.
- Raw API output -> game packaging without a human art gate.
- Automatic Pixel Snapper pass on clean native Sprite Fusion output.
- Silent silhouette mutation.

## Testing principle
- First prove the new pipeline on a deliberately small batch.
- Do not mass-generate until candidate QC, direction QC, ESM wear QC, provenance, and promotion all pass end-to-end.
