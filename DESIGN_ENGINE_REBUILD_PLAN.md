# Design Engine Rebuild Plan

## Current decision

Generation remains stopped. V3/V4/V5 runtime and renderer work is preserved, but the old autonomous concept vocabulary is no longer trusted as a creative source.

## Target data flow

```text
curated reference evidence (offline research only)
    -> project-owned garment grammar ID
    -> project-owned palette story ID
    -> semantic recipe
    -> stable article adapter / renderer
    -> installed-Farmer composite
    -> structural, quality, and diversity gates
    -> human approval
```

The runtime generator begins at garment grammar and palette story. It never reads third-party pixels.

## Implementation stages after foundation review

1. **Schema integration** — add `garmentGrammarId`, `topologyGroup`, structural fingerprint, palette story ID, and protected semantic regions to recipes without changing rarity.
2. **Grammar validator** — require all structural fields, forbid coordinates and vague free-text construction, validate article/sleeve/runtime compatibility, and detect duplicate fingerprints.
3. **Palette selector** — choose stories by role compatibility and batch distance; enforce value and accent budgets; stop muted military fallbacks from dominating.
4. **Adapter mapping** — map each grammar's explicit structure to existing safe article components. Unsupported structure fails closed instead of degrading silently into a fitted top.
5. **Farmer compositor** — use installed Farmer 1.6.15 frames and proven Fashion Sense placement, output exact gameplay front/right/back/left plus flat/no-shading diagnostics.
6. **Diversity gate** — compare fingerprints, worn silhouettes, openings, focal topology, side/back carriers, and palette stories against accepted history and batch siblings.
7. **Human review** — label-blind article/readability/beauty review with `ACCEPT`, `REWORK`, or `REJECT`. No output batch until this stage exists.
8. **Only then, controlled proof** — a small Common/Uncommon/Rare batch across distant topology groups. Legendary/Mythic remain out of scope.

## Fail-closed behavior

- Unsupported grammar feature: reject recipe; do not substitute generic jacket geometry.
- Farmer composite convergence: reject even when semantic distance passes.
- Missing side/back construction: reject before rendering a batch.
- Palette story collision: reselect palette only if structure already passed.
- Weak beauty: human rework/reject; adding decoration is not an automatic repair.

## Required tooling before generation resumes

- JSON schema for both reference records and garment grammars;
- structural fingerprint/duplicate report;
- palette value/role validator;
- installed-Farmer compositor with verified direction labels;
- pairwise silhouette and construction report;
- persistent accepted/rejected design registry;
- regression suite proving vanilla renderer, FS anchors, direction mapping, and native sleeve contract remain unchanged.

## Known limitations to preserve honestly

- The upper-body Farmer envelope limits true width and length changes.
- Native sleeves are runtime-safe but constrain volume silhouettes.
- Coordinated FS layers are proven for the frozen hoodie contract, not as a universal solution.
- True long coats, independent lower garments, and moving tails remain unproven/archived.
- A 16×16 logical Shirt can improve collar, opening, panels, pockets, trim, and optical mass, but cannot guarantee a fundamentally different body outline.
- Static Farmer composites do not establish motion safety.

## Review recommendation

Approve the taxonomy and weak-family list before implementing. The most valuable next reference work is not another military pack: add henley, polo, overshirt, moto, modern streetwear, sportswear, and construction-led cyber examples. Then implement the gate/tooling and run a deliberately small proof across distant topology groups.

## Stop declaration

No garment, texture, preset, contact sheet, Legendary, or Mythic output was generated in this recovery phase.
