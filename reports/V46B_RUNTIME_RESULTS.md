# V4.6B Runtime Results

User runtime evidence found severe lower-body detachment with the original
Scale-2 anchor. The generated custom Pants layer was 64 display pixels too low.
The shared contract has been corrected from `BodyPosition (0,-2)` to `(0,30)`;
all six appearances require a fresh runtime test.

| Appearance | Idle | Walk | Run | Tools | Sit | Horse | Equip/recolor | Promotion |
|---|---|---|---|---|---|---|---|---|
| Harborline Fitted Trousers | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |
| Ridgeline Panel Trousers | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |
| Cedar Day Shorts | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |
| Bramble Cuff Shorts | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |
| Willow A-Line Skirt | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |
| Heather Pleat Skirt | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | RETEST REQUIRED | EXPERIMENTAL |

Update this report only from observed game behavior using
`reports/V46B_RUNTIME_TEST_CHECKLIST.md`.

The pre-correction failure cannot be counted as evidence for or against the
corrected runtime contract.

