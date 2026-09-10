# V1 to V2 recipe migration

Migration utility: Generator V2 `2.0.0`  
Purpose: deterministic regression comparison, not automatic art direction.

V1's `detail`, `secondaryDetail`, and `pattern` fields were interpreted as evidence about construction. Large, legal regions were retained first; button dots and chest marks were demoted to micro details. When a V1 combination exceeded its V2 rarity budget, the migration records the dropped or construction-absorbed cue rather than hiding the loss.

All 20 migrated recipes pass the V2 schema and compatibility rules. This only confirms faithful legal translation; it does not mean the migrated recipes are optimal V2 designs.

## 1. Harbor Band Tee (`lifestyle-v1-01`)

- V1 flat fields: `detail=lower_trim`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=regular`; `neckline=crew`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=contrast_band`; `panelLayout=solid`.
- Substantial features: `structured_lower_band`.
- Micro details: none.
- Color blocking: primary `body`, secondary `hem`, accent `none`.
- Translation: detail lower_trim -> substantialFeatures structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 2. Meadow Everyday Tee (`lifestyle-v1-02`)

- V1 flat fields: `detail=none`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=relaxed`; `neckline=round`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=plain`; `panelLayout=solid`.
- Substantial features: none.
- Micro details: none.
- Color blocking: primary `body`, secondary `none`, accent `none`.
- Translation: No V1 decoration existed; construction was inferred from archetype..
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 3. Bluebell Pin Tee (`lifestyle-v1-03`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=None`, `pattern=simple_border`.
- V2 construction: `fit=regular`; `neckline=round`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=contrast_band`; `panelLayout=solid`.
- Substantial features: `structured_lower_band`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `hem`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 4. Cedar Pin Tee (`lifestyle-v1-04`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=center_stripe`, `pattern=none`.
- V2 construction: `fit=relaxed`; `neckline=crew`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=plain`; `panelLayout=upper_lower_split`.
- Substantial features: `major_panel_contrast`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `hem`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: detail center_stripe -> substantialFeatures major_panel_contrast.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 5. Hearth Ribbed Sweater (`lifestyle-v1-05`)

- V1 flat fields: `detail=lower_trim`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=relaxed`; `neckline=crew`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=ribbed`; `panelLayout=solid`.
- Substantial features: `ribbed_hem`.
- Micro details: none.
- Color blocking: primary `body`, secondary `ribbing`, accent `none`.
- Translation: detail lower_trim -> substantialFeatures ribbed_hem.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 6. Woodland Ribbed Sweater (`lifestyle-v1-06`)

- V1 flat fields: `detail=lower_trim`, `secondaryDetail=None`, `pattern=horizontal_stripe`.
- V2 construction: `fit=regular`; `neckline=shallow_v`; `collar=wide`; `closure=none`; `layering=overlay_panel`; `hem=structured`; `panelLayout=yoke`.
- Substantial features: `yoke`.
- Micro details: none.
- Color blocking: primary `body`, secondary `yoke`, accent `none`.
- Translation: detail lower_trim -> substantialFeatures ribbed_hem.
- Translation: pattern horizontal_stripe -> substantialFeatures wrapping_stripe.
- Translation: Uncommon budget retained construction-first features and dropped/deferred: ribbed_hem, wrapping_stripe.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 7. Mistral Pin Sweater (`lifestyle-v1-07`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=None`, `pattern=simple_border`.
- V2 construction: `fit=relaxed`; `neckline=shallow_v`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=structured`; `panelLayout=solid`.
- Substantial features: `structured_lower_band`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `hem`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 8. Garnet Ribbed Sweater (`lifestyle-v1-08`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=lower_trim`, `pattern=none`.
- V2 construction: `fit=relaxed`; `neckline=round`; `collar=none`; `closure=none`; `layering=single_layer`; `hem=ribbed`; `panelLayout=solid`.
- Substantial features: `ribbed_hem`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `ribbing`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: detail lower_trim -> substantialFeatures ribbed_hem.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 9. Cedar Button Shirt (`lifestyle-v1-09`)

- V1 flat fields: `detail=button_line`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=small_folded`; `closure=buttons`; `layering=single_layer`; `hem=plain`; `panelLayout=center_placket`.
- Substantial features: `center_placket`.
- Micro details: none.
- Color blocking: primary `body`, secondary `placket`, accent `none`.
- Translation: detail button_line -> substantialFeatures center_placket.
- Translation: button pixels were demoted to microDetails tiny_button; the placket remains structural.
- Translation: Common micro budget dropped/deferred: tiny_button.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 10. Meadow Pocket Shirt (`lifestyle-v1-10`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=None`, `pattern=vertical_trim`.
- V2 construction: `fit=fitted`; `neckline=open`; `collar=small_folded`; `closure=buttons`; `layering=single_layer`; `hem=plain`; `panelLayout=center_placket`.
- Substantial features: `center_placket`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `placket`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern vertical_trim -> placket/panel construction rather than a decorative pixel line.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 11. Harbor Button Shirt (`lifestyle-v1-11`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=button_line`, `pattern=simple_border`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=small_folded`; `closure=buttons`; `layering=single_layer`; `hem=contrast_band`; `panelLayout=center_placket`.
- Substantial features: `structured_lower_band`, `center_placket`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `placket`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: detail button_line -> substantialFeatures center_placket.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Translation: button pixels were demoted to microDetails tiny_button; the placket remains structural.
- Translation: Rare micro budget dropped/deferred: tiny_button.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 12. Bluebell Button Shirt (`lifestyle-v1-12`)

- V1 flat fields: `detail=button_line`, `secondaryDetail=None`, `pattern=vertical_trim`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=small_folded`; `closure=buttons`; `layering=single_layer`; `hem=plain`; `panelLayout=center_placket`.
- Substantial features: `center_placket`.
- Micro details: `tiny_button`.
- Color blocking: primary `body`, secondary `placket`, accent `placket`.
- Translation: detail button_line -> substantialFeatures center_placket.
- Translation: pattern vertical_trim -> placket/panel construction rather than a decorative pixel line.
- Translation: button pixels were demoted to microDetails tiny_button; the placket remains structural.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 13. Woodland Layer Jacket (`lifestyle-v1-13`)

- V1 flat fields: `detail=inner_layer`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=relaxed`; `neckline=open`; `collar=small_folded`; `closure=center_open`; `layering=visible_inner_layer`; `hem=structured`; `panelLayout=split_outer_panels`.
- Substantial features: `contrast_inner_layer`.
- Micro details: none.
- Color blocking: primary `outer_panels`, secondary `inner_layer`, accent `none`.
- Translation: detail inner_layer -> substantialFeatures contrast_inner_layer.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 14. Garnet Button Jacket (`lifestyle-v1-14`)

- V1 flat fields: `detail=button_line`, `secondaryDetail=None`, `pattern=vertical_trim`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=small_folded`; `closure=buttons`; `layering=overlay_panel`; `hem=structured`; `panelLayout=center_placket`.
- Substantial features: `center_placket`.
- Micro details: `tiny_button`.
- Color blocking: primary `outer_panels`, secondary `placket`, accent `placket`.
- Translation: detail button_line -> substantialFeatures center_placket.
- Translation: pattern vertical_trim -> placket/panel construction rather than a decorative pixel line.
- Translation: button pixels were demoted to microDetails tiny_button; the placket remains structural.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 15. Hearth Layer Jacket (`lifestyle-v1-15`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=inner_layer`, `pattern=simple_border`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=small_folded`; `closure=center_open`; `layering=visible_inner_layer`; `hem=contrast_band`; `panelLayout=split_outer_panels`.
- Substantial features: `structured_lower_band`, `contrast_inner_layer`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `outer_panels`, secondary `inner_layer`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: detail inner_layer -> substantialFeatures contrast_inner_layer.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 16. Mistral Layer Jacket (`lifestyle-v1-16`)

- V1 flat fields: `detail=lower_trim`, `secondaryDetail=inner_layer`, `pattern=none`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=wide`; `closure=center_open`; `layering=visible_inner_layer`; `hem=contrast_band`; `panelLayout=split_outer_panels`.
- Substantial features: `structured_lower_band`, `contrast_inner_layer`.
- Micro details: none.
- Color blocking: primary `outer_panels`, secondary `inner_layer`, accent `none`.
- Translation: detail lower_trim -> substantialFeatures structured_lower_band.
- Translation: detail inner_layer -> substantialFeatures contrast_inner_layer.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 17. Harbor Center-Trim Top (`lifestyle-v1-17`)

- V1 flat fields: `detail=center_stripe`, `secondaryDetail=None`, `pattern=none`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=sailor`; `closure=none`; `layering=overlay_panel`; `hem=plain`; `panelLayout=yoke`.
- Substantial features: `yoke`.
- Micro details: none.
- Color blocking: primary `body`, secondary `yoke`, accent `none`.
- Translation: detail center_stripe -> substantialFeatures major_panel_contrast.
- Translation: Common budget retained construction-first features and dropped/deferred: major_panel_contrast.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 18. Meadow Pin-Collar Top (`lifestyle-v1-18`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=None`, `pattern=simple_border`.
- V2 construction: `fit=fitted`; `neckline=open`; `collar=sailor`; `closure=none`; `layering=overlay_panel`; `hem=plain`; `panelLayout=yoke`.
- Substantial features: `yoke`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `yoke`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Translation: Uncommon budget retained construction-first features and dropped/deferred: structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 19. Garnet Pin-Collar Top (`lifestyle-v1-19`)

- V1 flat fields: `detail=center_stripe`, `secondaryDetail=chest_accent`, `pattern=simple_border`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=sailor`; `closure=none`; `layering=overlay_panel`; `hem=contrast_band`; `panelLayout=yoke`.
- Substantial features: `yoke`, `structured_lower_band`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `yoke`, accent `body`.
- Translation: detail center_stripe -> substantialFeatures major_panel_contrast.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Translation: Rare budget retained construction-first features and dropped/deferred: major_panel_contrast.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.

## 20. Bluebell Pin-Collar Top (`lifestyle-v1-20`)

- V1 flat fields: `detail=chest_accent`, `secondaryDetail=None`, `pattern=simple_border`.
- V2 construction: `fit=regular`; `neckline=open`; `collar=sailor`; `closure=none`; `layering=overlay_panel`; `hem=plain`; `panelLayout=yoke`.
- Substantial features: `yoke`.
- Micro details: `small_chest_accent`.
- Color blocking: primary `body`, secondary `yoke`, accent `body`.
- Translation: detail chest_accent -> microDetails small_chest_accent.
- Translation: pattern simple_border -> hem construction plus structured_lower_band.
- Translation: Uncommon budget retained construction-first features and dropped/deferred: structured_lower_band.
- Caveat: Faithful deterministic migration for regression comparison; not an optimal V2 redesign.
