# Lab 03 Evaluation

Automated proxy result: **PROMISING_HYBRID**.

Overall: baseline **8.81** -> hybrid **9.29** (**+0.48**).

Hybrid dimension averages:
- silhouette fidelity: 10.00
- palette/material resemblance: 8.77
- pattern continuity: 8.07
- motif location: 8.80
- four-view coherence: 9.87
- Stardew readability: 9.53
- junk control: 9.95

Compared with Lab 02 Full PT, Lab 03 is +0.11 overall while recovering most cleanliness/coherence losses. The strongest architecture is therefore source-pixels-first with selective PT feature deltas, not wholesale PT rendering.
