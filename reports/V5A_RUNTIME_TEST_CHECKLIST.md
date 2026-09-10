# V5A Unified Garment Runtime Test Checklist

All nine prototypes begin at **EXPERIMENTAL / NOT TESTED**. Static validation does not promote them.

## Install

Copy this entire folder into your Stardew `Mods` folder:

```text
/run/media/deck/USD00/RNG_clothing/test-packs/fashionsense/RNG-Clothing-V5A-Unified-Garments
```

Requirements: Stardew Valley 1.6.15, SMAPI, and Fashion Sense 7.5.0. Restart SMAPI, use `fs_add_mirror` if you need a Hand Mirror, then select the appearances in Fashion Sense's **Shirts** category.

## Garments

- [ ] Meadowline Day Dress — Common Dress
- [ ] Berryglass Pinafore Dress — Uncommon Dress; sleeveless coverage check
- [ ] Gilded Starfall Dress — Rare Dress
- [ ] Mapleforge Work One-Piece — Common One-Piece
- [ ] Circuit Cadet Uniform — Uncommon One-Piece
- [ ] Ribbonward Story Costume — Rare One-Piece
- [ ] Slateway Long Cardigan — Common Long Outerwear
- [ ] Brasswatch Field Coat — Uncommon Long Outerwear
- [ ] Rookwatch Field Long Jacket — Rare Long Outerwear

Repeat the following matrix for each garment. Record `PASS`, `FAIL`, or `NOT TESTED`; never infer untested states.

## Standing and direction

- [ ] front/down — top anchor, waist, hem, legs
- [ ] right — sleeve/body join and lower side mass
- [ ] back/up — back construction and lower termination
- [ ] left — mirror correctness and lower side mass
- [ ] rapid direction changes — no detached or stale frame

## Movement

- [ ] walk front
- [ ] walk back
- [ ] walk right
- [ ] walk left
- [ ] run front/back
- [ ] run side-to-side
- [ ] garment does not detach from torso
- [ ] extended hem does not reveal accidental body holes
- [ ] legs do not clip through in a way that destroys article identity

## Tools and held items

- [ ] axe
- [ ] pickaxe
- [ ] hoe
- [ ] watering can
- [ ] scythe
- [ ] fishing rod
- [ ] slingshot if available
- [ ] hold an item overhead
- [ ] eat/drink
- [ ] sleeves remain coordinated with the torso palette

## Sitting and transport — highest risk

- [ ] sit facing front
- [ ] sit facing side
- [ ] stand up from sitting
- [ ] mount horse
- [ ] ride front/back
- [ ] ride right/left
- [ ] dismount
- [ ] extended hem does not float, cut through the body, or remain rigid in an unacceptable position

## Environment and transitions

- [ ] enter swimming state; garment hides cleanly
- [ ] exit swimming state; garment returns at the correct anchor
- [ ] enter bathing-suit transition; garment hides cleanly
- [ ] exit bathing state; garment restores correctly
- [ ] bed/sleep transition if visible
- [ ] festival/special pose encountered during normal test

## Fashion Sense and multiplayer

- [ ] equip in mirror
- [ ] unequip
- [ ] recolor primary fabric
- [ ] mirror preview matches world direction mapping
- [ ] sleeveless pinafore shows intentional skin arms without holes
- [ ] fitted/short sleeve colors update correctly
- [ ] local player retains selection after save/reload
- [ ] remote farmer rendering — NOT TESTED until a second player observes it
- [ ] host/client appearance sync
- [ ] host/client color sync

## Failure record

For every failure record:

```text
garment:
article:
direction:
Farmer state/frame:
problem:
screenshot filename:
repeatable: yes/no
```

## Promotion rule

```text
EXPERIMENTAL
  -> required runtime states pass
RUNTIME_PASS
  -> in-game art/rarity review passes
ART_PASS
  -> compatibility and regression review passes
PRODUCTION_READY
```

Do not promote an entire article family from one garment. Dress, One-Piece, and Bounded Long Outerwear need separate evidence.
