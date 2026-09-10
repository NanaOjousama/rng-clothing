# TFWR Master Roadmap / Blueprint / Handoff

**Project:** Forgotten Weaponsmith - Reconstruction (TFWR) + RNG Clothing / Fashion System  
**Updated snapshot:** 2026-08-31  
**Purpose:** source-of-truth handoff for ChatGPT/Codex work.  
**Priority:** preserve quality, runtime safety, i18n, controller/Steam Deck usability, and compatibility before expanding scope.

---

## 1. How to use this document

Read this document before proposing changes. Continue from **Current Exact Status** and **Immediate Next Work**. Preserve **Do Not Regress** decisions unless a newer user-approved report or runtime test supersedes them.

Feature requests describe the desired player experience. Before implementing, inspect vanilla Stardew Valley 1.6.15, Fashion Sense / Content Patcher contracts, approved framework references, and the existing project toolbox. Prefer native/framework solutions over custom rendering or invasive Harmony.

---

## 2. North star

**Explore -> Encounter -> Discover -> Reconstruct -> Master -> Collect -> Customize**

- Weapons provide combat identity and progression.
- Random/themed encounters provide discovery and replayability.
- Clothing provides collection, expression, rarity chase, and event rewards.
- Emily becomes the in-world fashion customization bridge.
- Core weapon progression must remain dependable; RNG adds optional excitement, cosmetics, themes, motifs, palettes, and collection depth.

The systems should feel like one world experience, not disconnected menus.

---

# 3. Current Exact Status

## 3.1 TFWR progression direction

The old duplicate-number / weapon-gacha core progression is retired.

- **T1:** recovery / identification.
- **T1 -> T2:** mastery-centered progression.
- **T2 -> T3:** investigation / story / trial, with a Signature Memory Core or equivalent catalyst.
- **T3 -> T4:** weapon-specific final awakening.
- **RNG:** optional discovery, replayability, encounter variants, cosmetics, motifs, palettes, fashion rewards, and collection chase.

Core weapon progression must never be RNG-blocked.

## 3.2 Clothing generator state

The clothing generator has moved beyond architecture-only experiments and now has a credible production foundation.

### Proven / preserved

- V3 Design / Surface Variety Engine: **PASS / preserve**.
- V4 upper-garment article translation: **PASS / preserve**.
- Fashion Sense HD renderer principle: **16x16 logical Shirt art at Scale 2** for FS garments; direct logical pixels; nearest-neighbor previews only.
- Global post-V5E gameplay art-polish stage: **implemented / preserve**.
- Stable sleeve runtime contract: **native Farmer arm path**; rejected custom full sleeve atlas must not return without new proof.
- V5D masculine benchmark policy: **preserve**.
- Hoodie layered architecture: user-confirmed working; keep as a proven advanced garment reference.
- V6 production batch: **30 garments** generated with credible Common -> Uncommon -> Rare separation.
- Rare ceiling calibration: **PASS** at static/art-grammar level.

### V6 production proof

The V6 batch established:

- **12 Common** enhanced vanilla garments.
- **12 Uncommon** Fashion Sense higher-detail garments with broader article variety.
- **6 Rare** premium Fashion Sense garments.
- strong batch diversity, no exact semantic duplicates, and only minimal center-panel dominance.
- Uncommon visibly introduces garment-category variety instead of merely adding decoration.
- Rare can be premium without consuming Legendary spectacle.

### Accepted ceiling anchors

These are visual calibration anchors, not items that every future output must copy.

**Upper edge of Uncommon:**
- V6 Uncommon #21.
- V6 Uncommon #22.

Future Uncommon output should not substantially exceed these in premium feel or expressive intensity without Rare review.

**Upper edge of Rare:**
- Juniper Vale Cardigan.
- Nocturne Silver Waistcoat.
- Cedarline Reserve Jacket is also a strong clean upper-Rare example.

Future Rare output should not become more expressive/spectacular than these without Legendary review.

### Archived / non-production R&D

Do not delete, but do not treat these as active production targets:

