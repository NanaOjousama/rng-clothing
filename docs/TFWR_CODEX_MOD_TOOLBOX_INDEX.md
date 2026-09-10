# TFWR Codex Mod Toolbox Index
**Purpose:** AI-readable capability catalog for Forgotten Weaponsmith – Reconstruction (TFWR)  
**Status:** Current toolbox guidance  
**Last updated:** 2026-08-28

---

# 0. How Codex MUST use this file

This file is not a list of dependencies to install.

It is a **capability index**. Before implementing a TFWR feature, Codex should scan this file for existing Stardew Valley frameworks, tools, APIs, reference implementations, and compatibility targets that may help.

## Required decision process

For every non-trivial feature request:

1. Identify the feature category.
   - UI
   - events/cinematics
   - quests/progression
   - world spawning
   - maps
   - combat
   - rendering
   - animation
   - audio
   - NPC schedules/dialogue
   - collection/archive
   - multiplayer
   - debugging/testing
   - compatibility
   - other

2. Search the relevant capability section in this file.

3. Build a shortlist of the **2–4 best-fitting candidates**.
   - Rank by **fit for the exact task first**.
   - Use the toolbox rank as a secondary signal.
   - Do not choose a higher global rank if a lower-ranked tool fits the requested job better.

4. Compare the shortlist on:
   - Exact feature coverage
   - Stardew Valley 1.6 / SMAPI compatibility
   - Steam Deck / Linux compatibility
   - Controller implications
   - Multiplayer implications
   - Runtime/performance cost
   - Harmony patch footprint
   - Input conflicts
   - Maintenance risk
   - Compatibility risk with common mods
   - Licensing / source reuse rights
   - Whether TFWR can achieve the same result cleanly without the dependency

5. Choose one of these implementation modes:
   - **TFWR-native**
   - **Runtime dependency**
   - **Optional integration**
   - **Copy/adapt source pattern**
   - **Read-only reference**
   - **Dev/test tool**
   - **Compatibility target**

6. If a new runtime dependency would be added:
   - STOP.
   - Explain the candidate.
   - Explain the exact feature it enables.
   - Explain why TFWR-native code is worse or insufficient.
   - Explain controller, Steam Deck/Linux, multiplayer, performance, maintenance, compatibility, and licensing implications.
   - Ask the user for approval before modifying dependency declarations or writing dependency-required code.

7. Prefer the **smallest dependency set** that fully solves the requested feature.

8. Never install a framework "just in case."

---

# 1. TFWR architecture rules that override framework convenience

These rules take priority over any framework listed below.

## TFWR must remain authoritative for:

- Weapon ownership
- Mastery
- Memory Fragments
- T1 / T2 / T3 / T4 progression
- Reconstruction state
- Investigation state
- Signature unlock state
- Final Awakening state
- Combat meters
- Weapon-specific status effects
- Perfect Block logic
- Enhanced-A routing
- Signature activation
- Boss/trial completion state
- Reward recovery
- Save migration
- Required progression guarantees

A framework may **present**, **trigger**, **visualize**, or **assist** these systems, but should not become a second source of truth unless the user explicitly approves an architectural change.

## Compatibility principles

Prefer:
- narrow integration;
- Stardew-native systems;
- fail-open behavior;
- minimal Harmony patching;
- event-driven logic;
- Content Patcher / GSQ / trigger-action integration where appropriate;
- controller-friendly UI and interactions;
- i18n/localized player-facing text;
- deterministic recovery for required progression.

Avoid:
- global input suppression;
- broad invasive patches without necessity;
- duplicated progression authorities;
- mouse-only interfaces;
- uncontrolled RNG for mandatory progression;
- hardcoded player-facing strings;
- dependencies that solve only a tiny problem TFWR can solve cleanly itself.

---

# 2. Rank definitions

| Rank | Meaning |
|---|---|
| **S** | Permanent TFWR toolbox item; foundational or unusually valuable |
| **A** | Strong candidate for a matching TFWR feature |
| **B** | Useful situational candidate |
| **C** | Reference/archive only unless a precise need appears |
| **COMPAT** | Do not depend on it; test interoperability |
| **DEV-S/A/B/C** | Development-only tool |
| **REJECT** | Do not spend development time on it |

Important: **Rank is not an install instruction.**

---

# 3. Quick capability lookup

Use this table first when a request arrives.

