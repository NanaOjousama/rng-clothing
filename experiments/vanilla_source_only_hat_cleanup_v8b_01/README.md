# Stardew-only v8b hat cleanup + strict-capacity batch

This experiment remains isolated from the production generator.

User feedback corrected the hat decoration rule:
- Small Cap (#79) has too little room for added line/band treatment; it is recolor-only.
- Hat sprite #98 may support a small band, but the band belongs on the crown, not across the brim.
- A technical safe mask is not sufficient by itself; decoration must also land on a semantically sensible hat region.

New strict-capacity test batch:
- Hunter's Cap (#15): recolor only
- Trucker Hat (#16): recolor only
- Sailor's Cap (#17): recolor only
- Fishing Hat (#55): recolor + small crown band, brim untouched

This supports a stricter vanilla-only rule: recolor/material treatment is the default. Additional hat decoration is opt-in only for constructions with obvious readable capacity and a semantically appropriate crown/body zone.
