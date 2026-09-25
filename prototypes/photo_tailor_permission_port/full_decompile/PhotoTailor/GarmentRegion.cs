using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentRegion
{
	[JsonPropertyName("id")]
	public int Id { get; set; }

	[JsonPropertyName("role")]
	public string Role { get; set; } = "whole";

	[JsonPropertyName("left")]
	public double Left { get; set; }

	[JsonPropertyName("top")]
	public double Top { get; set; }

	[JsonPropertyName("width")]
	public double Width { get; set; } = 1.0;

	[JsonPropertyName("height")]
	public double Height { get; set; } = 1.0;

	[JsonPropertyName("pattern")]
	public string Pattern { get; set; } = "solid";

	[JsonPropertyName("palette_indices")]
	public List<int> PaletteIndices { get; set; } = new List<int>();

	[JsonPropertyName("layer")]
	public int Layer { get; set; }
}