- broad procedural pants.
- shorts.
- broad procedural shoes.
- standalone skirts.
- dresses built by stretching a Shirt layer over moving legs.
- long coats / one-piece costumes built by stretching a Shirt layer over moving legs.

Reason: runtime tests showed stiff or disconnected torso-attached geometry when garment art intrudes into moving leg space.

---

# 4. Final Clothing Rarity Contract

## 4.1 Rarity table

| Rarity | Player feeling | Renderer / capability | Design rule | Typical scope | Special behavior / VFX |
|---|---|---|---|---|---|
| **Common** | “nice basic shirt” | Vanilla Stardew clothing renderer | Simple, clean, everyday | Enhanced vanilla shirts, tees, simple sweaters, button shirts, sailor tops | None |
| **Uncommon** | “oooh, this looks better” | Fashion Sense HD simple-article renderer | Better design + more garment variety | FS shirts, sweaters, vests, waistcoats, cardigans, jackets, light outerwear | Usually none |
| **Rare** | “oh damn, this is special” | Premium Fashion Sense complex-capable renderer | **Premium quality, minimal design** | Premium crewnecks, fitted knits, refined cardigans, polished vests/waistcoats, premium minimal jackets/workwear | Generally none; spectacle remains restrained |
| **Legendary** | “WHOA, where did you get that?” | Advanced Fashion Sense coordinated clothing | **Everything Rare has + stronger design + signature identity** | Hoodies, signature jackets, statement outerwear, ceremonial/fantasy pieces, event-worthy garments | Special behavior much more likely; restrained VFX when appropriate |
| **Mythic** | Absolute chase tier | Highest feasible clothing capability | Bespoke / extreme / unforgettable | Potential premium full-costume presentation, dresses, unusual coordinated outfits if proven feasible | Strongest animation/VFX/state behavior when appropriate |

## 4.2 Permanent rarity laws

> **Rare gets premium quality with minimal design. Legendary gets spectacle + identity.**

> **Rare may use advanced construction, but not advanced spectacle.**

> **A lower tier may use sophisticated construction, but it must not consume the defining visual tricks reserved for the tier above it.**

### Common

Common is intentionally restrained.

- Vanilla renderer only.
- Primarily simple shirts/tops.
- Better design taste than vanilla basics, but not more systemic complexity.
- No coordinated multi-layer systems.
- No hoodies.
- No premium statement silhouettes.

Common should feel like: **“vanilla shirts, but nicer.”**

### Uncommon

Uncommon is where fashion variety becomes visibly exciting.

- Fashion Sense higher-detail rendering.
- More garment categories.
- Better collars, openings, cuff reads, paneling, knit bands, layering cues, and reconstructed side/back views.
- Still grounded and wearable.
- Do not let Uncommon drift into premium-luxury or event-reward territory.

### Rare

Rare is the premium normal-garment tier.

- Preserve top-tier execution quality.
- Hold back design drama.
- Minimal/elegant/clean visual concepts.
- Advanced construction is allowed when it improves fit or quality.
- Multi-layer construction is allowed when technically useful, but should remain visually restrained.
- Avoid dramatic silhouettes, strong VFX, reactive behavior, iconic event identity, large motifs, or multiple spectacle hooks.

Mental test:

- “Wow, that is a really nice garment.” -> Rare.
- “WHOA, where did you get that?” -> likely Legendary.

### Legendary

Legendary inherits Rare quality, then adds identity and presentation power.

Legendary may add:

- signature silhouette.
- stronger thematic identity.
- richer/coordinated layering.
- more memorable front/side/back construction.
- stronger surface design.
- more unusual garment types.
- event/encounter-worthy presentation.
- special behavior much more often.
- restrained VFX when thematically justified.

**Hoodies begin at Legendary** in the current rarity plan. Rare may use premium sweaters/crewnecks instead.

A Legendary piece should be visibly above the Rare ceiling at normal gameplay size, not only on an enlarged contact sheet.

### Mythic - provisional