| User request / capability | Best first candidates | Secondary candidates | Default direction |
|---|---|---|---|
| Custom TFWR menu / UI / catalog | **StardewUI Continued** | Theme Manager, StardewLocalAPI | StardewUI first |
| Controller-friendly UI | **StardewUI Continued** | Better Crafting patterns, Quest Journal patterns | TFWR-specific UI with controller focus |
| Dynamic map/world changes | **Content Patcher + BETAS** | DMTE, FTM | Use smallest combo |
| Dynamic monsters / objects / anomalies | **Farm Type Manager** | BETAS, TFWR C# | FTM for ambient/random; TFWR for required |
| Custom event actor poses / opacity / layering | **Extra Event Commands** | MotionFramework | Native events + EEC |
| Complex custom Farmer animation | **MotionFramework** | Extra Event Commands | Use only if native animation is insufficient |
| CG / visual-novel style memory sequence | **StardewCGEvents** | Calcifer CG patterns | Rare/high-impact scenes |
| Branching event logic | **True Rune: Events** | Better Events Core, native events | Native first, framework if needed |
| Quest board / repeatable requests | **More Quests Framework** | Quest Journal integration | TFWR owns progression state |
| Investigation presentation | **TFWR + CP/BETAS** | MQF for optional/side tasks | Do not outsource core progression |
| Physical collection/archive room | **Custom Museum Framework** | StardewUI, Furniture Framework | CMF presentation; TFWR owns state |
| 32×32 item icons | **Double Size Sprite (DSS)** | Sprites in Detail | POC before dependency |
| Held weapon/swing placement | **TFWR custom renderer** | DSS if supported | TFWR owns pivot/offset |
| Ranged weapon system | **Archery** | Slingshot Framework | Only when a ranged weapon exists |
| Combat architecture ideas | **AMF, StarQuality, Combat Overhaul** | RandomStars | Reference, not authority |
| Deterministic RNG | **SeededRandom / EPU patterns** | TFWR native RNG service | Prefer TFWR implementation |
| NPC conditional schedules | **Custom Schedule Keys** | True Rune Schedule Director | Simpler tool first |
| Reactive dialogue | **Content Patcher + TFWR tokens** | True Rune Dialogue Director | CP first |
| World travel/off-map destinations | Central Station | Custom warp/location refs | Only if needed |
| Dynamic audio | Dynamic Music | SAAT, Positional Audio | Feature-specific |
| Map debugging | **TileSense + Data Layers** | Map Fixer, Player Coordinates | Dev tools only |
| Combat testing | **Combat Dummy** | StardewLocalAPI | Dev tool only |
| General dev/debug workstation | **StardewLocalAPI** | True Rune Toolkit, Debug Mode | Dev tool only |
| Event authoring/testing | **StardewLocalAPI + Cutscene Maker** | Events Editor | Dev only |
| Localization QA | Internationalization QA tool | TFWR tests | Dev only |
| Framework/source architecture patterns | **Pathoschild/StardewMods** | SophieShared, SpaceCore source | Copy/adapt when license allows |

---

# 4. UI / menu / interface tools

## StardewUI Continued
**Rank:** S  
**Category:** UI framework  
**Mode:** Runtime candidate  
**Primary purpose:** Build custom Stardew-style menus using declarative UI, binding, layouts, themes, and reusable components.

### Best TFWR uses
- Reconstruction Forge menu
- Echo Archive catalog
- Weapon detail pages
- Mastery / Memory Fragment display
- Investigation Ledger
- Echo Resonator menu
- Banner/pull presentation
- Debug/admin UI
- Controller-focused menu navigation

### Use when
- TFWR needs a substantial custom menu.
- Layout complexity is growing.
- Controller focus/navigation needs to be systematic.
- Reusable components are desirable.

### Do not use when
- A tiny one-off vanilla menu is enough.
- The feature can be done cleanly with a simple existing TFWR menu.

### Notes
- Current preferred UI framework.
- Highest-priority candidate when the user asks for "a better UI."
- Codex should compare alternatives, but this should usually be shortlisted first.

---

## Theme Manager
**Rank:** B-/C+  
**Category:** UI theming  
**Mode:** Reference / optional runtime candidate  
**Primary purpose:** Allow selectable UI colors/fonts/theme data and third-party theme packs.

### Best TFWR uses
- User-selectable themes
- External theme-pack support
- Theme customization beyond TFWR's own visual style

### Use when
- The user explicitly wants third-party selectable themes.

### Do not use when
- TFWR only needs its own themed UI.
- StardewUI styling already covers the requirement.

### Licensing
- Restrictive / All Rights Reserved.
- Do not copy source.

---

## Better Crafting
**Rank:** A reference  
**Category:** UI/controller architecture reference  
**Mode:** Read-only reference / optional integration patterns  
**Primary purpose:** Excellent examples of complex controller-friendly Stardew menu architecture.

### Best TFWR uses
- Focus navigation patterns
- Category/tab navigation
- Search/filter UX
- Controller ergonomics
- Scrolling lists
- Complex menu organization

### Do not use as
- TFWR progression authority
- Reconstruction system itself

---

## Quest Journal
**Rank:** B+  
**Category:** Quest UX  
**Mode:** Optional integration / reference  
**Primary purpose:** Enhanced quest browsing and controller-friendly journal UX.

### Best TFWR uses
- Optional integration for MQF quests
- UX reference for Investigation Ledger

### Default
TFWR should still have its own Investigation Ledger if core progression needs custom presentation.

---

# 5. Events / cinematics / memory scenes

