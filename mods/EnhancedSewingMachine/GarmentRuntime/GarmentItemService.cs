using System;
using System.Collections.Generic;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Objects;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal sealed class GarmentItemService
    {
        private readonly GarmentRegistry registry;
        private readonly IMonitor monitor;
        private readonly HashSet<string> warnedInvalidPayloads = new(StringComparer.Ordinal);

        public GarmentItemService(GarmentRegistry registry, IMonitor monitor)
        {
            this.registry = registry;
            this.monitor = monitor;
        }

        public Hat CreateHat(string garmentId, long seed)
        {
            if (!this.registry.TryGet(garmentId, out RegisteredGarment registered))
                throw new InvalidOperationException($"Unknown garment '{garmentId}'.");

            Item item = ItemRegistry.Create(GarmentCarrier.CarrierQualifiedId);
            if (item is not Hat hat)
                throw new InvalidOperationException($"Carrier '{GarmentCarrier.CarrierQualifiedId}' did not resolve to a Hat.");

            GarmentTemplateMetadata metadata = registered.Definition.Metadata?.Clone() ?? new GarmentTemplateMetadata();
            var instance = new GarmentInstanceData
            {
                GarmentId = registered.Definition.Id,
                GenerationVersion = registered.Definition.DefinitionVersion,
                Seed = seed,
                Category = registered.Definition.Category,
                Family = metadata.Family,
                Construction = metadata.Construction,
                Material = metadata.Material,
                Palette = metadata.Palette,
                Motif = metadata.Motif,
                GeneratorId = metadata.GeneratorId,
                GeneratorVersion = metadata.GeneratorVersion,
                GeneratorSeed = metadata.GeneratorSeed,
                Style = metadata.Style,
                QualityTier = metadata.QualityTier,
                Decals = metadata.Decals,
                Classification = metadata.Classification,
                Render = registered.Definition.ToSnapshot(registered.AppearanceDigest)
            };
            Write(hat, instance);
            return hat;
        }

        public void Write(Hat hat, GarmentInstanceData instance)
        {
            if (hat == null)
                throw new ArgumentNullException(nameof(hat));
            if (instance == null || !instance.IsUsable())
                throw new ArgumentException("Garment instance is incomplete.", nameof(instance));

            string json = GarmentInstanceCodec.Encode(instance);
            hat.modData[GarmentInstanceKeys.Instance] = json;
            hat.modData[GarmentInstanceKeys.GarmentId] = instance.GarmentId;
            hat.modData[GarmentInstanceKeys.AppearanceDigest] = instance.Render.AppearanceDigest ?? "";
            hat.modData[GarmentInstanceKeys.GenerationVersion] = instance.GenerationVersion.ToString(System.Globalization.CultureInfo.InvariantCulture);
        }

        public bool TryRead(Hat hat, out GarmentInstanceData instance)
        {
            instance = null;
            if (hat == null || !GarmentCarrier.IsCarrier(hat))
                return false;
            if (!hat.modData.TryGetValue(GarmentInstanceKeys.Instance, out string json))
                return false;

            if (!GarmentInstanceCodec.TryDecode(json, out instance, out string error))
            {
                if (this.warnedInvalidPayloads.Add(json))
                    this.monitor.Log($"Ignored invalid garment instance on {hat.QualifiedItemId}: {error}", LogLevel.Warn);
                return false;
            }

            return true;
        }
    }

    internal static class GarmentCarrier
    {
        public const string CarrierItemId = "RNGClothing.ESM.GeneratedHat";
        public const string CarrierQualifiedId = "(H)" + CarrierItemId;
        public const string LegacyProofItemId = "RNGClothing.ESM.ProofHat";
        public const string LegacyProofQualifiedId = "(H)" + LegacyProofItemId;

        public const string TextureAsset = "Mods/RNGClothing/ESM/CarrierHat";
        public const string TextureDataField = @"Mods\RNGClothing\ESM\CarrierHat";

        public static bool IsCarrier(Hat hat)
            => hat != null
                && (hat.QualifiedItemId == CarrierQualifiedId
                    || hat.QualifiedItemId == LegacyProofQualifiedId);
    }
}
