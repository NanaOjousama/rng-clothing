# V4.5 Extended-Garment Capability Audit

## Evidence boundary

Audit target: installed Fashion Sense **7.5.0** for Stardew Valley 1.6.15. Installed manifest version is 7.5.0; installed `FashionSense.dll` is 404,992 bytes with SHA-256 `28ea84800dadae414e8190e12b5e94f0db57184c0932452ebe99cd061e6412a6`. Source behavior was checked against the previously verified official 7.5.0 source commit `39e9e9e13c9f9a78416172e73a229cf8703ddb59` and its shipped example pack.

Classifications below describe **RNG Clothing project readiness**, not merely whether Fashion Sense can deserialize a model. `SAFE NOW` means the source contract is sufficiently bounded for a static/default-body generator. `EXPERIMENTAL` means Fashion Sense supports the layer but V4.5 still needs the runtime checklist. `LATER` requires a larger renderer/animation milestone. `NOT RECOMMENDED` means a loadable asset would be misleading evidence.

## Source-level shared contract

- `PantsModel` and `ShoesModel` use `StartingPosition`, integer `BodyPosition`, arbitrary integer `PantsSize`/`ShoesSize`, Scale, shared color masks, and shared animation lists.
- `AccessoryModel` uses `StartingPosition`, integer `HeadPosition`, arbitrary `AccessorySize`, shared animations, and `DrawBehindHead`, `DrawAfterPlayer`, `DrawAfterSleeves`, or generic `DrawOrderOverride`.
- `PantsModel` adds `HideLegs` and `HideShadow`; `ShoesModel` adds `DrawBeforePants`.
- Default current layer sequence is Player → Shoes → Pants → Shirt → Hair → Accessories → Sleeves → Hat, with back-facing and model-specific reordering. Generic draw-order overrides and animation-frame overrides can move a layer relative to another appearance type.
- Native Farmer feature offsets are applied unless `DisableNativeOffset=true`. Pants, shoes, and hair receive the male-body Y adjustment; accessories additionally receive accessory direction/height offsets.
- Default `HideWhileSwimming` and `HideWhileWearingBathingSuit` are true, but Accessories override both defaults to false. A body-sized accessory must explicitly opt into hiding if that is desired.
- Fashion Sense uses a model's source rectangle plus the selected animation frame. An animation changes the source rectangle; it does not deform or automatically articulate garment art.
- Appearance IDs and colors are stored in Farmer `modData`; Pants, Shoes, and accessory slots have Hand Mirror/API selection. Pants and Shoes may also use item integration. Accessories have no native wearable-item contract.
- Coordinated parts may be collected in a preset outfit, but a Shirt item cannot atomically equip a separate Accessory coat tail.

## Candidate capability map

### 1. PANTS — EXPERIMENTAL

- **FS asset:** `Pants/<name>/pants.json|png`; four `*Pants` direction models.
- **Canvas/frame:** arbitrary. Official examples include full 16×32 Farmer-frame templates and compact assets. V4.5 uses 16×12 compact authored frames at Scale 4.
- **Anchor:** `BodyPosition`; V4.5 uses `(0,-20)`, close to the compact official lower-body examples. This is a prototype value, not a body-mod-independent universal.
- **Draw order:** over Player/Shoes and under Shirt by default. `HideLegs`/`HideShadow` can replace underlying geometry but increase compatibility risk.
- **Animation:** full correctness requires mapping Farmer frames or explicit standing/walk/run/tool/horse/sit conditions. V4.5 only authors four walk/run phases and leaves `HideLegs=false`.
- **Controller/UI:** first-class Pants category; optional item-backed pants possible. Prototype uses Hand Mirror only.
- **Steam Deck:** tiny texture and one authored-color draw; negligible in isolation. Animation changes source rectangles rather than draw count.
- **Body mods:** Body feature offsets can move Pants, but the generated coverage mask targets the default Farmer and may expose/overlap custom legs.
- **Semantic translation:** strong: waistband, side seam, knee panel, cuff, utility rhythm.
- **Additional code:** article masks, leg-phase templates, full Farmer-frame mapping, body-coverage/leg-separation validators.
- **Verdict:** supported by Fashion Sense; not production-ready until motion/tool/horse/sitting tests pass.

### 2. SKIRT — EXPERIMENTAL

- **FS asset:** Pants. Fashion Sense has no separate Skirt type; the official example pack implements a grass skirt as `Pants`.
- **Canvas/frame:** arbitrary; official compact example uses 16×10 with `BodyPosition.Y=-21`. V4.5 uses that exact contract size/anchor but original geometry.
- **Draw order:** Pants layer, under Shirt. A skirt can overlay native legs; wide/long hems may need `HideLegs` and far more pose art.
- **Animation:** a short fitted/flared skirt can author walk/run sway. Sitting, horse, and tools can expose the static hem limitation.
- **Controller/Deck/multiplayer:** same as Pants.
- **Body mods:** high risk at hip and leg junction, especially wider bodies.
- **Semantic translation:** good for waistband, pleats, panel split, hem border, side accent.
- **Additional code:** short-skirt directional and movement templates; seated/horse hem states; leg-occlusion validation.
- **Verdict:** a short skirt is plausible; long/full skirts are `LATER`.

### 3. BOOTS / SHOES — EXPERIMENTAL, LOWEST-RISK NEW TYPE

