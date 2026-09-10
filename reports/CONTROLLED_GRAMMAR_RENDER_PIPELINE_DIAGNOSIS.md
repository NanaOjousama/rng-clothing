# Controlled Grammar Render-Pipeline Diagnosis

## Conclusion

The quality regression is real, but it is isolated to the new controlled-test branch. Orchard Bound Tee did **not** use an older 8×8 renderer or a Fashion Sense fallback. It used the correct 16×16 logical Shirt atlas, Scale 2, BodyPosition `(0,32)`, and native Farmer sleeve contract. The failure is that the exporter routed the semantic recipe directly into a new **structure-only rasterizer** and exported its role grid as finished art.

The proven V5E/V6 construction, HD lighting, edge-exposure, material shading, and post-V5E polish stages were bypassed entirely. This is a render-stage selection error, not a failure of the new grammar or palette research.

**Recommendation: restore the proven V5B/V5D/V5E/HD renderer as the final art backend and plug the new semantic grammars and palette stories into it through an adapter. A narrow extra-shading patch on the controlled rasterizer is not sufficient.**

## Orchard Bound Tee call trace

1. `generator/data/reference_engine/controlled_grammar_palette_test.json` selects `FITTED_TEE`, `COTTON_TEE`, and `SPRING_ORCHARD`.
2. `generator/controlled_test/engine.py::generate_controlled_test_recipes` attaches the grammar, material, and palette records to the recipe.
3. `tools/generate_controlled_grammar_palette_test.py::main` calls `render_controlled_garment` directly.
4. `generator/renderers/fashionsense/reference_grammar.py::render_controlled_garment` creates a flat role grid, invokes the hard-coded `_fitted_tee`, runs `_selective_finish`, resolves each role directly to one palette color, and stacks the frames.
5. The exporter writes that result directly to the Fashion Sense pack. It never calls `render_fs_v5b`, `render_fs_v5d`, `render_fs_v5e`, `render_fs_hd_v2`, or `polish_upper_frames`.

## What actually regressed

### Correct runtime contract

- Logical frame: 16×16.
- Atlas: 16×64 for front/right/left/back.
- Fashion Sense Scale: 2.
- BodyPosition: `(0,32)`.
- Native Farmer sleeves: enabled through three `SleeveColors`.
- Custom Sleeves atlas: absent.

The problem is therefore not 8×8 generation, Scale, anchoring, or Fashion Sense category fallback.

### Structure-only renderer exported as final art

`reference_grammar.py::_base_shape` fills nearly the entire opaque torso with `PrimaryFabric`. For FITTED_TEE, `_fitted_tee` adds only a four-cell neckline, a 2×2 accent, and two hem-corner cells per direction. `_selective_finish` adds only sparse contour anchors and a two- or three-cell highlight on row zero. There is no broad light plane, shadow mass, form-aware side shading, material-specific fold treatment, cuff rhythm, or full edge-exposure pass.

Orchard Bound Tee's front contains 200 opaque pixels, of which **183 (91.5%) are the identical PrimaryFabric color**. It uses five colors in front and four in every other direction. By comparison, the prior polished Sunfield Pathfinder front uses eleven active colors and changes 38 shade-role cells during post-V5E polish; its side views also use ten or eleven active colors.

The difference is not merely color count. The older HD pipeline explicitly creates a large upper-left light plane, a lower-right shadow mass, exposed-edge roles, gesture hierarchy, termination treatment, cuffs, highlight clusters, and micro details before post-polish. The controlled renderer implements none of those stages.

### Art-polish stage skipped

The proven V6 route is:

`render_fs_v5b/v5c2/v5d/v5e -> polish_upper_frames -> stack/export`

The controlled route is:

`render_controlled_garment -> direct role-to-RGB conversion -> stack/export`

`polish_upper_frames` is never imported or called by the controlled generator. Also, post-V5E polish alone cannot repair the current output because that pass preserves alpha geometry and assumes a richer upstream role/mask model. The missing upstream HD construction and shade-role stages must be restored first.

### Material behavior was not implemented

The full `materialBehavior` record is loaded into each semantic recipe, but the controlled renderer does not interpret it. `_selective_finish` only sorts material IDs into two booleans (`soft` or `crisp`) and changes a few anchor/highlight cells. The returned `material_behavior_id` simply echoes `recipe["materialId"]`.

The validator then declares “material behavior applied” when that echoed string equals the input material ID. This is a false-positive validation contract: it proves selection, not pixel-level material behavior.

