using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using SkiaSharp;

namespace PhotoTailor;

internal static class SleeveSignalExtractor
{
	private readonly record struct PixelSample(Rgb Color, bool LeftSleeve, double LocalU, double LocalV);

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

	private const int MapWidth = 12;

	private const int MapHeight = 12;

	public static SleeveSignal Extract(SKBitmap bitmap, SKRectI requestedBox, string coverage, bool productBackground, IReadOnlyList<string> fallbackPhotoPalette, bool[]? externalBackgroundMask = null)
	{
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fa: Unknown result type (might be due to invalid IL or missing references)
		//IL_0201: Unknown result type (might be due to invalid IL or missing references)
		if (coverage == "sleeveless")
		{
			return SleeveSignal.Empty;
		}
		SKRectI val = ClampRect(requestedBox, bitmap.Width, bitmap.Height);
		bool[] externalBackground = externalBackgroundMask ?? (productBackground ? BuildExternalBackgroundMask(bitmap) : null);
		double num = coverage switch
		{
			"short_sleeve" => 0.4, 
			"three_quarter_sleeve" => 0.82, 
			"long_sleeve" => 0.95, 
			_ => 0.68, 
		};
		List<Rgb> list = (from rgb in fallbackPhotoPalette.Select(ParseHex)
			where rgb.HasValue
			select rgb.Value).ToList();
		List<PixelSample> list2 = new List<PixelSample>();
		int num2 = Math.Max(1, ((SKRectI)(ref val)).Width * ((SKRectI)(ref val)).Height);
		int num3 = Math.Max(1, (int)Math.Sqrt((double)num2 / 18000.0));
		for (int num4 = ((SKRectI)(ref val)).Top; num4 < ((SKRectI)(ref val)).Bottom; num4 += num3)
		{
			double num5 = ((double)num4 + 0.5 - (double)((SKRectI)(ref val)).Top) / (double)((SKRectI)(ref val)).Height;
			if (num5 < 0.055 || num5 >= num)
			{
				continue;
			}
			for (int num6 = ((SKRectI)(ref val)).Left; num6 < ((SKRectI)(ref val)).Right; num6 += num3)
			{
				double num7 = ((double)num6 + 0.5 - (double)((SKRectI)(ref val)).Left) / (double)((SKRectI)(ref val)).Width;
				bool flag = num7 < 0.34;
				bool flag2 = num7 >= 0.6599999999999999;
				if (!flag && !flag2)
				{
					continue;
				}
				SKColor pixel = bitmap.GetPixel(num6, num4);
				if (IsGarmentPixel(bitmap, num6, num4, pixel, productBackground, externalBackground))
				{
					Rgb color = new Rgb(((SKColor)(ref pixel)).Red, ((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue);
					if ((productBackground || list.Count <= 0 || !IsLikelySkin(color) || IsLikelySkin(list[0]) || !(Distance(color, list[0]) > 34.0)) && (productBackground || list.Count <= 0 || !(list.Min((Rgb right) => Distance(color, right)) > 92.0)))
					{
						double localU = (flag ? (num7 / 0.34) : ((num7 - 0.6599999999999999) / 0.34));
						double localV = (num5 - 0.055) / (num - 0.055);
						list2.Add(new PixelSample(color, flag, localU, localV));
					}
				}
			}
		}
		if (list2.Count < 12)
		{
			return FromFallback(list);
		}
		List<Rgb> list3 = list2.Select((PixelSample sample) => sample.Color).ToList();
		int num8 = Math.Min(8, Math.Max(1, list3.Count / 45));
		(List<RgbF>, int[], int[]) tuple = KMeans(list3, num8);
		List<RgbF> centers = tuple.Item1;
		int[] item = tuple.Item2;
		int[] counts = tuple.Item3;
		List<int> list4 = (from index in Enumerable.Range(0, num8)
			orderby counts[index] descending
			select index).ToList();
		List<Rgb> palette = new List<Rgb>();
		List<int> list5 = Enumerable.Repeat(-1, num8).ToList();
		int num9 = Math.Max(2, (int)Math.Ceiling((double)list2.Count * 0.012));
		foreach (int item2 in list4)
		{
			if (counts[item2] < num9 && palette.Count >= 2)
			{
				continue;
			}
			Rgb candidate = centers[item2].Rounded;
			int num10 = palette.FindIndex((Rgb left) => Distance(left, candidate) < 11.0);
			if (num10 < 0)
			{
				if (palette.Count == 8)
				{
					continue;
				}
				num10 = palette.Count;
				palette.Add(candidate);
			}
			list5[item2] = num10;
		}
		if (palette.Count == 0)
		{
			return FromFallback(list);
		}
		int cluster;
		for (cluster = 0; cluster < num8; cluster++)
		{
			if (list5[cluster] < 0)
			{
				list5[cluster] = Enumerable.Range(0, palette.Count).MinBy((int index) => Distance(centers[cluster].Rounded, palette[index]));
			}
		}
		int[][] array = (from _ in Enumerable.Range(0, 144)
			select new int[palette.Count]).ToArray();
		for (int num11 = 0; num11 < list2.Count; num11++)
		{
			PixelSample pixelSample = list2[num11];
			int num12 = Math.Clamp((int)(pixelSample.LocalU * 6.0), 0, 5);
			int num13 = (pixelSample.LeftSleeve ? num12 : (6 + num12));
			int num14 = Math.Clamp((int)(pixelSample.LocalV * 12.0), 0, 11);
			array[num14 * 12 + num13][list5[item[num11]]]++;
		}
		List<int> patternMap = array.Select((int[] cell) => (cell.Sum() != 0) ? Enumerable.Range(0, cell.Length).MaxBy((int index) => cell[index]) : (-1)).ToList();
		return new SleeveSignal(palette.Select((Rgb rgb) => rgb.Hex).ToList(), patternMap, 12, 12);
	}

	private static SleeveSignal FromFallback(List<Rgb> fallback)
	{
		if (fallback.Count == 0)
		{
			return SleeveSignal.Empty;
		}
		return new SleeveSignal((from color in fallback.Distinct().Take(8)
			select color.Hex).ToList(), new List<int>(), 0, 0);
	}

	private static bool IsGarmentPixel(SKBitmap bitmap, int x, int y, SKColor pixel, bool productBackground, bool[]? externalBackground)
	{
		//IL_0028: Unknown result type (might be due to invalid IL or missing references)
		if (((SKColor)(ref pixel)).Alpha < 32)
		{
			return false;
		}
		if (externalBackground != null && externalBackground[y * bitmap.Width + x])
		{
			return false;
		}
		if (productBackground)
		{
			return true;
		}
		return !IsNearNeutralBackground(pixel, 244, 10);
	}

	private static bool IsLikelySkin(Rgb color)
	{
		int num = Math.Max(color.R, Math.Max(color.G, color.B));
		int num2 = Math.Min(color.R, Math.Min(color.G, color.B));
		if (color.R >= 90 && color.G >= 55 && color.B >= 40 && (double)(int)color.R > (double)(int)color.G * 1.025 && (double)(int)color.G > (double)(int)color.B * 1.015 && color.R - color.B >= 24)
		{
			return num - num2 >= 28;
		}
		return false;
	}

	private static bool[] BuildExternalBackgroundMask(SKBitmap bitmap)
	{
		int width = bitmap.Width;
		int height = bitmap.Height;
		bool[] mask = new bool[width * height];
		Queue<int> pending = new Queue<int>();
		for (int i = 0; i < width; i++)
		{
			Enqueue(i, 0);
			Enqueue(i, height - 1);
		}
		for (int j = 1; j < height - 1; j++)
		{
			Enqueue(0, j);
			Enqueue(width - 1, j);
		}
		while (pending.Count > 0)
		{
			int num = pending.Dequeue();
			int num2 = num % width;
			int num3 = num / width;
			if (num2 > 0)
			{
				Enqueue(num2 - 1, num3);
			}
			if (num2 + 1 < width)
			{
				Enqueue(num2 + 1, num3);
			}
			if (num3 > 0)
			{
				Enqueue(num2, num3 - 1);
			}
			if (num3 + 1 < height)
			{
				Enqueue(num2, num3 + 1);
			}
		}
		return mask;
		void Enqueue(int x, int y)
		{
			//IL_001d: Unknown result type (might be due to invalid IL or missing references)
			int num4 = y * width + x;
			if (!mask[num4] && IsExternalBackgroundColor(bitmap.GetPixel(x, y)))
			{
				mask[num4] = true;
				pending.Enqueue(num4);
			}
		}
	}

	private static bool IsExternalBackgroundColor(SKColor pixel)
	{
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		if (((SKColor)(ref pixel)).Alpha >= 20)
		{
			return IsNearNeutralBackground(pixel, 185, 25);
		}
		return true;
	}

	private static bool IsNearNeutralBackground(SKColor pixel, int minimum, int maximumSpread)
	{
		int num = Math.Min(((SKColor)(ref pixel)).Red, Math.Min(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
		int num2 = Math.Max(((SKColor)(ref pixel)).Red, Math.Max(((SKColor)(ref pixel)).Green, ((SKColor)(ref pixel)).Blue));
		if (num > minimum)
		{
			return num2 - num < maximumSpread;
		}
		return false;
	}

	private static Rgb? ParseHex(string value)
	{
		if (value.Length != 7 || value[0] != '#')
		{
			return null;
		}
		if (!byte.TryParse(value.AsSpan(1, 2), NumberStyles.HexNumber, null, out var result) || !byte.TryParse(value.AsSpan(3, 2), NumberStyles.HexNumber, null, out var result2) || !byte.TryParse(value.AsSpan(5, 2), NumberStyles.HexNumber, null, out var result3))
		{
			return null;
		}
		return new Rgb(result, result2, result3);
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
		for (int num = 0; num < 12; num++)
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

	private static double Distance(Rgb left, Rgb right)
	{
		return Distance(left.AsFloat, right.AsFloat);
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
