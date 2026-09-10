# V4.6 Lower-Body Runtime Test Checklist

## Setup

Copy `test-packs/fashionsense/RNG-Clothing-V46-LowerBody-Runtime/` into Stardew Valley's `Mods` directory, with Fashion Sense 7.5.0 installed separately. Start through SMAPI, run `fs_add_mirror`, and equip each prototype through the Pants or Shoes tab.

Test all four: Wayfarer Field Trousers (Common), Crossline Scout Trousers (Rare), Trailguard Field Shoes (Common), and Rampart Scout Boots (Rare). Repeat lower-body checks with both shoe/pants pairings where practical.

Useful diagnostics: `fs_display_player_frames`, `fs_display_movement`, and `fs_record_frames`. All boxes begin unchecked; none is pre-validated.

## Idle

- [ ] front
- [ ] back
- [ ] left
- [ ] right

## Walk

- [ ] front
- [ ] back
- [ ] left
- [ ] right

## Run

- [ ] front
- [ ] back
- [ ] left
- [ ] right

## Tools

- [ ] axe
- [ ] pickaxe
- [ ] hoe
- [ ] watering can
- [ ] scythe
- [ ] fishing rod

## General

- [ ] hold item
- [ ] eat/drink
- [ ] sit
- [ ] get up from sitting

## Transport

- [ ] mount horse
- [ ] ride front/back/side
- [ ] dismount

## Water

- [ ] swimming (appearance hides cleanly)
- [ ] bathing transition (appearance hides cleanly)
- [ ] exit water (appearance restores correctly)

## Multiplayer

- [ ] local farmer
- [ ] remote farmer
- [ ] equip sync
- [ ] color sync

## Fashion Sense

- [ ] equip
- [ ] unequip
- [ ] recolor
- [ ] mirror UI preview

## Additional compatibility checks

- [ ] Wayfarer + Trailguard
- [ ] Wayfarer + Rampart
- [ ] Crossline + Trailguard
- [ ] Crossline + Rampart
- [ ] save/reload retains both appearances and colors
- [ ] direction change mid-step does not leave a stale source frame
- [ ] pass-out/bed transition has no floating lower-body pixels
- [ ] no new SMAPI warning/error during the full run
- [ ] controller can select/recolor both categories
- [ ] no material Steam Deck frame-time or menu-response regression

## Failure record

For every failure, add one row. Keep screenshots outside the pack and record the filename.

| Article | Rarity | Direction | Farmer state/frame | Visible problem | Screenshot filename | SMAPI error? |
|---|---|---|---|---|---|---|
| | | | | | | |

## Promotion rule

Static success does not check a box. An article may move from `EXPERIMENTAL` to `RUNTIME_PASS` only after both of its prototypes pass every relevant row on the default Farmer. Art review happens afterward; `RUNTIME_PASS` is not `ART_PASS` or `PRODUCTION_READY`.