Mythic is **not guaranteed to ship**. It must earn its existence.

Desired Mythic privileges if feasibility is proven:

- everything Legendary can do, pushed further.
- strongest VFX / animation / state behavior where appropriate.
- bespoke, extreme identity.
- rarest visual concepts.
- premium unified full-costume presentation.
- dresses / one-piece-looking outfits where feasible.

Important implementation rule: “one-piece” describes the **player-facing visual concept**, not necessarily one literal sprite/layer. A Mythic outfit may use multiple coordinated FS components under the hood.

**Feasibility gate:** if Codex cannot consistently create premium, fitted, clean, runtime-safe Mythic clothing that is clearly above Legendary, remove Mythic entirely and let Legendary remain the top clothing rarity.

Do not accept “Legendary + extra particles” as Mythic.

---

# 5. Clothing Art / Generator Rules

## 5.1 Gameplay is authoritative

Contact sheets are useful, but actual Farmer gameplay is the final quality judge.

Always verify at normal gameplay footprint:

- front.
- side.
- back.
- movement where relevant.
- tool/interaction frames where relevant.

A garment that looks excellent enlarged but weak on the Farmer has not passed.

## 5.2 Global art-polish contract

The reusable post-V5E polish stage should remain generator-wide, not garment-specific.

Preserve:

- clean edge weight.
- intentional dark anchors.
- connected upper-left lit runs.
- readable silhouette.
- clear plane separation.
- restrained shading.
- bounded inner layers.
- authored side/back cues.
- no speckle noise.
- no arbitrary detail just because resolution exists.

Do not use a uniform dark sticker outline around every surface. Keep outlines clean and readable while preserving form.

## 5.3 Resolution budget

For Fashion Sense garments, extra logical resolution must be spent in this order:

1. body coverage.
2. article identity.
3. silhouette.
4. construction.
5. shoulder / sleeve / neckline relationships.
6. layering / openings.
7. surface design and color blocking.
8. small meaningful details.
9. shading / finishing.

Direct logical pixels only. No downsampling or antialiasing. Nearest-neighbor only for preview enlargement.

## 5.4 Reference-learning rule

Benchmark packs are research/reference material only.

Learn:

- construction grammar.
- silhouette logic.
- motif placement logic.
- palette hierarchy.
- surface composition.
- directional reconstruction.

Do not use benchmark pixels as generator source art.

---

# 6. Hoodie Architecture - Proven Advanced Reference

The hoodie system is the current reference for a coordinated high-tier garment.

## 6.1 Architecture

A hoodie may coordinate:

- Shirt/body.
- native Farmer sleeves or proven sleeve route.
- Hood/Hat.
- optional accessory where truly necessary.
- preset assembly.
- bounded state/weather behavior.
- narrowly scoped Content Patcher policy edits when needed.

Do not make the player manually assemble unrelated components.

## 6.2 Hair policy lessons

Fashion Sense 7.5.0 does not expose a generic partial-hair clipping mask.

Current safe principles:

- preserve front hair where possible.
- use hood occlusion for side hair where acceptable.
- back hair can be hidden directionally where needed.
- custom/modded hair remains experimental if it exceeds vanilla contracts.
- do not build a generic custom hair renderer or invasive Fashion Sense private-method patch just for hood clipping.

## 6.3 Rarity placement

The advanced/reactive hoodie family is now **Legendary**, not Rare.

A plain premium hoodless sweater/crewneck belongs in Rare. A hoodie’s stronger silhouette, coordinated hood architecture, and potential state behavior reserve it for Legendary in the current ladder.

## 6.4 First hoodie reward concept

Future gameplay/story idea:

- Emily gives the player the first Legendary hoodie through an event.
- She hints that the hood behaves differently in rain rather than explaining the whole mechanic in a tutorial box.
- Example clue tone: “Try wearing it the next time it rains.”
- This becomes the player’s introduction to special clothing behavior.

Do not implement story integration inside the clothing generator milestone; keep this as a future gameplay track.

---

# 7. Future Emily Customization Architecture

