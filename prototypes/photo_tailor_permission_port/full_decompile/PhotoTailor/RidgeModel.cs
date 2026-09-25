using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class RidgeModel
{
	[JsonPropertyName("coefficients")]
	public List<List<double>> Coefficients { get; set; } = new List<List<double>>();

	[JsonPropertyName("intercept")]
	public List<double> Intercept { get; set; } = new List<double>();
}
