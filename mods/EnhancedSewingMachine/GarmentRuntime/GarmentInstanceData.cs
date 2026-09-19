namespace EnhancedSewingMachine.GarmentRuntime
{
    internal sealed class GarmentInstanceData
    {
        public const int CurrentSchemaVersion = 1;

        public int SchemaVersion { get; set; } = CurrentSchemaVersion;
        public string GarmentId { get; set; }
        public int GenerationVersion { get; set; } = 1;
        public long Seed { get; set; }
        public string Category { get; set; } = "Hat";
        public string Family { get; set; } = "";
        public string Construction { get; set; } = "";
        public string Material { get; set; } = "";
        public string Palette { get; set; } = "";
        public string Motif { get; set; } = "";
        public string GeneratorId { get; set; } = "";
        public int GeneratorVersion { get; set; } = 1;
        public long GeneratorSeed { get; set; }
        public string Style { get; set; } = "";
        public string QualityTier { get; set; } = "";
        public string Decals { get; set; } = "";
        public string Classification { get; set; } = "";
        public int FitOffsetX { get; set; }
        public int FitOffsetY { get; set; }
        public float FitScale { get; set; } = 1f;
        public GarmentRenderSnapshot Render { get; set; }

        public bool IsUsable()
            => this.SchemaVersion == CurrentSchemaVersion
                && this.GenerationVersion > 0
                && !string.IsNullOrWhiteSpace(this.GarmentId)
                && string.Equals(this.Category, "Hat", System.StringComparison.OrdinalIgnoreCase)
                && this.Render != null;

        public GarmentInstanceData Clone()
            => new()
            {
                SchemaVersion = this.SchemaVersion,
                GarmentId = this.GarmentId,
                GenerationVersion = this.GenerationVersion,
                Seed = this.Seed,
                Category = this.Category,
                Family = this.Family,
                Construction = this.Construction,
                Material = this.Material,
                Palette = this.Palette,
                Motif = this.Motif,
                GeneratorId = this.GeneratorId,
                GeneratorVersion = this.GeneratorVersion,
                GeneratorSeed = this.GeneratorSeed,
                Style = this.Style,
                QualityTier = this.QualityTier,
                Decals = this.Decals,
                Classification = this.Classification,
                FitOffsetX = this.FitOffsetX,
                FitOffsetY = this.FitOffsetY,
                FitScale = this.FitScale,
                Render = this.Render?.Clone()
            };
    }

    internal static class GarmentInstanceKeys
    {
        public const string Instance = "RNGClothing.ESM/Instance";
        public const string GarmentId = "RNGClothing.ESM/GarmentId";
        public const string AppearanceDigest = "RNGClothing.ESM/AppearanceDigest";
        public const string GenerationVersion = "RNGClothing.ESM/GenerationVersion";
    }
}