## Extra Event Commands
**Rank:** A+  
**Category:** Event presentation  
**Mode:** Runtime candidate  
**Primary purpose:** Extend Stardew events with actor rotation, opacity, layering, temporary actor handling, Farmer sprite changes, clothing control, and overhead text.

### Best TFWR uses
- Awakening scenes
- Memory visions
- Reconstruction ceremonies
- NPC staging
- Apparitions
- Layering characters/effects
- Temporary pose changes

### Strengths
- No broad Harmony surgery observed in audit.
- Strong fit with native event-first design.

### Use when
- Native event commands almost work, but presentation needs more control.

### Do not use when
- Native event commands already handle the scene.

---

## StardewCGEvents
**Rank:** A  
**Category:** Cinematic / CG events  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Visual-novel / CG-style presentation inside Stardew events.

### Best TFWR uses
- Major memory revelations
- Weapon-origin visions
- Awakening splash scenes
- Rare dramatic story moments

### Use sparingly
High-impact scenes only.

---

## Better Events Core
**Rank:** A-  
**Category:** Event utility framework  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Event utilities and scene control.

### Best TFWR uses
- Event utilities not cleanly handled by vanilla
- Support layer beside Extra Event Commands

### Default
Native event commands first.

---

## True Rune: Events
**Rank:** B+/A-  
**Category:** Branching event framework  
**Mode:** Runtime candidate  
**Primary purpose:** Complex branching, fragments, outcomes, and non-trivial event logic.

### Best TFWR uses
- Branching memory outcomes
- Multi-stage event logic
- Complex conditional narrative scenes

### Use when
Native events + CP conditions become unwieldy.

---

## MotionFramework
**Rank:** A-/B+  
**Category:** Custom Farmer animation  
**Mode:** Runtime candidate  
**Primary purpose:** Custom Farmer motion/animation sequences.

### Best TFWR uses
- Ritual animations
- Awakening poses
- Reconstruction ceremonies
- Special story motions

### Caution
Do not automatically use for timing-sensitive normal melee combat.

---

## Miihau Event Helper
**Rank:** A  
**Category:** Small VFX/event utility source  
**Mode:** Copy/adapt source when license permits  
**Primary purpose:** Reusable scene effects such as moving lights, motes, wisps, firefly-like effects, emotes.

### Best TFWR uses
- Memory wisps
- Ambient Echo motes
- Floating lights
- Short event VFX

### Preferred architectural use
Adapt small ideas into TFWR-native services instead of adding a whole dependency where possible.

---

# 6. Quests / progression presentation

## More Quests Framework (MQF)
**Rank:** A+  
**Category:** Quest/board framework  
**Mode:** Runtime candidate  
**Primary purpose:** Custom quests, boards, repeatable objectives, structured quest content.

### Best TFWR uses
- Werdon request board
- Echo jobs
- Optional side requests
- Repeatable combat/exploration requests
- Adventurer-style task boards

### Important restriction
MQF should NOT become the authoritative owner of:
- T1–T4 progression
- Reconstruction unlock state
- Signature unlocks
- weapon mastery
- mandatory investigation state

TFWR owns those systems.

---

## Dynamic Special Orders
**Rank:** B+  
**Category:** Special-order/progression reference  
**Mode:** Reference / situational runtime candidate  
**Primary purpose:** Dynamically structured special-order content.

### Best TFWR uses
- Reference for dynamic Reconstruction Requests
- Optional request systems

---

## Special Orders Extended
**Rank:** B  
**Category:** Special-order utilities  
**Mode:** Reference / situational candidate  
**Primary purpose:** Create/remove/manipulate special orders dynamically.

---

## Chronicler
**Rank:** B  
**Category:** Quest/progress/testing reference  
**Mode:** Read-only reference  
**Primary purpose:** Quest/progression patterns.

---

# 7. World spawning / anomalies / Resonance Events

## Farm Type Manager (FTM)
**Rank:** A  
**Category:** Dynamic world spawning  
**Mode:** Runtime candidate  
**Primary purpose:** Spawn monsters, objects, forage, environmental content, and dynamic world elements.

### Best TFWR uses
- Resonance Events
- Ambient monsters
- Memory anomalies
- Relic spawns
- Strange objects
- Dynamic world encounters

### Important restriction
Required progression should not rely on uncontrolled FTM randomness.

### Recommended split
TFWR C#:
- decides that a required encounter exists
- guarantees recovery
- grants authoritative rewards

FTM:
- makes ambient/random world content appear

---

## BETAS
**Rank:** S/A  
**Category:** Trigger / GSQ / world glue  
**Mode:** Runtime candidate  
**Primary purpose:** Express conditions and trigger actions using Stardew-native systems.

### Best TFWR uses
- Investigation clues
- World reactions
- Triggered anomalies
- Context-sensitive interactions
- Stardew activity hooks
- CP-friendly state exposure

### Strength
Excellent way to make TFWR feel integrated with Stardew instead of running everything through custom polling.

### Caution
Avoid using its JSON Harmony features when direct TFWR C# is cleaner and safer.

