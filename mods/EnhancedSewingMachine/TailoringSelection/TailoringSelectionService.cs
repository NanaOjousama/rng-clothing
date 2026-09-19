using System;
using System.Collections.Generic;
using System.Linq;
using StardewModdingAPI;
using EnhancedSewingMachine.GarmentRuntime;

namespace EnhancedSewingMachine.TailoringSelection
{
    internal sealed class TailoringSelectionService
    {
        private const string BiasPath = "assets/tailoring/biases.json";
        private readonly IModHelper helper;
        private readonly IMonitor monitor;
        private readonly GarmentRegistry registry;

        public TailoringSelectionService(
            IModHelper helper,
            IMonitor monitor,
            GarmentRegistry registry)
        {
            this.helper = helper;
            this.monitor = monitor;
            this.registry = registry;
        }

        public TailoringBiasCatalog Catalog { get; private set; }

        public bool Load()
        {
            try
            {
                TailoringBiasCatalog catalog =
                    this.helper.Data.ReadJsonFile<TailoringBiasCatalog>(BiasPath);

                if (catalog == null)
                {
                    this.Catalog = null;
                    this.monitor.Log(
                        "Tailoring bias catalog is missing; tailoring selection is disabled.",
                        LogLevel.Error);
                    return false;
                }

                if (!catalog.TryValidate(out string error))
                {
                    this.Catalog = null;
                    this.monitor.Log(
                        $"Tailoring bias catalog is invalid; tailoring selection is disabled. {error}",
                        LogLevel.Error);
                    return false;
                }

                this.Catalog = catalog;
                this.monitor.Log(
                    $"Tailoring selection loaded {catalog.Textiles.Count} Textile and " +
                    $"{catalog.Inspirations.Count} Inspiration profile(s).",
                    LogLevel.Debug);
                return true;
            }
            catch (Exception ex)
            {
                this.Catalog = null;
                this.monitor.Log(
                    $"Tailoring bias catalog failed to load; tailoring selection is disabled. {ex}",
                    LogLevel.Error);
                return false;
            }
        }

        public bool TrySelect(
            string textileId,
            string inspirationId,
            long sewingSeed,
            out TailoringSelectionResult result,
            out string error)
        {
            var candidates = this.registry.All
                .Select(ToCandidate)
                .ToArray();

            return TailoringSelector.TrySelect(
                candidates,
                this.Catalog,
                textileId,
                inspirationId,
                sewingSeed,
                out result,
                out error);
        }

        public IEnumerable<string> TextileIds()
            => this.Catalog?.Textiles?.Keys
                ?.OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
                ?.ToArray()
                ?? Array.Empty<string>();

        public IEnumerable<string> InspirationIds()
            => this.Catalog?.Inspirations?.Keys
                ?.OrderBy(x => x, StringComparer.OrdinalIgnoreCase)
                ?.ToArray()
                ?? Array.Empty<string>();

        private static TailoringSelectionCandidate ToCandidate(RegisteredGarment registered)
        {
            GarmentDefinition d = registered.Definition;
            GarmentTemplateMetadata m = d.Metadata ?? new GarmentTemplateMetadata();
            return new TailoringSelectionCandidate
            {
                GarmentId = d.Id,
                Family = m.Family,
                Construction = m.Construction,
                Material = m.Material,
                Style = m.Style,
                Palette = m.Palette,
                Motif = m.Motif,
                Decals = m.Decals,
                Classification = m.Classification,
                GeneratorId = m.GeneratorId
            };
        }
    }
}