Emily is the planned in-world clothing personalization bridge.

## 7.1 Future-proof garment metadata now

Generated garments should preserve semantic customization metadata so future systems do not need to reverse-engineer finished pixels.

Possible semantic regions where applicable:

- `PrimaryFabric`
- `SecondaryFabric`
- `Sleeve`
- `Cuff`
- `Collar`
- `Lapel`
- `Hem`
- `Pocket`
- `Trim`
- `Accent`
- `HoodOuter`
- `HoodLining`
- `Drawstring`
- `MotifSocket`
- `InsigniaSocket`
- `MetalDetail`
- `ButtonDetail`

Not every garment should expose every region.

## 7.2 Protected pixels

By default:

- **core outline is protected.**
- **structural seams are protected.**
- decorative piping / edge treatment may be exposed as `Trim` when it is intentionally part of the design.

Reason: unrestricted outline/seam recoloring can destroy contrast and garment readability.

## 7.3 Rarity and customization richness

- Common: very few simple regions.
- Uncommon: moderate region variety.
- Rare: richer premium regions but restrained design.
- Legendary: richer customization opportunities, motif/insignia sockets where appropriate.
- Mythic: only if implemented; potentially the richest controlled customization, without allowing edits that destroy signature identity.

## 7.4 Future encounter currency loop

Planned concept:

**Random encounter -> earn fashion/customization currency -> visit Emily -> customize an owned garment -> save personalized variant.**

Possible services later:

- recolor fabric.
- recolor trim.
- recolor collar/hood/sleeve/cuff.
- apply/remove unlocked motifs.
- restore original.
- save a custom variant.

Motifs may themselves be encounter discoveries.

Do not implement Emily UI, currency spending, or runtime recolor systems until garment generation and rarity ceilings are stable.

---

# 8. Mythic Full-Costume / Dress R&D

Status: **future feasibility research only**.

The user’s definition of “possible” is not “can a sprite be drawn on the Farmer.” It means:

- premium.
- fitted.
- clean.
- cohesive.
- convincing front/side/back.
- stable through movement.
- no rigid torso-attached block over moving legs.

Before Mythic full costumes/dresses become a production feature, prove one carefully controlled prototype across:

- idle front/right/back/left.
- walk/run.
- tools.
- sit/stand.
- horse/mount where applicable.
- body-offset branches.
- layer/leg occlusion.

If a single premium prototype cannot pass, do not build a procedural Mythic costume generator. Remove or narrow Mythic instead.

---

# 9. Weapon Directions

- **Frostbite:** Chill -> Freeze -> Shatter; Triple Stab/block; Winter’s Grasp; stronger T4 slow/stagger payoff.
- **Thunder Breathing:** Static Discharge; block-based Enhanced A; signature retained; T4 chain/arc still to finalize.
- **Zangetsu’s Edge:** Spiritual Pressure; perfect block fills pressure + speed; Getsuga Tensho; stronger high-pressure T4.
- **Sun Breathing / Hinokami:** Flame Rhythm; Fire Wheel on perfect-timing block; two-rotation Fire Ring; T4 pushes enemies/projectiles; strong aura/Sunburn feedback.
- **Bankai: Thousand Petals:** Bleed/petals; Petal Reversal; Petal Storm; stronger bleed/shield T4.
- **Emberfang:** Dagger; Ember stacks; Flame Dash; Cinder Bite detonation; spreading T4.
- **Lostvayne:** Counter Echo charges/phantom slashes; autonomous clone; Clone Dominion T4.
- **Dragon Slayer:** heavy penalty + Momentum; heavy guard/step; shockwave finisher; stronger stagger/cleave T4.
- **Beast Fangs:** three-Fang dual-sword chain; contextual A follow-ups; Whirling Fangs signature; faster/stronger T4 chain.

## Enhanced-A architecture

`EnhancedActionService` policies:

- PreserveVanillaSpecial.
- EnhanceVanillaSpecial.
- ReplaceVanillaSpecial.
- ContextualFollowUp.