---

## Interactive Objects Framework
**Rank:** A-  
**Category:** Interactive world objects  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Physical interactive devices and world objects.

### Best TFWR uses
- Echo Resonator
- Interactive workshop machines
- Physical memory devices
- Ritual objects

---

## Furniture Framework
**Rank:** B  
**Category:** Furniture/world decoration  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Custom physical workshop/archive furnishings.

---

# 8. Maps / Memory Realm / dynamic locations

## Content Patcher
**Rank:** S  
**Category:** Content/world framework  
**Mode:** Core runtime dependency / integration  
**Primary purpose:** Patch maps, data, dialogue, assets, shops, events, and world content based on conditions.

### Best TFWR uses
- State-driven map changes
- Realm atmosphere changes
- Dialogue reactions
- Investigation clues
- Event assets
- Weapon/world presentation

### Architectural rule
TFWR C# owns state; CP presents it.

---

## Dynamic Map Tiles Extended (DMTE)
**Rank:** A-/B+  
**Category:** Dynamic maps  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Change map tiles/environment dynamically.

### Best TFWR uses
- Memory Realm transformations
- Progressive map corruption
- Opening/closing hidden routes
- Changing shrine states

### Use when
Content Patcher alone is not sufficient for dynamic tile behavior.

---

## Additional Mine Maps
**Rank:** B+  
**Category:** Mine/map system reference  
**Mode:** Reference / future runtime candidate  
**Primary purpose:** Expand or alter mine floor variety.

### Best TFWR uses
- Memory Realm mine-like progression
- Hidden deeper mine routes
- Resonant Depths research

---

## Persistent Mines
**Rank:** B+  
**Category:** Mine persistence reference  
**Mode:** Reference / future candidate  
**Primary purpose:** Preserve state in mine-like environments.

### Best TFWR uses
- Persistent Memory Realm state
- Resonant Depths
- Returning to previously changed floors

---

## Extra Map Actions
**Rank:** B/C  
**Category:** Map interaction utility  
**Mode:** Reference / situational candidate  
**Primary purpose:** Additional map-triggered behaviors.

### Default
Prefer native trigger actions / BETAS if equivalent.

---

## Map Fixer
**Rank:** DEV-A  
**Category:** Map debugging  
**Mode:** Dev tool  
**Purpose:** Detect/fix map issues.

---

## TileSense
**Rank:** DEV-S  
**Category:** Map inspection  
**Mode:** Dev tool  
**Purpose:** Inspect exact tile/property data at runtime.

### Best TFWR uses
- Tiled debugging
- Warp/action property validation
- Collision/property inspection
- Realm map debugging

---

## Data Layers
**Rank:** DEV-S  
**Category:** Map visualization  
**Mode:** Dev tool  
**Purpose:** Visualize map passability/data layers/regions.

### Relationship to TileSense
Use both:
- TileSense = exact tile/property inspection
- Data Layers = spatial overview

---

# 9. Collection / Archive / museum-style systems

## Custom Museum Framework (CMF)
**Rank:** A  
**Category:** Collection/display framework  
**Mode:** Runtime candidate  
**Primary purpose:** Custom museum-like displays and collection spaces.

### Best TFWR uses
- Echo Archive
- Forgotten Armory
- Physical weapon-history displays
- Memory exhibit rooms
- Tier-based physical collection presentation

### Important restriction
CMF should present/archive state, not own:
- weapon progression
- ownership
- mastery
- T1–T4 state

TFWR owns those.

---

## Stardew Aquarium
**Rank:** B reference  
**Category:** Collection UI/reference  
**Mode:** Read-only/copy only with GPL compliance  
**Primary purpose:** Collection/pagination/controller design ideas.

---

# 10. Rendering / sprites / weapon visuals

## Double Size Sprite (DSS)
**Rank:** A  
**Category:** High-resolution item rendering  
**Mode:** Runtime candidate pending POC  
**Primary purpose:** Use 2× resolution source sprites while preserving vanilla logical footprint.

### Best TFWR uses
- 32×32 weapon inventory sprites
- Better item visual fidelity

### Required proof-of-concept before adoption
Test one weapon in:
- inventory
- toolbar
- shop
- TFWR custom menu
- held idle
- swing
- special
- dropped item
- hold-up animation

### Architectural rule
If DSS solves only menu/icon surfaces, TFWR should still own held/swing scale, pivot, offset, and combat placement.

---

## TFWR custom weapon renderer
**Rank:** S internal  
**Category:** TFWR-native rendering  
**Mode:** Native implementation  
**Purpose:** Weapon-specific held/swing placement and animation identity.

### Best TFWR uses
- Per-weapon scale
- Per-weapon pivot
- attack offsets
- special-move positioning
- anime weapon silhouettes

---

## Sprites in Detail
**Rank:** B  
**Category:** High-resolution rendering reference/framework  
**Mode:** Backup candidate  
**Primary purpose:** Broader sprite-detail rendering.

