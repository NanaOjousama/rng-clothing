using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class SemanticItem
{
	[JsonPropertyName("item_id")]
	public string ItemId { get; set; } = "";

	[JsonPropertyName("name")]
	public string Name { get; set; } = "";

	[JsonPropertyName("sprite_index")]
	public int SpriteIndex { get; set; }

	[JsonPropertyName("latent")]
	public List<double> Latent { get; set; } = new List<double>();
}
