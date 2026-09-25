using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class OutfitSpec
{
	[JsonPropertyName("outfit_name")]
	public string OutfitName { get; set; } = "Photo Outfit";

	[JsonPropertyName("items")]
	public List<GarmentSpec> Items { get; set; } = new List<GarmentSpec>();
}
