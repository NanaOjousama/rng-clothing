using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentSpec
{
	[JsonPropertyName("schema_version")]
	public int SchemaVersion { get; set; } = 1;

	[JsonPropertyName("logical_garment_id")]
	public string LogicalGarmentId { get; set; } = "";

	[JsonPropertyName("render_role")]
	public string RenderRole { get; set; } = "whole";

	[JsonPropertyName("artwork_top")]
	public double ArtworkTop { get; set; }

	[JsonPropertyName("artwork_bottom")]
	public double ArtworkBottom { get; set; } = 1.0;

	[JsonPropertyName("blueprint")]
	public GarmentBlueprint? Blueprint { get; set; }

	[JsonPropertyName("category")]
	public string Category { get; set; } = "shirt";

	[JsonPropertyName("name")]
	public string Name { get; set; } = "Photo Garment";

	[JsonPropertyName("semantic_description")]
	public string SemanticDescription { get; set; } = "shirt";

	[JsonPropertyName("primary_color")]
	public string PrimaryColor { get; set; } = "#3A3946";

	[JsonPropertyName("secondary_color")]
	public string SecondaryColor { get; set; } = "#22A65F";

	[JsonPropertyName("accent_color")]
	public string AccentColor { get; set; } = "#FAF6F6";

	[JsonPropertyName("palette")]
	public List<string> Palette { get; set; } = new List<string>();

	[JsonPropertyName("sleeve_palette")]
	public List<string> SleevePalette { get; set; } = new List<string>();

	[JsonPropertyName("sleeve_pattern_map")]
	public List<int> SleevePatternMap { get; set; } = new List<int>();

	[JsonPropertyName("sleeve_pattern_width")]
	public int SleevePatternWidth { get; set; }

	[JsonPropertyName("sleeve_pattern_height")]
	public int SleevePatternHeight { get; set; }

	[JsonPropertyName("pattern_map")]
	public List<int> PatternMap { get; set; } = new List<int>();

	[JsonPropertyName("pattern_width")]
	public int PatternWidth { get; set; }

	[JsonPropertyName("pattern_height")]
	public int PatternHeight { get; set; }

	[JsonPropertyName("pattern")]
	public string Pattern { get; set; } = "solid";

	[JsonPropertyName("silhouette")]
	public string Silhouette { get; set; } = "shirt";

	[JsonPropertyName("coverage")]
	public string Coverage { get; set; } = "standard";

	[JsonPropertyName("neckline")]
	public string Neckline { get; set; } = "";

	[JsonPropertyName("detail")]
	public string Detail { get; set; } = "none";

	[JsonPropertyName("confidence")]
	public double Confidence { get; set; }
}
