# Structural vs Decorative Rules

## Permanent classification

Structural properties define what the garment is:

- silhouette, shoulder, neckline, collar, lapel;
- opening/closure, torso mass, layering;
- waist, hem, sleeve, cuff;
- pocket/panel topology;
- asymmetry;
- side and back reconstruction.

Decorative properties style an already readable garment:

- palette story;
- motif, insignia socket, small accent;
- trim and piping when not silhouette-defining;
- fabric pattern or texture;
- shading and highlights.

Some features are contextual. A broad sailor collar is structural; a one-pixel stripe on it is decorative. A bomber's ribbed waist band is structural; a contrast color on that band is decorative. A hoodie hood is structural; lining color is decorative.

## Diversity law

Structural diversity is evaluated first and has veto power.

1. Build a structural fingerprint from all structural fields.
2. Compare candidate against every accepted garment and batch sibling.
3. Ignore name, rarity, theme label, palette, motif, and shading during the first comparison.
4. Reject when the Farmer composite still reads as the same article/construction.
5. Only after structural acceptance compare palette and surface composition.

A decorative difference cannot rescue:

- the same fitted torso with a new center stripe;
- the same short jacket with recolored panels;
- the same collar/opening/hem with another motif;
- a front-only distinction that disappears on side/back views;
- an article identity that exists only in its recipe name.

## Minimum distinctness

For different grammars, require differences on at least four of these ten visible axes: outer silhouette, shoulder, neckline/collar, opening, torso proportion, waist/hem, layering, dominant construction gesture, side reconstruction, back reconstruction. At least two differences must be in the first six.

For the same grammar family, variants may share more topology, but must change a real subtype feature such as fitted vs relaxed mass, pullover vs zip opening, cardigan vs crew closure, or formal vs utility pocket/hem logic. Color-block changes alone are variants, not new structural designs.

## Surface composition after structure

An accepted structure gets one primary focal system and zero to two supports, constrained by garment topology. Motifs remain connected clusters; trim wraps or terminates intentionally; patterns use bounded regions. Shading follows form last.

## Protected semantics

`ExteriorContour`, `BodyCoverage`, `StructuralSeams`, `ArticleOpening`, `SignatureSilhouette`, and required direction carriers are protected from palette/customization changes. Future customization may alter fabric roles, trims, and sockets without erasing article identity.

## Validation response

- Structural duplicate: reject or merge grammar.
- Weak worn article read: revise adapter/grammar, not surface decoration.
- Side/back collapse: revise directional reconstruction.
- Palette collision: choose another palette story after structural pass.
- Excess detail: remove the lowest-priority decorative system; never remove a structural cue first.
