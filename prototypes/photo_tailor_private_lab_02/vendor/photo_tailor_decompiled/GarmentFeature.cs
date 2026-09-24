using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentFeature
{
	[JsonPropertyName("type")]
	public string Type { get; set; } = "";

	[JsonPropertyName("x")]
	public double X { get; set; }

	[JsonPropertyName("y")]
	public double Y { get; set; }

	[JsonPropertyName("width")]
	public double Width { get; set; }

	[JsonPropertyName("height")]
	public double Height { get; set; }

	[JsonPropertyName("side")]
	public string Side { get; set; } = "center";

	[JsonPropertyName("palette_index")]
	public int PaletteIndex { get; set; } = -1;

	[JsonPropertyName("layer")]
	public int Layer { get; set; }

	[JsonPropertyName("confidence")]
	public double Confidence { get; set; }
}