### Use when
DSS cannot satisfy the required surfaces.

---

## Prismatic Valley Framework
**Rank:** C+  
**Category:** Color/prismatic rendering  
**Mode:** Reference / optional future candidate  
**Primary purpose:** Color and prismatic effects for supported item/entity types.

### Best TFWR uses
- Prismatic Memory items
- cosmetic color effects on supported assets

### Do not use as
Primary TFWR melee weapon glow/rendering solution.

---

## PoohCore
**Rank:** B  
**Category:** NPC logical sizing/dialogue utility  
**Mode:** Situational reference/runtime candidate  
**Primary purpose:** Truly oversized NPC dimensions / related behavior.

### Not an alternative to
DSS.

---

# 11. Combat frameworks and references

## Advanced Melee Framework (AMF)
**Rank:** A reference / COMPAT  
**Category:** Combat framework  
**Mode:** Read-only reference + compatibility target  
**Primary purpose:** Custom melee actions, specials, staged attacks, projectiles, action lifecycle.

### Best TFWR uses
- Study staged combat architecture
- Study special attack implementations
- Study projectile/action lifecycle

### Do not use as
TFWR's combat authority.

TFWR keeps:
- EnhancedActionService
- Perfect Block
- weapon-specific meters
- signature routing
- T1–T4 progression

---

## StarQuality
**Rank:** A reference / COMPAT  
**Category:** Weapon progression/combat reference  
**Mode:** Read-only reference + compatibility target  
**Primary purpose:** Weapon traits, per-target state, weapon XP, tooltips, proc/cooldown patterns.

### Best TFWR uses
- Per-target combat state patterns
- Tooltip architecture
- Weapon XP/progression implementation ideas
- Status/cooldown patterns

### Do not use as
TFWR's weapon progression system.

---

## Combat Overhaul
**Rank:** A reference / COMPAT  
**Category:** Combat overhaul  
**Mode:** Read-only reference + compatibility target  
**Primary purpose:** Heavy combat redesign, weapon identity, committed attacks, special handling.

### Best TFWR uses
- Combat feel research
- Weapon identity ideas
- Compatibility testing

### Caution
High overlap with TFWR melee/special systems.

---

## RandomStars
**Rank:** B reference / COMPAT  
**Category:** Custom weapon implementation reference  
**Mode:** Read-only reference + compatibility target  
**Primary purpose:** Custom weapon classes, animation, projectile, Harmony implementation patterns.

---

## Bonghits' Weapon Expansion
**Rank:** B reference  
**Category:** Weapon content-pack example  
**Mode:** Reference  
**Primary purpose:** Example content/data setup for expanded weapons.

---

## Scaling Weapons
**Rank:** COMPAT  
**Category:** Weapon progression compatibility target  
**Mode:** Test only  
**Purpose:** Ensure TFWR's weapon stats/progression coexist safely.

---

# 12. Ranged weapon frameworks

## Archery
**Rank:** B+ now / A if needed  
**Category:** Ranged weapon framework  
**Mode:** Runtime candidate / compatibility target  
**Primary purpose:** Custom bows/crossbows/ammo/projectiles/special attacks.

### Best TFWR uses
- Future anime bow
- Crossbow
- Dedicated ranged weapon archetype
- Custom ammo/projection system

### Cautions
- Large Harmony footprint
- Tool/input patching
- Controller behavior needs dedicated testing
- Source permissions restrictive

### Default
Do not install until a real TFWR ranged weapon is being implemented.

---

## Slingshot Framework
**Rank:** B  
**Category:** Projectile/slingshot framework  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Slingshot-oriented ranged systems.

### Compare against Archery when
A future TFWR ranged weapon is designed.

---

# 13. NPC schedules / dialogue / reactions

## Content Patcher + TFWR tokens
**Rank:** S default  
**Category:** Dialogue/world reaction  
**Mode:** Core integration  
**Primary purpose:** Conditional dialogue and world reactions based on TFWR state.

### Best TFWR uses
- NPC reactions to weapon tiers
- investigation dialogue
- post-reconstruction dialogue
- seasonal/contextual reactions

---

## Custom Schedule Keys
**Rank:** B+/A-  
**Category:** NPC schedules  
**Mode:** Runtime candidate  
**Primary purpose:** Conditional schedule variants.

### Best TFWR uses
- Clint appears at investigation location
- Emily appears for a clue
- Marlon appears during a memory hunt
- Memory Smith schedule states

### Default
Preferred over a heavier schedule framework when simple condition-based schedules are enough.

---

## True Rune: Schedule Director
**Rank:** B  
**Category:** Advanced NPC scheduling  
**Mode:** Runtime candidate  
**Primary purpose:** Complex priority-based runtime schedule decisions.

### Use when
Multiple competing schedule conditions become difficult to manage.

---

## True Rune: Dialogue Director
**Rank:** B+  
**Category:** Reactive dialogue  
**Mode:** Runtime candidate  
**Primary purpose:** Priority, rotation, usage quotas, runtime dialogue rules.

