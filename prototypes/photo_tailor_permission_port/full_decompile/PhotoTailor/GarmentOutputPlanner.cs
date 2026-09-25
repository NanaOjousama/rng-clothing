using System;
using System.Collections.Generic;
using System.Linq;

namespace PhotoTailor;

internal static class GarmentOutputPlanner
{
	private static readonly HashSet<string> CompositeSilhouettes = new HashSet<string>(StringComparer.Ordinal)
	{
		"coat", "trench_coat", "overcoat", "raincoat", "long_raincoat", "parka", "tunic", "long_tunic", "overalls", "jumpsuit",
		"romper", "bodysuit", "dress", "mini_dress", "midi_dress", "maxi_dress"
	};

	public static OutfitSpec Plan(OutfitSpec recognized)
	{
		ArgumentNullException.ThrowIfNull(recognized, "recognized");
		List<GarmentSpec> list = new List<GarmentSpec>();
		foreach (GarmentSpec item in recognized.Items)
		{
			string silhouette = NormalizeSilhouette(item.Silhouette);
			if (!IsCompositeSilhouette(silhouette))
			{
				list.Add(item);
				continue;
			}
			string logicalId = (string.IsNullOrWhiteSpace(item.LogicalGarmentId) ? Guid.NewGuid().ToString("N") : item.LogicalGarmentId);
			double num = ResolveArtworkSplit(item);
			list.Add(ClonePart(item, "shirt", silhouette, "上装", logicalId, "upper", 0.0, num));
			list.Add(ClonePart(item, "pants", silhouette, "下装", logicalId, "lower", num, 1.0));
		}
		return new OutfitSpec
		{
			OutfitName = recognized.OutfitName,
			Items = list
		};
	}

	public static bool IsCompositeSilhouette(string silhouette)
	{
		return CompositeSilhouettes.Contains(NormalizeSilhouette(silhouette));
	}

	public static bool NeedsSleeveSignal(string category, string silhouette)
	{
		if (!string.Equals(category, "shirt", StringComparison.OrdinalIgnoreCase))
		{
			return IsCompositeSilhouette(silhouette);
		}
		return true;
	}

	public static string BuildRenderSuffix(string batchSuffix, int itemIndex)
	{
		if (string.IsNullOrWhiteSpace(batchSuffix))
		{
			throw new ArgumentException("Batch suffix cannot be empty.", "batchSuffix");
		}
		if (itemIndex < 0)
		{
			throw new ArgumentOutOfRangeException("itemIndex");
		}
		return $"{batchSuffix}_{itemIndex:D2}";
	}

	private static GarmentSpec ClonePart(GarmentSpec source, string category, string silhouette, string partName, string logicalId, string renderRole, double artworkTop, double artworkBottom)
	{
		return new GarmentSpec
		{
			SchemaVersion = source.SchemaVersion,
			LogicalGarmentId = logicalId,
			RenderRole = renderRole,
			ArtworkTop = artworkTop,
			ArtworkBottom = artworkBottom,
			Blueprint = CloneBlueprint(source.Blueprint),
			Category = category,
			Name = source.Name + "（" + partName + "）",
			SemanticDescription = source.SemanticDescription,
			PrimaryColor = source.PrimaryColor,
			SecondaryColor = source.SecondaryColor,
			AccentColor = source.AccentColor,
			Palette = new List<string>(source.Palette),
			SleevePalette = new List<string>(source.SleevePalette),
			SleevePatternMap = new List<int>(source.SleevePatternMap),
			SleevePatternWidth = source.SleevePatternWidth,
			SleevePatternHeight = source.SleevePatternHeight,
			PatternMap = new List<int>(source.PatternMap),
			PatternWidth = source.PatternWidth,
			PatternHeight = source.PatternHeight,
			Pattern = source.Pattern,
			Silhouette = silhouette,
			Coverage = source.Coverage,
			Neckline = source.Neckline,
			Detail = source.Detail,
			Confidence = source.Confidence
		};
	}

	private static double ResolveArtworkSplit(GarmentSpec source)
	{
		return Math.Clamp(source.Blueprint?.Regions.Where((GarmentRegion region) => string.Equals(region.Role, "lower", StringComparison.OrdinalIgnoreCase)).Select((GarmentRegion region) => region.Top).FirstOrDefault((double value) => value > 0.0) ?? 0.5, 0.28, 0.72);
	}

	private static GarmentBlueprint? CloneBlueprint(GarmentBlueprint? source)
	{
		if (source == null)
		{
			return null;
		}
		GarmentProportions garmentProportions = source.Proportions ?? new GarmentProportions();
		return new GarmentBlueprint
		{
			SemanticType = source.SemanticType,
			CanvasWidth = source.CanvasWidth,
			CanvasHeight = source.CanvasHeight,
			OccupancyMap = new List<int>(source.OccupancyMap ?? new List<int>()),
			RegionMap = new List<int>(source.RegionMap ?? new List<int>()),
			AttributeCandidates = (source.AttributeCandidates ?? new List<AttributeCandidate>()).Select((AttributeCandidate candidate) => new AttributeCandidate
			{
				Group = candidate.Group,
				Value = candidate.Value,
				Category = candidate.Category,
				Score = candidate.Score,
				Rank = candidate.Rank
			}).ToList(),
			Proportions = new GarmentProportions
			{
				Fit = garmentProportions.Fit,
				SourceAspectRatio = garmentProportions.SourceAspectRatio,
				GarmentLength = garmentProportions.GarmentLength,
				ShoulderWidth = garmentProportions.ShoulderWidth,
				TorsoWidth = garmentProportions.TorsoWidth,
				WaistWidth = garmentProportions.WaistWidth,
				HemWidth = garmentProportions.HemWidth,
				SleeveLength = garmentProportions.SleeveLength,
				SleeveVolume = garmentProportions.SleeveVolume,
				NecklineWidth = garmentProportions.NecklineWidth,
				NecklineDepth = garmentProportions.NecklineDepth,
				OpenFront = garmentProportions.OpenFront,
				Asymmetric = garmentProportions.Asymmetric
			},
			Regions = (source.Regions ?? new List<GarmentRegion>()).Select((GarmentRegion region) => new GarmentRegion
			{
				Id = region.Id,
				Role = region.Role,
				Left = region.Left,
				Top = region.Top,
				Width = region.Width,
				Height = region.Height,
				Pattern = region.Pattern,
				PaletteIndices = new List<int>(region.PaletteIndices ?? new List<int>()),
				Layer = region.Layer
			}).ToList(),
			Features = (source.Features ?? new List<GarmentFeature>()).Select((GarmentFeature feature) => new GarmentFeature
			{
				Type = feature.Type,
				X = feature.X,
				Y = feature.Y,
				Width = feature.Width,
				Height = feature.Height,
				Side = feature.Side,
				PaletteIndex = feature.PaletteIndex,
				Layer = feature.Layer,
				Confidence = feature.Confidence
			}).ToList()
		};
	}

	private static string NormalizeSilhouette(string value)
	{
		return (value ?? "").Trim().ToLowerInvariant().Replace('-', '_')
			.Replace(' ', '_');
	}
}
