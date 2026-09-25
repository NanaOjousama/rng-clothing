using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using SkiaSharp;

namespace PhotoTailor;

internal sealed class LocalOutfitAnalyzer
{
	private readonly record struct Score(string Value, double Similarity);

	private readonly record struct ForegroundInfo(SKRectI Box, bool ProductBackground, double BackgroundRatio);

	private readonly record struct TextureSample(List<Rgb> Palette, List<int> Map, int Width, int Height);

	private readonly record struct Rgb(byte R, byte G, byte B)
	{
		public RgbF AsFloat => new RgbF((int)R, (int)G, (int)B);

		public string Hex => $"#{R:X2}{G:X2}{B:X2}";

		public Rgb(int r, int g, int b)
			: this((byte)r, (byte)g, (byte)b)
		{
		}
	}

	private readonly record struct RgbF(double R, double G, double B)
	{
		public Rgb Rounded => new Rgb((int)Math.Clamp(Math.Round(R), 0.0, 255.0), (int)Math.Clamp(Math.Round(G), 0.0, 255.0), (int)Math.Clamp(Math.Round(B), 0.0, 255.0));
	}

	private sealed class FashionLabelFile
	{
		[JsonPropertyName("labels")]
		public List<FashionLabel> Labels { get; set; } = new List<FashionLabel>();
	}

	private sealed class FashionLabel
	{
		[JsonPropertyName("group")]
		public string Group { get; set; } = "";

		[JsonPropertyName("value")]
		public string Value { get; set; } = "";

		[JsonPropertyName("category")]
		public string Category { get; set; } = "";

		[JsonPropertyName("embedding")]
		public float[] Embedding { get; set; } = Array.Empty<float>();
	}

	private const int BlueprintMapSize = 64;

	private static readonly float[] Mean = new float[3] { 0.5f, 0.5f, 0.5f };

	private static readonly float[] Std = new float[3] { 0.5f, 0.5f, 0.5f };

	private static readonly Dictionary<string, Rgb> NamedColors = new Dictionary<string, Rgb>(StringComparer.Ordinal)
	{
		["black"] = new Rgb(25, 22, 25),
		["white"] = new Rgb(242, 242, 238),
		["gray"] = new Rgb(130, 132, 132),
		["charcoal"] = new Rgb(45, 50, 45),
		["mint green"] = new Rgb(76, 190, 145),
		["teal"] = new Rgb(0, 160, 150),
		["green"] = new Rgb(42, 128, 63),
		["blue"] = new Rgb(55, 100, 180),
		["navy blue"] = new Rgb(25, 42, 82),
		["red"] = new Rgb(185, 48, 46),
		["orange"] = new Rgb(218, 112, 38),
		["yellow"] = new Rgb(225, 194, 56),
		["purple"] = new Rgb(119, 72, 151),
		["pink"] = new Rgb(220, 126, 157),
		["coral"] = new Rgb(240, 132, 105),
		["burgundy"] = new Rgb(109, 26, 70),
		["cream"] = new Rgb(240, 228, 176),
		["brown"] = new Rgb(116, 73, 48),
		["beige"] = new Rgb(205, 188, 151)
	};

	private readonly string modelPath;

	private readonly List<FashionLabel> labels;

	private readonly Lazy<InferenceSession> session;

	public LocalOutfitAnalyzer(string modDirectory)
	{
		modelPath = Path.Combine(modDirectory, "models", "marqo_fashion_siglip_vision_uint8.onnx");
		string text = Path.Combine(modDirectory, "models", "fashion_siglip_labels.json");
		if (!File.Exists(text))
		{
			throw new FileNotFoundException("离线服装标签文件不存在。", text);
		}
		labels = JsonSerializer.Deserialize<FashionLabelFile>(File.ReadAllText(text))?.Labels ?? throw new InvalidDataException("离线服装标签文件无法读取。");
		if (labels.Count == 0 || labels.Any((FashionLabel label) => label.Embedding.Length != 768))
		{
			throw new InvalidDataException("离线服装标签文件格式不正确。");
		}
		session = new Lazy<InferenceSession>(delegate
		{
			if (!File.Exists(modelPath))
			{
				throw new FileNotFoundException("离线照片识别模型不存在。", modelPath);
			}
			SessionOptions options = new SessionOptions
			{
				GraphOptimizationLevel = GraphOptimizationLevel.ORT_ENABLE_ALL,
				InterOpNumThreads = 1
			};
			return new InferenceSession(modelPath, options);
		}, LazyThreadSafetyMode.ExecutionAndPublication);
	}

	public OutfitSpec Analyze(string imagePath)
	{
		//IL_0052: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e7: Unknown result type (might be due to invalid IL or missing references)
		//IL_025f: Unknown result type (might be due to invalid IL or missing references)
		//IL_026d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0272: Unknown result type (might be due to invalid IL or missing references)
		//IL_0276: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b9: Unknown result type (might be due to invalid IL or missing references)
		if (!File.Exists(imagePath))
		{
			throw new FileNotFoundException("选择的图片已经不存在。", imagePath);
		}
		SKBitmap val = SKBitmap.Decode(imagePath) ?? throw new InvalidDataException("无法读取这张图片，请改用 PNG、JPG 或 WEBP 格式。");
		try
		{
			if (val.Width < 24 || val.Height < 24)
			{
				throw new InvalidDataException("图片尺寸太小，至少需要 24×24 像素。");
			}
			ForegroundInfo foregroundInfo = FindForegroundBox(val);
			SKRectI box = foregroundInfo.Box;
			double num = (double)(((SKRectI)(ref box)).Width * ((SKRectI)(ref box)).Height) / (double)(val.Width * val.Height);
			bool num2 = foregroundInfo.ProductBackground || (foregroundInfo.BackgroundRatio >= 0.22 && num <= 0.88);
			List<GarmentSpec> list = new List<GarmentSpec>();
			if (num2)
			{
				double[] embedding = Embed(val, box, foregroundInfo.ProductBackground);
				List<Score> scores = Scores(embedding, "category");
				string category = PickProductCategory(scores, box, embedding);
				list.Add(Describe(val, box, embedding, category, foregroundInfo.ProductBackground));
			}
			else
			{
				SKRectI val2 = default(SKRectI);
				foreach (KeyValuePair<string, (double, double, double, double)> item in new Dictionary<string, (double, double, double, double)>
				{
					["hat"] = (0.12, 0.0, 0.88, 0.3),
					["shirt"] = (0.1, 0.16, 0.9, 0.62),
					["pants"] = (0.12, 0.45, 0.88, 0.88),
					["boots"] = (0.08, 0.7, 0.92, 1.0)
				})
				{
					var (category2, tuple2) = item;
					((SKRectI)(ref val2))._002Ector((int)((double)val.Width * tuple2.Item1), (int)((double)val.Height * tuple2.Item2), Math.Max((int)((double)val.Width * tuple2.Item3), 1), Math.Max((int)((double)val.Height * tuple2.Item4), 1));
					val2 = ClampRect(val2, val.Width, val.Height);
					double[] embedding2 = Embed(val, val2, productBackground: false);
					List<Score> source = Scores(embedding2, "category");
					double similarity = source.First((Score pair) => pair.Value == category2).Similarity;
					double similarity2 = source.First((Score pair) => pair.Value == "none").Similarity;
					double num3 = source.Where((Score pair) => pair.Value != category2 && pair.Value != "none").Max((Score pair) => pair.Similarity);
					bool flag = similarity >= Math.Max(similarity2 + 0.006, num3 - 0.012);
					if (!flag && category2 == "shirt")
					{
						bool num4 = Scores(embedding2, "silhouette", "shirt")[0].Similarity >= 0.036;
						bool flag2 = similarity >= similarity2 - 0.014 && similarity >= num3 - 0.035;
						flag = num4 & flag2;
					}
					if (flag)
					{
						list.Add(Describe(val, val2, embedding2, category2, productBackground: false));
					}
				}
			}
			return GarmentOutputPlanner.Plan(new OutfitSpec
			{
				OutfitName = Path.GetFileNameWithoutExtension(imagePath),
				Items = list
			});
		}
		finally
		{
			((IDisposable)val)?.Dispose();
		}
	}

	public OutfitSpec Analyze(string imagePath, IReadOnlyList<GarmentCropSelection> selections)
	{
		//IL_00d7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00de: Expected O, but got Unknown
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_0105: Unknown result type (might be due to invalid IL or missing references)
		//IL_010a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0121: Unknown result type (might be due to invalid IL or missing references)
		//IL_0151: Unknown result type (might be due to invalid IL or missing references)
		//IL_0160: Unknown result type (might be due to invalid IL or missing references)
		ArgumentNullException.ThrowIfNull(selections, "selections");
		if (selections.Count == 0)
		{
			return Analyze(imagePath);
		}
		if (!File.Exists(imagePath))
		{
			throw new FileNotFoundException("选择的图片已经不存在。", imagePath);
		}
		SKBitmap val = SKBitmap.Decode(imagePath) ?? throw new InvalidDataException("无法读取这张图片，请改用 PNG、JPG 或 WEBP 格式。");
		try
		{
			if (val.Width < 24 || val.Height < 24)
			{
				throw new InvalidDataException("图片尺寸太小，至少需要 24×24 像素。");
			}
			List<GarmentSpec> list = new List<GarmentSpec>(selections.Count);
			SKRectI val2 = default(SKRectI);
			foreach (GarmentCropSelection selection in selections)
			{
				ArgumentNullException.ThrowIfNull(selection, "selection");
				(int Left, int Top, int Right, int Bottom) tuple = ResolveCropSelection(selection, val.Width, val.Height);
				int item = tuple.Left;
				int item2 = tuple.Top;
				int item3 = tuple.Right;
				int item4 = tuple.Bottom;
				string text = NormalizeCropCategoryHint(selection.CategoryHint);
				((SKRectI)(ref val2))._002Ector(item, item2, item3, item4);
				SKBitmap val3 = new SKBitmap();
				try
				{
					if (!val.ExtractSubset(val3, val2))
					{
						throw new InvalidDataException("无法裁切所选衣物区域。");
					}
					SKRectI val4 = new SKRectI(0, 0, val3.Width, val3.Height);
					bool productBackground = FindForegroundBox(val3).ProductBackground;
					double[] embedding = Embed(val3, val4, productBackground);
					string category = ((text == "auto") ? PickProductCategory(Scores(embedding, "category"), val4, embedding) : text);
					list.Add(Describe(val3, val4, embedding, category, productBackground, text == "auto"));
				}
				finally
				{
					((IDisposable)val3)?.Dispose();
				}
			}
			return GarmentOutputPlanner.Plan(new OutfitSpec
			{
				OutfitName = Path.GetFileNameWithoutExtension(imagePath),
				Items = list
			});
		}
		finally
		{
			((IDisposable)val)?.Dispose();
		}
	}

