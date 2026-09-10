# Hoodie Weather Runtime Test Checklist

Status: **EXPERIMENTAL — NOT RUNTIME PASSED**

Test appearance: **Hoodie Weather Test - Harbor Haze**

## Install

With Stardew Valley closed, copy both folders below into the normal Stardew `Mods` directory:

- `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/[FS] RNG Clothing Hoodie Weather Test`
- `test-packs/fashionsense/RNG-Clothing-Hoodie-Weather-Test/[CP] RNG Clothing Hoodie Weather Test`

Requirements: SMAPI, Fashion Sense 7.5.0, and Content Patcher 2.9.1 or newer. Fully restart through SMAPI, then equip **Hoodie Weather Test - Harbor Haze** under Fashion Sense presets.

## Clear weather / indoors — hood down

- [ ] Front: folded hood protrudes around neck/shoulders; center is masked by Player.
- [ ] Front: no giant circular hood behind head.
- [ ] Front: normal hair remains visible and naturally occludes hood.
- [ ] Right: lowered fold stays attached to neck/shoulder.
- [ ] Back: folded hood remains visible behind hair.
- [ ] Left: lowered fold stays attached to neck/shoulder.
- [ ] Walk all directions: no hood chunk near feet and no detached fold.
- [ ] Basic tool hold/use: no detached hood or drawstrings.

## Rain, storm, or snow outdoors — hood up

- [ ] State switches to hood up after going outdoors.
- [ ] Front: face opening is centered and not an oversized halo.
- [ ] Right: opening and rear hood mass align with head.
- [ ] Back: hood fully covers/frames the back of the head.
- [ ] Left: mirrors the right alignment correctly.
- [ ] Walk all directions: raised hood tracks the head.
- [ ] Basic tool hold/use: hood stays head-attached.
- [ ] No raised or lowered hood component appears near feet.

If weather was changed with a debug command, cross an indoor/outdoor boundary before judging the Content Patcher hair mode.

## Hair modes

Default `FullHair`:

- [ ] Short hair leaves a convincing hood visible.
- [ ] Bangs/front fringe remain visible through the opening.
- [ ] Long hair occludes the hood naturally rather than forcing hood fabric over it.
- [ ] Record hairstyles that visually overwhelm or escape the hood.

Fallback `HiddenHair`:

1. Close the game.
2. Edit `[CP] RNG Clothing Hoodie Weather Test/config.json`.
3. Change `HoodUpHairMode` from `FullHair` to `HiddenHair`.
4. Restart through SMAPI.

- [ ] Hood down still preserves normal Hair.
- [ ] Hood up hides Hair cleanly.
- [ ] Face remains visible and centered.
- [ ] No stale hair state remains after returning indoors/clear.

## State transitions

- [ ] indoors clear → outdoors rain/snow: down to up.
- [ ] outdoors wet → indoors: up to down.
- [ ] outdoors wet → outdoors clear on a later day: up to down.
- [ ] save/reload while wet outdoors: correct state restored.
- [ ] save/reload indoors: hood down restored.
- [ ] swimming/bathing suit: Hat hides as configured.

## Failure record

For each failure record:

- direction;
- hood state;
- weather/location;
- hairstyle and hair mode;
- Farmer action/frame;
- visible problem;
- screenshot filename.

Do not promote the hood beyond `EXPERIMENTAL` until all four directions and both weather states have been observed in live gameplay.
