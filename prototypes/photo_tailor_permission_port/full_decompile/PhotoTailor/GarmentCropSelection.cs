using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentCropSelection
{
	[JsonPropertyName("left")]
	public double Left { get; set; }

	[JsonPropertyName("top")]
	public double Top { get; set; }

	[JsonPropertyName("right")]
	public double Right { get; set; } = 1.0;

	[JsonPropertyName("bottom")]
	public double Bottom { get; set; } = 1.0;

	[JsonPropertyName("category_hint")]
	public string CategoryHint { get; set; } = "auto";
}
