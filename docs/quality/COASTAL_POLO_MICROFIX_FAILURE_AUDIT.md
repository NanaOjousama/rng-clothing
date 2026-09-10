# Coastal Knit Polo Micro-Fix Failure Audit

Status: **AUDIT COMPLETE — NO ART CHANGES**

The failed human review is supported by the pipeline evidence. The before and after files are distinct and contain 32 changed logical pixels, but alpha/silhouette geometry did not change anywhere. Most changes are local role/color substitutions. The rear collar's intended row-0 mask change was removed by `polish_upper_frames`; the palette adapter later made those same row-0 cells different only because they retained a `Trim` fabric assignment.

## 1. Exact final logical pixel diff

Coordinates use zero-based `(x,y)` within each 16×16 logical direction.

### Front

Changed pixels: **0**. The front is byte-identical.

### Right

Changed pixels: **10**.

| Coordinate | Old role / color | New role / color |
|---|---|---|
| `(6,1)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |
| `(7,1)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.LIGHT` / `#859FA0FF` |
| `(9,1)` | `PrimaryFabric.DEEP_CREASE` / `#20323DFF` | `PrimaryFabric.SHADOW` / `#69888DFF` |
| `(6,2)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |
| `(8,2)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.BASE` / `#55777CFF` |
| `(7,3)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(9,3)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(8,4)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(9,4)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.SHADOW` / `#69888DFF` |
| `(9,5)` | `PrimaryFabric.BASE` / `#90B4B5FF` | `PrimaryFabric.SHADOW` / `#69888DFF` |

### Back

Changed pixels: **12**.

| Coordinate | Old role / color | New role / color |
|---|---|---|
| `(5,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(6,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(7,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(8,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(9,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(10,0)` | `PrimaryFabric.EXTERIOR_CONTOUR` / `#14222BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(5,1)` | `Trim.BASE` / `#55777CFF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |
| `(6,1)` | `Trim.BASE` / `#55777CFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(7,1)` | `Trim.BASE` / `#55777CFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(8,1)` | `Trim.SHADOW` / `#3E5A63FF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(9,1)` | `Trim.SHADOW` / `#3E5A63FF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(10,1)` | `Trim.SHADOW` / `#3E5A63FF` | `PrimaryFabric.SHADOW` / `#69888DFF` |

### Left

Changed pixels: **10**.

| Coordinate | Old role / color | New role / color |
|---|---|---|
| `(6,1)` | `PrimaryFabric.DEEP_CREASE` / `#20323DFF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |
| `(8,1)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(9,1)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.SHADOW` / `#69888DFF` |
| `(7,2)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.BASE` / `#55777CFF` |
| `(9,2)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.SHADOW` / `#69888DFF` |
| `(6,3)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `Trim.SHADOW` / `#3E5A63FF` |
| `(8,3)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(6,4)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |
| `(7,4)` | `PrimaryFabric.STRUCTURAL_EDGE` / `#29404BFF` | `PrimaryFabric.BASE` / `#90B4B5FF` |
| `(6,5)` | `PrimaryFabric.BASE` / `#90B4B5FF` | `PrimaryFabric.LIGHT` / `#ABC5C3FF` |

## 2. Stage-by-stage diff

The reconstructed pre-fix endpoint exactly matches the archived before atlas. The reconstructed post-fix endpoint exactly matches the archived after atlas.

### Right

| Stage | Changed cells | Coordinates |
|---|---:|---|
| Carrier/base input | 0 | none |
| After V3 component compilation | 12 | `(6,1) (7,1) (9,1) (6,2) (7,2) (8,2) (7,3) (8,3) (9,3) (8,4) (9,4) (9,5)` |
| After `polish_upper_frames` | 12 | same 12 coordinates |
| After `soften_shared_rear_neck` | 12 | same 12 coordinates |
| After material/palette adapter | 10 | `(7,2)` and `(8,3)` collapse to the same resolved output; remaining coordinates match the final list |
| Final logical atlas | 10 | same as material/palette adapter |

The requested side change first exists after **V3 component compilation**. Polish does not remove its coordinate footprint. The palette adapter makes two changed mask cells resolve to their prior final colors, leaving ten final color changes. However, alpha never changes, so there is no new collar silhouette—only shade/fabric-role changes inside the old silhouette.

### Back

| Stage | Changed cells | Coordinates |
|---|---:|---|
| Carrier/base input | 0 | none |
| After V3 component compilation | 9 | `(5,0) (6,0) (7,0) (8,0) (9,0) (10,0) (5,1) (8,1) (9,1)` |
| After `polish_upper_frames` | 3 | `(5,1) (8,1) (9,1)` |
| After `soften_shared_rear_neck` | 3 | same 3 coordinates |
| After material/palette adapter | 12 | row 0 `x=5..10` and row 1 `x=5..10` |
| Final logical atlas | 12 | same as material/palette adapter |

The requested back change first exists after **V3 component compilation**. `polish_upper_frames` removes all six row-0 mask/shade changes. The palette adapter later makes row 0 look different only because the cells retained `Trim` fabric ownership; it resolves the unchanged exterior-contour mask to `Trim.SHADOW`. This is a color-role substitution, not a surviving collar-shape displacement.