### Palette mapping exposed rather than caused the flatness

The new palette story was applied correctly as a role-to-color lookup. It did not erase an existing shaded image; no shaded image existed upstream. Because 91.5% of Orchard's front cells were assigned `PrimaryFabric`, direct semantic color resolution produced the visible flat fill. The palette specifications are not the root cause and should be preserved.

### Grammar data was attached but not translated through the real engine

The complete `recipe["grammar"]` semantic object is attached by the controlled recipe assembler, but `reference_grammar.py` does not consume its fields. It dispatches only on `grammarId` to twelve hand-authored minimal coordinate functions. Likewise, the ten `axes` values are used only by diversity validation, not art generation.

The result is a topology proof, not a finished grammar implementation.

### Validation allowed prototype art to pass

The controlled validator checks dimensions, alpha, coverage, role membership, a four-to-eight role count, existence of named directional signals, and opaque-pixel count. It has no floor for:

- dominant-fill percentage;
- broad light/shadow plane coverage;
- exterior contour continuity and edge weight;
- material-specific pixel evidence;
- neckline/cuff/hem readability at Farmer scale;
- front/back visual differentiation;
- comparison against V5E/V6 quality anchors.

Consequently, a nearly flat body with a handful of semantic signal cells passed static validation.

## Exact responsible files/modules

### Replace as a final-art path

- `generator/renderers/fashionsense/reference_grammar.py`
  - `_base_shape`
  - `_selective_finish`
  - the twelve hard-coded author functions, including `_fitted_tee`
  - `render_controlled_garment`
- `tools/generate_controlled_grammar_palette_test.py`
  - direct call to `render_controlled_garment`
  - direct export of `render.texture`
- `generator/controlled_test/validation.py`
  - false-positive material check
  - insufficient visual-quality thresholds
- `tools/validate_controlled_grammar_palette_test.py`
  - faithfully revalidates the same insufficient render contract

### Preserve as research/semantic input

- `generator/data/reference_engine/controlled_grammar_palette_test.json`
- `generator/controlled_test/engine.py`
- `specs/reference_corpus/garment_grammars.json`
- `specs/palettes/color_roles.json`
- `specs/palettes/material_color_behavior.json`
- `specs/palettes/palette_stories.json`
- all reference-corpus and palette-research documentation

No proven production renderer module was overwritten by this experiment. The regression was introduced by selecting a parallel minimal renderer in the controlled-test exporter.

## Preserve / revert / replace plan

### Preserve

1. The semantic garment grammar records and the selected twelve-grammar allowlist.
2. Project-owned palette stories and semantic color roles.
3. Material behavior specifications.
4. Structural-versus-decorative rules and directional reconstruction data.
5. The proven Fashion Sense runtime contract: 16×16 logical frames, Scale 2, `(0,32)`, native Farmer sleeves.
6. The isolated experimental test-pack/output paths.
7. The controlled renderer's topology functions only as disposable structural masks or implementation sketches—not as exportable art.

### Revert/disable

1. Stop treating `reference_grammar.render_controlled_garment` output as final clothing art.
2. Stop exporting or runtime-testing the current twelve-item pack as a quality proof.
3. Remove the current `PASS_STATIC` interpretation from quality evaluation; it only proves schema/runtime-shape validity.
4. Do not attempt to rescue the flat output by adding more accent pixels, motifs, or palette contrast.

No old production renderer needs a source-code revert because it was not changed.

### Replace

1. Add a semantic adapter from each approved reference grammar into the established HD region/exposure/gesture model used by `render_fs_hd_v2` and the upper-article translators.
2. Translate the new palette roles into both mask frames and resolved default-color frames rather than assigning one direct RGB per broad region.
3. Implement actual material behavior as shade-role and cluster policy: plane size, value spacing, edge treatment, ribbing/fold rules, and highlight/shadow distribution.
4. Route the adapted result through the proven article construction backend and `polish_upper_frames` before export.
5. Upgrade validation with dominant-fill caps, required light/shadow mass, material-evidence metrics, directional visual-difference checks, and direct V5E/V6 quality-anchor comparisons.

## Decision

A narrower fix is **not** sufficient. Adding more calls inside `_selective_finish` would recreate a second, weaker art engine and continue bypassing the proven one. Restore the old high-quality renderer as the final backend, preserve the new grammar/palette work as semantic inputs, and implement only the adapter needed to translate those inputs into the proven region, shade-role, construction, and post-polish stages.

Do not generate another garment batch until that routing change and its quality validation are reviewed.