- **FS asset:** `Shoes/<name>/shoes.json|png`; four `*Shoes` models.
- **Canvas/frame:** arbitrary. Official examples use 16×16 compact boots and a 16×32 full Farmer-frame shoe template. V4.5 uses 16×12 at Scale 4.
- **Anchor:** `BodyPosition`; prototype uses `(0,-20)`, matching compact official footwear placement.
- **Draw order:** Shoes normally precede Pants; `DrawBeforePants` makes that explicit and lets trousers cover the boot shaft.
- **Animation:** compact boots still need step phases. Tool/horse/sit poses can change leg placement even when foot art is small.
- **Controller/UI:** first-class Shoes category, API, optional boot-item integration. Prototype uses Hand Mirror.
- **Steam Deck:** minimal texture/draw cost.
- **Body mods:** lower risk than pants, but shoe/leg offsets and nonstandard feet remain compatibility points.
- **Semantic translation:** strong enough for shaft, cuff, strap, sole, toe, and material contrast.
- **Additional code:** step templates, pants/boot overlap rules, full-frame fallback.
- **Verdict:** most promising next production target, but V4.5 runtime is not yet tested.

### 4. CAPE / MANTLE — EXPERIMENTAL

- **FS asset:** body-sized Accessory. The official example pack includes a `FlowingCape` with 16×16 front, 16×32 back, 32×32 sides and movement frames.
- **Canvas/frame:** arbitrary `AccessorySize`; V4.5 uses 24×32, Scale 4, three authored phases.
- **Anchor:** `HeadPosition`; prototype uses `(4,0)` to center a 24-wide source around the default 16-wide Farmer.
- **Draw order:** V4.5 front clasp is after Shirt; back/side mantle is before Player. These per-direction choices require runtime review around hair, sleeves, tools, and horse.
- **Animation:** an Accessory can animate, but it is not physically simulated and is not automatically synchronized to a shirt unless authored/synced explicitly.
- **Swimming:** Accessories default visible in water/bathing; prototype explicitly hides in both.
- **Controller/UI:** Accessory category/slots; no item-backed equip. A preset can coordinate it with other appearances.
- **Steam Deck:** one extra layer/draw; prototype texture is 72×128 = 36,864 uncompressed RGBA bytes. Negligible alone, but many animated multi-mask accessories add draw calls and cached mask textures.
- **Body mods:** head/body offsets and silhouette width can make the shoulder anchor float or clip.
- **Semantic translation:** strong for shoulder anchor, back field, border, fold, clasp, and original back crest.
- **Additional code:** action-specific movement templates, upper-garment compatibility, hair/sleeve/tool occlusion gates.
- **Verdict:** framework-supported and visually valuable, but still experimental.

### 5. COAT-TAIL COMPANION LAYER — NOT RECOMMENDED YET

- **FS asset:** lower body-sized Accessory, normally before Player/Shirt, paired with an upper Shirt through a preset.
- **Canvas/frame:** technically arbitrary; V4.5 renders a diagnostic 24×24 Scale-4 split-tail atlas.
- **Anchor/order:** `HeadPosition` plus direction-specific ordering. There is no native waist-anchored garment type.
- **Animation:** must coordinate with legs, upper jacket, tools, horse, sitting, swimming, and the selected upper garment. Separate appearance animation can drift from the shirt/legs.
- **UX/multiplayer:** separate accessory selection; preset coordination is possible, atomic shirt-item equip is not. Peers need identical pack and preset/appearance IDs.
- **Body mods:** high risk.
- **Semantic translation:** possible for split tail, edge trim, and back hem, but semantic success does not solve motion.
- **Additional code:** paired state management, many pose templates, clipping validation, probably a dedicated runtime companion controller.
- **Verdict:** diagnostic asset only; deliberately absent from the test pack.

### 6. TRUE LONG OUTERWEAR — NOT RECOMMENDED

Fashion Sense has no Long Coat type. It can be approximated by Shirt + Pants or Shirt + Accessory, but no inspected contract supplies automatic multi-layer articulation or atomic equipment. Until a coat-tail companion passes every runtime state, calling the combination true long outerwear would overpromise.

### 7. WAIST ACCESSORY / BELT-LIKE LAYER — EXPERIMENTAL

- **FS asset:** body-sized Accessory or, preferably, a semantic region embedded into Pants/Shirt.
- **Risk:** standalone accessory ordering between Shirt and Pants, non-body `HeadPosition`, separate equip state, and body-mod width.
- **Recommendation:** keep belt/harness rhythms inside Pants for now. A standalone animated belt provides little freedom relative to its compatibility cost.

### 8. BACK EMBLEM / BACK ACCESSORY — SAFE NOW, COMPACT ONLY

- **FS asset:** Accessory with back model and quiet/transparent front/sides, or a motif embedded in a mantle/shirt.
- **Risk:** small if it stays on the upper back and uses a bounded default-body anchor. Hair and cape conflicts remain.
- **Semantics:** V3 motifs translate directly. This is safer than a full cape but was folded into the mantle prototype instead of receiving a separate asset.

### 9. LOWER-BODY STRAP / HARNESS-LIKE LAYER — LATER AS STANDALONE; EXPERIMENTAL INSIDE PANTS

A restrained strap painted as a Pants surface region follows the Pants source frame and is the preferred route. A separate Accessory strap would duplicate pants/leg synchronization and draw-order problems. V4.5 tests one semantic harness rhythm inside Rare trousers only.

## Platform and performance conclusion

Fashion Sense is a SMAPI/.NET mod and the inspected contracts contain no Windows-only renderer path. The Steam Deck concern is workload, not platform API. The six installable V4.5 textures total about **96 KB uncompressed RGBA**; the excluded coat tail adds about 27 KB. Authored-color prototypes use one base draw each and no color-mask overlay draws. This is immaterial next to game textures. The meaningful costs arrive with many simultaneous accessories, multiple color-mask layers, lights, or animation textures—not source-rectangle animation by itself.

No performance or multiplayer behavior has been measured in-game in this milestone. Source support is not runtime evidence.

