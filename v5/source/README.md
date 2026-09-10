# Authored-source path (preferred visual trunk)

Good authored source art is the construction authority. Silhouettes come from
real assets kept pixel-exact; the generator recolours, combines and decorates
them under compatibility rules. It does not invent garment silhouettes.

    ingest.py    read-only scan of `generator conent` -> what each pack declares
    pngread.py   PNG reader wide enough for the library (adds sub-byte palette)
    audit.py     what each appearance actually draws, per direction
    semantic.py  the family's authored value vocabulary; our roles on top of it
    decompose.py families, base + delta dissection, the reconstruction test
    library.py   runtime: SourceBase, SourceComponent, provenance
    render.py    recolour without redrawing; Fashion Sense atlas; credits

Build:  tools/build_source_families.py -> source_catalog/families.json
PoC:    tools/source_poc.py, tools/build_source_poc_pack.py

## Status of the procedural generator

`v5/ag.py`, `v5/grammar.py`, `v5/library/*` and the projection/architecture
machinery are NOT deleted and NOT deprecated. They move to support and
research status:

  * QC and measurement (`tools/analyze_*`, `qc_*`) apply to both paths and
    remain the shared quality instrumentation.
  * Slot / Family / Architecture / scoped variables, deterministic seeding,
    legality and compatibility rules, style tags, semantic occupancy, the
    complexity budget, palettes and tone profiles, the Fashion Sense exporter
    and the QC Bridge are all reused by this path rather than replaced.
  * Procedural silhouette construction is no longer the source of finished
    garment shapes. It stays available for research and as a fallback where no
    authored source exists.

## The rule the reconstruction test enforces

A dissection is only trusted if base + delta rebuilds the original source
byte-for-byte. A variant that cannot be rebuilt is not modelled as a
decoration: it is promoted to its own base and kept pixel-exact. See
`decompose.reconstruct_report`.
