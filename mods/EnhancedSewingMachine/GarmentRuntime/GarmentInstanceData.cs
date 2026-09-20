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
        // Front/down view keeps the original fields for save compatibility.
        public int FitOffsetX { get; set; }
        public int FitOffsetY { get; set; }
        public int FitRightOffsetX { get; set; }
        public int FitRightOffsetY { get; set; }
        public int FitLeftOffsetX { get; set; }
        public int FitLeftOffsetY { get; set; }
        public int FitBackOffsetX { get; set; }
        public int FitBackOffsetY { get; set; }
        public float FitScale { get; set; } = 1f;

        public int GetFitOffsetX(int facingDirection)
            => facingDirection switch
            {
                0 => this.FitBackOffsetX,
                1 => this.FitRightOffsetX,
                3 => this.FitLeftOffsetX,
                _ => this.FitOffsetX
            };

        public int GetFitOffsetY(int facingDirection)
            => facingDirection switch
            {
                0 => this.FitBackOffsetY,
                1 => this.FitRightOffsetY,
                3 => this.FitLeftOffsetY,
                _ => this.FitOffsetY
            };

        public void SetFitOffset(int facingDirection, int x, int y)
        {
            switch (facingDirection)
            {
                case 0:
                    this.FitBackOffsetX = x;
                    this.FitBackOffsetY = y;
                    break;
                case 1:
                    this.FitRightOffsetX = x;
                    this.FitRightOffsetY = y;
                    break;
                case 3:
                    this.FitLeftOffsetX = x;
                    this.FitLeftOffsetY = y;
                    break;
                default:
                    this.FitOffsetX = x;
                    this.FitOffsetY = y;
                    break;
            }
        }

        public void ResetAllFitOffsets()
        {
            this.FitOffsetX = 0;
            this.FitOffsetY = 0;
            this.FitRightOffsetX = 0;
            this.FitRightOffsetY = 0;
            this.FitLeftOffsetX = 0;
            this.FitLeftOffsetY = 0;
            this.FitBackOffsetX = 0;
            this.FitBackOffsetY = 0;
        }
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
                FitRightOffsetX = this.FitRightOffsetX,
                FitRightOffsetY = this.FitRightOffsetY,
                FitLeftOffsetX = this.FitLeftOffsetX,
                FitLeftOffsetY = this.FitLeftOffsetY,
                FitBackOffsetX = this.FitBackOffsetX,
                FitBackOffsetY = this.FitBackOffsetY,
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