### Default
Use CP + TFWR tokens first.

---

# 14. Audio

## Dynamic Music
**Rank:** A-/B+  
**Category:** Dynamic music  
**Mode:** Runtime candidate / reference  
**Primary purpose:** State/location/context-dependent music behavior.

### Best TFWR uses
- Memory Realm music layers
- Resonance Event music
- awakening state music
- boss encounter transitions

---

## SAAT
**Rank:** B  
**Category:** Audio framework/reference  
**Mode:** Reference / runtime candidate if exact feature requires it  
**Primary purpose:** Extended audio handling.

---

## Positional Audio
**Rank:** B  
**Category:** Spatial audio  
**Mode:** Runtime candidate / reference  
**Primary purpose:** Location-aware sound sources.

### Best TFWR uses
- whispering memory objects
- shrine ambience
- off-screen supernatural audio cues

---

# 15. Source libraries / copy-adapt candidates

## Pathoschild/StardewMods
**Rank:** S  
**Category:** Engineering source library  
**Mode:** Copy/adapt/reference  
**License:** MIT  
**Primary purpose:** High-quality SMAPI architecture patterns.

### Best TFWR uses
- BaseIntegration
- safe optional integrations
- Harmony patch structure
- cached conditions
- console commands
- tile/map helpers
- testing patterns
- fail-open design
- Content Patcher integration patterns

### Codex rule
This should be one of the first source libraries inspected when writing reusable TFWR infrastructure.

---

## sophiesalacia/StardewMods
**Rank:** A source library  
**Category:** Engineering/event source library  
**Mode:** Copy/adapt/reference  
**License:** MIT

### Most useful subprojects
#### SophieShared
- event-hook registration
- command registration
- Harmony scaffolding
- shared logging/helpers
- Content Patcher API handling

#### Calcifer
- trigger zones
- stat milestone triggers
- CG event command patterns
- token patterns
- event/tween structure

#### MapLightingUtil
- dynamic light handling

#### WildHavenCSharp
- teleport/network patterns

#### CommunityUpgradeFramework
- progression/menu/request pattern reference

### Low-value parts
Do not create separate TFWR inventory entries for every tiny utility inside the repo unless a task specifically needs it.

---

## SpaceCore source
**Rank:** A source reference  
**Category:** Framework internals  
**Mode:** Read-only reference  
**Purpose:** Learn extension patterns and understand existing TFWR dependency behavior.

---

## Expanded Preconditions Utility / SeededRandom patterns
**Rank:** A- reference  
**Category:** Deterministic RNG/reference  
**Mode:** Reference / copy only after license confirmation  
**Primary purpose:** Seeded deterministic selection patterns.

### Best TFWR uses
- daily/weekly deterministic anomalies
- reproducible clue selection
- save-safe seeded outcomes

### Default
Prefer TFWR-native deterministic RNG service after studying the pattern.

---

# 16. Development / QA tools

These belong in `modtool/`, not TFWR runtime dependencies.

## StardewLocalAPI
**Rank:** DEV-S  
**Purpose:** General dev workstation for event/dialogue/audio/content testing, coordinates, exports, and custom development helpers.

**Best TFWR uses**
- event testing
- dialogue testing
- audio testing
- Content Patcher data inspection/export
- coordinate work
- custom TFWR dev panel

---

## True Rune: Modder Toolkit
**Rank:** DEV-S  
**Purpose:** Debug portraits, NPCs, schedules, flags, events, and force-trigger state.

---

## Combat Dummy
**Rank:** DEV-S  
**Purpose:** Measure combat damage, DPS, max hit, knockback, and balance.

---

## TileSense
**Rank:** DEV-S  
**Purpose:** Exact tile/property inspection.

---

## Data Layers
**Rank:** DEV-S  
**Purpose:** Spatial visualization of map data/passability/layers.

---

## Debug Mode
**Rank:** DEV-S  
**Purpose:** General Stardew/SMAPI debugging.

---

## Map Fixer
**Rank:** DEV-A  
**Purpose:** Map validation/repair workflow.

---

## Dependency Graph
**Rank:** DEV-A  
**Purpose:** Inspect dependency relationships.

---

## Multiplayer Mod Checker
**Rank:** DEV-A  
**Purpose:** Verify multiplayer mod parity/compatibility.

---

## Internationalization QA
**Rank:** DEV-A  
**Purpose:** Find missing/incorrect localization coverage.

---

## Item Checker
**Rank:** DEV-A/B  
**Purpose:** Locate/test item state and useful GSQs during development.

### Do not use as
A TFWR runtime progression dependency.

---

## SDV NPC Sheet Generator
**Rank:** DEV-A  
**Purpose:** Generate vanilla-compatible NPC sprite sheets and action frames.

### Best TFWR uses
- Werdon
- event actors
- temporary NPC placeholders
- custom action sheets

### Platform note
Windows-oriented packaged tool; primarily use on the Windows dev machine.

---

