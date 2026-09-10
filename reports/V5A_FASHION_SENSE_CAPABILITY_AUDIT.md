# V5A Fashion Sense Extended-Garment Capability Audit

## Evidence and version boundary

This audit targets installed Fashion Sense **7.5.0** with Stardew Valley 1.6.15. The local 7.5.0 source and shipped examples under `FASHION SENSE/FashionSense-stable/` are the runtime authority. The previously verified source revision is `39e9e9e13c9f9a78416172e73a229cf8703ddb59`.

Fashion Sense has no native `Dress`, `OnePiece`, or `Coat` appearance model. Relevant framework types are `Shirt`, `Sleeves`, `Pants`, `Accessory`, and full `Body`. V5A therefore cannot claim a dedicated dress/coat runtime.

## Shirt contract used by V5A

`ShirtModel` supports arbitrary integer `ShirtSize`, per-direction `StartingPosition`, `BodyPosition`, `Scale`, `SleeveColors`, `HideSleeves`, grayscale/color masks, animation metadata, and draw-order overrides inherited from `AppearanceModel`.

The 7.5.0 draw path:

- obtains the source rectangle from `StartingPosition` and `ShirtSize`;
- draws at the Farmer position plus native feature offsets;
- uses `BodyPosition` as the texture origin;
- multiplies source pixels by `Scale`;
- does not derive a different anchor from a taller `ShirtSize`.

V5A keeps the proven Scale-2 torso top at `BodyPosition (0,32)` and increases only frame height. Each appearance uses a 16-pixel width and a 19, 20, 22, or 24-pixel height. Direction rows are contiguous:

```text
Front: 0
Right: frameHeight
Left:  2 * frameHeight
Back:  3 * frameHeight
```

Fashion Sense direction ownership remains `FrontShirt` = down/front, `RightShirt` = right, `LeftShirt` = left, and `BackShirt` = up/back.

## Layer consequence

The default 7.5.0 layer sequence places Pants before Shirt. A taller Shirt can therefore cover the waist/hip and a bounded upper-thigh area without a second Pants appearance. This makes a static unified silhouette possible.

It does **not** make the lower hem leg-aware. Shirt feature offsets follow the torso/Farmer frame, while individual legs and pants can articulate beneath it. The following remain runtime questions:

- stride overlap and leg exposure;
- tool poses;
- sitting compression;
- horse pose;
- unusual festival/special frames;
- multiplayer remote rendering.

The pack explicitly sets `HideWhileSwimming` and `HideWhileWearingBathingSuit` to `true`, so the expected water behavior is framework-driven hiding, not a swimming dress/coat animation.

## Sleeve contract

Fashion Sense separates two mechanisms:

1. `ShirtModel.SleeveColors` recolors the current native/custom animated sleeve layer.
2. `SleevesModel` supplies a separately equipped custom sleeve appearance with its own size, position, source frames, masks, draw order, and extensive animation mapping.

The built-in Default Short/Tall sleeve examples use 16×32 logical source frames plus a large animation contract covering idle, movement, tools, sitting, horse, and special poses. `AppearanceSyncing` synchronizes animation, not equipment selection. A preset can coordinate shirt and sleeve IDs, but that is a multi-appearance outfit workflow.

V5A consequently classifies sleeves as:

| Sleeve intent | V5A translation | Status |
|---|---|---|
| sleeveless | hide sleeve layer and remove shirt-owned sleeve cells | prototype-safe, runtime untested |
| short sleeve | existing animated sleeve layer plus semantic colors | prototype-safe, bounded |
| fitted long sleeve | existing animated sleeve layer plus semantic colors | prototype-safe, bounded; exact visible length depends on active sleeve model |
| loose/oversized | separate full animation sleeve atlas | companion required; not generated |
| off-shoulder | custom skin-masked sleeves and coverage variant | companion required; not generated |
| one-shoulder | asymmetric, direction-aware full sleeve atlas | companion required; not generated |

Peach Body/seasonal-sleeve research informs the semantic categories and the need to treat sleeve silhouette separately from torso art. Peach Body is not required or referenced as a dependency.

## Article decisions

| Article | Implementation | Capability status |
|---|---|---|
| Dress | one taller Shirt frame with reconstructed bodice→waist→unified lower mass | **EXPERIMENTAL** |
| One-piece/costume | one taller Shirt frame with coordinated upper, belt/sash, and lower panels | **EXPERIMENTAL** |
| bounded long outerwear | taller Shirt with open/split outer panels and a maximum 24-row frame | **EXPERIMENTAL** |
| floor-length dress | would need stronger pose/leg handling | **not attempted** |
| true long coat with moving tails | needs companion animation/layer work | **not ready** |
| loose or oversized custom sleeves | needs complete Sleeves atlas and coordinated equip UX | **not attempted** |

## Technical decision

V5A uses one extended Fashion Sense Shirt appearance per garment. This is the smallest non-invasive prototype that can create visible article variety and can be selected in the existing Shirt mirror category. No custom runtime patch, Body replacement, Pants companion, Accessory companion, Peach Body dependency, or Fashion Sense source code is shipped.

This is an honest static prototype—not a runtime capability claim.
