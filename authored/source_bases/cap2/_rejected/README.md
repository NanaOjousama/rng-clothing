# Rolled back — built on a false `front_emblem` classification

The region at Front x8-11, y10 was classified as a decorative emblem because it
is mathematically enclosed: a 4-cell island of brighter values surrounded by a
single darker value. That test was structurally correct and semantically wrong.

**Those cells are the lit top surface of the VISOR seen head-on.** Evidence:

* they sit inside the rows 9-12 band, which is the visor; the band is dark at
  its edges and lit through its centre, which is how a peak curving toward the
  viewer is shaded
* in the worn capture they land directly above the farmer's eyes, on the
  visor's front face -- not on any crown panel
* the profile view carries the same bright values (steps 5-6) on the part of
  the hat that projects past the crown's own edge, i.e. the peak
* Cap 1 has the identical structure at the identical cells. That was read as
  "the author reuses this decoration on two constructions". It is the opposite:
  two caps sharing a structural feature is exactly what one expects, and it was
  evidence AGAINST it being a decoration

Everything downstream of the misclassification is void:

    motifs.json          a starter set for a zone that does not exist
    emblem_grammar.json  a 4x3 "front panel" that is really visor surface
    compatibility.json   base x emblem rules for a non-existent component
    manifest.json        base-with-hole + component decomposition
    family.json          promotion notes citing emblem axes

The palette-role finding is NOT void and has been carried forward: tinting
collapses the visor-to-outline separation from 24 to 13. That measurement was
about structural roles and stands on its own.

Kept for the record. Nothing here should be used.
