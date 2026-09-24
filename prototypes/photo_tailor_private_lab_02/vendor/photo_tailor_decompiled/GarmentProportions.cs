using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GarmentProportions
{
	[JsonPropertyName("fit")]
	public string Fit { get; set; } = "regular";

	[JsonPropertyName("source_aspect_ratio")]
	public double SourceAspectRatio { get; set; } = 1.0;

	[JsonPropertyName("garment_length")]
	public double GarmentLength { get; set; } = 1.0;

	[JsonPropertyName("shoulder_width")]
	public double ShoulderWidth { get; set; } = 0.5;

	[JsonPropertyName("torso_width")]
	public double TorsoWidth { get; set; } = 0.5;

	[JsonPropertyName("waist_width")]
	public double WaistWidth { get; set; } = 0.5;

	[JsonPropertyName("hem_width")]
	public double HemWidth { get; set; } = 0.5;

	[JsonPropertyName("sleeve_length")]
	public double SleeveLength { get; set; }

	[JsonPropertyName("sleeve_volume")]
	public double SleeveVolume { get; set; }

	[JsonPropertyName("neckline_width")]
	public double NecklineWidth { get; set; } = 0.25;

	[JsonPropertyName("neckline_depth")]
	public double NecklineDepth { get; set; } = 0.08;

	[JsonPropertyName("open_front")]
	public bool OpenFront { get; set; }

	[JsonPropertyName("asymmetric")]
	public bool Asymmetric { get; set; }
}