A cannot trigger signature; Q/right-stick remains signature. `EnhancedGuardService` handles defensive behavior. Preserve vanilla cooldowns/behavior unless explicitly handled.

---

# 10. Themed Encounter Reward Ecosystem

Locked principle: themed encounters explain where rewards came from.

Examples:

- Sun encounter -> Sun weapon-memory clue + possible Sun clothing/palette/flame motif/accessory.
- field/scout encounter -> fieldwear, insignia/motif unlocks, muted military palettes, themed cosmetic rewards.

Cosmetics should feel sourced from the encounter, not stapled on.

Long-term loop:

**Explore -> encounter -> discover -> reconstruct -> master -> collect -> customize -> hunt rarer encounters -> complete themes.**

A separate story/gameplay brainstorming thread is recommended so clothing renderer implementation does not become mixed with encounter writing and narrative design.

---

# 11. Permanent Technical / Compatibility Rules

- i18n/localization for all player-facing text.
- controller / Steam Deck first-class.
- minimal invasive Harmony.
- preserve vanilla behavior when possible.
- fail open safely.
- avoid global input suppression/shared-state conflicts.
- approved dependencies may be used normally.
- new dependencies must be justified before adding manifests/dependency-required code.
- keep Steam Deck performance bounded.
- scan the TFWR toolbox/framework references before non-trivial implementation.
- validate current game/framework versions before relying on private behavior.

## Vanilla-first research rule

Before implementing or redesigning a Stardew-facing feature, inspect relevant Stardew Valley 1.6.15 assets/data/decompiled code. Wiki pages are orientation; installed game data/code are authoritative.

Important clothing sources include:

- `Content/Data/Shirts.xnb`
- `Content/Data/Pants.xnb`
- `Content/Data/Hats.xnb`
- `Content/Data/Boots.xnb`
- `Content/Data/TailoringRecipes.xnb`
- `Content/Characters/Farmer/shirts.xnb`
- `Content/Characters/Farmer/pants.xnb`
- `Content/Characters/Farmer/hats.xnb`
- `Content/Characters/Farmer/shoeColors.xnb`
- `Content/Characters/Farmer/farmer_base.xnb`
- `Content/Characters/Farmer/farmer_girl_base.xnb`

Important decompiled areas:

- `StardewValley.Objects.Clothing`
- `StardewValley.Objects.Hat`
- `StardewValley.Objects.Boots`
- `StardewValley.FarmerRenderer`
- `StardewValley.FarmerSprite`
- `StardewValley.Menus.TailoringMenu`

---

# 12. Masculine Clothing Benchmark Policy

Permanent policy file: `specs/MALE_CLOTHING_BENCHMARK_RULES.md`.

Preserve broad masculine fashion coverage; never collapse masculine design to “dark generic jackets.”

Relevant design languages include:

- casual.
- work/farmwear.
- streetwear.
- sweatwear.
- knit/cardigan.
- formal/suit.
- vest/waistcoat.
- jacket/outerwear.
- military/fieldwear.
- period/gentleman.
- fantasy/adventurer.
- armor/tunic/tabard.
- uniform.
- alt/dark.

Masculine does not mean only dark palettes or broad shoulders. Light, pastel, colorful, elegant, cute, rugged, academic, historical, sporty, and fantasy masculine styles are valid when construction supports them.

---

# 13. Roadmap From Current State

## Immediate - current clothing thread

1. **Legendary calibration batch.**
   - Generate a small set of Legendary prototypes.
   - Compare directly against Rare ceiling anchors.
   - Legendary must visibly clear Rare at gameplay size.
   - Include clearly different garment families; do not make six short jackets.
   - Hoodies begin here.
   - Do not touch Mythic yet.

2. **Legendary quality gate.**
   - Reject anything that reads as “Rare with more trim.”
   - Require signature identity, stronger silhouette, richer presentation.
   - Preserve restraint; do not use heavy VFX as a crutch.

3. **Add/retain semantic customization metadata** in production recipes without implementing Emily UI yet.