## 3. Before/after source verification

The QC sheet did not use the same atlas twice, cached aliases, a wrong atlas, or duplicate Farmer outputs.

| Evidence | Path | SHA-256 |
|---|---|---|
| Before logical atlas | `output/hybrid-v3-phase2/polo-microfix/before-shirt.png` | `3a0da5ed0e94cd8cdf74f919bc08858861f8790d18c21772a6c16d2650f987ad` |
| After logical atlas | `output/hybrid-v3-phase2/polo-microfix/after-shirt.png` | `ad26feecd9e9ff4e8c93b761e23b43e392c6d613673c236b7d2d0c3efa854afc` |
| Before Farmer composite | `output/hybrid-v3-phase2/polo-microfix/farmer-before.png` | `66d7de20039517024306cf7f86aab3a55807e2a261a384105955d7f3a6777bc6` |
| After Farmer composite | `output/hybrid-v3-phase2/polo-microfix/farmer-after.png` | `8c64f9c8fade6b3cd0289dca6631d15a4889c19cfd46d5d8cf02a82ed5ed4b14` |
| QC sheet | `output/comparisons/HYBRID_V3_PHASE2_COASTAL_POLO_MICROFIX_QC.png` | `2f068d3712d21b6973ec9047399bcea3af7e402907fc646ebd02824fd886cfb8` |

The before/after atlas paths differ, their hashes differ, the Farmer paths differ, and their hashes differ. The audit rebuilt both endpoint textures independently and matched both archived atlas pixel arrays exactly.

## 4. Back collar audit

Old explicit collar band:

`(5,1) (6,1) (7,1) (8,1) (9,1) (10,1)`

New intended explicit collar band:

`(5,0) (6,0) (7,0) (8,0) (9,0) (10,0)`

New under-collar fabric row:

`(5,1) (6,1) (7,1) (8,1) (9,1) (10,1)`

Semantic coordinate displacement: **1 logical pixel upward** (`y=1` to `y=0`).  
Alpha/silhouette displacement: **0 pixels**. The same row-0 cells were already opaque exterior contour.

The component compiler therefore requested a one-row role shift, but polish removed the row-0 mask difference. At final output, row 0 is only recolored from `PrimaryFabric.EXTERIOR_CONTOUR` to `Trim.SHADOW`; no collar alpha mass moved upward. The visible change is primarily cosmetic color reassignment, explaining why human review saw no convincing new placement or under-collar gap.

## 5. Right collar audit

Old explicit collar cells:

`(8,1) (9,2)`

New intended five-cell folded wedge:

`(7,1) (8,1) (8,2) (9,2) (9,3)`

The new compiler also reassigned a surrounding upper-side knit plane in rows 1–5. Its region ledger consequently lists 17 collar-component-owned cells, but only five are the intended wedge.

Silhouette/alpha change: **none**. The new wedge occupies already-opaque pixels. It is expressed only with light/base/shadow roles, and the surrounding carrier contours remain. The request for a cleaner folded-collar *silhouette* was therefore not implemented; only its internal colors were changed.

## 6. Right torso dark region

The pre-fix dark upper-middle region consists of these final cells:

`(5,1) (6,1) (7,1) (9,1) (10,1) (6,2) (8,2) (9,2) (10,2) (7,3) (9,3) (8,4) (9,4)`

Ownership:

- `(9,2)` is the old explicit collar cell (`Trim.SHADOW`).
- The other 12 dark cells originate in the inherited V5/HD carrier/permanent shade field. The BODY compiler records them under the broad `silhouette` ledger but does not create those dark values.

The micro-fix changes/lightens nine of those inherited dark cells plus one lower base cell `(9,5)`. It leaves `(5,1)`, `(10,1)`, and `(10,2)` dark, and it introduces a `Trim.SHADOW` at `(9,3)`. Because the surrounding inherited dark carrier structure remains and alpha is unchanged, the side still reads as substantially the same dark cluster at Farmer scale.

## 7. Verdict

| Requested fix | Verdict | Evidence |
|---|---|---|
| Back collar | **IMPLEMENTED THEN OVERWRITTEN** | Component compilation moves the role band up one row, but polish removes all six row-0 mask differences. Final output reintroduces only a trim recolor on unchanged alpha. |
| Right collar | **NOT IMPLEMENTED** | Five-cell internal role wedge exists, but collar silhouette/alpha displacement is zero; inherited surrounding contour remains. |
| Right torso | **IMPLEMENTED** | Ten final role/color changes survive, but the scope is insufficient: three major inherited dark cells and surrounding contour structure remain, so human-scale appearance changes little. |

This audit does not claim visual improvement. The prior micro-fix failed its human visual goal despite producing technically different files.

## 8. Audit artifacts

- Stage diff image: `output/comparisons/COASTAL_POLO_STAGE_DIFF_AUDIT.png`
- Machine-readable evidence: `output/hybrid-v3-phase2/polo-microfix/failure-audit-data.json`

No art, compiler, renderer, atlas, pack, recipe, or runtime file was changed by this audit.
