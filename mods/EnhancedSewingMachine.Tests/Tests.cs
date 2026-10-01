using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xna.Framework;
using EnhancedSewingMachine.GarmentRuntime;
using EnhancedSewingMachine.TailoringSelection;

namespace EnhancedSewingMachine.Tests
{
    internal static class Tests
    {
        private static int failures;

        private static void Check(string name, bool ok)
        {
            Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {name}");
            if (!ok) failures++;
        }

        private static bool Near(float a, float b, float eps = 0.0001f)
            => MathF.Abs(a - b) <= eps;

        private static bool Near(Vector2 a, Vector2 b, float eps = 0.0001f)
            => Near(a.X, b.X, eps) && Near(a.Y, b.Y, eps);

        private static GarmentDefinition Build32()
        {
            return new GarmentDefinition
            {
                Id = "dev.test32",
                Category = "Hat",
                DefinitionVersion = 3,
                WornTexture = "assets/test32.png",
                FrameWidth = 32,
                FrameHeight = 32,
                RenderScale = .5f,
                HairMode = GarmentHairMode.Obscured,
                VanillaReferenceAnchor = new IntPoint(10, 16),
                Metadata = new GarmentTemplateMetadata
                {
                    Family = "DadCap",
                    Construction = "soft-crown",
                    Material = "cotton",
                    Palette = "stone-blue",
                    Motif = "plain"
                },
                Directions = new Dictionary<string, DirectionFrame>(StringComparer.OrdinalIgnoreCase)
                {
                    ["Front"] = new DirectionFrame { SourceX = 0, SourceY = 0, AnchorX = 16, AnchorY = 25, OffsetY = -4 },
                    ["Right"] = new DirectionFrame { SourceX = 0, SourceY = 32, AnchorX = 12, AnchorY = 25, OffsetY = -4 },
                    ["Back"] = new DirectionFrame { SourceX = 0, SourceY = 64, AnchorX = 16, AnchorY = 25, OffsetY = -4 },
                    ["Left"] = new DirectionFrame
                    {
                        MirrorOf = "Right",
                        FlipX = true,
                        AnchorX = 20,
                        AnchorY = 25,
                        OffsetY = -4
                    }
                }
            };
        }

        private static TailoringBiasCatalog BuildBiasCatalog()
        {
            return new TailoringBiasCatalog
            {
                Textiles = new Dictionary<string, TailoringBiasProfile>
                {
                    ["cotton"] = new TailoringBiasProfile
                    {
                        BaseWeight = 100,
                        ConstructionWeights = new Dictionary<string, int>
                        {
                            ["soft_cap"] = 80,
                            ["felt_hat"] = -10,
                            ["knit_cap"] = 10
                        }
                    },
                    ["wool"] = new TailoringBiasProfile
                    {
                        BaseWeight = 100,
                        ConstructionWeights = new Dictionary<string, int>
                        {
                            ["soft_cap"] = -20,
                            ["felt_hat"] = 80,
                            ["knit_cap"] = 50
                        }
                    }
                },
                Inspirations = new Dictionary<string, TailoringBiasProfile>
                {
                    ["sunflower"] = new TailoringBiasProfile
                    {
                        BaseWeight = 100,
                        StyleWeights = new Dictionary<string, int>
                        {
                            ["cottagecore"] = 50,
                            ["casual"] = 10
                        },
                        MotifWeights = new Dictionary<string, int>
                        {
                            ["flower"] = 90
                        },
                        DecalWeights = new Dictionary<string, int>
                        {
                            ["flower_daisy"] = 50
                        }
                    },
                    ["frozen-tear"] = new TailoringBiasProfile
                    {
                        BaseWeight = 100,
                        StyleWeights = new Dictionary<string, int>
                        {
                            ["smart"] = 40
                        },
                        PaletteWeights = new Dictionary<string, int>
                        {
                            ["WINTER_FROST_INK"] = 100
                        }
                    }
                }
            };
        }