4. **Small live-runtime candidate testing** remains required before broad production packaging.

## Near

1. Freeze Legendary ceiling once a clear Rare-vs-Legendary visual separation is proven.
2. Produce a balanced production candidate pool across Common / Uncommon / Rare / Legendary.
3. Keep Common and Uncommon essentially stable; only fix regressions or obvious quality drift.
4. Maintain Rare’s “premium quality, minimal design” ceiling.
5. Keep Legendary as the first spectacle/identity tier.

## Parallel story/gameplay track

Use a separate conversation/workstream for:

- random encounter structure.
- Emily event writing.
- first Legendary hoodie reward event.
- encounter currency.
- motif unlocks.
- clothing reward distribution.
- NPC clues and themed discoveries.
- seasonal/weather/festival hooks.

## Mid

1. Emily semantic customization prototype.
2. Encounter currency + motif/customization unlock flow.
3. Themed collection generation from proven garment families.
4. Clothing reward resolver for encounters/events.
5. Collection UI/save schema only after reward/item identity is stable.
6. Optional small curated shoe-event system if still desired.

## Later

1. Legendary event/encounter reward integration.
2. Full TFWR fashion integration.
3. Emily/Werdon/Forge reactions and contextual dialogue.
4. Optional cosmetic weapon-fashion resonance.
5. Mythic feasibility trial only after Legendary is mature.
6. If Mythic cannot clearly and consistently exceed Legendary at premium runtime quality, remove Mythic.

---

# 14. Recommended Quality Pipeline

For every future generator milestone:

1. semantic recipe validation.
2. renderer/static contract validation.
3. 32px gameplay-footprint sheet.
4. front/right/back/left sheet.
5. batch diversity/rejection gate.
6. compare against rarity ceiling anchors.
7. human **KEEP / REWORK / TRASH** review.
8. live Farmer runtime test for selected candidates.
9. only then production packaging/integration.

Do not promote a whole batch just because automated/static tests pass.

---

# 15. Suggestions / Improvements To Preserve

## 15.1 Rarity feature budgets

Maintain explicit “spectacle budgets,” not only visual-density budgets.

Suggested rule:

- Common: no special hooks.
- Uncommon: article variety, no spectacle hook.
- Rare: one premium construction idea + restrained finishing.
- Legendary: one or two signature identity/presentation hooks.
- Mythic: multiple coordinated signature systems only if feasibility is proven.

## 15.2 Ceiling-anchor checks

Keep representative ceiling anchors in the generator QA workflow.

When a new garment approaches a tier boundary, compare it directly against the established upper-edge examples at gameplay size.

## 15.3 Recipe versioning

Give production garments stable semantic IDs/schema versions so future Emily customization, reward tables, and save data can refer to a garment independent of regenerated PNG filenames.

## 15.4 Runtime-pack sanitation

When replacing test packs, delete old installed copies instead of merge-copying. Stale Fashion Sense component folders can reintroduce old runtime regressions.

## 15.5 Human taste gate

Automated validators are guardrails, not beauty judges. Continue explicit user review of gameplay-sized output.

---

# 16. Do Not Regress

- Do not revive duplicate-number core weapon progression.
- Do not throw away V3 because one article adapter is weak.
- Do not build separate full design brains per rarity or garment type.
- Do not equate rarity with noise.
- Do not make Common ugly or overdesigned.
- Do not let Uncommon creep above its established ceiling.
- Do not over-buff Rare.
- Do not let Rare steal Legendary’s spectacle/identity.
- Do not make Legendary merely “Rare with extra trim.”
- Do not promise Mythic if the generator cannot produce genuine Mythic quality.
- Do not downscale generated art.
- Do not judge clothing solely from enlarged isolated previews.
- Do not reintroduce the rejected custom full-pose Sleeves atlas without new runtime proof.
- Do not stretch Shirt-layer art over moving legs again without a fundamentally better native/layered solution.
- Do not resurrect broad procedural pants/shoes simply because references exist.
- Do not reduce masculine fashion to dark generic jackets.
- Do not create invasive custom hair rendering for one hoodie.
- Do not invent custom rendering/state machinery before checking vanilla/Fashion Sense/Content Patcher/native options.
- Do not expose core outline or structural seams as unrestricted Emily recolor channels.

