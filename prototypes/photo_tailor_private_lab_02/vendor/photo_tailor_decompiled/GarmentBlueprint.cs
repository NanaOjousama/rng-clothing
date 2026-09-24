using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentBlueprint
{
	[JsonPropertyName("semantic_type")]
	public string SemanticType { get; set; } = "";

	[JsonPropertyName("canvas_width")]
	public int CanvasWidth { get; set; }

	[JsonPropertyName("canvas_height")]
	public int CanvasHeight { get; set; }

	[JsonPropertyName("occupancy_map")]
	public List<int> OccupancyMap { get; set; } = new List<int>();

	[JsonPropertyName("region_map")]
	public List<int> RegionMap { get; set; } = new List<int>();

	[JsonPropertyName("attribute_candidates")]
	public List<AttributeCandidate> AttributeCandidates { get; set; } = new List<AttributeCandidate>();

	[JsonPropertyName("proportions")]
	public GarmentProportions Proportions { get; set; } = new GarmentProportions();

	[JsonPropertyName("regions")]
	public List<GarmentRegion> Regions { get; set; } = new List<GarmentRegion>();

	[JsonPropertyName("features")]
	public List<GarmentFeature> Features { get; set; } = new List<GarmentFeature>();
}