	internal static (int Left, int Top, int Right, int Bottom) ResolveCropSelection(GarmentCropSelection selection, int imageWidth, int imageHeight)
	{
		ArgumentNullException.ThrowIfNull(selection, "selection");
		if (imageWidth < 1 || imageHeight < 1)
		{
			throw new ArgumentOutOfRangeException("imageWidth", "图片尺寸必须大于零。");
		}
		if (!double.IsFinite(selection.Left) || !double.IsFinite(selection.Top) || !double.IsFinite(selection.Right) || !double.IsFinite(selection.Bottom))
		{
			throw new InvalidDataException("衣物选择框坐标必须是有效数字。");
		}
		double num = Math.Clamp(selection.Left, 0.0, 1.0);
		double num2 = Math.Clamp(selection.Top, 0.0, 1.0);
		double num3 = Math.Clamp(selection.Right, 0.0, 1.0);
		double num4 = Math.Clamp(selection.Bottom, 0.0, 1.0);
		if (num3 <= num || num4 <= num2)
		{
			throw new InvalidDataException("衣物选择框没有有效面积，请重新框选。");
		}
		int num5 = Math.Clamp((int)Math.Floor(num * (double)imageWidth), 0, imageWidth - 1);
		int num6 = Math.Clamp((int)Math.Floor(num2 * (double)imageHeight), 0, imageHeight - 1);
		int num7 = Math.Clamp((int)Math.Ceiling(num3 * (double)imageWidth), num5 + 1, imageWidth);
		int num8 = Math.Clamp((int)Math.Ceiling(num4 * (double)imageHeight), num6 + 1, imageHeight);
		if (num7 - num5 < 24 || num8 - num6 < 24)
		{
			throw new InvalidDataException("衣物选择框太小，宽度和高度至少需要 24 像素。");
		}
		return (Left: num5, Top: num6, Right: num7, Bottom: num8);
	}

	internal static string NormalizeCropCategoryHint(string? categoryHint)
	{
		string text = (string.IsNullOrWhiteSpace(categoryHint) ? "auto" : categoryHint.Trim().ToLowerInvariant());
		switch (text)
		{
		case "auto":
		case "shirt":
		case "pants":
		case "hat":
		case "boots":
			return text;
		default:
			throw new InvalidDataException("不支持的衣物类别提示“" + categoryHint + "”，请选择 auto、shirt、pants、hat 或 boots。");
		}
	}

	private GarmentSpec Describe(SKBitmap bitmap, SKRectI box, double[] embedding, string category, bool productBackground, bool allowCompositeSilhouette = true)
	{
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_032a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0333: Unknown result type (might be due to invalid IL or missing references)
		//IL_0342: Unknown result type (might be due to invalid IL or missing references)
		//IL_0355: Unknown result type (might be due to invalid IL or missing references)
		//IL_0383: Unknown result type (might be due to invalid IL or missing references)
		//IL_0545: Unknown result type (might be due to invalid IL or missing references)
		List<Score> categoryScores = Scores(embedding, "category");
		List<Score> list = Scores(embedding, "silhouette", category);
		if (!allowCompositeSilhouette)
		{
			List<Score> list2 = list.Where((Score score3) => !GarmentOutputPlanner.IsCompositeSilhouette(score3.Value)).ToList();
			if (list2.Count > 0)
			{
				list = list2;
			}
		}
		Score selected = list[0];
		List<Score> list3 = Scores(embedding, "pattern");
		Score score = list3[0];
		string text = score.Value;
		if ((text == "horizontal_stripes" || text == "vertical_stripes") ? true : false)
		{
			text = DetectStripeDirection(bitmap, box, text);
		}
		string value = selected.Value;
		bool flag = GarmentOutputPlanner.NeedsSleeveSignal(category, value);
		string category2 = (flag ? "shirt" : category);
		List<Score> list4 = Scores(embedding, "coverage", category2);
		string text2 = ((list4.Count > 0) ? list4[0].Value : "standard");
		List<Score> list5 = Scores(embedding, "neckline", category2);
		List<Score> list6 = Scores(embedding, "detail", category2);
		string text3 = list5.FirstOrDefault().Value ?? "";
		string text4 = list6.FirstOrDefault().Value ?? "none";
		if (category == "shirt" && selected.Value == "shirt" && text2 == "short_sleeve" && text3 == "collared" && text4 != "buttons")
		{
			Score score2 = list.FirstOrDefault((Score score3) => score3.Value == "polo");
			if (score2.Value == "polo" && score2.Similarity >= selected.Similarity - 0.006)
			{
				selected = score2;
			}
		}
		selected = PreferSpecificSilhouette(category, selected, list);
		value = selected.Value;
		if (value != null)
		{
			int length = value.Length;
			if (length != 6)
			{
				if (length == 10)
				{
					char c = value[2];
					if (c != 'd')
					{
						if (c != 'n')
						{
							if (c == 'x' && (value == "maxi_skirt" || value == "maxi_dress"))
							{
								goto IL_02ce;
							}
						}
						else if (value == "mini_skirt" || value == "mini_dress")
						{
							goto IL_02d7;
						}
					}
					else if (value == "midi_skirt" || value == "midi_dress")
					{
						goto IL_02ce;
					}
				}
			}
			else if (value == "shorts")
			{
				goto IL_02d7;
			}
		}
		string text5 = text2;
		goto IL_02e4;
		IL_02ce:
		text5 = "long";
		goto IL_02e4;
		IL_02e4:
		text2 = text5;
		if (list6.Count == 0 || list6[0].Similarity < 0.02)
		{
			text4 = "none";
		}
		if (value == "bodysuit")
		{
			text4 = "none";
		}
		bool[] array = BuildExternalBackgroundMask(bitmap, box);
		List<Rgb> list7 = ExtractColors(bitmap, box, category, productBackground, array);
		TextureSample texture = ExtractTextureSample(bitmap, box, category, text, list7, productBackground, array);
		List<int> list8 = BuildBlueprintOccupancy(bitmap, box, category, productBackground, array, texture.Palette);
		texture = MaskTextureToGarment(texture, list8, text);
		SleeveSignal sleeveSignal = (flag ? SleeveSignalExtractor.Extract(bitmap, box, text2, productBackground, texture.Palette.Select((Rgb color) => color.Hex).ToList(), array) : SleeveSignal.Empty);
		List<string> list9 = list7.Select(NearestColorName).ToList();
		string semanticDescription = string.Join(" ", new string[8]
		{
			list9[0],
			list9[1],
			list9[2],
			text.Replace('_', ' '),
			text2.Replace('_', ' '),
			value.Replace('_', ' '),
			text3.Replace('_', ' '),
			(text4 == "none") ? "" : text4.Replace('_', ' ')
		}.Where((string value3) => !string.IsNullOrWhiteSpace(value3)));
		string name = CultureInfo.InvariantCulture.TextInfo.ToTitleCase($"{list9[0]} {text.Replace('_', ' ')} {value.Replace('_', ' ')}");
		double value2 = Math.Clamp(0.72 + (selected.Similarity + score.Similarity) * 0.12, 0.55, 0.99);
		GarmentBlueprint blueprint = BuildBlueprint(bitmap, box, category, value, text, text2, text3, text4, productBackground, array, texture, categoryScores, list, list3, list4, list5, list6, list8);
		return new GarmentSpec
		{
			SchemaVersion = 3,
			LogicalGarmentId = Guid.NewGuid().ToString("N"),
			RenderRole = "whole",
			Blueprint = blueprint,
			Category = category,
			Name = name,
			SemanticDescription = semanticDescription,
			PrimaryColor = list7[0].Hex,
			SecondaryColor = list7[1].Hex,
			AccentColor = list7[2].Hex,
			Palette = texture.Palette.Select((Rgb color) => color.Hex).ToList(),
			SleevePalette = sleeveSignal.Palette,
			SleevePatternMap = sleeveSignal.PatternMap,
			SleevePatternWidth = sleeveSignal.PatternWidth,
			SleevePatternHeight = sleeveSignal.PatternHeight,
			PatternMap = texture.Map,
			PatternWidth = texture.Width,
			PatternHeight = texture.Height,
			Pattern = text,
			Silhouette = value,
			Coverage = text2,
			Neckline = text3,
			Detail = text4,
			Confidence = Math.Round(value2, 4)
		};
		IL_02d7:
		text5 = "short";
		goto IL_02e4;
	}

