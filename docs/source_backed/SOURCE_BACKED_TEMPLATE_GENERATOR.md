# Source-Backed Template Generator

## Architecture

The construction template owns geometry. Approved mod-author sources donate reusable art vocabulary and proven parts. The generator does not redraw or normalize the template silhouette.

Pipeline:

`approved source corpus -> exact deconstruction -> source transfer library -> template contract -> compatibility/zone planner -> palette/material/pattern/motif rolls -> export/QC`

Round Trip remains the fidelity proof: neutral source/template content must survive ingestion/export without geometry or wear drift. Source-backed template generation extends that principle with controlled variation.

## 1. Source-backed template generator

A template is a swappable construction contract, not a renderer. It supplies the final silhouette, directional construction, contact/band shape, semantic zones, anchors and geometry hashes. Shared generator logic supplies compatible variation from the deconstructed source library.

The first registered contract is `slouch_pl24`, using the approved coherent PixelLab cardinal frames Front=0, Right=2, Left=6, Back=4. Those four tracked PNGs are byte/hash pinned under `authored/templates/slouch_pl24/`.

## 2. Required inputs

Every template must declare:

- approved cardinal construction frames;
- exact file hashes and alpha-geometry hashes;
- frame size, slot, category and family;
- semantic zones and placement anchors;
- geometry-lock policy;
- allowed reusable part categories;
- incompatibility rules;
- source transfer library;
- family roll/exclusion matrix;
- wear/export contract for the target runtime.

Missing inputs are a validation failure, not permission to infer or normalize them.

## 3. Reusable part categories

The new derived catalog is `source_catalog/SOURCE_TRANSFER_LIBRARY.json`.

- `STYLE_PROFILE` — family-authored value vocabulary, role order and tone rhythm.
- `MATERIAL_PATTERN` — surface treatment requiring an explicit target surface zone.
- `MOTIF` — small in-silhouette decoration seated in a target zone.
- `ATTACHMENT` — additive geometry placed only at a declared attachment edge.
- `HARDWARE` — small rigid additive accent with the same edge requirement.
- `REUSABLE_COMPONENT` — reconstruction-proven reusable delta not yet semantically specialized.
- `BASE_SPECIFIC` — usable only on its exact authored base.
- `ALTERNATE_CONSTRUCTION` — different geometry; candidate for its own template, never an overlay.

## 4. Safe transfer rules

1. Target template alpha/silhouette is authoritative.
2. Style profiles may alter colour/value treatment, never alpha.
3. Surface patterns and motifs may affect only opaque cells in declared zones.
4. Attachments/hardware may add alpha only at declared attachment edges.
5. No reusable component may use blind source coordinates on another template; it must map through a semantic zone/anchor.
6. Base alpha may never be removed by a transfer.
7. Neutral template render must round-trip exactly before any generated variant is accepted.
8. Source provenance and attribution remain attached to every donor/part in the transfer library.

## 5. Incompatibility rules

- `BASE-SPECIFIC` cannot cross to another construction.
- `ALTERNATE_CONSTRUCTION`/reference-only deltas are never overlays; promote them to their own template after review.
- Missing required semantic zone = deny.
- Unsupported part kind = deny.
- Generic `BRIMLESS_HAT`/V5 normalization = deny for the slouch family.
- Resample-to-fit = deny for locked templates.
- Any operation that removes locked template alpha = deny.
- Attachments that fail edge/extent checks = deny.

## 6. Per-template contract

Contracts live in `generator/data/templates/` and are registered in `generator/data/templates/index.json`.

The contract owns only construction-specific facts: frames, hashes, zones, anchors, allowed categories and incompatibilities. Shared transfer logic lives in `v5/source/template_transfer.py`. Swapping a construction therefore means adding/changing a template contract, not adding another renderer or copying generator logic.

`slouch_pl24` additionally links to `generator/data/headwear/slouch_beanie_roll_matrix.json` and the existing slouch motif library. Its hand-edited curved band, rear slouch mass, contact edge and directional silhouette are locked.

## Source reclassification

`tools/build_source_transfer_library.py` derives the new transfer catalog from the existing exact source corpus and `families.json`; it does not modify third-party art.

Current corpus classification:

- 319 Fashion Sense appearances;
- 53 deconstructed source families / style donors;
- 12 reconstruction-proven `FAMILY_REUSABLE` parts;
- 43 `SAME_BASE_ONLY` parts;
- 108 alternate constructions/reference-only variants.

This is intentionally conservative. A source part becoming `REUSABLE` proves reconstruction inside its authored family; cross-template use still requires the target template contract to expose a compatible semantic zone.

## Validation

Run:

- `python3 tools/build_source_transfer_library.py`
- `python3 tools/validate_source_template_generator.py`
- `python3 tools/validate_slouch_beanie_roll_matrix.py`
- `python3 -m unittest v5.tests.test_template_transfer v5.tests.test_source_beanie_family`

A future generated batch should be built from the registered template plus an explicit transfer plan. It must not resurrect the deleted generic slouch style-translation proof.
