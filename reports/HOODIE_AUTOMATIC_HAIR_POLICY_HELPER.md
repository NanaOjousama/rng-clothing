# Rare+ hoodie automatic vanilla-hair policy helper

## Decision

The helper is cleanly feasible and implemented as an **optional, narrowly scoped SMAPI mod**. It does not clip Hair, replace a renderer, patch `FarmerRenderer`, patch Fashion Sense, or draw anything.

The clean implementation is appearance selection:

1. the player-facing Harbor Haze Hat remains the normal/manual policy appearance;
2. the Fashion Sense pack contains two locked internal Hat appearances with identical PNG pixels, anchors, animation frames, masks, and draw order;
3. Content Patcher gives those internal appearances fixed state-aware policies:
   - automatic `HideBackOnly`;
   - automatic `PreserveFrontOnly`;
4. the helper uses Fashion Sense 7.5.0's public API to select the appropriate Hat for the local Farmer.

This avoids shared/global mutation of Fashion Sense appearance data. The policy remains a property of the equipped per-Farmer Hat ID.

## Authoritative mapping

The mapping is copied from and statically validated against `output/fashionsense/hoodie-vanilla-hair-audit/audit.json`:

- supported vanilla IDs: `0–55` and `100–117` (74 total);
- default passing policy: `HideBackOnly`;
- masculine vanilla body branch `PreserveFrontOnly`: `17, 24, 26, 29, 33, 34, 101, 102, 103, 104`;
- feminine vanilla body branch `PreserveFrontOnly`: `17, 24, 26, 28, 29, 33, 34, 100, 101, 102, 103, 104, 115`.

IDs `28`, `100`, and `115` are therefore body-branch-specific. The helper uses vanilla `Farmer.IsMale` to select the audited masculine or feminine offset branch.

The auditable mapping lives in `vanilla-hair-policy-map.json`, not in renderer code. `tools/validate_hoodie_hair_policy_helper.py` rejects any divergence from the completed audit.

## Exact scope and behavior

The helper acts only when all of the following are true:

- the equipped Shirt is `RNGClothing.FashionSense.HoodieWeatherTest/Shirt/Harbor Haze Weather Hoodie`;
- the equipped Hat is the Harbor Haze base Hat or one of its two locked automatic variants;
- the Farmer is the local player for the active SMAPI screen.

Hood-up is the same native state used by the Fashion Sense appearance: current location is outdoors and `Game1.IsRainingHere` or `Game1.IsSnowingHere` is true.

- Hood down: restore the base Hat. The CP contract sets all four `HideHair` fields false, so normal Hair is preserved.
- Hood up + audited passing vanilla Hair: select the locked `Auto HideBackOnly` Hat.
- Hood up + audited severe case for the current body branch: select the locked `Auto PreserveFrontOnly` Hat.
- Unsupported state: restore/fall open to the base Hat and the user's normal CP `HoodUpHairMode` configuration.

The helper does not take control of unrelated Shirts or Hats. If the player replaces the Harbor Haze Hat with an unrelated Hat, it does nothing.

## Unsupported and fail-open cases

V1 automatic selection intentionally does not claim support for:

- Fashion Sense/custom Hair appearances;
- Hair IDs outside the 74 audited vanilla IDs;
- Fashion Sense custom bodies, whose Hair offsets were not part of the two vanilla body-branch audit;
- arbitrary modded hairstyle sheets or injected hairstyle IDs.

In each case, the helper restores the base Harbor Haze Hat if it had selected an internal policy Hat, then leaves behavior to the normal configured CP policy. It does not hide Hair wholesale as an automatic fallback.

## Multiplayer and per-Farmer isolation

- The update path evaluates only `Game1.player` and requires `Farmer.IsLocalPlayer`.
- It never iterates or mutates remote Farmers.
- Fashion Sense's supported `SetAppearance` API writes the local Farmer's networked appearance state, so other clients can observe the selected Hat normally.
- There are no custom multiplayer messages and no shared policy variable.
- Each client must have the `[FS]` and `[CP]` content packs to render the internal Hat IDs. Each player who wants automatic selection should also install the optional `[SMAPI]` helper.
- Split-screen uses the active screen's local `Game1.player`; this design is per-Farmer, but split-screen still needs live confirmation.

## Compatibility and performance

- audited game: Stardew Valley 1.6.15;
- target framework: Fashion Sense 7.5.0;
- helper target: SMAPI 4.0+;
- policy data: Content Patcher 2.9.1+.

The helper polls four times per second. A poll performs two Fashion Sense appearance-ID reads, a weather/location check, and at most one hash-set lookup. It calls `SetAppearance` only when the desired Hat ID changes—normally on hood state, hairstyle, body branch, or appearance changes. There is no draw-loop work, texture generation, reflection, Harmony, or rendering allocation. Expected Steam Deck cost is negligible relative to normal Fashion Sense drawing.

Fashion Sense logs its normal “mod changed your Hat appearance” message when an actual policy transition occurs. This should happen only at state/policy transitions, not every poll.

## Files

- source: `test-helpers/RNG-Clothing-Hoodie-HairPolicy/`
- optional installable helper: `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/[SMAPI] RNG Clothing Hoodie Hair Policy/`
- updated FS child: version `1.6.0`;
- updated CP child: version `1.4.0`;
- helper: version `1.0.0`;
- validation: `output/fashionsense/hoodie-weather-test/hair-policy-helper-validation.json`.

## Runtime status

Static generation, build, map validation, FS/CP validation, and the prior 592-composite hairstyle audit pass. The helper remains **EXPERIMENTAL_PENDING_USER_TEST**. It does not promote the hoodie template to `FROZEN_RUNTIME_PASS` without live state-transition and multiplayer evidence.