## Cutscene Maker for Content Patcher
**Rank:** DEV-A  
**Purpose:** Author/test event scripts more quickly.

---

## Dialogue Tester
**Rank:** DEV-A/B  
**Purpose:** Test dialogue during development.

---

## Events Editor
**Rank:** DEV-C  
**Purpose:** Simple scratch event runner.

### Default
Fallback only; StardewLocalAPI + Cutscene Maker + modern debugging tools are preferred.

---

# 17. Compatibility targets

Codex should not add these as TFWR dependencies merely to "support" them.

Instead, test TFWR against them where relevant.

| Mod/framework | Why it matters |
|---|---|
| Combat Overhaul | Direct combat/special overlap |
| Advanced Melee Framework | Melee special/action overlap |
| StarQuality | Weapon progression/stats/tooltips overlap |
| Scaling Weapons | Weapon stat progression overlap |
| RandomStars | Custom weapon/render/combat patches |
| Archery | Ranged/input overlap |
| Slingshot Framework | Projectile/ranged overlap |
| Lookup Anything | Item/NPC hover integration |
| Stardew Access | Accessibility interoperability |
| Star Control | Controller/radial integration |
| Quest Journal | Quest UI coexistence |
| Quest Helper | Hint/quest coexistence |
| Automate | Machine/Resonator interoperability |
| Item Extender | Weapon/item rendering/tooltip behavior |
| Solid Foundations | Building/world compatibility if relevant |
| Custom Warp Locations | Warp/location interoperability if relevant |

---

# 18. Legacy / reference-only frameworks

Keep only as historical or compatibility references.

## Expanded Preconditions Utility
Legacy compatibility/reference; do not design new TFWR systems around it unless specifically needed.

## Mail Framework Mod
Legacy/compatibility only; modern Stardew systems preferred.

## Dynamic Game Assets
Legacy architecture/reference only; modern 1.6 data systems preferred.

## Json Assets
Compatibility reference for old content; not preferred for new TFWR architecture.

## PyTK Lite
Legacy reference only.

## Extra Map Layers / Custom Tile Sheet
Mostly historical references under Stardew 1.6.

## Some Old Things
Useful for migration/backward compatibility research.

---

# 19. Reject / remove from active design consideration

## Arbitrary Tilesheet Access
**Decision:** REJECT  
Modern asset handling supersedes it.

## ExtendedLootTables
**Decision:** REJECT  
Too weak/primitive for TFWR required progression and deterministic recovery.

## Mod Template Builder
**Decision:** REJECT  
TFWR already exists and uses ModBuildConfig.

## Museum Donation Checker
**Decision:** REJECT / link-only  
Too narrow to justify a dependency.

## Custom Visual Event Command
**Decision:** REJECT  
Redundant with stronger event/cinematic tools.

## T's Content Patcher Toolkit
**Decision:** REJECT from active toolbox  
Lower value than current dev stack.

## HD Sprites Redux
**Decision:** REJECT for TFWR weapon rendering  
Far broader than the focused 32×32 requirement.

## Custom Companions for Lostvayne clone
**Decision:** REJECT for clone architecture  
Use a TFWR-native lightweight clone controller instead.

## Scaling Weapons as progression authority
**Decision:** REJECT as architecture  
Compatibility target only.

## Demiacle Classes / custom ORM
**Decision:** REJECT  
Unnecessary complexity / poor fit.

## Explosive Grabber
**Decision:** REJECT  
Too narrow.

## Colored Junimo Crop Levels
**Decision:** REJECT  
Too narrow.

## SDVUtilities
**Decision:** Signature/namespace reference only; not usable as a normal source library.

---

# 20. Default solution stacks by feature

These are starting points, not mandatory dependency bundles.

## A. Custom TFWR UI
1. TFWR C#
2. StardewUI Continued
3. Content Patcher only where asset/state presentation helps
4. StardewLocalAPI for testing

Avoid adding Theme Manager unless third-party themes are a requirement.

---

## B. Memory Realm / hidden supernatural route
Start with:
1. TFWR C# authoritative state
2. Content Patcher
3. BETAS
4. Extra Event Commands

Then add only if the design needs them:
- FTM for dynamic monsters/anomalies
- DMTE for runtime tile changes
- MotionFramework for custom ritual animations
- StardewCGEvents for major visions
- Additional Mine Maps / Persistent Mines ideas for mine-like structure

Important:
Do not design the Realm around a dependency bundle.
Design the experience first using the smallest applicable subset of approved tools.

---

## C. Reconstruction / Investigation system
1. TFWR Investigation/Reconstruction services
2. Content Patcher + TFWR tokens
3. BETAS for world triggers/conditions
4. More Quests Framework only for quest/board presentation where useful
5. StardewUI for Investigation Ledger

---

## D. Echo Archive
1. TFWR Archive Service
2. Custom Museum Framework for physical displays
3. StardewUI for detailed catalog
4. Furniture Framework only if workshop furnishing requires it

---

