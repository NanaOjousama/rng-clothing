using System;
using System.Collections.Generic;
using System.Linq;

namespace EnhancedSewingMachine.TailoringSelection
{
    internal sealed class TailoringSelectionCandidate
    {
        public string GarmentId { get; set; } = "";
        public string Family { get; set; } = "";
        public string Construction { get; set; } = "";
        public string Material { get; set; } = "";
        public string Style { get; set; } = "";
        public string Palette { get; set; } = "";
        public string Motif { get; set; } = "";
        public string Decals { get; set; } = "";
        public string Classification { get; set; } = "";
        public string GeneratorId { get; set; } = "";

        public IEnumerable<string> MotifTokens()
            => SplitTokens(this.Motif);

        public IEnumerable<string> DecalTokens()
            => SplitTokens(this.Decals);

        private static IEnumerable<string> SplitTokens(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                yield break;

            foreach (string token in value.Split(','))
            {
                string clean = token.Trim();
                if (clean.Length > 0)
                    yield return clean;
            }
        }
    }

    internal sealed class TailoringSelectionScore
    {
        public TailoringSelectionCandidate Candidate { get; set; }
        public long Weight { get; set; }
        public int TextileAdjustment { get; set; }
        public int InspirationAdjustment { get; set; }
    }

    internal sealed class TailoringSelectionResult
    {
        public string TextileId { get; set; }
        public string InspirationId { get; set; }
        public long SewingSeed { get; set; }
        public string GarmentId { get; set; }
        public IReadOnlyList<TailoringSelectionScore> Scores { get; set; }
    }

    internal static class TailoringSelector
    {
        public static bool TrySelect(
            IEnumerable<TailoringSelectionCandidate> candidates,
            TailoringBiasCatalog catalog,
            string textileId,
            string inspirationId,
            long sewingSeed,
            out TailoringSelectionResult result,
            out string error)
        {
            result = null;
            if (catalog == null)
            {
                error = "Tailoring bias catalog is not loaded.";
                return false;
            }
            if (!catalog.TryValidate(out error))
                return false;

            TailoringBiasProfile textile = catalog.FindTextile(textileId);
            if (textile == null)
            {
                error = $"Unknown Textile '{textileId}'.";
                return false;
            }

            TailoringBiasProfile inspiration = catalog.FindInspiration(inspirationId);
            if (inspiration == null)
            {
                error = $"Unknown Inspiration '{inspirationId}'.";
                return false;
            }

            var scored = new List<TailoringSelectionScore>();
            foreach (TailoringSelectionCandidate candidate in candidates ?? Array.Empty<TailoringSelectionCandidate>())
            {
                if (!IsProductionGenerated(candidate))
                    continue;
                if (!Compatible(candidate, textile) || !Compatible(candidate, inspiration))
                    continue;

                int textileAdjustment = Score(candidate, textile);
                int inspirationAdjustment = Score(candidate, inspiration);
                long weight = Math.Max(
                    1,
                    (long)textile.BaseWeight
                    + inspiration.BaseWeight
                    + textileAdjustment
                    + inspirationAdjustment);

                scored.Add(new TailoringSelectionScore
                {
                    Candidate = candidate,
                    Weight = weight,
                    TextileAdjustment = textileAdjustment,
                    InspirationAdjustment = inspirationAdjustment
                });
            }

            if (scored.Count == 0)
            {
                error = "No compiled production garments are compatible with those tailoring inputs.";
                return false;
            }

            scored.Sort((a, b) => string.Compare(
                a.Candidate.GarmentId,
                b.Candidate.GarmentId,
                StringComparison.Ordinal));

            ulong total = 0;
            foreach (TailoringSelectionScore score in scored)
                total = checked(total + (ulong)score.Weight);

            ulong mixedSeed = unchecked((ulong)sewingSeed);
            mixedSeed ^= StableHash(textileId);
            mixedSeed = SplitMix64(mixedSeed);
            mixedSeed ^= StableHash(inspirationId);
            mixedSeed = SplitMix64(mixedSeed);

            ulong roll = SplitMix64(mixedSeed) % total;
            TailoringSelectionScore chosen = scored[0];
            ulong cursor = 0;
            foreach (TailoringSelectionScore score in scored)
            {
                cursor += (ulong)score.Weight;
                if (roll < cursor)
                {
                    chosen = score;
                    break;
                }
            }

            result = new TailoringSelectionResult
            {
                TextileId = textileId,
                InspirationId = inspirationId,
                SewingSeed = sewingSeed,
                GarmentId = chosen.Candidate.GarmentId,
                Scores = scored
            };
            error = null;
            return true;
        }

        private static bool IsProductionGenerated(TailoringSelectionCandidate c)
            => c != null
                && !string.IsNullOrWhiteSpace(c.GarmentId)
                && !string.IsNullOrWhiteSpace(c.GeneratorId)
                && string.Equals(c.Classification, "PRODUCTION", StringComparison.OrdinalIgnoreCase);

        private static bool Compatible(TailoringSelectionCandidate c, TailoringBiasProfile profile)
        {
            if (profile == null)
                return true;

            if (profile.DeniedConstructions != null
                && profile.DeniedConstructions.Any(x => Eq(x, c.Construction)))
                return false;

            if (profile.AllowedConstructions != null
                && profile.AllowedConstructions.Count > 0
                && !profile.AllowedConstructions.Any(x => Eq(x, c.Construction)))
                return false;

            return true;
        }

        private static int Score(TailoringSelectionCandidate c, TailoringBiasProfile p)
        {
            int score = 0;
            score += Lookup(p.FamilyWeights, c.Family);
            score += Lookup(p.ConstructionWeights, c.Construction);
            score += Lookup(p.MaterialWeights, c.Material);
            score += Lookup(p.StyleWeights, c.Style);
            score += Lookup(p.PaletteWeights, c.Palette);

            foreach (string motif in c.MotifTokens())
                score += Lookup(p.MotifWeights, motif);
            foreach (string decal in c.DecalTokens())
                score += Lookup(p.DecalWeights, decal);

            return score;
        }

        private static int Lookup(Dictionary<string, int> table, string key)
        {
            if (table == null || string.IsNullOrWhiteSpace(key))
                return 0;

            foreach (var pair in table)
            {
                if (Eq(pair.Key, key))
                    return pair.Value;
            }

            return 0;
        }

        private static bool Eq(string a, string b)
            => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);

        private static ulong StableHash(string text)
        {
            const ulong Offset = 14695981039346656037UL;
            const ulong Prime = 1099511628211UL;
            ulong hash = Offset;
            foreach (char ch in (text ?? "").ToLowerInvariant())
            {
                hash ^= ch;
                hash *= Prime;
            }
            return hash;
        }

        private static ulong SplitMix64(ulong state)
        {
            ulong z = state + 0x9E3779B97F4A7C15UL;
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9UL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBUL;
            return z ^ (z >> 31);
        }
    }
}
