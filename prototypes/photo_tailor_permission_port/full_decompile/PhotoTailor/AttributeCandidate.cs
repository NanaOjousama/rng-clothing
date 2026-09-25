using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class AttributeCandidate
{
	[JsonPropertyName("group")]
	public string Group { get; set; } = "";

	[JsonPropertyName("value")]
	public string Value { get; set; } = "";

	[JsonPropertyName("category")]
	public string Category { get; set; } = "";

	[JsonPropertyName("score")]
	public double Score { get; set; }

	[JsonPropertyName("rank")]
	public int Rank { get; set; }
}
