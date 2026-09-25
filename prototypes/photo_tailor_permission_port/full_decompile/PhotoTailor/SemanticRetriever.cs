using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace PhotoTailor;

internal sealed class SemanticRetriever
{
	private readonly Dictionary<string, SemanticModel> models = new Dictionary<string, SemanticModel>(StringComparer.OrdinalIgnoreCase);

	public SemanticRetriever(string modDirectory)
	{
		string[] array = new string[4] { "shirts", "pants", "hats", "boots" };
		foreach (string text in array)
		{
			string text2 = Path.Combine(modDirectory, "models", "semantic_" + text + ".json");
			SemanticModel semanticModel = JsonSerializer.Deserialize<SemanticModel>(File.ReadAllText(text2));
			if (semanticModel == null)
			{
				throw new InvalidDataException("Invalid semantic model: " + text2);
			}
			models[text] = semanticModel;
		}
	}

	public SemanticItem Retrieve(string category, string query)
	{
		string text = category switch
		{
			"shirt" => "shirts", 
			"pants" => "pants", 
			"hat" => "hats", 
			"boots" => "boots", 
			_ => throw new InvalidOperationException("Unsupported garment category: " + category), 
		};
		SemanticModel semanticModel = models[text];
		string text2 = " " + query.ToLowerInvariant() + " ";
		double[] array = new double[semanticModel.Vocabulary.Count];
		for (int i = 0; i < array.Length; i++)
		{
			int num = CountOccurrences(text2, semanticModel.Vocabulary[i]);
			if (num > 0)
			{
				array[i] = (1.0 + Math.Log(num)) * semanticModel.Idf[i];
			}
		}
		Normalize(array);
		double[] array2 = new double[semanticModel.Ridge.Intercept.Count];
		for (int j = 0; j < array2.Length; j++)
		{
			double num2 = semanticModel.Ridge.Intercept[j];
			List<double> list = semanticModel.Ridge.Coefficients[j];
			for (int k = 0; k < array.Length; k++)
			{
				num2 += list[k] * array[k];
			}
			array2[j] = num2;
		}
		Normalize(array2);
		SemanticItem semanticItem = null;
		double num3 = double.NegativeInfinity;
		foreach (SemanticItem item in semanticModel.Items)
		{
			double num4 = 0.0;
			for (int l = 0; l < array2.Length; l++)
			{
				num4 += array2[l] * item.Latent[l];
			}
			if (num4 > num3)
			{
				num3 = num4;
				semanticItem = item;
			}
		}
		return semanticItem ?? throw new InvalidOperationException("The " + text + " model has no items.");
	}

	private static int CountOccurrences(string text, string token)
	{
		if (token.Length == 0)
		{
			return 0;
		}
		int num = 0;
		int startIndex = 0;
		while ((startIndex = text.IndexOf(token, startIndex, StringComparison.Ordinal)) >= 0)
		{
			num++;
			startIndex += token.Length;
		}
		return num;
	}

	private static void Normalize(double[] values)
	{
		double num = Math.Sqrt(values.Sum((double value) => value * value));
		if (!(num < 1E-08))
		{
			for (int num2 = 0; num2 < values.Length; num2++)
			{
				values[num2] /= num;
			}
		}
	}
}
