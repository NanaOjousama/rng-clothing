# AssemblyIndex

Metadata index of an **installed** .NET assembly — type and member *shapes*
only.

## Why it exists

The Stardew wiki documents the *modding* APIs, not the game's own class surface.
Questions like "what does `IClickableMenu` expose for controller snapping?" or
"how does `TailoringMenu` name its members?" have no wiki answer — verified: a
`gamepad|snapTo` search across the whole wiki + SMAPI mirror returns nothing,
while this index answers both immediately. That is why the technical authority
hierarchy puts the installed assembly **above** the wiki: it is read from the
binary the game is actually running.

## What it does and does not do

Uses `MetadataLoadContext`, which reads metadata without executing or JITing the
assembly — the same technique as the Cheerful Pixels study. **No IL bodies are
decompiled.** The output therefore contains names, signatures, inheritance and
enum members: the API's shape, never its implementation and never game content.

Its output is **gitignored** and must stay so — it is derived from game files.
Regenerate rather than share it.

## Use

    dotnet build tools/AssemblyIndex -c Release
    dotnet run --project tools/AssemblyIndex -c Release --no-build -- \
        "$STARDEW_DIR/Stardew Valley.dll" \
        references/stardew-official/assembly/stardew_index.json

An optional third argument onward filters by namespace/name substring, for a
smaller index:

    ... stardew_index.json Menus Objects

Then query with `jq`:

    jq -r '.types[]|select(.name=="StardewValley.Menus.IClickableMenu")
           |.methods[]|select(test("snap|GamePad"))' \
       references/stardew-official/assembly/stardew_index.json

Resolution note: only the target assembly's own directory is probed. A Stardew
install is self-contained (it ships `System.Private.CoreLib` beside the game),
so this reads the exact framework the game runs on. Adding the SDK's shared
runtime as well gives two assemblies the same simple name and core-assembly
resolution fails outright — that was a real failure here, not a hypothetical.

Current index: **1093 public types** from Stardew Valley 1.6.15.