        private static List<TailoringSelectionCandidate> BuildSelectionCandidates()
        {
            return new List<TailoringSelectionCandidate>
            {
                new TailoringSelectionCandidate
                {
                    GarmentId = "gen.soft",
                    Construction = "soft_cap",
                    Family = "soft_cap",
                    Style = "casual",
                    Palette = "COASTAL_SEAFOAM_CORAL",
                    Classification = "PRODUCTION",
                    GeneratorId = "v5.authored"
                },
                new TailoringSelectionCandidate
                {
                    GarmentId = "gen.felt",
                    Construction = "felt_hat",
                    Family = "felt_hat",
                    Style = "smart",
                    Palette = "WINTER_FROST_INK",
                    Motif = "pin,band",
                    Decals = "side_pin",
                    Classification = "PRODUCTION",
                    GeneratorId = "v5.authored"
                },
                new TailoringSelectionCandidate
                {
                    GarmentId = "gen.flower",
                    Construction = "knit_cap",
                    Family = "knit_cap",
                    Style = "cottagecore",
                    Palette = "DESERT_CLAY_TURQUOISE",
                    Motif = "flower,bow",
                    Decals = "flower_daisy",
                    Classification = "PRODUCTION",
                    GeneratorId = "v5.authored"
                },
                new TailoringSelectionCandidate
                {
                    GarmentId = "dev.proof32",
                    Construction = "debug",
                    Classification = "",
                    GeneratorId = ""
                },
                new TailoringSelectionCandidate
                {
                    GarmentId = "reference.cap",
                    Construction = "cap_baseball",
                    Classification = "REFERENCE",
                    GeneratorId = "v5.source-backed"
                }
            };
        }

