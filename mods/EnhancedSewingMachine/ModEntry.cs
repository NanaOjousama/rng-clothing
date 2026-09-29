using System;
using System.Globalization;
using System.Linq;
using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Objects;
using StardewValley.GameData.Objects;
using EnhancedSewingMachine.GarmentRuntime;
using EnhancedSewingMachine.TailoringSelection;
using EnhancedSewingMachine.EnhancedTailoring;

namespace EnhancedSewingMachine
{
    internal sealed class ModEntry : Mod
    {
        private GarmentRuntimeHost runtime;
        private TailoringSelectionService tailoring;
        private EnhancedTailoringShell tailoringShell;
        private ModConfig config;

        public override void Entry(IModHelper helper)
        {
            this.config = helper.ReadConfig<ModConfig>() ?? new ModConfig();
            this.runtime = new GarmentRuntimeHost(helper, this.Monitor);
            this.tailoring = new TailoringSelectionService(helper, this.Monitor, this.runtime.Registry, this.config.ContentSourceMode);
            this.tailoringShell = new EnhancedTailoringShell(
                helper,
                this.Monitor,
                this.runtime,
                this.tailoring);
            FarmerRendererPatch.Host = this.runtime;

            helper.Events.Content.AssetRequested += this.OnAssetRequested;
            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.Display.MenuChanged += this.tailoringShell.OnMenuChanged;
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.Input.ButtonPressed += this.tailoringShell.OnButtonPressed;
            helper.Events.GameLoop.UpdateTicked += this.tailoringShell.OnUpdateTicked;
            helper.Events.Display.RenderedActiveMenu += this.tailoringShell.OnRenderedActiveMenu;

            helper.ConsoleCommands.Add(
                "rng_garment",
                "Generated garment dev command: list | reload | give <id> [seed] | equip <id> [seed] | inspect",
                this.OnGarmentCommand);

            helper.ConsoleCommands.Add(
                "rng_tailor",
                "Tailoring selection dev command: profiles | reload | shell | fragments [count] | roll <textile> <inspiration> <seed> | equip <textile> <inspiration> <seed>",
                this.OnTailoringCommand);

            // Keep the Phase 1 command as a convenience alias.
            helper.ConsoleCommands.Add(
                "rng_garment_hat",
                "Legacy alias: equip the 32px Garment Runtime proof hat.",
                (_, _) => this.GiveOrEquip(GarmentRuntimeHost.LegacyProofGarmentId, null, equip: true));

            try
            {
                var harmony = new Harmony(this.ModManifest.UniqueID);
                harmony.PatchAll();
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"Could not patch FarmerRenderer; Enhanced Sewing Machine will fail open. {ex}", LogLevel.Error);
                FarmerRendererPatch.Host = null;
            }
        }



        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            if (e.Button != SButton.K)
                return;
            if (!Context.IsWorldReady || Game1.activeClickableMenu != null)
                return;
            if (!Context.IsPlayerFree)
                return;

