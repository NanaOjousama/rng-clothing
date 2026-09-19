using System;
using System.Collections.Generic;
using System.Linq;

namespace EnhancedSewingMachine.TailoringSelection
{
    internal sealed class TailoringBiasCatalog
    {
        public int SchemaVersion { get; set; } = 1;
        public Dictionary<string, TailoringBiasProfile> Textiles { get; set; } = new();
        public Dictionary<string, TailoringBiasProfile> Inspirations { get; set; } = new();

        public bool TryValidate(out string error)
        {
            if (this.SchemaVersion != 1)
            {
                error = $"Unsupported tailoring bias schema {this.SchemaVersion}.";
                return false;
            }

            if (this.Textiles == null || this.Textiles.Count == 0)
            {
                error = "At least one Textile profile is required.";
                return false;
            }

            if (this.Inspirations == null || this.Inspirations.Count == 0)
            {
                error = "At least one Inspiration profile is required.";
                return false;
            }

            foreach (var pair in this.Textiles.Concat(this.Inspirations))
            {
                if (string.IsNullOrWhiteSpace(pair.Key) || pair.Value == null)
                {
                    error = "Tailoring profile IDs and profile objects must be non-empty.";
                    return false;
                }

                if (!pair.Value.TryValidate(out error))
                {
                    error = $"{pair.Key}: {error}";
                    return false;
                }
            }

            error = null;
            return true;
        }

        public TailoringBiasProfile FindTextile(string id)
            => Find(this.Textiles, id);

        public TailoringBiasProfile FindInspiration(string id)
            => Find(this.Inspirations, id);

        private static TailoringBiasProfile Find(
            Dictionary<string, TailoringBiasProfile> source,
            string id)
        {
            if (source == null || string.IsNullOrWhiteSpace(id))
                return null;

            foreach (var pair in source)
            {
                if (string.Equals(pair.Key, id, StringComparison.OrdinalIgnoreCase))
                    return pair.Value;
            }

            return null;
        }
    }

    internal sealed class TailoringBiasProfile
    {
        public string Label { get; set; } = "";
        public int BaseWeight { get; set; } = 100;

        public Dictionary<string, int> FamilyWeights { get; set; } = new();
        public Dictionary<string, int> ConstructionWeights { get; set; } = new();
        public Dictionary<string, int> MaterialWeights { get; set; } = new();
        public Dictionary<string, int> StyleWeights { get; set; } = new();
        public Dictionary<string, int> PaletteWeights { get; set; } = new();
        public Dictionary<string, int> MotifWeights { get; set; } = new();
        public Dictionary<string, int> DecalWeights { get; set; } = new();

        // Optional hard compatibility gate. Empty means all production
        // constructions are compatible and the weight tables only bias.
        public List<string> AllowedConstructions { get; set; } = new();
        public List<string> DeniedConstructions { get; set; } = new();

        public bool TryValidate(out string error)
        {
            if (this.BaseWeight <= 0 || this.BaseWeight > 1_000_000)
            {
                error = "BaseWeight must be between 1 and 1,000,000.";
                return false;
            }

            foreach (var table in WeightTables())
            {
                if (table == null)
                    continue;

                foreach (var pair in table)
                {
                    if (string.IsNullOrWhiteSpace(pair.Key))
                    {
                        error = "Weight table keys must be non-empty.";
                        return false;
                    }

                    if (pair.Value < -100_000 || pair.Value > 100_000)
                    {
                        error = $"Weight '{pair.Key}' is outside the safety range.";
                        return false;
                    }
                }
            }

            error = null;
            return true;
        }

        private IEnumerable<Dictionary<string, int>> WeightTables()
        {
            yield return this.FamilyWeights;
            yield return this.ConstructionWeights;
            yield return this.MaterialWeights;
            yield return this.StyleWeights;
            yield return this.PaletteWeights;
            yield return this.MotifWeights;
            yield return this.DecalWeights;
        }
    }
}
