"""RNG Clothing V5 — Phase 1 architecture proof.

Pipeline: authored GarmentPlan -> compose -> colorize -> validate -> preview/export.

NO-POLISH INVARIANT
-------------------
Every opaque output cell traces to the authored blank or to one authored piece
(``RoleImage.src``). No module in this package inspects neighbouring cells to
shade, smooth, outline, reinforce or otherwise "improve" a sprite. If the art
is wrong, fix the authored data. ``rngc/tests/test_phase1.py`` enforces this.

This package imports nothing from the legacy ``generator`` package.
"""

__version__ = "5.0.0-phase1"
