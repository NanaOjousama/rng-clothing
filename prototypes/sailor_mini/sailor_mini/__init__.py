"""Mini Sailor generator prototype — SAILOR_TOP / CLASSIC_SQUARE_FLAP only.

Isolated proof of concept. Imports nothing from `generator/`, `rngc/` or `tools/`.

Pipeline:
    seed -> resolve -> dependency filter -> ResolvedSpec
         -> ArchitecturePlan (construction geometry)
         -> RenderPlan (art grammar: edges, contrast, occlusion, trim)
         -> direction rendering (front / side / back / left=mirror(side))
         -> batch previews
"""

__version__ = "0.1.0-prototype"
FAMILY = "SAILOR_TOP"
ARCHITECTURE = "CLASSIC_SQUARE_FLAP"