## E. Resonance Events
1. TFWR Resonance Event Service
2. BETAS
3. Farm Type Manager for ambient/random spawned content
4. Content Patcher for visual/world changes
5. Dynamic Music or Positional Audio if the experience needs audio escalation

---

## F. Awakening cinematic
1. Native Stardew event
2. Extra Event Commands
3. MotionFramework only if custom Farmer animation is necessary
4. StardewCGEvents only for a true CG/vision sequence
5. Miihau-derived TFWR VFX for wisps/lights

---

## G. 32×32 weapon presentation
1. DSS proof-of-concept
2. TFWR custom held/swing renderer
3. Sprites in Detail only if DSS fails a required surface

---

## H. New ranged anime weapon
1. Define exact weapon behavior first
2. Compare Archery vs Slingshot Framework
3. Audit controller/input/Harmony conflicts
4. Ask user before adding either dependency

---

# 21. Codex response template when choosing tools

When Codex determines that one or more toolbox items could help a request, report the decision in this structure:

## Toolbox scan

**Requested feature:**  
[short description]

**Relevant candidates found:**
1. [Candidate] — [rank] — [why it fits]
2. [Candidate] — [rank] — [why it fits]
3. [Candidate] — [rank] — [why it fits]

**Best fit:**  
[chosen option]

**Why:**  
[exact reasons]

**TFWR-native alternative:**  
[brief explanation]

**Dependency required?**  
Yes / No

**If yes:**
- Feature enabled:
- Why native code is worse:
- Stardew/SMAPI compatibility:
- Steam Deck/Linux:
- Controller:
- Multiplayer:
- Performance:
- Harmony/input risk:
- Maintenance risk:
- Compatibility risk:
- License:
- Fallback without dependency:

**Implementation mode:**  
TFWR-native / runtime dependency / optional integration / copy-adapt / reference-only / dev-tool / compatibility-target

If dependency is new, wait for user approval.

---

# 22. Folder placement rules

## `modtool/`
Put runnable development utilities here.

Recommended:

```text
modtool/
├── combat/
│   └── CombatDummy/
├── debug/
│   ├── TrueRuneModderToolkit/
│   ├── DebugMode/
│   └── ItemChecker/
├── maps/
│   ├── TileSense/
│   ├── DataLayers/
│   ├── MapFixer/
│   └── PlayerCoordinates/
├── events/
│   ├── StardewLocalAPI/
│   ├── CutsceneMaker/
│   ├── DialogueTester/
│   └── legacy/
│       └── EventsEditor/
├── compatibility/
│   ├── DependencyGraph/
│   └── MultiplayerModChecker/
├── i18n/
│   └── InternationalizationQA/
└── art/
    └── NPCSheetGenerator/
```

## `references/`
Put source libraries, framework candidates, code examples, architecture research, and compatibility notes here.

```text
references/
├── engineering/
├── combat/
├── ui/
├── quests/
├── events/
├── world/
├── maps/
├── rendering/
├── audio/
├── integrations/
└── audit/
```

## Raw archives
Do not track giant ZIPs/decompiled binaries in Git.

Suggested ignored locations:

```text
modtool/_downloads/
references/_archives/
```

Track notes, source where licensing permits, API interfaces, manifests, audit conclusions, and links instead.

---

# 23. Source reuse / licensing rules

Codex must distinguish between:

## Safe copy/adapt candidates
Examples:
- Pathoschild/StardewMods — MIT
- sophiesalacia/StardewMods — MIT
- specifically permissive source identified in the audit

## Reference-only or permission-required
Examples:
- Archery source
- Theme Manager
- Events Editor
- decompiled binaries without an explicit permissive license
- restrictive Nexus releases

Rules:
1. Never assume decompiled code can be copied.
2. Never assume Nexus source permissions are permissive.
3. If uncertain, use architecture/pattern understanding only.
4. Preserve required attribution/license notices.
5. Ask the user before introducing GPL/copyleft obligations into TFWR source.

---

# 24. High-priority shortlist

If Codex only has time to scan a few items, use this order:

1. Pathoschild/StardewMods
2. StardewUI Continued
3. Content Patcher
4. SpaceCore
5. BETAS
6. Extra Event Commands
7. More Quests Framework
8. Farm Type Manager
9. StardewLocalAPI
10. Custom Museum Framework
11. Double Size Sprite
12. sophiesalacia/StardewMods
13. MotionFramework
14. StardewCGEvents
15. AMF / StarQuality / Combat Overhaul as combat references

---

# 25. Final rule

The purpose of this toolbox is:

> **Before TFWR invents a new subsystem, first check whether the Stardew modding ecosystem already provides a clean, compatible, controller-friendly, Steam-Deck-friendly way to do it.**

But the opposite rule is equally important:

> **Do not force TFWR through a framework just because a framework exists.**

The best solution is the smallest architecture that:
- fits the requested feature;
- preserves TFWR ownership of core state;
- feels native to Stardew;
- remains compatible;
- is maintainable;
- and performs well on Steam Deck.