            try
            {
                var machine = ItemRegistry.Create<StardewValley.Object>("(BC)247");
                machine.Location = Game1.currentLocation;
                machine.checkForAction(Game1.player);
                this.Helper.Input.Suppress(e.Button);
            }
            catch (Exception ex)
            {
                this.Monitor.Log(
                    $"Could not open Enhanced Sewing Machine from K hotkey; vanilla behavior is unchanged. {ex.Message}",
                    LogLevel.Warn);
            }
        }

        private void OnGameLaunched(object sender, GameLaunchedEventArgs e)
        {
            this.runtime.Load();
            this.tailoring.Load();
            this.Helper.GameContent.InvalidateCache("Data/Hats");
            this.Helper.GameContent.InvalidateCache("Data/Objects");
            this.Helper.GameContent.InvalidateCache(GarmentCarrier.TextureAsset);
        }

        private void OnAssetRequested(object sender, AssetRequestedEventArgs e)
        {
            if (e.NameWithoutLocale.IsEquivalentTo("Data/Objects"))
            {
                e.Edit(asset =>
                {
                    var objects = asset.AsDictionary<string, ObjectData>().Data;
                    objects[FashionFragmentItem.ItemId] = new ObjectData
                    {
                        Name = "Fashion Fragment",
                        DisplayName = this.Helper.Translation.Get("item.fashion-fragment.name"),
                        Description = this.Helper.Translation.Get("item.fashion-fragment.description"),
                        Type = "Basic",
                        Category = 0,
                        Price = 0,
                        Texture = null,
                        SpriteIndex = 428,
                        Edibility = -300,
                        CanBeGivenAsGift = false,
                        CanBeTrashed = true,
                        ExcludeFromFishingCollection = true,
                        ExcludeFromShippingCollection = true,
                        ExcludeFromRandomSale = true,
                        ContextTags = new System.Collections.Generic.List<string>
                        {
                            FashionFragmentItem.ContextTag
                        }
                    };
                }, AssetEditPriority.Late);
                return;
            }

            if (e.NameWithoutLocale.IsEquivalentTo(GarmentCarrier.TextureAsset))
            {
                e.LoadFromModFile<Texture2D>("assets/carrier_hat_20x80.png", AssetLoadPriority.Exclusive);
                return;
            }

            if (e.NameWithoutLocale.IsEquivalentTo("Data/Hats"))
            {
                e.Edit(asset =>
                {
                    var hats = asset.AsDictionary<string, string>().Data;
                    string name = this.Helper.Translation.Get("carrier.hat.name");
                    string description = this.Helper.Translation.Get("carrier.hat.description");

                    string row = string.Join('/',
                        "RNGGeneratedHat",
                        description,
                        "true",
                        "true",
                        "",
                        name,
                        "0",
                        GarmentCarrier.TextureDataField);

                    hats[GarmentCarrier.CarrierItemId] = row;

                    // Phase 1 dev-save compatibility. This can be removed after the
                    // project has no saves containing the old proof carrier.
                    hats[GarmentCarrier.LegacyProofItemId] = row;
                }, AssetEditPriority.Late);
            }
        }

        private void OnGarmentCommand(string command, string[] args)
        {
            string sub = args.ElementAtOrDefault(0)?.Trim().ToLowerInvariant() ?? "list";
            switch (sub)
            {
                case "list":
                    foreach (RegisteredGarment garment in this.runtime.Registry.All)
                    {
                        GarmentDefinition def = garment.Definition;
                        this.Monitor.Log(
                            $"{def.Id} | {def.FrameWidth}x{def.FrameHeight} @ {def.RenderScale:0.###} | " +
                            $"family={def.Metadata?.Family ?? ""} construction={def.Metadata?.Construction ?? ""} " +
                            $"generator={def.Metadata?.GeneratorId ?? ""} generatorSeed={def.Metadata?.GeneratorSeed ?? 0}",
                            LogLevel.Info);
                    }
                    return;

                case "reload":
                    this.runtime.Load();
                    this.Monitor.Log($"Reloaded garment registry: {this.runtime.Registry.Count} definition(s).", LogLevel.Info);
                    return;

                case "give":
                case "equip":
                {
                    string id = args.ElementAtOrDefault(1);
                    if (string.IsNullOrWhiteSpace(id))
                    {
                        this.Monitor.Log("Usage: rng_garment give|equip <garment-id> [seed]", LogLevel.Info);
                        return;
                    }

                    long? seed = null;
                    string seedArg = args.ElementAtOrDefault(2);
                    if (!string.IsNullOrWhiteSpace(seedArg))
                    {
                        if (!long.TryParse(seedArg, NumberStyles.Integer, CultureInfo.InvariantCulture, out long parsed))
                        {
                            this.Monitor.Log($"Seed '{seedArg}' is not a signed 64-bit integer.", LogLevel.Info);
                            return;
                        }
                        seed = parsed;
                    }

                    this.GiveOrEquip(id, seed, equip: sub == "equip");
                    return;
                }

                case "inspect":
                    this.InspectEquipped();
                    return;

                default:
                    this.Monitor.Log("Usage: rng_garment list | reload | give <id> [seed] | equip <id> [seed] | inspect", LogLevel.Info);
                    return;
            }
        }

        private void OnTailoringCommand(string command, string[] args)
        {
            string sub = args.ElementAtOrDefault(0)?.Trim().ToLowerInvariant() ?? "profiles";
            switch (sub)
            {
                case "profiles":
                    this.Monitor.Log(
                        "Textiles: " + string.Join(", ", this.tailoring.TextileIds()),
                        LogLevel.Info);
                    this.Monitor.Log(
                        "Inspirations: " + string.Join(", ", this.tailoring.InspirationIds()),
                        LogLevel.Info);
                    return;

                case "reload":
                    if (this.tailoring.Load())
                        this.Monitor.Log("Reloaded tailoring bias profiles.", LogLevel.Info);
                    return;

                case "shell":
                    this.Monitor.Log(this.tailoringShell.DescribeState(), LogLevel.Info);
                    return;

                case "fragments":
                {
                    if (!Context.IsWorldReady)
                    {
                        this.Monitor.Log(this.Helper.Translation.Get("command.no-save"), LogLevel.Info);
                        return;
                    }

                    int count = 25;
                    string countArg = args.ElementAtOrDefault(1);
                    if (!string.IsNullOrWhiteSpace(countArg)
                        && (!int.TryParse(countArg, NumberStyles.Integer, CultureInfo.InvariantCulture, out count)
                            || count <= 0
                            || count > 999))
                    {
                        this.Monitor.Log("Usage: rng_tailor fragments [1..999]", LogLevel.Info);
                        return;
                    }

                    Item fragments = ItemRegistry.Create(FashionFragmentItem.QualifiedItemId);
                    fragments.Stack = count;
                    if (!Game1.player.addItemToInventoryBool(fragments))
                    {
                        this.Monitor.Log(this.Helper.Translation.Get("command.inventory-full"), LogLevel.Info);
                        return;
                    }

                    this.Monitor.Log(
                        this.Helper.Translation.Get("command.fragments.success", new { count }),
                        LogLevel.Info);
                    return;
                }

                case "roll":
                case "equip":
                {
                    string textile = args.ElementAtOrDefault(1);
                    string inspiration = args.ElementAtOrDefault(2);
                    string seedArg = args.ElementAtOrDefault(3);
                    if (string.IsNullOrWhiteSpace(textile)
                        || string.IsNullOrWhiteSpace(inspiration)
                        || !long.TryParse(seedArg, NumberStyles.Integer, CultureInfo.InvariantCulture, out long seed))
                    {
                        this.Monitor.Log(
                            "Usage: rng_tailor roll|equip <textile> <inspiration> <seed>",
                            LogLevel.Info);
                        return;
                    }

                    if (!this.tailoring.TrySelect(
                        textile,
                        inspiration,
                        seed,
                        out TailoringSelectionResult result,
                        out string error))
                    {
                        this.Monitor.Log($"Tailoring selection failed: {error}", LogLevel.Error);
                        return;
                    }

                    TailoringSelectionScore chosen = result.Scores
                        .First(x => x.Candidate.GarmentId == result.GarmentId);

                    string leaders = string.Join(
                        " | ",
                        result.Scores
                            .OrderByDescending(x => x.Weight)
                            .ThenBy(x => x.Candidate.GarmentId, StringComparer.Ordinal)
                            .Take(4)
                            .Select(x =>
                                $"{x.Candidate.GarmentId}:{x.Weight}" +
                                $"(T{x.TextileAdjustment:+#;-#;0},I{x.InspirationAdjustment:+#;-#;0})"));

                    this.Monitor.Log(
                        $"Tailoring roll textile={textile} inspiration={inspiration} seed={seed} " +
                        $"=> {result.GarmentId} weight={chosen.Weight}. Top weights: {leaders}",
                        LogLevel.Info);

                    if (sub == "equip")
                        this.GiveOrEquip(result.GarmentId, seed, equip: true);
                    return;
                }

                default:
                    this.Monitor.Log(
                        "Usage: rng_tailor profiles | reload | shell | fragments [count] | roll <textile> <inspiration> <seed> | equip <textile> <inspiration> <seed>",
                        LogLevel.Info);
                    return;
            }
        }

        private void GiveOrEquip(string garmentId, long? requestedSeed, bool equip)
        {
            if (!Context.IsWorldReady)
            {
                this.Monitor.Log(this.Helper.Translation.Get("command.no-save"), LogLevel.Info);
                return;
            }

            long seed = requestedSeed ?? Random.Shared.NextInt64(0, long.MaxValue);
            Hat hat;
            try
            {
                hat = this.runtime.CreateHat(garmentId, seed);
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"Could not create garment '{garmentId}': {ex.Message}", LogLevel.Error);
                return;
            }

            if (equip)
            {
                Hat previous = Game1.player.hat.Value;
                if (previous != null && !Game1.player.addItemToInventoryBool(previous))
                {
                    this.Monitor.Log(this.Helper.Translation.Get("command.inventory-full"), LogLevel.Info);
                    return;
                }

                Game1.player.hat.Value = hat;
                this.Monitor.Log(
                    this.Helper.Translation.Get("command.equip.success", new { id = garmentId, seed }),
                    LogLevel.Info);
                return;
            }

            if (!Game1.player.addItemToInventoryBool(hat))
            {
                this.Monitor.Log(this.Helper.Translation.Get("command.inventory-full"), LogLevel.Info);
                return;
            }

            this.Monitor.Log(
                this.Helper.Translation.Get("command.give.success", new { id = garmentId, seed }),
                LogLevel.Info);
        }

        private void InspectEquipped()
        {
            if (!Context.IsWorldReady)
            {
                this.Monitor.Log(this.Helper.Translation.Get("command.no-save"), LogLevel.Info);
                return;
            }

            Hat hat = Game1.player.hat.Value;
            if (hat == null)
            {
                this.Monitor.Log("No hat is equipped.", LogLevel.Info);
                return;
            }

            if (!this.runtime.TryReadInstance(hat, out GarmentInstanceData instance))
            {
                this.Monitor.Log($"Equipped hat {hat.QualifiedItemId} is not a generated garment instance.", LogLevel.Info);
                return;
            }

            this.Monitor.Log(
                $"GarmentId={instance.GarmentId} seed={instance.Seed} gen={instance.GenerationVersion} " +
                $"family={instance.Family} construction={instance.Construction} material={instance.Material} " +
                $"palette={instance.Palette} motif={instance.Motif} " +
                $"generator={instance.GeneratorId} generatorSeed={instance.GeneratorSeed} generatorVersion={instance.GeneratorVersion} " +
                $"style={instance.Style} tier={instance.QualityTier} decals={instance.Decals} class={instance.Classification} " +
                $"frame={instance.Render.FrameWidth}x{instance.Render.FrameHeight} scale={instance.Render.RenderScale:0.###} " +
                $"digest={instance.Render.AppearanceDigest}",
                LogLevel.Info);
        }
    }
}