	private double[] Embed(SKBitmap bitmap, SKRectI requestedBox, bool productBackground)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_0018: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_001f: Expected O, but got Unknown
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_008e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0046: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f0: Unknown result type (might be due to invalid IL or missing references)
		SKRectI val = ClampRect(requestedBox, bitmap.Width, bitmap.Height);
		SKBitmap val2 = new SKBitmap();
		try
		{
			if (!bitmap.ExtractSubset(val2, val))
			{
				throw new InvalidDataException("无法裁切所选图片。");
			}
			if (productBackground)
			{
				for (int i = 0; i < val2.Height; i++)
				{
					for (int j = 0; j < val2.Width; j++)
					{
						if (IsProductBackground(val2.GetPixel(j, i)))
						{
							val2.SetPixel(j, i, SKColors.White);
						}
					}
				}
			}
			SKBitmap val3 = val2.Resize(new SKImageInfo(224, 224, (SKColorType)6, (SKAlphaType)2), (SKFilterQuality)3) ?? throw new InvalidDataException("无法缩放所选图片。");
			try
			{
				DenseTensor<float> denseTensor = new DenseTensor<float>(new ReadOnlySpan<int>(new int[4] { 1, 3, 224, 224 }));
				for (int k = 0; k < 224; k++)
				{
					for (int l = 0; l < 224; l++)
					{
						SKColor pixel = val3.GetPixel(l, k);
						denseTensor[new int[4] { 0, 0, k, l }] = ((float)(int)((SKColor)(ref pixel)).Red / 255f - Mean[0]) / Std[0];
						denseTensor[new int[4] { 0, 1, k, l }] = ((float)(int)((SKColor)(ref pixel)).Green / 255f - Mean[1]) / Std[1];
						denseTensor[new int[4] { 0, 2, k, l }] = ((float)(int)((SKColor)(ref pixel)).Blue / 255f - Mean[2]) / Std[2];
					}
				}
				List<NamedOnnxValue> inputs = new List<NamedOnnxValue> { NamedOnnxValue.CreateFromTensor("pixel_values", denseTensor) };
				using IDisposableReadOnlyCollection<DisposableNamedOnnxValue> source = session.Value.Run(inputs);
				float[] source2 = source.First((DisposableNamedOnnxValue value) => value.Name == "image_embeds").AsEnumerable<float>().ToArray();
				double norm = Math.Sqrt(source2.Sum((float value) => value * value));
				if (norm < 1E-08)
				{
					throw new InvalidDataException("离线识别模型返回了空结果。");
				}
				return source2.Select((float value) => (double)value / norm).ToArray();
			}
			finally
			{
				((IDisposable)val3)?.Dispose();
			}
		}
		finally
		{
			((IDisposable)val2)?.Dispose();
		}
	}

	private List<Score> Scores(double[] embedding, string group, string category = "")
	{
		return (from grouping in labels.Where((FashionLabel label) => label.Group == @group && (category.Length == 0 || label.Category.Length == 0 || label.Category == category)).GroupBy<FashionLabel, string>((FashionLabel label) => label.Value, StringComparer.Ordinal)
			select new Score(grouping.Key, (@group == "category") ? grouping.Average((FashionLabel label) => Dot(label.Embedding, embedding)) : grouping.Max((FashionLabel label) => Dot(label.Embedding, embedding))) into score
			orderby score.Similarity descending
			select score).ToList();
	}

	private string PickProductCategory(List<Score> scores, SKRectI foreground, double[] embedding)
	{
		string value = scores.First((Score score) => score.Value != "none").Value;
		if (value != "pants")
		{
			return value;
		}
		double similarity = scores.First((Score score) => score.Value == "pants").Similarity;
		double similarity2 = scores.First((Score score) => score.Value == "shirt").Similarity;
		double similarity3 = Scores(embedding, "silhouette", "shirt").First().Similarity;
		double similarity4 = Scores(embedding, "silhouette", "pants").First().Similarity;
		if (similarity3 >= similarity4 + 0.018)
		{
			return "shirt";
		}
		if ((double)((SKRectI)(ref foreground)).Width >= (double)((SKRectI)(ref foreground)).Height * 1.05 && similarity2 >= similarity - 0.018)
		{
			return "shirt";
		}
		return value;
	}

	private static double Dot(float[] left, double[] right)
	{
		double num = 0.0;
		for (int i = 0; i < left.Length; i++)
		{
			num += (double)left[i] * right[i];
		}
		return num;
	}

	private static ForegroundInfo FindForegroundBox(SKBitmap bitmap)
	{
		//IL_0061: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_0263: Unknown result type (might be due to invalid IL or missing references)
		//IL_0274: Unknown result type (might be due to invalid IL or missing references)
		//IL_0142: Unknown result type (might be due to invalid IL or missing references)
		int num = Math.Max(2, (int)((double)Math.Min(bitmap.Width, bitmap.Height) * 0.05));
		int num2 = 0;
		int num3 = 0;
		int num4 = 0;
		for (int i = 0; i < bitmap.Height; i++)
		{
			for (int j = 0; j < bitmap.Width; j++)
			{
				bool num5 = j < num || j >= bitmap.Width - num || i < num || i >= bitmap.Height - num;
				bool flag = IsProductBackground(bitmap.GetPixel(j, i));
				if (flag)
				{
					num4++;
				}
				if (num5)
				{
					num3++;
					if (flag)
					{
						num2++;
					}
				}
			}
		}
		bool flag2 = num3 > 0 && (double)num2 / (double)num3 >= 0.55;
		int num6 = bitmap.Width;
		int num7 = bitmap.Height;
		int num8 = -1;
		int num9 = -1;
		for (int k = 0; k < bitmap.Height; k++)
		{
			for (int l = 0; l < bitmap.Width; l++)
			{
				SKColor pixel = bitmap.GetPixel(l, k);
				int num10 = Math.Min(((SKColor)(ref pixel)).Red, Math.Min(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
				int num11 = Math.Max(((SKColor)(ref pixel)).Red, Math.Max(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
				bool num12;
				if (!flag2)
				{
					if (((SKColor)(ref pixel)).Alpha < 20)
					{
						continue;
					}
					num12 = !IsProductBackground(pixel);
				}
				else
				{
					if (((SKColor)(ref pixel)).Alpha < 20 || num11 <= 60)
					{
						continue;
					}
					num12 = num11 - num10 >= 24;
				}
				if (num12)
				{
					num6 = Math.Min(num6, l);
					num8 = Math.Max(num8, l);
					num7 = Math.Min(num7, k);
					num9 = Math.Max(num9, k);
				}
			}
		}
		double backgroundRatio = (double)num4 / (double)(bitmap.Width * bitmap.Height);
		if (num8 < 0 || (num8 - num6 + 1) * (num9 - num7 + 1) < 20)
		{
			return new ForegroundInfo(new SKRectI(0, 0, bitmap.Width, bitmap.Height), flag2, backgroundRatio);
		}
		int num13 = num8 - num6 + 1;
		int num14 = num9 - num7 + 1;
		int num15 = Math.Max(2, (int)((double)num13 * 0.05));
		int num16 = Math.Max(2, (int)((double)num14 * 0.05));
		return new ForegroundInfo(ClampRect(new SKRectI(num6 - num15, num7 - num16, num8 + 1 + num15, num9 + 1 + num16), bitmap.Width, bitmap.Height), flag2, backgroundRatio);
	}

	private static string DetectStripeDirection(SKBitmap bitmap, SKRectI box, string fallback)
	{
		//IL_00af: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0104: Unknown result type (might be due to invalid IL or missing references)
		//IL_0106: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d4: Unknown result type (might be due to invalid IL or missing references)
		//IL_010f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_011a: Unknown result type (might be due to invalid IL or missing references)
		//IL_011c: Unknown result type (might be due to invalid IL or missing references)
		int num = ((SKRectI)(ref box)).Left + (int)((double)((SKRectI)(ref box)).Width * 0.22);
		int num2 = ((SKRectI)(ref box)).Left + (int)((double)((SKRectI)(ref box)).Width * 0.78);
		int num3 = ((SKRectI)(ref box)).Top + (int)((double)((SKRectI)(ref box)).Height * 0.16);
		int num4 = ((SKRectI)(ref box)).Top + (int)((double)((SKRectI)(ref box)).Height * 0.94);
		if (num2 - num < 3 || num4 - num3 < 3)
		{
			return fallback;
		}
		double num5 = 0.0;
		double num6 = 0.0;
		int num7 = 0;
		int num8 = 0;
		for (int i = num3; i < num4; i++)
		{
			for (int j = num; j < num2; j++)
			{
				SKColor pixel = bitmap.GetPixel(j, i);
				if (j + 1 < num2)
				{
					SKColor pixel2 = bitmap.GetPixel(j + 1, i);
					if (!IsWhiteBackground(pixel) && !IsWhiteBackground(pixel2))
					{
						num5 += ColorDistance(pixel, pixel2);
						num7++;
					}
				}
				if (i + 1 < num4)
				{
					SKColor pixel3 = bitmap.GetPixel(j, i + 1);
					if (!IsWhiteBackground(pixel) && !IsWhiteBackground(pixel3))
					{
						num6 += ColorDistance(pixel, pixel3);
						num8++;
					}
				}
			}
		}
		if (num7 < 24 || num8 < 24)
		{
			return fallback;
		}
		num5 /= (double)num7;
		num6 /= (double)num8;
		if (num6 > num5 * 1.35)
		{
			return "horizontal_stripes";
		}
		if (num5 > num6 * 1.35)
		{
			return "vertical_stripes";
		}
		return fallback;
	}

	private static List<Rgb> ExtractColors(SKBitmap bitmap, SKRectI box, string category, bool productBackground, bool[]? externalBackground)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		//IL_001a: Unknown result type (might be due to invalid IL or missing references)
		//IL_006c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0071: Unknown result type (might be due to invalid IL or missing references)
		SKRectI val = ResolveGarmentSampleBox(box, category, productBackground, bitmap.Width, bitmap.Height);
		List<Rgb> list = new List<Rgb>();
		int num = Math.Max(1, ((SKRectI)(ref val)).Width * ((SKRectI)(ref val)).Height);
		int num2 = Math.Max(1, (int)Math.Sqrt((double)num / 12000.0));
		for (int i = ((SKRectI)(ref val)).Top; i < ((SKRectI)(ref val)).Bottom; i += num2)
		{
			for (int j = ((SKRectI)(ref val)).Left; j < ((SKRectI)(ref val)).Right; j += num2)
			{
				SKColor pixel = bitmap.GetPixel(j, i);
				if (((SKColor)(ref pixel)).Alpha >= 32 && !IsExternalBackground(bitmap, j, i, externalBackground))
				{
					list.Add(new Rgb(((SKColor)(ref pixel)).Red, ((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
				}
			}
		}
		if (list.Count < 16)
		{
			return new List<Rgb>
			{
				new Rgb(58, 57, 70),
				new Rgb(34, 166, 95),
				new Rgb(250, 246, 246)
			};
		}
		int num3 = Math.Min(5, Math.Max(1, list.Count / 20));
		(List<RgbF>, int[], int[]) tuple = KMeans(list, num3);
		List<RgbF> centers = tuple.Item1;
		int[] item = tuple.Item3;
		double total = item.Sum();
		double[] weights = item.Select((int count) => (double)count / total).ToArray();
		int primary = Enumerable.Range(0, num3).MaxBy((int index) => weights[index]);
		int secondary = Enumerable.Range(0, num3).MaxBy((int index) => Distance(centers[index], centers[primary]) * (0.35 + weights[index]));
		HashSet<int> chosen = new HashSet<int> { primary, secondary };
		List<int> list2 = (from index in Enumerable.Range(0, num3)
			where !chosen.Contains(index)
			select index).ToList();
		int num4 = ((list2.Count > 0) ? list2.MaxBy((int index) => Math.Min(Distance(centers[index], centers[primary]), Distance(centers[index], centers[secondary])) * (0.25 + weights[index])) : primary);
		List<int> list3 = new List<int>();
		foreach (int item3 in new int[3] { primary, secondary, num4 }.Concat(from index in Enumerable.Range(0, num3)
			orderby weights[index] descending
			select index))
		{
			if (!list3.Contains(item3))
			{
				list3.Add(item3);
			}
			if (list3.Count == 3)
			{
				break;
			}
		}
		while (list3.Count < 3)
		{
			int item2;
			if (list3.Count <= 0)
			{
				item2 = 0;
			}
			else
			{
				item2 = list3[list3.Count - 1];
			}
			list3.Add(item2);
		}
		return (from index in list3.Take(3)
			select centers[index].Rounded).ToList();
	}

	private static TextureSample ExtractTextureSample(SKBitmap bitmap, SKRectI box, string category, string pattern, List<Rgb> keyColors, bool productBackground, bool[]? externalBackground)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_03bb: Unknown result type (might be due to invalid IL or missing references)
		SKRectI val = ResolveGarmentSampleBox(box, category, productBackground, bitmap.Width, bitmap.Height);
		List<Rgb> list = new List<Rgb>();
		int num = Math.Max(1, (int)Math.Sqrt((double)(((SKRectI)(ref val)).Width * ((SKRectI)(ref val)).Height) / 16000.0));
		for (int i = ((SKRectI)(ref val)).Top; i < ((SKRectI)(ref val)).Bottom; i += num)
		{
			for (int j = ((SKRectI)(ref val)).Left; j < ((SKRectI)(ref val)).Right; j += num)
			{
				SKColor pixel = bitmap.GetPixel(j, i);
				if (((SKColor)(ref pixel)).Alpha >= 32 && !IsExternalBackground(bitmap, j, i, externalBackground))
				{
					list.Add(new Rgb(((SKColor)(ref pixel)).Red, ((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
				}
			}
		}
		List<Rgb> palette = new List<Rgb>(keyColors);
		if (list.Count >= 24)
		{
			int num2;
			switch (pattern)
			{
			case "logo":
			case "graphic":
			case "floral":
			case "plaid":
			case "polka_dot":
				num2 = 48;
				break;
			case "horizontal_stripes":
			case "vertical_stripes":
			case "gradient":
				num2 = 32;
				break;
			default:
				num2 = 18;
				break;
			}
			int num3 = num2;
			int num4 = Math.Min(num3, Math.Max(6, list.Count / 120));
			var (list2, _, counts) = KMeans(list, num4);
			foreach (int item in from index in Enumerable.Range(0, num4)
				orderby counts[index] descending
				select index)
			{
				Rgb candidate = list2[item].Rounded;
				if (palette.All((Rgb existing) => Distance(existing.AsFloat, candidate.AsFloat) >= 7.0))
				{
					palette.Add(candidate);
				}
				if (palette.Count == num3)
				{
					break;
				}
			}
		}
		while (palette.Count < 4)
		{
			List<Rgb> list3 = palette;
			List<Rgb> list4 = palette;
			list3.Add(list4[list4.Count - 1]);
		}
		List<int> list5 = new List<int>(4096);
		for (int num5 = 0; num5 < 64; num5++)
		{
			int num6 = ((SKRectI)(ref val)).Top + ((SKRectI)(ref val)).Height * num5 / 64;
			int val2 = ((SKRectI)(ref val)).Top + ((SKRectI)(ref val)).Height * (num5 + 1) / 64;
			for (int num7 = 0; num7 < 64; num7++)
			{
				int num8 = ((SKRectI)(ref val)).Left + ((SKRectI)(ref val)).Width * num7 / 64;
				int val3 = ((SKRectI)(ref val)).Left + ((SKRectI)(ref val)).Width * (num7 + 1) / 64;
				int[] votes = new int[palette.Count];
				for (int num9 = num6; num9 < Math.Max(num6 + 1, val2); num9++)
				{
					for (int num10 = num8; num10 < Math.Max(num8 + 1, val3); num10++)
					{
						SKColor pixel2 = bitmap.GetPixel(num10, num9);
						if (((SKColor)(ref pixel2)).Alpha >= 32 && !IsExternalBackground(bitmap, num10, num9, externalBackground))
						{
							RgbF value = new RgbF((int)((SKColor)(ref pixel2)).Red, (int)((SKColor)(ref pixel2)).Green, (int)((SKColor)(ref pixel2)).Blue);
							int num11 = Enumerable.Range(0, palette.Count).MinBy((int index) => Distance(value, palette[index].AsFloat));
							votes[num11]++;
						}
					}
				}
				if (votes.Sum() == 0)
				{
					list5.Add(-1);
					continue;
				}
				list5.Add(Enumerable.Range(0, palette.Count).MaxBy((int index) => votes[index]));
			}
		}
		list5 = CleanTextureMap(list5, palette, pattern, 64, 64);
		return new TextureSample(palette, list5, 64, 64);
	}

	private static Score PreferSpecificSilhouette(string category, Score selected, IReadOnlyList<Score> candidates)
	{
		if (category != "pants" || selected.Value != "skirt")
		{
			return selected;
		}
		HashSet<string> specificSkirts = new HashSet<string>(StringComparer.Ordinal) { "mini_skirt", "midi_skirt", "maxi_skirt", "pleated_skirt", "pencil_skirt" };
		Score result = (from candidate in candidates
			where specificSkirts.Contains(candidate.Value)
			orderby candidate.Similarity descending
			select candidate).FirstOrDefault();
		if (result.Value == null || !(result.Similarity >= selected.Similarity - 0.012))
		{
			return selected;
		}
		return result;
	}

	private static List<int> CleanTextureMap(IReadOnlyList<int> source, IReadOnlyList<Rgb> palette, string pattern, int width, int height)
	{
		if (source.Count < width * height || palette.Count == 0)
		{
			return source.ToList();
		}
		List<int> list = source.Take(width * height).ToList();
		int[] histogram = new int[palette.Count];
		foreach (int item in list)
		{
			if (item >= 0 && item < histogram.Length)
			{
				histogram[item]++;
			}
		}
		int occupied = histogram.Sum();
		if (occupied == 0)
		{
			return list;
		}
		int baseIndex = Enumerable.Range(0, histogram.Length).MaxBy((int num5) => histogram[num5]);
		double baseLuma = RelativeLuma(palette[baseIndex]);
		bool flag;
		switch (pattern)
		{
		case "logo":
		case "graphic":
		case "horizontal_stripes":
		case "vertical_stripes":
		case "plaid":
		case "polka_dot":
			flag = true;
			break;
		default:
			flag = false;
			break;
		}
		bool structuredDarkPattern = flag;
		List<int> list2 = (from index2 in Enumerable.Range(0, palette.Count)
			where !IsSuspiciousDark(index2)
			select index2).ToList();
		if (list2.Count == 0)
		{
			list2.Add(baseIndex);
		}
		for (int num = 0; num < list.Count; num++)
		{
			int index = list[num];
			if (IsSuspiciousDark(index))
			{
				list[num] = list2.MinBy((int candidate) => Distance(palette[index].AsFloat, palette[candidate].AsFloat) + Math.Max(0.0, 0.24 - RelativeLuma(palette[candidate])) * 180.0);
			}
		}
		if (!structuredDarkPattern)
		{
			List<int> list3 = list.ToList();
			for (int num2 = 0; num2 < height; num2++)
			{
				for (int num3 = 0; num3 < width; num3++)
				{
					int num4 = num2 * width + num3;
					int current2 = list3[num4];
					if (current2 < 0)
					{
						continue;
					}
					List<int> list4 = new List<int>();
					if (num3 > 0 && list3[num4 - 1] >= 0)
					{
						list4.Add(list3[num4 - 1]);
					}
					if (num3 + 1 < width && list3[num4 + 1] >= 0)
					{
						list4.Add(list3[num4 + 1]);
					}
					if (num2 > 0 && list3[num4 - width] >= 0)
					{
						list4.Add(list3[num4 - width]);
					}
					if (num2 + 1 < height && list3[num4 + width] >= 0)
					{
						list4.Add(list3[num4 + width]);
					}
					if (list4.Count >= 2 && list4.All((int value) => value != current2))
					{
						list[num4] = (from value in list4
							group value by value into @group
							orderby @group.Count() descending, @group.Key
							select @group).First().Key;
					}
				}
			}
		}
		return list;
		bool IsSuspiciousDark(int num5)
		{
			if (num5 < 0 || num5 >= palette.Count || num5 == baseIndex)
			{
				return false;
			}
			double num6 = RelativeLuma(palette[num5]);
			double num7 = (double)histogram[num5] / (double)occupied;
			if (!(num6 < 0.17) || !(baseLuma - num6 >= 0.12))
			{
				return false;
			}
			if (structuredDarkPattern)
			{
				return histogram[num5] < 2;
			}
			return num7 < 0.16;
		}
	}

	private static double RelativeLuma(Rgb color)
	{
		return (0.2126 * (double)(int)color.R + 0.7152 * (double)(int)color.G + 0.0722 * (double)(int)color.B) / 255.0;
	}

	private static GarmentBlueprint BuildBlueprint(SKBitmap bitmap, SKRectI box, string category, string silhouette, string pattern, string coverage, string neckline, string detail, bool productBackground, bool[]? externalBackground, TextureSample texture, List<Score> categoryScores, List<Score> silhouetteScores, List<Score> patternScores, List<Score> coverageScores, List<Score> necklineScores, List<Score> detailScores, IReadOnlyList<int> sharedOccupancy)
	{
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f7: Unknown result type (might be due to invalid IL or missing references)
		List<int> list = ((sharedOccupancy.Count >= 4096) ? sharedOccupancy.Take(4096).ToList() : BuildBlueprintOccupancy(bitmap, box, category, productBackground, externalBackground, texture.Palette));
		bool composite = GarmentOutputPlanner.IsCompositeSilhouette(silhouette);
		double verticalSplit = CompositeVerticalSplit(silhouette);
		List<int> regionMap = BuildRegionMap(list, 64, 64, category, composite, verticalSplit, coverage, neckline);
		List<AttributeCandidate> list2 = new List<AttributeCandidate>();
		AddCandidates(list2, "category", "", categoryScores);
		AddCandidates(list2, "silhouette", category, silhouetteScores);
		AddCandidates(list2, "pattern", "", patternScores);
		AddCandidates(list2, "coverage", category, coverageScores);
		AddCandidates(list2, "neckline", category, necklineScores);
		AddCandidates(list2, "detail", category, detailScores);
		return new GarmentBlueprint
		{
			SemanticType = silhouette,
			CanvasWidth = 64,
			CanvasHeight = 64,
			OccupancyMap = list,
			RegionMap = regionMap,
			AttributeCandidates = list2,
			Proportions = BuildProportions(list, regionMap, 64, 64, box, silhouette, coverage, neckline, detail),
			Regions = BuildRegions(regionMap, 64, 64, texture, pattern, verticalSplit),
			Features = BuildFeatures(texture, silhouette, pattern, neckline, detail, patternScores, necklineScores, detailScores)
		};
	}

	private static void AddCandidates(List<AttributeCandidate> target, string group, string category, IReadOnlyList<Score> scores)
	{
		for (int i = 0; i < Math.Min(3, scores.Count); i++)
		{
			target.Add(new AttributeCandidate
			{
				Group = group,
				Value = scores[i].Value,
				Category = category,
				Score = Math.Round(scores[i].Similarity, 6),
				Rank = i + 1
			});
		}
	}

	private static List<int> BuildBlueprintOccupancy(SKBitmap bitmap, SKRectI box, string category, bool productBackground, bool[]? externalBackground, IReadOnlyList<Rgb> palette)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		//IL_001a: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f1: Unknown result type (might be due to invalid IL or missing references)
		int num = 64;
		int num2 = 64;
		SKRectI val = ResolveGarmentSampleBox(box, category, productBackground, bitmap.Width, bitmap.Height);
		List<int> list = new List<int>(num * num2);
		int num3 = Math.Max(1, ((SKRectI)(ref val)).Width * ((SKRectI)(ref val)).Height);
		int num4 = Math.Max(1, (int)Math.Sqrt((double)num3 / 42000.0));
		for (int i = 0; i < num2; i++)
		{
			int num5 = ((SKRectI)(ref val)).Top + ((SKRectI)(ref val)).Height * i / num2;
			int val2 = ((SKRectI)(ref val)).Top + ((SKRectI)(ref val)).Height * (i + 1) / num2;
			for (int j = 0; j < num; j++)
			{
				int num6 = ((SKRectI)(ref val)).Left + ((SKRectI)(ref val)).Width * j / num;
				int val3 = ((SKRectI)(ref val)).Left + ((SKRectI)(ref val)).Width * (j + 1) / num;
				int num7 = 0;
				int num8 = 0;
				for (int k = num5; k < Math.Max(num5 + 1, val2); k += num4)
				{
					for (int l = num6; l < Math.Max(num6 + 1, val3); l += num4)
					{
						num7++;
						SKColor pixel = bitmap.GetPixel(l, k);
						if (((SKColor)(ref pixel)).Alpha >= 32 && !IsExternalBackground(bitmap, l, k, externalBackground))
						{
							RgbF color = new RgbF((int)((SKColor)(ref pixel)).Red, (int)((SKColor)(ref pixel)).Green, (int)((SKColor)(ref pixel)).Blue);
							if (productBackground || palette.Count <= 0 || !(palette.Min((Rgb candidate) => Distance(color, candidate.AsFloat)) > 88.0))
							{
								num8++;
							}
						}
					}
				}
				list.Add((num8 >= Math.Max(1, (int)Math.Ceiling((double)num7 * 0.16))) ? 1 : 0);
			}
		}
		if (list.Sum() < 12)
		{
			for (int num9 = 2; num9 < num2 - 1; num9++)
			{
				int num10 = ((num9 < num2 / 3) ? (num * 3 / 10) : (num / 4));
				for (int num11 = num / 2 - num10; num11 <= num / 2 + num10; num11++)
				{
					list[num9 * num + Math.Clamp(num11, 0, num - 1)] = 1;
				}
			}
		}
		return list;
	}

	private static TextureSample MaskTextureToGarment(TextureSample texture, IReadOnlyList<int> occupancy, string pattern)
	{
		int num = texture.Width * texture.Height;
		if (num <= 0 || texture.Map.Count < num || occupancy.Count < num)
		{
			return texture;
		}
		List<int> list = texture.Map.Take(num).ToList();
		for (int i = 0; i < num; i++)
		{
			if (occupancy[i] == 0)
			{
				list[i] = -1;
			}
		}
		list = CleanTextureMap(list, texture.Palette, pattern, texture.Width, texture.Height);
		return new TextureSample(texture.Palette, list, texture.Width, texture.Height);
	}

	private static List<int> BuildRegionMap(IReadOnlyList<int> occupancy, int width, int height, string category, bool composite, double verticalSplit, string coverage, string neckline)
	{
		bool flag = (category == "shirt") | composite;
		double num = coverage switch
		{
			"sleeveless" => 0.13, 
			"short_sleeve" => 0.48, 
			"three_quarter_sleeve" => 0.74, 
			"long_sleeve" => 0.96, 
			_ => 0.62, 
		};
		List<int> list = Enumerable.Repeat(0, width * height).ToList();
		for (int i = 0; i < height; i++)
		{
			double num2 = ((double)i + 0.5) / (double)height;
			for (int j = 0; j < width; j++)
			{
				int index = i * width + j;
				if (occupancy[index] != 0)
				{
					double num3 = ((double)j + 0.5) / (double)width;
					if (flag && neckline == "collared" && num2 <= 0.25 && num3 >= 0.29 && num3 <= 0.71)
					{
						list[index] = 7;
					}
					else if (flag && coverage != "sleeveless" && num2 <= num && num3 < 0.31)
					{
						list[index] = 5;
					}
					else if (flag && coverage != "sleeveless" && num2 <= num && num3 > 0.69)
					{
						list[index] = 6;
					}
					else if (composite)
					{
						list[index] = ((num2 < verticalSplit) ? 3 : 4);
					}
					else if (category == "shirt")
					{
						list[index] = 2;
					}
					else if (category == "pants")
					{
						list[index] = 4;
					}
					else
					{
						list[index] = 1;
					}
				}
			}
		}
		return list;
	}

	private static List<GarmentRegion> BuildRegions(IReadOnlyList<int> regionMap, int width, int height, TextureSample texture, string pattern, double verticalSplit)
	{
		Dictionary<int, string> obj = new Dictionary<int, string>
		{
			[1] = "whole",
			[2] = "torso",
			[3] = "upper",
			[4] = "lower",
			[5] = "left_sleeve",
			[6] = "right_sleeve",
			[7] = "collar"
		};
		List<GarmentRegion> list = new List<GarmentRegion>();
		foreach (KeyValuePair<int, string> item in obj)
		{
			var (id, text2) = item;
			List<int> list2 = (from index in Enumerable.Range(0, regionMap.Count)
				where regionMap[index] == id
				select index).ToList();
			if (list2.Count != 0)
			{
				int num2 = list2.Min((int index) => index % width);
				int num3 = list2.Max((int index) => index % width);
				int num4 = list2.Min((int index) => index / width);
				int num5 = list2.Max((int index) => index / width);
				list.Add(new GarmentRegion
				{
					Id = id,
					Role = text2,
					Left = RoundUnit((double)num2 / (double)width),
					Top = RoundUnit((double)num4 / (double)height),
					Width = RoundUnit((double)(num3 - num2 + 1) / (double)width),
					Height = RoundUnit((double)(num5 - num4 + 1) / (double)height),
					Pattern = pattern,
					PaletteIndices = CollectRegionPaletteIndices(texture, text2, verticalSplit),
					Layer = ((text2 == "collar") ? 1 : 0)
				});
			}
		}
		return list;
	}

	private static List<int> CollectRegionPaletteIndices(TextureSample texture, string role, double verticalSplit)
	{
		HashSet<int> hashSet = new HashSet<int>();
		for (int i = 0; i < texture.Height; i++)
		{
			double num = ((double)i + 0.5) / (double)texture.Height;
			for (int j = 0; j < texture.Width; j++)
			{
				double num2 = ((double)j + 0.5) / (double)texture.Width;
				if (role switch
				{
					"upper" => num < verticalSplit, 
					"lower" => num >= verticalSplit, 
					"left_sleeve" => num2 < 0.34, 
					"right_sleeve" => num2 > 0.66, 
					"collar" => num < 0.25 && num2 >= 0.25 && num2 <= 0.75, 
					_ => true, 
				})
				{
					int num3 = texture.Map[i * texture.Width + j];
					if (num3 >= 0 && num3 < texture.Palette.Count)
					{
						hashSet.Add(num3);
					}
				}
			}
		}
		return hashSet.OrderBy((int value) => value).ToList();
	}

	private unsafe static GarmentProportions BuildProportions(IReadOnlyList<int> occupancy, IReadOnlyList<int> regionMap, int width, int height, SKRectI sourceBox, string silhouette, string coverage, string neckline, string detail)
	{
		List<int> source = (from index in Enumerable.Range(0, occupancy.Count)
			where occupancy[index] != 0
			select index).ToList();
		int num = source.Min((int index) => index / width);
		int num2 = source.Max((int index) => index / width);
		int num3 = Math.Max(1, num2 - num + 1);
		double value = RowSpanNear(occupancy, width, height, num + (int)((double)num3 * 0.18));
		double value2 = RowSpanNear(occupancy, width, height, num + (int)((double)num3 * 0.38));
		double num4 = RowSpanNear(occupancy, width, height, num + (int)((double)num3 * 0.62));
		double num5 = RowSpanNear(occupancy, width, height, num2 - 1);
		if (silhouette != null)
		{
			int length = silhouette.Length;
			if (length != 5)
			{
				if (length != 10)
				{
					if (length == 13 && silhouette == "pleated_skirt")
					{
						goto IL_01d9;
					}
				}
				else
				{
					char c = silhouette[2];
					if (c != 'd')
					{
						if (c != 'n')
						{
							if (c == 'x' && (silhouette == "maxi_skirt" || silhouette == "maxi_dress"))
							{
								goto IL_01d9;
							}
						}
						else if (silhouette == "mini_skirt" || silhouette == "mini_dress")
						{
							goto IL_01d9;
						}
					}
					else if (silhouette == "midi_skirt" || silhouette == "midi_dress")
					{
						goto IL_01d9;
					}
				}
			}
			else
			{
				char c = silhouette[0];
				if (c != 'd')
				{
					if (c == 's' && silhouette == "skirt")
					{
						goto IL_01d9;
					}
				}
				else if (silhouette == "dress")
				{
					goto IL_01d9;
				}
			}
		}
		bool flag = false;
		goto IL_01e1;
		IL_01d9:
		flag = true;
		goto IL_01e1;
		IL_01e1:
		if (flag)
		{
			switch (silhouette)
			{
			case "midi_skirt":
			case "maxi_skirt":
			case "midi_dress":
			case "maxi_dress":
				flag = true;
				break;
			default:
				flag = false;
				break;
			}
			bool flag2 = flag;
			num4 = Math.Min(num4, flag2 ? 0.38 : 0.56);
			num5 = Math.Max(num5, flag2 ? 0.94 : ((silhouette == "mini_skirt") ? 0.7 : 0.8));
		}
		else if (silhouette == "pencil_skirt")
		{
			num4 = Math.Min(num4, 0.58);
			num5 = Math.Clamp(num5, 0.44, 0.6);
		}
		int num6 = regionMap.Count((int num7) => (uint)(num7 - 5) <= 1u);
		double value3 = coverage switch
		{
			"sleeveless" => 0.0, 
			"short_sleeve" => 0.38, 
			"three_quarter_sleeve" => 0.68, 
			"long_sleeve" => 0.94, 
			_ => (num6 > 0) ? 0.55 : 0.0, 
		};
		double value4 = Math.Clamp((double)num6 / (double)Math.Max(1, width * height / 3), 0.0, 1.0);
		object obj = neckline switch
		{
			"v_neck" => (0.28, 0.22), 
			"collared" => (0.42, 0.16), 
			"turtleneck" => (0.22, 0.03), 
			"hooded" => (0.46, 0.13), 
			_ => (0.3, 0.09), 
		};
		double item = ((ValueTuple<double, double>*)(&obj))->Item1;
		double item2 = ((ValueTuple<double, double>*)(&obj))->Item2;
		GarmentProportions garmentProportions = new GarmentProportions();
		garmentProportions.Fit = InferFit(silhouette);
		garmentProportions.SourceAspectRatio = Math.Round((double)((SKRectI)(ref sourceBox)).Width / (double)Math.Max(1, ((SKRectI)(ref sourceBox)).Height), 4);
		garmentProportions.GarmentLength = RoundUnit((double)num3 / (double)height);
		garmentProportions.ShoulderWidth = RoundUnit(value);
		garmentProportions.TorsoWidth = RoundUnit(value2);
		garmentProportions.WaistWidth = RoundUnit(num4);
		garmentProportions.HemWidth = RoundUnit(num5);
		garmentProportions.SleeveLength = RoundUnit(value3);
		garmentProportions.SleeveVolume = RoundUnit(value4);
		garmentProportions.NecklineWidth = RoundUnit(item);
		garmentProportions.NecklineDepth = RoundUnit(item2);
		GarmentProportions garmentProportions2 = garmentProportions;
		flag = ((detail == "buttons" || detail == "zipper") ? true : false);
		bool flag3 = flag;
		if (!flag3)
		{
			bool flag4;
			switch (silhouette)
			{
			case "cardigan":
			case "overcoat":
			case "raincoat":
			case "blazer":
			case "jacket":
			case "coat":
			case "trench_coat":
			case "denim_jacket":
			case "leather_jacket":
			case "long_raincoat":
			case "parka":
				flag4 = true;
				break;
			default:
				flag4 = false;
				break;
			}
			flag3 = flag4;
		}
		garmentProportions2.OpenFront = flag3;
		garmentProportions.Asymmetric = DetectAsymmetry(occupancy, width, height);
		return garmentProportions;
	}

	private static double RowSpanNear(IReadOnlyList<int> occupancy, int width, int height, int targetY)
	{
		int num = 0;
		int y;
		for (y = Math.Max(0, targetY - 2); y <= Math.Min(height - 1, targetY + 2); y++)
		{
			List<int> list = (from x in Enumerable.Range(0, width)
				where occupancy[y * width + x] != 0
				select x).ToList();
			if (list.Count > 0)
			{
				num = Math.Max(num, list[list.Count - 1] - list[0] + 1);
			}
		}
		return (double)num / (double)width;
	}

	private static bool DetectAsymmetry(IReadOnlyList<int> occupancy, int width, int height)
	{
		int num = 0;
		int num2 = 0;
		for (int i = 0; i < height; i++)
		{
			for (int j = 0; j < width / 2; j++)
			{
				bool flag = occupancy[i * width + j] != 0;
				bool flag2 = occupancy[i * width + (width - 1 - j)] != 0;
				if (flag || flag2)
				{
					num++;
					if (flag != flag2)
					{
						num2++;
					}
				}
			}
		}
		if (num > 0)
		{
			return (double)num2 / (double)num >= 0.2;
		}
		return false;
	}

	private static string InferFit(string silhouette)
	{
		switch (silhouette)
		{
		case "leggings":
		case "bodysuit":
		case "camisole":
		case "halter_top":
		case "pencil_skirt":
			return "fitted";
		case "overcoat":
		case "long_tunic":
		case "sweatshirt":
		case "parka":
		case "tunic":
		case "hoodie":
		case "coat":
		case "trench_coat":
		case "wide_leg_pants":
			return "oversized";
		default:
			return "regular";
		}
	}

	private static List<GarmentFeature> BuildFeatures(TextureSample texture, string silhouette, string pattern, string neckline, string detail, IReadOnlyList<Score> patternScores, IReadOnlyList<Score> necklineScores, IReadOnlyList<Score> detailScores)
	{
		List<GarmentFeature> list = new List<GarmentFeature>();
		if ((pattern == "logo" || pattern == "graphic") ? true : false)
		{
			var (x, y, width, height) = FindMotifBounds(texture);
			AddFeature(list, pattern, x, y, width, height, "center", 2, 2, FeatureConfidence(patternScores, pattern));
		}
		if (detail != "none" && IsSelectedOrCompetitive(detail, "buttons", detailScores))
		{
			AddFeature(list, "buttons", 0.47, 0.2, 0.06, 0.56, "center", 2, 2, FeatureConfidence(detailScores, "buttons"));
		}
		if (detail != "none" && IsSelectedOrCompetitive(detail, "zipper", detailScores))
		{
			AddFeature(list, "zipper", 0.485, 0.18, 0.03, 0.62, "center", 1, 2, FeatureConfidence(detailScores, "zipper"));
		}
		if (detail != "none" && IsSelectedOrCompetitive(detail, "pockets", detailScores))
		{
			double confidence = FeatureConfidence(detailScores, "pockets");
			AddFeature(list, "pocket", 0.2, 0.52, 0.18, 0.18, "left", 1, 1, confidence);
			AddFeature(list, "pocket", 0.62, 0.52, 0.18, 0.18, "right", 1, 1, confidence);
		}
		if (IsSelectedOrCompetitive(neckline, "collared", necklineScores))
		{
			AddFeature(list, "collar", 0.31, 0.06, 0.38, 0.19, "center", 1, 2, FeatureConfidence(necklineScores, "collared"));
		}
		var (num, num2) = FindHorizontalFeature(texture);
		bool flag;
		switch (silhouette)
		{
		case "jumpsuit":
		case "overcoat":
		case "midi_dress":
		case "mini_dress":
		case "maxi_dress":
		case "trench_coat":
		case "coat":
		case "dress":
		case "romper":
			flag = true;
			break;
		default:
			flag = false;
			break;
		}
		if (flag && num2 >= 0.18)
		{
			AddFeature(list, "belt", 0.16, num - 0.035, 0.68, 0.07, "center", 1, 2, Math.Round(Math.Clamp(0.52 + num2 * 0.45, 0.0, 0.96), 4));
		}
		else if (silhouette == "trench_coat")
		{
			AddFeature(list, "belt", 0.16, 0.54, 0.68, 0.07, "center", 1, 2, 0.62);
		}
		return list;
	}

	private static bool IsSelectedOrCompetitive(string selected, string value, IReadOnlyList<Score> scores)
	{
		if (selected == value)
		{
			return true;
		}
		if (scores.Count == 0)
		{
			return false;
		}
		int num = scores.ToList().FindIndex((Score score) => score.Value == value);
		if (num >= 0 && num < 2)
		{
			return scores[num].Similarity >= scores[0].Similarity - 0.004;
		}
		return false;
	}

	private static double FeatureConfidence(IReadOnlyList<Score> scores, string value)
	{
		Score score = scores.FirstOrDefault((Score candidate) => candidate.Value == value);
		if (score.Value == null)
		{
			return 0.6;
		}
		return Math.Round(Math.Clamp(0.55 + score.Similarity * 3.5, 0.35, 0.98), 4);
	}

	private static void AddFeature(List<GarmentFeature> target, string type, double x, double y, double width, double height, string side, int paletteIndex, int layer, double confidence)
	{
		double num = Math.Clamp(x, 0.0, 1.0);
		double num2 = Math.Clamp(y, 0.0, 1.0);
		target.Add(new GarmentFeature
		{
			Type = type,
			X = RoundUnit(num),
			Y = RoundUnit(num2),
			Width = RoundUnit(Math.Clamp(width, 0.0, 1.0 - num)),
			Height = RoundUnit(Math.Clamp(height, 0.0, 1.0 - num2)),
			Side = side,
			PaletteIndex = paletteIndex,
			Layer = layer,
			Confidence = Math.Round(Math.Clamp(confidence, 0.0, 1.0), 4)
		});
	}

	private static (double X, double Y, double Width, double Height) FindMotifBounds(TextureSample texture)
	{
		Dictionary<int, int> dictionary = (from value in texture.Map
			where value >= 0
			group value by value).ToDictionary((IGrouping<int, int> group) => group.Key, (IGrouping<int, int> group) => group.Count());
		if (dictionary.Count < 2)
		{
			return (X: 0.3, Y: 0.24, Width: 0.4, Height: 0.28);
		}
		int key = dictionary.MaxBy((KeyValuePair<int, int> pair) => pair.Value).Key;
		List<(int, int)> list = new List<(int, int)>();
		for (int num = 0; num < texture.Height * 4 / 5; num++)
		{
			for (int num2 = texture.Width / 8; num2 < texture.Width * 7 / 8; num2++)
			{
				int num3 = texture.Map[num * texture.Width + num2];
				if (num3 >= 0 && num3 != key)
				{
					list.Add((num2, num));
				}
			}
		}
		if (list.Count < 2)
		{
			return (X: 0.3, Y: 0.24, Width: 0.4, Height: 0.28);
		}
		int num4 = list.Min<(int, int)>(((int X, int Y) point) => point.X);
		int num5 = list.Max<(int, int)>(((int X, int Y) point) => point.X);
		int num6 = list.Min<(int, int)>(((int X, int Y) point) => point.Y);
		int num7 = list.Max<(int, int)>(((int X, int Y) point) => point.Y);
		double num8 = Math.Clamp((double)num4 / (double)texture.Width, 0.16, 0.68);
		double num9 = Math.Clamp((double)num6 / (double)texture.Height, 0.1, 0.66);
		double val = Math.Clamp((double)(num5 - num4 + 1) / (double)texture.Width, 0.16, 0.68);
		double val2 = Math.Clamp((double)(num7 - num6 + 1) / (double)texture.Height, 0.12, 0.48);
		return (X: num8, Y: num9, Width: Math.Min(val, 1.0 - num8), Height: Math.Min(val2, 1.0 - num9));
	}

	private static (double Y, double Strength) FindHorizontalFeature(TextureSample texture)
	{
		int val = texture.Height * 2 / 5;
		int val2 = texture.Height * 7 / 10;
		int num = texture.Height / 2;
		double num2 = 0.0;
		for (int i = Math.Max(1, val); i <= Math.Min(texture.Height - 1, val2); i++)
		{
			int num3 = 0;
			int num4 = 0;
			for (int j = texture.Width / 6; j < texture.Width * 5 / 6; j++)
			{
				int num5 = texture.Map[(i - 1) * texture.Width + j];
				int num6 = texture.Map[i * texture.Width + j];
				if (num5 >= 0 && num6 >= 0)
				{
					num3++;
					if (num5 != num6)
					{
						num4++;
					}
				}
			}
			double num7 = ((num3 == 0) ? 0.0 : ((double)num4 / (double)num3));
			if (num7 > num2)
			{
				num2 = num7;
				num = i;
			}
		}
		return (Y: ((double)num + 0.5) / (double)texture.Height, Strength: num2);
	}

	private static double CompositeVerticalSplit(string silhouette)
	{
		switch (silhouette)
		{
		case "bodysuit":
		case "romper":
			return 0.56;
		case "mini_dress":
			return 0.5;
		case "midi_dress":
		case "dress":
			return 0.43;
		case "maxi_dress":
			return 0.36;
		case "tunic":
			return 0.55;
		case "long_tunic":
			return 0.48;
		case "raincoat":
		case "parka":
		case "coat":
			return 0.5;
		case "overcoat":
		case "trench_coat":
		case "long_raincoat":
			return 0.44;
		default:
			return 0.5;
		}
	}

	private static double RoundUnit(double value)
	{
		return Math.Round(Math.Clamp(value, 0.0, 1.0), 4);
	}

	private static (List<RgbF> Centers, int[] Assignments, int[] Counts) KMeans(List<Rgb> pixels, int clusters)
	{
		List<RgbF> centers = new List<RgbF> { pixels[pixels.Count / 2].AsFloat };
		while (centers.Count < clusters)
		{
			Rgb rgb = pixels.MaxBy((Rgb rgb2) => centers.Min((RgbF center) => Distance(rgb2.AsFloat, center)));
			centers.Add(rgb.AsFloat);
		}
		int[] array = new int[pixels.Count];
		int[] array2 = new int[clusters];
		for (int num = 0; num < 14; num++)
		{
			Array.Clear(array2);
			double[] array3 = new double[clusters];
			double[] array4 = new double[clusters];
			double[] array5 = new double[clusters];
			for (int num2 = 0; num2 < pixels.Count; num2++)
			{
				RgbF pixel = pixels[num2].AsFloat;
				int num3 = (array[num2] = Enumerable.Range(0, clusters).MinBy((int index) => Distance(pixel, centers[index])));
				array2[num3]++;
				array3[num3] += pixel.R;
				array4[num3] += pixel.G;
				array5[num3] += pixel.B;
			}
			for (int num4 = 0; num4 < clusters; num4++)
			{
				if (array2[num4] > 0)
				{
					centers[num4] = new RgbF(array3[num4] / (double)array2[num4], array4[num4] / (double)array2[num4], array5[num4] / (double)array2[num4]);
				}
			}
		}
		return (Centers: centers, Assignments: array, Counts: array2);
	}

	private static string NearestColorName(Rgb color)
	{
		return NamedColors.MinBy<KeyValuePair<string, Rgb>, double>((KeyValuePair<string, Rgb> pair) => Distance(color.AsFloat, pair.Value.AsFloat)).Key;
	}

	private static bool IsWhiteBackground(SKColor pixel)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		return IsNearWhiteBackground(pixel, 238, 14);
	}

	private static bool IsProductBackground(SKColor pixel)
	{
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		if (((SKColor)(ref pixel)).Alpha >= 20)
		{
			return IsNearWhiteBackground(pixel, 185, 24);
		}
		return true;
	}

	private static bool IsExternalBackground(SKBitmap bitmap, int x, int y, bool[]? mask)
	{
		if (mask != null)
		{
			return mask[y * bitmap.Width + x];
		}
		return false;
	}

	private static SKRectI ResolveGarmentSampleBox(SKRectI box, string category, bool productBackground, int bitmapWidth, int bitmapHeight)
	{
		//IL_02e1: Unknown result type (might be due to invalid IL or missing references)
		//IL_02e9: Unknown result type (might be due to invalid IL or missing references)
		double num;
		double num2;
		double num3;
		double num4;
		if (!productBackground)
		{
			(num, num2, num3, num4) = category switch
			{
				"shirt" => (0.27, 0.16, 0.73, 0.68), 
				"pants" => (0.16, 0.08, 0.84, 0.94), 
				"hat" => (0.2, 0.04, 0.8, 0.75), 
				"boots" => (0.25, 0.42, 0.75, 0.98), 
				_ => (0.2, 0.12, 0.8, 0.9), 
			};
		}
		else
		{
			(num, num2, num3, num4) = category switch
			{
				"shirt" => (0.24, 0.18, 0.76, 0.9), 
				"pants" => (0.18, 0.12, 0.82, 0.92), 
				"hat" => (0.12, 0.12, 0.88, 0.88), 
				"boots" => (0.1, 0.08, 0.9, 0.94), 
				_ => (0.18, 0.14, 0.82, 0.9), 
			};
		}
		return ClampRect(new SKRectI(((SKRectI)(ref box)).Left + (int)((double)((SKRectI)(ref box)).Width * num), ((SKRectI)(ref box)).Top + (int)((double)((SKRectI)(ref box)).Height * num2), ((SKRectI)(ref box)).Left + (int)((double)((SKRectI)(ref box)).Width * num3), ((SKRectI)(ref box)).Top + (int)((double)((SKRectI)(ref box)).Height * num4)), bitmapWidth, bitmapHeight);
	}

	private static bool[] BuildExternalBackgroundMask(SKBitmap bitmap, SKRectI requestedBox)
	{
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_008f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_0141: Unknown result type (might be due to invalid IL or missing references)
		//IL_0146: Unknown result type (might be due to invalid IL or missing references)
		//IL_0159: Unknown result type (might be due to invalid IL or missing references)
		//IL_015e: Unknown result type (might be due to invalid IL or missing references)
		//IL_042a: Unknown result type (might be due to invalid IL or missing references)
		//IL_042f: Unknown result type (might be due to invalid IL or missing references)
		//IL_04fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0501: Unknown result type (might be due to invalid IL or missing references)
		//IL_050f: Unknown result type (might be due to invalid IL or missing references)
		//IL_052d: Unknown result type (might be due to invalid IL or missing references)
		//IL_052f: Unknown result type (might be due to invalid IL or missing references)
		int width = bitmap.Width;
		int height = bitmap.Height;
		SKRectI val = ClampRect(requestedBox, width, height);
		bool[] mask = new bool[width * height];
		List<Rgb> border = new List<Rgb>();
		int num = Math.Max(1, (((SKRectI)(ref val)).Width + ((SKRectI)(ref val)).Height) / 360);
		for (int i = ((SKRectI)(ref val)).Left; i < ((SKRectI)(ref val)).Right; i += num)
		{
			SKColor pixel = bitmap.GetPixel(i, ((SKRectI)(ref val)).Top);
			SKColor pixel2 = bitmap.GetPixel(i, ((SKRectI)(ref val)).Bottom - 1);
			if (((SKColor)(ref pixel)).Alpha >= 20)
			{
				border.Add(new Rgb(((SKColor)(ref pixel)).Red, ((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
			}
			if (((SKColor)(ref pixel2)).Alpha >= 20)
			{
				border.Add(new Rgb(((SKColor)(ref pixel2)).Red, ((SKColor)(ref pixel2)).Green, ((SKColor)(ref pixel2)).Blue));
			}
		}
		for (int j = ((SKRectI)(ref val)).Top + 1; j < ((SKRectI)(ref val)).Bottom - 1; j += num)
		{
			SKColor pixel3 = bitmap.GetPixel(((SKRectI)(ref val)).Left, j);
			SKColor pixel4 = bitmap.GetPixel(((SKRectI)(ref val)).Right - 1, j);
			if (((SKColor)(ref pixel3)).Alpha >= 20)
			{
				border.Add(new Rgb(((SKColor)(ref pixel3)).Red, ((SKColor)(ref pixel3)).Green, ((SKColor)(ref pixel3)).Blue));
			}
			if (((SKColor)(ref pixel4)).Alpha >= 20)
			{
				border.Add(new Rgb(((SKColor)(ref pixel4)).Red, ((SKColor)(ref pixel4)).Green, ((SKColor)(ref pixel4)).Blue));
			}
		}
		if (border.Count == 0)
		{
			return mask;
		}
		int num2 = Math.Min(3, Math.Max(1, border.Count / 24));
		(List<RgbF>, int[], int[]) tuple = KMeans(border, num2);
		List<RgbF> centers = tuple.Item1;
		int[] assignments = tuple.Item2;
		int[] counts = tuple.Item3;
		int primary = Enumerable.Range(0, num2).MaxBy((int index) => counts[index]);
		List<int> acceptedCenters = (from index in Enumerable.Range(0, num2)
			where index == primary || (counts[index] >= Math.Max(3, counts[primary] / 5) && Distance(centers[index], centers[primary]) <= 58.0)
			select index).ToList();
		List<double> list = (from index in Enumerable.Range(0, border.Count)
			where assignments[index] == primary
			select Distance(border[index].AsFloat, centers[primary])).ToList();
		double average = ((list.Count > 0) ? list.Average() : 0.0);
		double num3 = ((list.Count > 1) ? Math.Sqrt(list.Sum((double value) => Math.Pow(value - average, 2.0)) / (double)list.Count) : 0.0);
		double backgroundThreshold = Math.Clamp(average + num3 * 2.2 + 10.0, 18.0, 48.0);
		double num4 = Math.Clamp(backgroundThreshold * 0.72, 13.0, 25.0);
		Queue<int> pending = new Queue<int>();
		for (int num5 = ((SKRectI)(ref val)).Left; num5 < ((SKRectI)(ref val)).Right; num5++)
		{
			EnqueueSeed(num5, ((SKRectI)(ref val)).Top);
			EnqueueSeed(num5, ((SKRectI)(ref val)).Bottom - 1);
		}
		for (int num6 = ((SKRectI)(ref val)).Top + 1; num6 < ((SKRectI)(ref val)).Bottom - 1; num6++)
		{
			EnqueueSeed(((SKRectI)(ref val)).Left, num6);
			EnqueueSeed(((SKRectI)(ref val)).Right - 1, num6);
		}
		while (pending.Count > 0)
		{
			int num7 = pending.Dequeue();
			int num8 = num7 % width;
			int num9 = num7 / width;
			SKColor pixel5 = bitmap.GetPixel(num8, num9);
			(int, int)[] array = new(int, int)[4]
			{
				(num8 - 1, num9),
				(num8 + 1, num9),
				(num8, num9 - 1),
				(num8, num9 + 1)
			};
			for (int num10 = 0; num10 < array.Length; num10++)
			{
				var (num11, num12) = array[num10];
				if (num11 < ((SKRectI)(ref val)).Left || num11 >= ((SKRectI)(ref val)).Right || num12 < ((SKRectI)(ref val)).Top || num12 >= ((SKRectI)(ref val)).Bottom)
				{
					continue;
				}
				int num13 = num12 * width + num11;
				if (!mask[num13])
				{
					SKColor pixel6 = bitmap.GetPixel(num11, num12);
					bool num14 = ((SKColor)(ref pixel6)).Alpha < 20;
					bool flag = BackgroundDistance(pixel6) <= backgroundThreshold * 1.35;
					bool flag2 = ColorDistance(pixel5, pixel6) <= num4;
					if (num14 || (flag & flag2))
					{
						mask[num13] = true;
						pending.Enqueue(num13);
					}
				}
			}
		}
		return mask;
		double BackgroundDistance(SKColor val2)
		{
			RgbF value = new RgbF((int)((SKColor)(ref val2)).Red, (int)((SKColor)(ref val2)).Green, (int)((SKColor)(ref val2)).Blue);
			return acceptedCenters.Min((int index) => Distance(value, centers[index]));
		}
		void EnqueueSeed(int x, int y)
		{
			//IL_001e: Unknown result type (might be due to invalid IL or missing references)
			//IL_0023: Unknown result type (might be due to invalid IL or missing references)
			//IL_0030: Unknown result type (might be due to invalid IL or missing references)
			int num15 = y * width + x;
			if (!mask[num15])
			{
				SKColor pixel7 = bitmap.GetPixel(x, y);
				if (((SKColor)(ref pixel7)).Alpha < 20 || !(BackgroundDistance(pixel7) > backgroundThreshold))
				{
					mask[num15] = true;
					pending.Enqueue(num15);
				}
			}
		}
	}

	private static bool IsNearWhiteBackground(SKColor pixel, int minimum, int maximumSpread)
	{
		int num = Math.Min(((SKColor)(ref pixel)).Red, Math.Min(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
		int num2 = Math.Max(((SKColor)(ref pixel)).Red, Math.Max(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
		if (num > minimum)
		{
			return num2 - num < maximumSpread;
		}
		return false;
	}

	private static double ColorDistance(SKColor left, SKColor right)
	{
		double num = ((SKColor)(ref left)).Red - ((SKColor)(ref right)).Red;
		double num2 = ((SKColor)(ref left)).Green - ((SKColor)(ref right)).Green;
		double num3 = ((SKColor)(ref left)).Blue - ((SKColor)(ref right)).Blue;
		return Math.Sqrt(num * num + num2 * num2 + num3 * num3);
	}

	private static double Distance(RgbF left, RgbF right)
	{
		double num = left.R - right.R;
		double num2 = left.G - right.G;
		double num3 = left.B - right.B;
		return Math.Sqrt(num * num + num2 * num2 + num3 * num3);
	}

	private static SKRectI ClampRect(SKRectI rect, int width, int height)
	{
		//IL_0054: Unknown result type (might be due to invalid IL or missing references)
		int num = Math.Clamp(((SKRectI)(ref rect)).Left, 0, Math.Max(0, width - 1));
		int num2 = Math.Clamp(((SKRectI)(ref rect)).Top, 0, Math.Max(0, height - 1));
		int num3 = Math.Clamp(((SKRectI)(ref rect)).Right, num + 1, width);
		int num4 = Math.Clamp(((SKRectI)(ref rect)).Bottom, num2 + 1, height);
		return new SKRectI(num, num2, num3, num4);
	}
}
