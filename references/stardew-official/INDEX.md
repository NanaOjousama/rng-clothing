# Stardew Valley / SMAPI — official technical reference (local mirror)

Gathered **2026-09-10** against the installed stack:
**Stardew Valley 1.6.15 / SMAPI 4.5.2**. Regenerate with
`python3 tools/index_stardew_reference.py`.

Scoped on purpose: only the `Modding:` pages this project reasons about,
plus SMAPI's docs and API-surface source. Not the whole wiki.

## Layers, in technical-authority order

| Layer | What it answers |
|---|---|
| `assembly/stardew_index.json` | classes/members of the **installed 1.6.15 assembly** (1093 types) — `IClickableMenu` controller snapping, `TailoringMenu` members. Outranks the wiki. Built by `tools/AssemblyIndex`; gitignored, because it derives from game files. |
| `smapi/docs/`, `smapi/src/` | SMAPI's own documentation and API surface |
| `wiki/` | official Modding: pages, as wikitext |

## How to query

```
rg -i 'IClickableMenu' references/stardew-official/
jq '.types[]|select(.name|test("Tailor"))' \
   references/stardew-official/assembly/stardew_index.json
```

## Wiki pages mirrored

### core

- [Modding:Common tasks](https://stardewvalleywiki.com/Modding%3ACommon_tasks) → `wiki/core/Common-tasks.wiki`
- [Modding:Index](https://stardewvalleywiki.com/Modding%3AIndex) → `wiki/core/Index.wiki`
- [Modding:Modder Guide](https://stardewvalleywiki.com/Modding%3AModder_Guide) → `wiki/core/Modder-Guide.wiki`
- [Modding:Modder Guide/Game Fundamentals](https://stardewvalleywiki.com/Modding%3AModder_Guide/Game_Fundamentals) → `wiki/core/Modder-Guide__Game-Fundamentals.wiki`
- [Modding:Modder Guide/Test and Troubleshoot](https://stardewvalleywiki.com/Modding%3AModder_Guide/Test_and_Troubleshoot) → `wiki/core/Modder-Guide__Test-and-Troubleshoot.wiki`

### smapi-api

- [Modding:Modder Guide/APIs](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs) → `wiki/smapi-api/Modder-Guide__APIs.wiki`
- [Modding:Modder Guide/APIs/Config](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Config) → `wiki/smapi-api/Modder-Guide__APIs__Config.wiki`
- [Modding:Modder Guide/APIs/Content](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Content) → `wiki/smapi-api/Modder-Guide__APIs__Content.wiki`
- [Modding:Modder Guide/APIs/Data](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Data) → `wiki/smapi-api/Modder-Guide__APIs__Data.wiki`
- [Modding:Modder Guide/APIs/Events](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Events) → `wiki/smapi-api/Modder-Guide__APIs__Events.wiki`
- [Modding:Modder Guide/APIs/Harmony](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Harmony) → `wiki/smapi-api/Modder-Guide__APIs__Harmony.wiki`
- [Modding:Modder Guide/APIs/Input](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Input) → `wiki/smapi-api/Modder-Guide__APIs__Input.wiki`
- [Modding:Modder Guide/APIs/Integrations](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Integrations) → `wiki/smapi-api/Modder-Guide__APIs__Integrations.wiki`
- [Modding:Modder Guide/APIs/Logging](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Logging) → `wiki/smapi-api/Modder-Guide__APIs__Logging.wiki`
- [Modding:Modder Guide/APIs/Manifest](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Manifest) → `wiki/smapi-api/Modder-Guide__APIs__Manifest.wiki`
- [Modding:Modder Guide/APIs/Multiplayer](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Multiplayer) → `wiki/smapi-api/Modder-Guide__APIs__Multiplayer.wiki`
- [Modding:Modder Guide/APIs/Reflection](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Reflection) → `wiki/smapi-api/Modder-Guide__APIs__Reflection.wiki`
- [Modding:Modder Guide/APIs/Translation](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Translation) → `wiki/smapi-api/Modder-Guide__APIs__Translation.wiki`
- [Modding:Modder Guide/APIs/Utilities](https://stardewvalleywiki.com/Modding%3AModder_Guide/APIs/Utilities) → `wiki/smapi-api/Modder-Guide__APIs__Utilities.wiki`

### content

- [Modding:Boots](https://stardewvalleywiki.com/Modding%3ABoots) → `wiki/content/Boots.wiki`
- [Modding:Common data field types](https://stardewvalleywiki.com/Modding%3ACommon_data_field_types) → `wiki/content/Common-data-field-types.wiki`
- [Modding:Content Patcher](https://stardewvalleywiki.com/Modding%3AContent_Patcher) → `wiki/content/Content-Patcher.wiki`
- [Modding:Hats](https://stardewvalleywiki.com/Modding%3AHats) → `wiki/content/Hats.wiki`
- [Modding:Items](https://stardewvalleywiki.com/Modding%3AItems) → `wiki/content/Items.wiki`
- [Modding:Migrate to Stardew Valley 1.6](https://stardewvalleywiki.com/Modding%3AMigrate_to_Stardew_Valley_1.6) → `wiki/content/Migrate-to-Stardew-Valley-1.6.wiki`
- [Modding:Object data](https://stardewvalleywiki.com/Modding%3AObject_data) → `wiki/content/Object-data.wiki`
- [Modding:Pants](https://stardewvalleywiki.com/Modding%3APants) → `wiki/content/Pants.wiki`
- [Modding:Recipe data](https://stardewvalleywiki.com/Modding%3ARecipe_data) → `wiki/content/Recipe-data.wiki`
- [Modding:Shirts](https://stardewvalleywiki.com/Modding%3AShirts) → `wiki/content/Shirts.wiki`
- [Modding:Tailoring](https://stardewvalleywiki.com/Modding%3ATailoring) → `wiki/content/Tailoring.wiki`

### compatibility

- [Modding:Mod compatibility](https://stardewvalleywiki.com/Modding%3AMod_compatibility) → `wiki/compatibility/Mod-compatibility.wiki`
- [Modding:Player Guide/Key Bindings](https://stardewvalleywiki.com/Modding%3APlayer_Guide/Key_Bindings) → `wiki/compatibility/Player-Guide__Key-Bindings.wiki`

## SMAPI clone

- `https://github.com/Pathoschild/SMAPI.git` @ `79f9bbb`
- sparse paths: `docs`, `src/SMAPI/Events`, `src/SMAPI/Framework/Events`, `src/SMAPI.Toolkit`
- 266 files
