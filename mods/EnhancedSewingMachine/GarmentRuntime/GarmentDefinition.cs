using System;
using System.Collections.Generic;
using System.IO;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal sealed class GarmentDefinition
    {
        public string Id { get; set; }
        public string Category { get; set; } = "Hat";
        public int DefinitionVersion { get; set; } = 1;
        public string WornTexture { get; set; }
        public int FrameWidth { get; set; }
        public int FrameHeight { get; set; }
        public float RenderScale { get; set; } = 1f;
        public IntPoint VanillaReferenceAnchor { get; set; } = new IntPoint(10, 16);
        public Dictionary<string, DirectionFrame> Directions { get; set; } = new(StringComparer.OrdinalIgnoreCase);
        public GarmentTemplateMetadata Metadata { get; set; } = new();

        public DirectionFrame Resolve(int facingDirection)
            => Resolve(DirectionName(facingDirection));

        public DirectionFrame Resolve(string direction)
        {
            if (string.IsNullOrWhiteSpace(direction)
                || this.Directions == null
                || !this.Directions.TryGetValue(direction, out DirectionFrame frame)
                || frame == null)
                return null;

            if (string.IsNullOrWhiteSpace(frame.MirrorOf))
                return frame.Clone();

            if (!this.Directions.TryGetValue(frame.MirrorOf, out DirectionFrame source)
                || source == null
                || !string.IsNullOrWhiteSpace(source.MirrorOf))
                return null;

            return frame.WithSourceFrom(source);
        }

        public bool TryValidate(int textureWidth, int textureHeight, out string error)
        {
            if (string.IsNullOrWhiteSpace(this.Id))
                return Fail("Id is required.", out error);
            if (!string.Equals(this.Category, "Hat", StringComparison.OrdinalIgnoreCase))
                return Fail($"Category '{this.Category}' is not supported in Phase 2.", out error);
            if (this.DefinitionVersion <= 0)
                return Fail("DefinitionVersion must be positive.", out error);
            if (string.IsNullOrWhiteSpace(this.WornTexture))
                return Fail("WornTexture is required.", out error);
            if (!IsSafeRelativeAssetPath(this.WornTexture))
                return Fail("WornTexture must be a safe mod-relative asset path.", out error);
            if (this.FrameWidth <= 0 || this.FrameHeight <= 0 || this.FrameWidth > 128 || this.FrameHeight > 128)
                return Fail("FrameWidth/FrameHeight must be between 1 and 128.", out error);
            if (!float.IsFinite(this.RenderScale) || this.RenderScale <= 0f || this.RenderScale > 8f)
                return Fail("RenderScale must be finite and in (0, 8].", out error);
            if (textureWidth <= 0 || textureHeight <= 0)
                return Fail("Texture dimensions must be positive.", out error);
            if (this.VanillaReferenceAnchor == null)
                return Fail("VanillaReferenceAnchor is required.", out error);

            foreach (string direction in RequiredDirections)
            {
                DirectionFrame resolved = this.Resolve(direction);
                if (resolved == null)
                    return Fail($"{direction} is missing or has an invalid mirror chain.", out error);

                if (resolved.SourceX < 0 || resolved.SourceY < 0
                    || resolved.SourceX + this.FrameWidth > textureWidth
                    || resolved.SourceY + this.FrameHeight > textureHeight)
                    return Fail($"{direction} source rectangle is outside {textureWidth}x{textureHeight}.", out error);

                if (Math.Abs(resolved.OffsetX) > 64 || Math.Abs(resolved.OffsetY) > 64)
                    return Fail($"{direction} offset exceeds the Phase 2 safety bound.", out error);
            }

            error = null;
            return true;
        }

        public GarmentRenderSnapshot ToSnapshot(string appearanceDigest)
        {
            var directions = new Dictionary<string, DirectionFrame>(StringComparer.OrdinalIgnoreCase);
            foreach (string direction in RequiredDirections)
            {
                DirectionFrame frame = this.Resolve(direction);
                if (frame != null)
                    directions[direction] = frame;
            }

            return new GarmentRenderSnapshot
            {
                DefinitionVersion = this.DefinitionVersion,
                WornTexture = this.WornTexture,
                FrameWidth = this.FrameWidth,
                FrameHeight = this.FrameHeight,
                RenderScale = this.RenderScale,
                VanillaReferenceAnchor = this.VanillaReferenceAnchor?.Clone() ?? new IntPoint(10, 16),
                Directions = directions,
                AppearanceDigest = appearanceDigest
            };
        }

        internal static string DirectionName(int facingDirection)
            => facingDirection switch
            {
                0 => "Back",
                1 => "Right",
                2 => "Front",
                3 => "Left",
                _ => null
            };

        internal static readonly string[] RequiredDirections = { "Front", "Right", "Back", "Left" };

        private static bool IsSafeRelativeAssetPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || Path.IsPathRooted(path) || path.Contains(':'))
                return false;
            string normalized = path.Replace('\\', '/');
            foreach (string part in normalized.Split('/'))
            {
                if (part == "..")
                    return false;
            }
            return true;
        }

        private static bool Fail(string message, out string error)
        {
            error = message;
            return false;
        }
    }

    internal sealed class GarmentRenderSnapshot
    {
        public int DefinitionVersion { get; set; } = 1;
        public string WornTexture { get; set; }
        public int FrameWidth { get; set; }
        public int FrameHeight { get; set; }
        public float RenderScale { get; set; } = 1f;
        public IntPoint VanillaReferenceAnchor { get; set; } = new IntPoint(10, 16);
        public Dictionary<string, DirectionFrame> Directions { get; set; } = new(StringComparer.OrdinalIgnoreCase);
        public string AppearanceDigest { get; set; }

        public DirectionFrame Resolve(int facingDirection)
        {
            string key = GarmentDefinition.DirectionName(facingDirection);
            if (key == null || this.Directions == null || !this.Directions.TryGetValue(key, out DirectionFrame frame))
                return null;
            return frame?.Clone();
        }

        public bool TryValidate(int textureWidth, int textureHeight, out string error)
        {
            var definition = new GarmentDefinition
            {
                Id = "snapshot",
                Category = "Hat",
                DefinitionVersion = this.DefinitionVersion,
                WornTexture = this.WornTexture,
                FrameWidth = this.FrameWidth,
                FrameHeight = this.FrameHeight,
                RenderScale = this.RenderScale,
                VanillaReferenceAnchor = this.VanillaReferenceAnchor,
                Directions = this.Directions
            };
            return definition.TryValidate(textureWidth, textureHeight, out error);
        }

        public GarmentRenderSnapshot Clone()
        {
            var directions = new Dictionary<string, DirectionFrame>(StringComparer.OrdinalIgnoreCase);
            if (this.Directions != null)
            {
                foreach (var pair in this.Directions)
                    directions[pair.Key] = pair.Value?.Clone();
            }

            return new GarmentRenderSnapshot
            {
                DefinitionVersion = this.DefinitionVersion,
                WornTexture = this.WornTexture,
                FrameWidth = this.FrameWidth,
                FrameHeight = this.FrameHeight,
                RenderScale = this.RenderScale,
                VanillaReferenceAnchor = this.VanillaReferenceAnchor?.Clone(),
                Directions = directions,
                AppearanceDigest = this.AppearanceDigest
            };
        }
    }

    internal sealed class GarmentTemplateMetadata
    {
        public string Family { get; set; } = "";
        public string Construction { get; set; } = "";
        public string Material { get; set; } = "";
        public string Palette { get; set; } = "";
        public string Motif { get; set; } = "";

        // Generator provenance is separate from the sewing/transaction seed on
        // the item instance. A compiled garment can therefore say exactly which
        // generator roll produced its pixels even when a future sewing roll
        // selected that compiled result from a pool.
        public string GeneratorId { get; set; } = "";
        public string ContentSource { get; set; } = "";
        public int GeneratorVersion { get; set; } = 1;
        public long GeneratorSeed { get; set; }
        public string Style { get; set; } = "";
        public string QualityTier { get; set; } = "";
        public string Decals { get; set; } = "";
        public string Classification { get; set; } = "";

        public GarmentTemplateMetadata Clone()
            => new()
            {
                Family = this.Family ?? "",
                Construction = this.Construction ?? "",
                Material = this.Material ?? "",
                Palette = this.Palette ?? "",
                Motif = this.Motif ?? "",
                GeneratorId = this.GeneratorId ?? "",
                ContentSource = this.ContentSource ?? "",
                GeneratorVersion = this.GeneratorVersion,
                GeneratorSeed = this.GeneratorSeed,
                Style = this.Style ?? "",
                QualityTier = this.QualityTier ?? "",
                Decals = this.Decals ?? "",
                Classification = this.Classification ?? ""
            };
    }

    internal sealed class DirectionFrame
    {
        public int SourceX { get; set; }
        public int SourceY { get; set; }
        public int AnchorX { get; set; }
        public int AnchorY { get; set; }
        public int OffsetX { get; set; }
        public int OffsetY { get; set; }
        public bool FlipX { get; set; }
        public string MirrorOf { get; set; }

        public DirectionFrame WithSourceFrom(DirectionFrame source)
        {
            DirectionFrame clone = this.Clone();
            clone.SourceX = source.SourceX;
            clone.SourceY = source.SourceY;
            clone.MirrorOf = null;
            return clone;
        }

        public DirectionFrame Clone()
            => new()
            {
                SourceX = this.SourceX,
                SourceY = this.SourceY,
                AnchorX = this.AnchorX,
                AnchorY = this.AnchorY,
                OffsetX = this.OffsetX,
                OffsetY = this.OffsetY,
                FlipX = this.FlipX,
                MirrorOf = this.MirrorOf
            };
    }

    internal sealed class IntPoint
    {
        public int X { get; set; }
        public int Y { get; set; }

        public IntPoint() { }
        public IntPoint(int x, int y) { this.X = x; this.Y = y; }

        public IntPoint Clone() => new(this.X, this.Y);
    }
}