---

# 17. Open Questions

- Exact Legendary ceiling and feature budget after calibration.
- Which Legendary behaviors/VFX remain subtle enough for Stardew readability.
- Whether any Mythic garment can meet the premium fitted runtime bar.
- Whether Mythic remains a real rarity or is removed.
- Final story structure for Emily’s first Legendary hoodie reward.
- Encounter currency name, pacing, and sinks.
- Motif unlock catalog and compatibility rules.
- Fashion Sense dye/customization implementation details.
- Stable production garment IDs/schema/versioning.
- Collection UI and duplicate policy.
- Which higher-variance sleeve silhouettes can become runtime-safe.
- Optional shoe-event scope.
- Signature obstacle penetration config final options.

---

# 18. Required Stardew Wiki Orientation Links

Installed game assets/code remain authoritative.

- https://stardewvalleywiki.com/Modding:Pants
- https://stardewvalleywiki.com/Modding:Shirts
- https://stardewvalleywiki.com/Modding:Hats
- https://stardewvalleywiki.com/Modding:Weapons
- https://stardewvalleywiki.com/Modding:Quest_data
- https://stardewvalleywiki.com/Modding:Boots
- https://stardewvalleywiki.com/Modding:Maps
- https://stardewvalleywiki.com/Modding:Location_contexts
- https://stardewvalleywiki.com/Modding:Location_data
- https://stardewvalleywiki.com/Modding:Museum
- https://stardewvalleywiki.com/Modding:Farmer_sprite
- https://stardewvalleywiki.com/Modding:Powers
- https://stardewvalleywiki.com/Modding:Tailoring

---

# 19. Important Source / Artifact List

Core handoff/toolbox:

- `TFWR_Mod_Toolbox_Final_Ranking_2026-08-28.pdf`
- `TFWR_Mod_Toolbox_Final_Ranking_2026-08-28.docx`
- `TFWR_CODEX_MOD_TOOLBOX_INDEX.md`
- `specs/MALE_CLOTHING_BENCHMARK_RULES.md`

Current clothing milestone artifacts:

- `V5E_GLOBAL_ART_POLISH_SHOWCASE.md`
- `V6_DESIGN_RARITY_TABLE.md`
- `V6_DIVERSITY_REJECTION_REPORT.md`
- `V6_PRODUCTION_BATCH_REPORT.md`
- `V6_RARE_CEILING_REPORT.md`
- `V6_GAMEPLAY_SIZE_30.png`
- `V6_UNCOMMON_CONTACT.png`
- `V6_RARE_PLUS_CONTACT.png`
- `V6_RARE_CEILING_CONTACT.png`
- `V6_RARE_CEILING_GAMEPLAY.png`

Hoodie / hair research artifacts:

- `HOODIE_FINAL_COMPLETION_PASS.md`
- `HOODIE_FINAL_RUNTIME_CHECKLIST.md`
- `HOODIE_VANILLA_HAIR_COMPATIBILITY.md`
- `HOOD_UP_HAIR_CLIPPING_FEASIBILITY.md`

---

# 20. Suggested Codex Handoff Message

> Read `TFWR_Master_Roadmap_Blueprint_Handoff_2026-08-31.md` as the current source of truth before changing TFWR or the RNG clothing generator. Preserve the rarity ceilings and Do Not Regress rules. Current clothing priority is **Legendary calibration**: Rare is already calibrated as premium quality with minimal design, and Legendary must visibly add signature identity, stronger silhouette, richer presentation, and event-worthy presence without drifting into unproven Mythic territory. Common and Uncommon are essentially stable. Hoodies begin at Legendary. Mythic is provisional and must pass a future premium full-costume/dress feasibility gate or be removed. Keep future Emily customization metadata semantic and protect core outlines/structural seams.

