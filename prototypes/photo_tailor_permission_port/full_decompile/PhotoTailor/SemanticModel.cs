using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class SemanticModel
{
	[JsonPropertyName("category")]
	public string Category { get; set; } = "";

	[JsonPropertyName("vocabulary")]
	public List<string> Vocabulary { get; set; } = new List<string>();

	[JsonPropertyName("idf")]
	public List<double> Idf { get; set; } = new List<double>();

	[JsonPropertyName("ridge")]
	public RidgeModel Ridge { get; set; } = new RidgeModel();

	[JsonPropertyName("items")]
	public List<SemanticItem> Items { get; set; } = new List<SemanticItem>();
}