        public static int Main()
        {
            Check("32px at renderScale .5 uses 2 display pixels/source-pixel",
                Near(PlacementMath.GetDrawScale(1f, .5f), 2f));
            Check("16px at renderScale 1 uses vanilla 4 display pixels/source-pixel",
                Near(PlacementMath.GetDrawScale(1f, 1f), 4f));
            Check("32*.5 nominal physical width equals 16*1",
                Near(32 * PlacementMath.GetDrawScale(1f, .5f),
                     16 * PlacementMath.GetDrawScale(1f, 1f)));

            Vector2 pivot = PlacementMath.GetVanillaHatPivot(
                new Vector2(100, 200), Vector2.Zero, Vector2.Zero,
                1f, featureX: 0, featureY: 0, hairstyleOffset: 0,
                heightOffset: 0, animationFlip: false);
            Check("vanilla pivot baseline follows installed 1.6.15 math",
                Near(pivot, new Vector2(92, 188)));

            Vector2 reference = PlacementMath.GetReferenceWorldPoint(
                pivot, Vector2.Zero, new Vector2(10, 16), 1f, 0f);
            Check("reference anchor maps through vanilla 4x density",
                Near(reference, new Vector2(132, 252)));

            Vector2 nudged = PlacementMath.GetCustomDrawPosition(reference, 1, -2, 1f, 0f);
            Check("direction offsets use vanilla logical pixel units",
                Near(nudged, new Vector2(136, 244)));

            GarmentDefinition def = Build32();
            DirectionFrame left = def.Resolve(3);
            Check("left can reuse right source rectangle",
                left != null && left.SourceY == 32 && left.SourceX == 0);
            Check("mirrored left keeps its own anchor and flip",
                left != null && left.FlipX && left.AnchorX == 20 && left.AnchorY == 25);
            Check("valid generic definition passes texture-bound validation",
                def.TryValidate(32, 96, out _));
            Check("obscured hair mode maps to Stardew covered-hair draw type",
                GarmentHairMode.ToVanillaDrawType(def.HairMode) == 1);

            GarmentDefinition badHair = Build32();
            badHair.HairMode = "mystery";
            Check("unknown hair mode is rejected",
                !badHair.TryValidate(32, 96, out _));

            GarmentDefinition badSource = Build32();
            badSource.Directions["Back"].SourceY = 80;
            Check("out-of-bounds source rectangle is rejected",
                !badSource.TryValidate(32, 96, out _));

            GarmentDefinition badMirror = Build32();
            badMirror.Directions["Right"].MirrorOf = "Front";
            Check("mirror-of-mirror chain is rejected",
                !badMirror.TryValidate(32, 96, out _));

            GarmentRenderSnapshot snapshot = def.ToSnapshot("abc123");
            def.RenderScale = 9f;
            def.Directions["Front"].AnchorX = 99;
            Check("resolved item snapshot is independent from later definition edits",
                Near(snapshot.RenderScale, .5f)
                && snapshot.Resolve(2).AnchorX == 16
                && snapshot.HairMode == GarmentHairMode.Obscured
                && snapshot.AppearanceDigest == "abc123");

            var instance = new GarmentInstanceData
            {
                GarmentId = "dev.test32",
                GenerationVersion = 3,
                Seed = 987654321,
                Category = "Hat",
                Family = "DadCap",
                Construction = "soft-crown",
                Material = "cotton",
                Palette = "stone-blue",
                Motif = "plain",
                GeneratorId = "v5.authored",
                GeneratorVersion = 1,
                GeneratorSeed = 424242,
                Style = "casual",
                QualityTier = "Rare",
                Decals = "bow_knot,cuff_stripe",
                Classification = "PRODUCTION",
                FitOffsetX = 1,
                FitOffsetY = -2,
                FitRightOffsetX = 3,
                FitRightOffsetY = -4,
                FitLeftOffsetX = -5,
                FitLeftOffsetY = 6,
                FitBackOffsetX = 7,
                FitBackOffsetY = -8,
                FitScale = 1.1f,
                FitRightScale = 0.95f,
                FitLeftScale = 1.2f,
                FitBackScale = 0.9f,
                Render = snapshot
            };
            string encoded = GarmentInstanceCodec.Encode(instance);
            bool decodedOk = GarmentInstanceCodec.TryDecode(encoded, out GarmentInstanceData decoded, out _);
            Check("garment instance codec round-trips identity and seed",
                decodedOk
                && decoded.GarmentId == instance.GarmentId
                && decoded.Seed == 987654321
                && decoded.GenerationVersion == 3);
            Check("garment instance codec round-trips generator metadata",
                decodedOk
                && decoded.Family == "DadCap"
                && decoded.Construction == "soft-crown"
                && decoded.Material == "cotton"
                && decoded.Palette == "stone-blue"
                && decoded.Motif == "plain"
                && decoded.GeneratorId == "v5.authored"
                && decoded.GeneratorVersion == 1
                && decoded.GeneratorSeed == 424242
                && decoded.Style == "casual"
                && decoded.QualityTier == "Rare"
                && decoded.Decals == "bow_knot,cuff_stripe"
                && decoded.Classification == "PRODUCTION");
            Check("garment instance codec round-trips resolved render snapshot",
                decodedOk
                && Near(decoded.Render.RenderScale, .5f)
                && decoded.Render.FrameWidth == 32
                && decoded.Render.Resolve(3).FlipX
                && decoded.Render.HairMode == GarmentHairMode.Obscured
                && decoded.Render.AppearanceDigest == "abc123");

            Check("garment fit offsets remain independent per direction",
                decodedOk
                && decoded.GetFitOffsetX(2) == 1
                && decoded.GetFitOffsetY(2) == -2
                && decoded.GetFitOffsetX(1) == 3
                && decoded.GetFitOffsetY(1) == -4
                && decoded.GetFitOffsetX(3) == -5
                && decoded.GetFitOffsetY(3) == 6
                && decoded.GetFitOffsetX(0) == 7
                && decoded.GetFitOffsetY(0) == -8
                && Near(decoded.GetFitScale(2), 1.1f)
                && Near(decoded.GetFitScale(1), 0.95f)
                && Near(decoded.GetFitScale(3), 1.2f)
                && Near(decoded.GetFitScale(0), 0.9f));

            GarmentInstanceData directionalFit = decoded.Clone();
            directionalFit.SetFitOffset(1, -2, 4);
            directionalFit.SetFitScale(2, 1.25f);
            Check("editing front scale does not change right/left/back",
                Near(directionalFit.GetFitScale(2), 1.25f)
                && Near(directionalFit.GetFitScale(1), 0.95f)
                && Near(directionalFit.GetFitScale(3), 1.2f)
                && Near(directionalFit.GetFitScale(0), 0.9f));
            directionalFit.SetFitScale(0, 0.85f);
            Check("editing back scale does not change front/right/left",
                Near(directionalFit.GetFitScale(0), 0.85f)
                && Near(directionalFit.GetFitScale(2), 1.25f)
                && Near(directionalFit.GetFitScale(1), 0.95f)
                && Near(directionalFit.GetFitScale(3), 1.2f));

            Check("editing right fit does not move front/left/back",
                directionalFit.GetFitOffsetX(1) == -2
                && directionalFit.GetFitOffsetY(1) == 4
                && directionalFit.GetFitOffsetX(2) == 1
                && directionalFit.GetFitOffsetY(2) == -2
                && directionalFit.GetFitOffsetX(3) == -5
                && directionalFit.GetFitOffsetY(0) == -8);

            directionalFit.ResetAllFitOffsets();
            directionalFit.ResetAllFitScales();
            Check("reset all clears every directional fit offset",
                directionalFit.GetFitOffsetX(2) == 0
                && directionalFit.GetFitOffsetY(2) == 0
                && directionalFit.GetFitOffsetX(1) == 0
                && directionalFit.GetFitOffsetY(1) == 0
                && directionalFit.GetFitOffsetX(3) == 0
                && directionalFit.GetFitOffsetY(3) == 0
                && directionalFit.GetFitOffsetX(0) == 0
                && directionalFit.GetFitOffsetY(0) == 0
                && Near(directionalFit.GetFitScale(2), 1f)
                && Near(directionalFit.GetFitScale(1), 1f)
                && Near(directionalFit.GetFitScale(3), 1f)
                && Near(directionalFit.GetFitScale(0), 1f));

            Check("invalid instance JSON fails closed",
                !GarmentInstanceCodec.TryDecode("{bad json", out _, out _));

            GarmentInstanceData future = instance.Clone();
            future.SchemaVersion = GarmentInstanceData.CurrentSchemaVersion + 1;
            Check("unknown future instance schema fails closed",
                !GarmentInstanceCodec.TryDecode(GarmentInstanceCodec.Encode(future), out _, out _));

            TailoringBiasCatalog biasCatalog = BuildBiasCatalog();
            List<TailoringSelectionCandidate> candidates = BuildSelectionCandidates();

            bool selA = TailoringSelector.TrySelect(
                candidates, biasCatalog, "cotton", "sunflower", 123456,
                out TailoringSelectionResult rollA, out _);
            bool selB = TailoringSelector.TrySelect(
                candidates, biasCatalog, "cotton", "sunflower", 123456,
                out TailoringSelectionResult rollB, out _);
            Check("tailoring selection is deterministic for the same inputs and seed",
                selA && selB && rollA.GarmentId == rollB.GarmentId);

            Check("tailoring selection excludes dev and reference-only garments",
                selA
                && rollA.Scores.Count == 3
                && rollA.Scores.All(x =>
                    x.Candidate.Classification == "PRODUCTION"
                    && !string.IsNullOrWhiteSpace(x.Candidate.GeneratorId)));

            TailoringSelectionScore flowerScore = rollA.Scores.FirstOrDefault(
                x => x.Candidate.GarmentId == "gen.flower");
            TailoringSelectionScore feltSunScore = rollA.Scores.FirstOrDefault(
                x => x.Candidate.GarmentId == "gen.felt");
            Check("Sunflower inspiration materially boosts flower/cottagecore metadata",
                flowerScore != null
                && feltSunScore != null
                && flowerScore.Weight > feltSunScore.Weight);

            bool frozenOk = TailoringSelector.TrySelect(
                candidates, biasCatalog, "wool", "frozen-tear", 999,
                out TailoringSelectionResult frozenRoll, out _);
            TailoringSelectionScore feltFrozen = frozenRoll?.Scores.FirstOrDefault(
                x => x.Candidate.GarmentId == "gen.felt");
            TailoringSelectionScore softFrozen = frozenRoll?.Scores.FirstOrDefault(
                x => x.Candidate.GarmentId == "gen.soft");
            Check("Wool + Frozen Tear strongly biases felt/winter metadata",
                frozenOk
                && feltFrozen != null
                && softFrozen != null
                && feltFrozen.Weight > softFrozen.Weight);

            Check("unknown tailoring profile fails cleanly",
                !TailoringSelector.TrySelect(
                    candidates, biasCatalog, "silk-does-not-exist", "sunflower", 1,
                    out _, out string badProfileError)
                && badProfileError.Contains("Unknown Textile", StringComparison.Ordinal));

            TailoringBiasCatalog gated = BuildBiasCatalog();
            gated.Textiles["cotton"].AllowedConstructions = new List<string> { "soft_cap" };
            bool gateOk = TailoringSelector.TrySelect(
                candidates, gated, "cotton", "sunflower", 77,
                out TailoringSelectionResult gatedRoll, out _);
            Check("optional textile compatibility gate can restrict construction",
                gateOk
                && gatedRoll.Scores.Count == 1
                && gatedRoll.Scores[0].Candidate.Construction == "soft_cap");

            Console.WriteLine(failures == 0 ? "ALL TESTS PASSED" : $"{failures} TEST(S) FAILED");
            return failures == 0 ? 0 : 1;
        }
    }
}
