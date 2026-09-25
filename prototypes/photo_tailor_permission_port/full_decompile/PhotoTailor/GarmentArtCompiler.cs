using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

namespace PhotoTailor;

internal static class GarmentArtCompiler
{
	private sealed record EvidenceCell(int X, int Y, int PaletteIndex);

	private sealed class PatternEvidence
	{
		public int Width { get; init; }

		public int Height { get; init; }

		public List<EvidenceCell> Cells { get; init; } = new List<EvidenceCell>();

		public int BaseIndex { get; init; }
	}

	private sealed class DecorativeEvidenceWindow
	{
		public int Top { get; init; }

		public int Bottom { get; init; }

		public double Score { get; init; }

		public GarmentArtRgb FabricReference { get; init; }

		public List<List<(int X, int Y)>> Components { get; init; } = new List<List<(int, int)>>();
	}

	private const int RampMiddle = 2;

	public static CompiledGarmentArt Compile(GarmentSpec spec)
	{
		ArgumentNullException.ThrowIfNull(spec, "spec");
		List<GarmentArtRgb> list = ResolvePalette(spec);
		PatternEvidence patternEvidence = ReadEvidence(spec, list.Count);
		GarmentArtRgb garmentArtRgb = (TryParseHex(spec.PrimaryColor, out var color) ? color : ((patternEvidence.Cells.Count > 0) ? list[Math.Clamp(patternEvidence.BaseIndex, 0, list.Count - 1)] : list[0]));
		string text = ResolvePattern(spec);
		bool flag = ((text == "other" || text == "unknown") ? true : false);
		bool flag2 = flag && IsSkirtLike(spec) && LooksLikeDecoratedTextile(patternEvidence, list, garmentArtRgb);
		switch (text)
		{
		case "tiered":
		case "floral":
		case "flower":
		case "checked":
		case "striped":
		case "stripes":
		case "colorblock":
		case "colourblock":
		case "plaid":
			flag = true;
			break;
		default:
			flag = false;
			break;
		}
		bool permitsMapStructure = flag || IsSkirtLike(spec);
		List<double> list2 = CompileTrustedTierRows(spec, patternEvidence, list, permitsMapStructure);
		List<GarmentColorBand> list3 = CompileBaseBands(patternEvidence, list, garmentArtRgb, list2, permitsMapStructure);
		List<GarmentMotifStamp> list4 = new List<GarmentMotifStamp>();
		int retainedEvidencePixels = 0;
		int rejectedIsolatedPixels = 0;
		flag = ((text == "floral" || text == "flower") ? true : false);
		if (flag | flag2)
		{
			(list4, retainedEvidencePixels, rejectedIsolatedPixels) = CompileFloralMotifs(spec, patternEvidence, list, garmentArtRgb);
		}
		CanonicalGarmentCanvas canonicalCanvas = PaintCanonicalCanvas(spec, flag2 ? "decorative" : text, list, garmentArtRgb, list3, list2, list4);
		var (artworkTop, artworkBottom) = ResolveArtworkRange(spec);
		return new CompiledGarmentArt(flag2 ? "decorative" : text, garmentArtRgb, BuildShadeRamp(garmentArtRgb), list3, list2, list4, retainedEvidencePixels, rejectedIsolatedPixels, canonicalCanvas, artworkTop, artworkBottom);
	}

	private static (double Top, double Bottom) ResolveArtworkRange(GarmentSpec spec)
	{
		double num = Math.Clamp(spec.ArtworkTop, 0.0, 1.0);
		double num2 = Math.Clamp(spec.ArtworkBottom, 0.0, 1.0);
		string text = (spec.RenderRole ?? "whole").Trim().ToLowerInvariant();
		if (num2 - num >= 0.05 && (text == "whole" || num > 0.0 || num2 < 1.0))
		{
			return (Top: num, Bottom: num2);
		}
		double num3 = spec.Blueprint?.Regions.Where((GarmentRegion region) => string.Equals(region.Role, "lower", StringComparison.OrdinalIgnoreCase)).Select((GarmentRegion region) => region.Top).FirstOrDefault((double value) => value > 0.0) ?? 0.0;
		if (num3 <= 0.0)
		{
			num3 = 0.5;
		}
		num3 = Math.Clamp(num3, 0.28, 0.72);
		if (!(text == "upper"))
		{
			if (text == "lower")
			{
				return (Top: num3, Bottom: 1.0);
			}
			return (Top: 0.0, Bottom: 1.0);
		}
		return (Top: 0.0, Bottom: num3);
	}

	private static CanonicalGarmentCanvas PaintCanonicalCanvas(GarmentSpec spec, string compiledPattern, IReadOnlyList<GarmentArtRgb> palette, GarmentArtRgb baseColor, IReadOnlyList<GarmentColorBand> bands, IReadOnlyList<double> tierRows, IReadOnlyList<GarmentMotifStamp> motifs)
	{
		GarmentCanvasRegion[] array = Enumerable.Repeat(GarmentCanvasRegion.Background, 6144).ToArray();
		string text = NormalizeToken(spec.Silhouette);
		string text2 = NormalizeToken(spec.Category);
		bool flag = IsCompositeCanvasSilhouette(text);
		bool skirtLike = IsSkirtLike(spec) || text.Contains("coat", StringComparison.Ordinal) || text.Contains("tunic", StringComparison.Ordinal) || text.Contains("raincoat", StringComparison.Ordinal) || text == "parka";
		GarmentProportions proportions = spec.Blueprint?.Proportions ?? new GarmentProportions();
		int centerX = 32;
		int num3;
		if (text2 == "hat")
		{
			int num = 22;
			int num2 = 60;
			num3 = num2;
			FillCanonicalHat(array, text, centerX);
		}
		else if (text2 == "boots")
		{
			int num = 46;
			int num2 = 88;
			num3 = num;
			FillCanonicalBoots(array, centerX);
		}
		else if (flag)
		{
			int num = 5;
			int num2 = 91;
			num3 = Math.Clamp(num + (int)Math.Round((double)(num2 - num) * ResolveArtworkSplit(spec)), 38, 62);
			FillCanonicalUpper(array, spec, proportions, centerX, num, num3 + 2);
			FillCanonicalLower(array, spec, proportions, centerX, num3 - 2, num2, skirtLike);
		}
		else if (text2 == "shirt")
		{
			int num = 8;
			int num2 = 82;
			num3 = num2;
			FillCanonicalUpper(array, spec, proportions, centerX, num, num2);
		}
		else
		{
			int num = 7;
			int num2 = 91;
			num3 = num;
			FillCanonicalLower(array, spec, proportions, centerX, num, num2, skirtLike);
		}
		(int Left, int Top, int Right, int Bottom) tuple = FindContentBounds(array, 64, 96);
		int item = tuple.Left;
		int item2 = tuple.Top;
		int item3 = tuple.Right;
		int item4 = tuple.Bottom;
		List<GarmentArtRgb> sleevePalette = ResolveSleevePalette(spec, palette, baseColor);
		GarmentArtRgba[] array2 = new GarmentArtRgba[6144];
		string sourcePattern = NormalizePattern(spec.Pattern);
		for (int i = item2; i <= item4; i++)
		{
			for (int j = item; j <= item3; j++)
			{
				int num4 = i * 64 + j;
				GarmentCanvasRegion garmentCanvasRegion = array[num4];
				if (garmentCanvasRegion == GarmentCanvasRegion.Background)
				{
					array2[num4] = GarmentArtRgba.Transparent;
					continue;
				}
				double u = ((double)(j - item) + 0.5) / Math.Max(1.0, item3 - item + 1);
				double v = ((double)(i - item2) + 0.5) / Math.Max(1.0, item4 - item2 + 1);
				GarmentArtRgb color = ResolveCanvasFieldColor(sourcePattern, compiledPattern, palette, sleevePalette, bands, baseColor, garmentCanvasRegion, u, v, j, i);
				int shadeStep = ResolveCanvasShade(array, 64, 96, j, i, item, item3, garmentCanvasRegion);
				GarmentArtRgb garmentArtRgb = Shade(color, shadeStep);
				array2[num4] = new GarmentArtRgba(garmentArtRgb.R, garmentArtRgb.G, garmentArtRgb.B, byte.MaxValue);
			}
		}
		GarmentArtRgba[] obj = (GarmentArtRgba[])array2.Clone();
		GarmentArtRgba[] array3 = new GarmentArtRgba[6144];
		GarmentProjectionScope[] projectionScopes = Enumerable.Repeat(GarmentProjectionScope.BaseField, 6144).ToArray();
		DrawCanonicalConstruction(obj, array2, array3, projectionScopes, array, spec, baseColor, palette, tierRows, motifs, item, item2, item3, item4, num3);
		return new CanonicalGarmentCanvas(obj, array2, array3, projectionScopes, array, item, item2, item3, item4);
	}

	private static double ResolveArtworkSplit(GarmentSpec spec)
	{
		double num = spec.Blueprint?.Regions.Where((GarmentRegion region) => string.Equals(region.Role, "lower", StringComparison.OrdinalIgnoreCase)).Select((GarmentRegion region) => region.Top).FirstOrDefault((double value) => value > 0.0) ?? 0.0;
		if (num <= 0.0)
		{
			num = 0.5;
		}
		return Math.Clamp(num, 0.34, 0.66);
	}

	private static void FillCanonicalUpper(GarmentCanvasRegion[] regions, GarmentSpec spec, GarmentProportions proportions, int centerX, int top, int bottom)
	{
		double num = ((proportions.ShoulderWidth > 0.0) ? proportions.ShoulderWidth : 0.58);
		double num2 = ((proportions.TorsoWidth > 0.0) ? proportions.TorsoWidth : 0.52);
		double num3 = ((proportions.WaistWidth > 0.0) ? proportions.WaistWidth : num2);
		int num4 = Math.Clamp((int)Math.Round(11.0 + num * 10.0), 14, 21);
		int num5 = Math.Clamp((int)Math.Round(10.0 + num2 * 9.0), 13, 19);
		int num6 = Math.Clamp((int)Math.Round(10.0 + num3 * 8.0), 12, 18);
		int num7 = top + 7;
		FillPolygon(regions, GarmentCanvasRegion.Torso, new(int, int)[6]
		{
			(centerX - num4, num7),
			(centerX + num4, num7),
			(centerX + num5, top + (bottom - top) * 2 / 3),
			(centerX + num6, bottom),
			(centerX - num6, bottom),
			(centerX - num5, top + (bottom - top) * 2 / 3)
		});
		string text = NormalizeToken(spec.Coverage);
		bool flag = text == "sleeveless" || (spec.Blueprint != null && proportions.SleeveLength <= 0.06);
		if (!flag)
		{
			bool flag2;
			switch (NormalizeToken(spec.Silhouette))
			{
			case "vest":
			case "tank_top":
			case "camisole":
			case "halter_top":
				flag2 = true;
				break;
			default:
				flag2 = false;
				break;
			}
			flag = flag2;
		}
		if (!flag)
		{
			double value = ((proportions.SleeveLength > 0.0) ? proportions.SleeveLength : (text.Contains("long", StringComparison.Ordinal) ? 0.92 : (text.Contains("short", StringComparison.Ordinal) ? 0.36 : 0.62)));
			int num8 = Math.Max(num7, bottom - 1);
			int min = Math.Min(num8, num7 + 10);
			int num9 = Math.Clamp(num7 + (int)Math.Round((double)(bottom - num7) * Math.Clamp(value, 0.24, 1.0)), min, num8);
			int num10 = Math.Clamp((int)Math.Round(4.0 + proportions.SleeveVolume * 5.0), 4, 9);
			int num11 = Math.Max(1, Math.Min(centerX - 1, 64 - centerX - 1));
			int min2 = Math.Min(num11, num4 + 10);
			int num12 = Math.Clamp(num4 + 8 + num10, min2, num11);
			FillPolygon(regions, GarmentCanvasRegion.LeftSleeve, new(int, int)[5]
			{
				(centerX - num4 + 2, num7),
				(centerX - num4 - 3, num7 + 2),
				(centerX - num12, num9 - 4),
				(centerX - num12 + num10, num9 + 1),
				(centerX - num5 + 1, Math.Min(bottom - 2, num9 - 5))
			});
			FillPolygon(regions, GarmentCanvasRegion.RightSleeve, new(int, int)[5]
			{
				(centerX + num4 - 2, num7),
				(centerX + num4 + 3, num7 + 2),
				(centerX + num12, num9 - 4),
				(centerX + num12 - num10, num9 + 1),
				(centerX + num5 - 1, Math.Min(bottom - 2, num9 - 5))
			});
			FillPolygon(regions, GarmentCanvasRegion.Torso, new(int, int)[6]
			{
				(centerX - num4, num7),
				(centerX + num4, num7),
				(centerX + num5, top + (bottom - top) * 2 / 3),
				(centerX + num6, bottom),
				(centerX - num6, bottom),
				(centerX - num5, top + (bottom - top) * 2 / 3)
			});
		}
	}

	private static void FillCanonicalLower(GarmentCanvasRegion[] regions, GarmentSpec spec, GarmentProportions proportions, int centerX, int top, int bottom, bool skirtLike)
	{
		int num = Math.Clamp((int)Math.Round(10.0 + Math.Max(0.35, proportions.WaistWidth) * 8.0), 12, 18);
		int num2 = Math.Clamp((int)Math.Round(12.0 + Math.Max(0.45, proportions.HemWidth) * 16.0), 16, 29);
		string text = NormalizeToken(spec.Silhouette);
		if ((text == "pencil_skirt" || text == "leggings") ? true : false)
		{
			num2 = Math.Min(num2, num + 2);
		}
		if (skirtLike || text.Contains("skirt", StringComparison.Ordinal))
		{
			FillPolygon(regions, GarmentCanvasRegion.Lower, new(int, int)[6]
			{
				(centerX - num, top),
				(centerX + num, top),
				(centerX + num2, bottom - 2),
				(centerX + num2 - 3, bottom),
				(centerX - num2 + 3, bottom),
				(centerX - num2, bottom - 2)
			});
			return;
		}
		int item = top + Math.Max(12, (bottom - top) / 4);
		int num3 = Math.Clamp((num - 2) / 2, 5, 9);
		bool flag = ((text == "wide_leg_pants" || text == "culottes") ? true : false);
		int num4 = (flag ? 1 : 2);
		FillPolygon(regions, GarmentCanvasRegion.Lower, new(int, int)[6]
		{
			(centerX - num, top),
			(centerX - num4, top),
			(centerX - num4, item),
			(centerX - num4 - 1, bottom),
			(centerX - num4 - num3 * 2, bottom),
			(centerX - num - 1, item)
		});
		FillPolygon(regions, GarmentCanvasRegion.Lower, new(int, int)[6]
		{
			(centerX + num4, top),
			(centerX + num, top),
			(centerX + num + 1, item),
			(centerX + num4 + num3 * 2, bottom),
			(centerX + num4 + 1, bottom),
			(centerX + num4, item)
		});
		for (int i = centerX - num; i <= centerX + num; i++)
		{
			SetRegion(regions, i, top, GarmentCanvasRegion.Lower);
		}
	}

	private static void FillCanonicalHat(GarmentCanvasRegion[] regions, string silhouette, int centerX)
	{
		int item = ((silhouette == "crown") ? 20 : 27);
		FillPolygon(regions, GarmentCanvasRegion.Upper, new(int, int)[6]
		{
			(centerX - 17, 48),
			(centerX - 13, item),
			(centerX + 13, item),
			(centerX + 17, 48),
			(centerX + 15, 55),
			(centerX - 15, 55)
		});
		for (int i = 53; i <= 58; i++)
		{
			for (int j = centerX - 24; j <= centerX + 24; j++)
			{
				SetRegion(regions, j, i, GarmentCanvasRegion.Hem);
			}
		}
	}

	private static void FillCanonicalBoots(GarmentCanvasRegion[] regions, int centerX)
	{
		FillPolygon(regions, GarmentCanvasRegion.Lower, new(int, int)[8]
		{
			(centerX - 22, 50),
			(centerX - 7, 50),
			(centerX - 8, 78),
			(centerX - 3, 84),
			(centerX - 4, 89),
			(centerX - 25, 89),
			(centerX - 27, 84),
			(centerX - 22, 76)
		});
		FillPolygon(regions, GarmentCanvasRegion.Lower, new(int, int)[8]
		{
			(centerX + 7, 50),
			(centerX + 22, 50),
			(centerX + 22, 76),
			(centerX + 27, 84),
			(centerX + 25, 89),
			(centerX + 4, 89),
			(centerX + 3, 84),
			(centerX + 8, 78)
		});
	}

	private static GarmentArtRgb ResolveCanvasFieldColor(string sourcePattern, string compiledPattern, IReadOnlyList<GarmentArtRgb> palette, IReadOnlyList<GarmentArtRgb> sleevePalette, IReadOnlyList<GarmentColorBand> bands, GarmentArtRgb baseColor, GarmentCanvasRegion region, double u, double v, int x, int y)
	{
		bool flag = region - 2 <= GarmentCanvasRegion.Torso;
		IReadOnlyList<GarmentArtRgb> readOnlyList = (flag ? sleevePalette : palette);
		GarmentArtRgb garmentArtRgb = bands.FirstOrDefault((GarmentColorBand band) => v >= band.Top && v <= band.Bottom)?.Color ?? baseColor;
		if (readOnlyList.Count == 0)
		{
			return garmentArtRgb;
		}
		flag = region - 2 <= GarmentCanvasRegion.Torso;
		GarmentArtRgb result = (flag ? readOnlyList[0] : garmentArtRgb);
		if (sourcePattern.Contains("horizontal", StringComparison.Ordinal) || (compiledPattern == "striped" && !sourcePattern.Contains("vertical", StringComparison.Ordinal)))
		{
			int num = Math.Clamp((int)Math.Floor(v * 10.0), 0, 9);
			return readOnlyList[num % Math.Min(readOnlyList.Count, 5)];
		}
		if (sourcePattern.Contains("vertical", StringComparison.Ordinal))
		{
			int num2 = Math.Clamp((int)Math.Floor(u * 9.0), 0, 8);
			return readOnlyList[num2 % Math.Min(readOnlyList.Count, 5)];
		}
		if (sourcePattern.Contains("plaid", StringComparison.Ordinal) || sourcePattern.Contains("check", StringComparison.Ordinal))
		{
			int num3 = Math.Abs(x) % 10;
			int num4 = Math.Abs(y) % 10;
			if (num3 <= 1 && readOnlyList.Count > 1)
			{
				return readOnlyList[1];
			}
			if (num4 <= 1 && readOnlyList.Count > 2)
			{
				return readOnlyList[2];
			}
		}
		if (sourcePattern.Contains("colorblock", StringComparison.Ordinal) || sourcePattern.Contains("colourblock", StringComparison.Ordinal))
		{
			int val = ((!(v < 0.36)) ? ((v < 0.68) ? 1 : 2) : 0);
			return readOnlyList[Math.Min(val, readOnlyList.Count - 1)];
		}
		if (sourcePattern.Contains("gradient", StringComparison.Ordinal) && readOnlyList.Count > 1)
		{
			return MixRgb(readOnlyList[0], readOnlyList[1], v);
		}
		return result;
	}

	private static int ResolveCanvasShade(IReadOnlyList<GarmentCanvasRegion> regions, int width, int height, int x, int y, int left, int right, GarmentCanvasRegion region)
	{
		if (CardinalNeighbors(x, y).Any(((int X, int Y) point) => point.X < 0 || point.X >= width || point.Y < 0 || point.Y >= height || regions[point.Y * width + point.X] == GarmentCanvasRegion.Background))
		{
			return -2;
		}
		double num = ((double)(x - left) + 0.5) / Math.Max(1.0, right - left + 1);
		if (region == GarmentCanvasRegion.Lower && Math.Abs(x - width / 2) % 9 <= 1)
		{
			return -1;
		}
		if ((num < 0.18 || num > 0.82) ? true : false)
		{
			return -1;
		}
		if (num > 0.42 && num < 0.6)
		{
			return 1;
		}
		return 0;
	}

	private static void DrawCanonicalConstruction(GarmentArtRgba[] display, GarmentArtRgba[] field, GarmentArtRgba[] projectionOverlay, GarmentProjectionScope[] projectionScopes, GarmentCanvasRegion[] regions, GarmentSpec spec, GarmentArtRgb baseColor, IReadOnlyList<GarmentArtRgb> palette, IReadOnlyList<double> tierRows, IReadOnlyList<GarmentMotifStamp> motifs, int left, int top, int right, int bottom, int splitY)
	{
		int num = 32;
		GarmentArtRgb color = Shade(baseColor, -1);
		GarmentArtRgb garmentArtRgb = Shade(baseColor, 1);
		GarmentArtRgb color2 = ((palette.Count > 2) ? palette[2] : garmentArtRgb);
		string text = NormalizeToken(spec.Neckline);
		string text2 = NormalizeToken(spec.Silhouette);
		int num2;
		int num4;
		if (regions.Any((GarmentCanvasRegion region) => region == GarmentCanvasRegion.Torso))
		{
			num2 = top + 7;
			int num3 = Math.Clamp((int)Math.Round(3.0 + (spec.Blueprint?.Proportions.NecklineWidth ?? 0.25) * 8.0), 4, 9);
			num4 = Math.Clamp((int)Math.Round(2.0 + (spec.Blueprint?.Proportions.NecklineDepth ?? 0.08) * 18.0), 3, 8);
			if (text.Contains("v", StringComparison.Ordinal))
			{
				DrawCanvasLine(display, field, projectionOverlay, projectionScopes, regions, num - num3, num2, num, num2 + num4, color, GarmentCanvasRegion.Collar, GarmentProjectionScope.FrontOnly);
				DrawCanvasLine(display, field, projectionOverlay, projectionScopes, regions, num, num2 + num4, num + num3, num2, color, GarmentCanvasRegion.Collar, GarmentProjectionScope.FrontOnly);
			}
			else
			{
				for (int num5 = num - num3; num5 <= num + num3; num5++)
				{
					double num6 = (double)Math.Abs(num5 - num) / Math.Max(1.0, num3);
					int y = num2 + (int)Math.Round((double)num4 * (1.0 - num6 * num6));
					OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num5, y, color, GarmentCanvasRegion.Collar, GarmentProjectionScope.FrontOnly);
				}
			}
			if (!text.Contains("collar", StringComparison.Ordinal))
			{
				GarmentBlueprint? blueprint = spec.Blueprint;
				if (blueprint == null || !blueprint.Features.Any((GarmentFeature feature) => NormalizeToken(feature.Type) == "collar"))
				{
					goto IL_022f;
				}
			}
			DrawCanvasLine(display, field, projectionOverlay, projectionScopes, regions, num - num3 - 2, num2, num - 1, num2 + 10, color2, GarmentCanvasRegion.Collar, GarmentProjectionScope.FrontOnly);
			DrawCanvasLine(display, field, projectionOverlay, projectionScopes, regions, num + num3 + 2, num2, num + 1, num2 + 10, color2, GarmentCanvasRegion.Collar, GarmentProjectionScope.FrontOnly);
			goto IL_022f;
		}
		goto IL_031d;
		IL_022f:
		GarmentBlueprint? blueprint2 = spec.Blueprint;
		bool flag = (blueprint2 != null && blueprint2.Proportions.OpenFront) || (spec.Blueprint?.Features.Any(delegate(GarmentFeature feature)
		{
			switch (NormalizeToken(feature.Type))
			{
			case "buttons":
			case "zipper":
			case "placket":
				return true;
			default:
				return false;
			}
		}) ?? false);
		if (!flag)
		{
			string text3 = NormalizeToken(spec.Detail);
			bool flag2 = ((text3 == "buttons" || text3 == "zipper") ? true : false);
			flag = flag2;
		}
		if (flag)
		{
			int num7 = Math.Min(bottom - 3, (splitY > top) ? splitY : (bottom - 3));
			DrawCanvasLine(display, field, projectionOverlay, projectionScopes, regions, num, num2 + num4, num, num7, color, GarmentCanvasRegion.Construction, GarmentProjectionScope.FrontOnly);
			for (int num8 = num2 + num4 + 6; num8 < num7; num8 += 8)
			{
				OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num + 2, num8, color2, GarmentCanvasRegion.Construction, GarmentProjectionScope.FrontOnly);
			}
		}
		goto IL_031d;
		IL_031d:
		if (splitY > top && splitY < bottom)
		{
			for (int num9 = left; num9 <= right; num9++)
			{
				OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num9, splitY, color, GarmentCanvasRegion.Construction, GarmentProjectionScope.AllFacings);
			}
		}
		foreach (double tierRow in tierRows)
		{
			int y2 = top + (int)Math.Round(tierRow * (double)Math.Max(1, bottom - top));
			for (int num10 = left; num10 <= right; num10++)
			{
				OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num10, y2, color, GarmentCanvasRegion.Construction, GarmentProjectionScope.AllFacings);
			}
		}
		for (int num11 = left; num11 <= right; num11++)
		{
			int num12 = -1;
			for (int num13 = Math.Max(top, bottom - 5); num13 <= bottom; num13++)
			{
				if (num13 >= 0 && num13 < 96 && regions[num13 * 64 + num11] != GarmentCanvasRegion.Background)
				{
					num12 = num13;
				}
			}
			if (num12 >= 0)
			{
				OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num11, num12, color, GarmentCanvasRegion.Hem, GarmentProjectionScope.AllFacings);
			}
		}
		foreach (GarmentMotifStamp item in motifs.Where((GarmentMotifStamp stamp) => stamp.Facing == GarmentArtFacing.Front))
		{
			PaintCanonicalMotif(display, field, projectionOverlay, projectionScopes, regions, item, left, top, right, bottom);
		}
		string text4 = NormalizePattern(spec.Pattern);
		if ((text4.Contains("logo", StringComparison.Ordinal) || text4.Contains("graphic", StringComparison.Ordinal)) && motifs.Count == 0)
		{
			int num14 = top + (bottom - top) * ((!text2.Contains("skirt", StringComparison.Ordinal)) ? 1 : 2) / 3;
			(int, int)[] array = new(int, int)[10]
			{
				(0, -4),
				(1, -2),
				(4, -1),
				(2, 1),
				(3, 4),
				(0, 2),
				(-3, 4),
				(-2, 1),
				(-4, -1),
				(-1, -2)
			};
			for (int num15 = 0; num15 < array.Length; num15++)
			{
				var (num16, num17) = array[num15];
				OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, num + num16, num14 + num17, color2, GarmentCanvasRegion.Motif, GarmentProjectionScope.FrontOnly);
			}
		}
	}

	private static void PaintCanonicalMotif(GarmentArtRgba[] display, GarmentArtRgba[] field, GarmentArtRgba[] projectionOverlay, GarmentProjectionScope[] projectionScopes, GarmentCanvasRegion[] regions, GarmentMotifStamp stamp, int left, int top, int right, int bottom)
	{
		int num = left + (int)Math.Round(stamp.X * (double)Math.Max(1, right - left));
		int num2 = top + (int)Math.Round(stamp.Y * (double)Math.Max(1, bottom - top));
		foreach (GarmentMotifPixel pixel in stamp.Pixels)
		{
			for (int i = 0; i < 2; i++)
			{
				for (int j = 0; j < 2; j++)
				{
					int x = num + pixel.X * 2 + j;
					int y = num2 + pixel.Y * 2 + i;
					OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, x, y, pixel.Color, GarmentCanvasRegion.Motif, GarmentProjectionScope.DisplayOnly);
				}
			}
		}
	}

	private static void DrawCanvasLine(GarmentArtRgba[] display, GarmentArtRgba[] field, GarmentArtRgba[] projectionOverlay, GarmentProjectionScope[] projectionScopes, GarmentCanvasRegion[] regions, int x0, int y0, int x1, int y1, GarmentArtRgb color, GarmentCanvasRegion region, GarmentProjectionScope scope)
	{
		int num = Math.Abs(x1 - x0);
		int num2 = ((x0 < x1) ? 1 : (-1));
		int num3 = -Math.Abs(y1 - y0);
		int num4 = ((y0 < y1) ? 1 : (-1));
		int num5 = num + num3;
		while (true)
		{
			OverlayCanvasPixel(display, field, projectionOverlay, projectionScopes, regions, x0, y0, color, region, scope);
			if (x0 != x1 || y0 != y1)
			{
				int num6 = num5 * 2;
				if (num6 >= num3)
				{
					num5 += num3;
					x0 += num2;
				}
				if (num6 <= num)
				{
					num5 += num;
					y0 += num4;
				}
				continue;
			}
			break;
		}
	}

	private static void OverlayCanvasPixel(GarmentArtRgba[] display, GarmentArtRgba[] field, GarmentArtRgba[] projectionOverlay, GarmentProjectionScope[] projectionScopes, GarmentCanvasRegion[] regions, int x, int y, GarmentArtRgb color, GarmentCanvasRegion region, GarmentProjectionScope scope)
	{
		if (x < 0 || x >= 64 || y < 0 || y >= 96)
		{
			return;
		}
		int num = y * 64 + x;
		if (field[num].A >= 16)
		{
			display[num] = new GarmentArtRgba(color.R, color.G, color.B, byte.MaxValue);
			if (scope - 2 <= GarmentProjectionScope.DisplayOnly)
			{
				projectionOverlay[num] = new GarmentArtRgba(color.R, color.G, color.B, byte.MaxValue);
				projectionScopes[num] = scope;
			}
			regions[num] = region;
		}
	}

	private static List<GarmentArtRgb> ResolveSleevePalette(GarmentSpec spec, IReadOnlyList<GarmentArtRgb> fallback, GarmentArtRgb baseColor)
	{
		List<GarmentArtRgb> list = new List<GarmentArtRgb>();
		foreach (string item in spec.SleevePalette)
		{
			if (TryParseHex(item, out var color))
			{
				list.Add(color);
			}
		}
		if (list.Count == 0)
		{
			list.AddRange(fallback.Take(5));
		}
		if (list.Count == 0)
		{
			list.Add(baseColor);
		}
		return list;
	}

	private static (int Left, int Top, int Right, int Bottom) FindContentBounds(IReadOnlyList<GarmentCanvasRegion> regions, int width, int height)
	{
		int num = width;
		int num2 = -1;
		int num3 = height;
		int num4 = -1;
		for (int i = 0; i < height; i++)
		{
			for (int j = 0; j < width; j++)
			{
				if (regions[i * width + j] != GarmentCanvasRegion.Background)
				{
					num = Math.Min(num, j);
					num2 = Math.Max(num2, j);
					num3 = Math.Min(num3, i);
					num4 = Math.Max(num4, i);
				}
			}
		}
		if (num2 < num || num4 < num3)
		{
			return (Left: width / 4, Top: height / 4, Right: width * 3 / 4, Bottom: height * 3 / 4);
		}
		return (Left: num, Top: num3, Right: num2, Bottom: num4);
	}

	private static void FillPolygon(GarmentCanvasRegion[] regions, GarmentCanvasRegion region, IReadOnlyList<(int X, int Y)> points)
	{
		if (points.Count < 3)
		{
			return;
		}
		int num = Math.Max(0, points.Min(((int X, int Y) point) => point.X));
		int num2 = Math.Min(63, points.Max(((int X, int Y) point) => point.X));
		int num3 = Math.Max(0, points.Min(((int X, int Y) point) => point.Y));
		int num4 = Math.Min(95, points.Max(((int X, int Y) point) => point.Y));
		for (int num5 = num3; num5 <= num4; num5++)
		{
			for (int num6 = num; num6 <= num2; num6++)
			{
				if (PointInPolygon((double)num6 + 0.5, (double)num5 + 0.5, points))
				{
					SetRegion(regions, num6, num5, region);
				}
			}
		}
	}

	private static bool PointInPolygon(double x, double y, IReadOnlyList<(int X, int Y)> points)
	{
		bool flag = false;
		int num = 0;
		int index = points.Count - 1;
		while (num < points.Count)
		{
			var (num2, num3) = points[num];
			var (num4, num5) = points[index];
			if ((double)num3 > y != (double)num5 > y && x < (double)(num4 - num2) * (y - (double)num3) / (double)(num5 - num3) + (double)num2)
			{
				flag = !flag;
			}
			index = num++;
		}
		return flag;
	}

	private static void SetRegion(GarmentCanvasRegion[] regions, int x, int y, GarmentCanvasRegion region)
	{
		if (x >= 0 && x < 64 && y >= 0 && y < 96)
		{
			regions[y * 64 + x] = region;
		}
	}

	private static GarmentArtRgb MixRgb(GarmentArtRgb left, GarmentArtRgb right, double amount)
	{
		double num = Math.Clamp(amount, 0.0, 1.0);
		return new GarmentArtRgb((byte)Math.Clamp((int)Math.Round((double)(int)left.R + (double)(right.R - left.R) * num), 0, 255), (byte)Math.Clamp((int)Math.Round((double)(int)left.G + (double)(right.G - left.G) * num), 0, 255), (byte)Math.Clamp((int)Math.Round((double)(int)left.B + (double)(right.B - left.B) * num), 0, 255));
	}

	private static string NormalizeToken(string? value)
	{
		return (value ?? "").Trim().ToLowerInvariant().Replace('-', '_')
			.Replace(' ', '_');
	}

	private static bool IsCompositeCanvasSilhouette(string silhouette)
	{
		switch (silhouette)
		{
		case "overcoat":
		case "overalls":
		case "raincoat":
		case "bodysuit":
		case "jumpsuit":
		case "dress":
		case "parka":
		case "tunic":
		case "maxi_dress":
		case "mini_dress":
		case "midi_dress":
		case "long_tunic":
		case "coat":
		case "trench_coat":
		case "long_raincoat":
		case "romper":
			return true;
		default:
			return false;
		}
	}

	private static bool LooksLikeDecoratedTextile(PatternEvidence evidence, IReadOnlyList<GarmentArtRgb> palette, GarmentArtRgb baseColor)
	{
		return FindDecorativeEvidenceWindow(evidence, palette) != null;
	}

	private static DecorativeEvidenceWindow? FindDecorativeEvidenceWindow(PatternEvidence evidence, IReadOnlyList<GarmentArtRgb> palette, bool allowFullCanvas = true)
	{
		if (evidence.Width < 8 || evidence.Height < 8 || evidence.Cells.Count < 64)
		{
			return null;
		}
		Dictionary<(int, int), int> dictionary = evidence.Cells.ToDictionary((EvidenceCell cell) => (X: cell.X, Y: cell.Y), (EvidenceCell cell) => cell.PaletteIndex);
		int num = Math.Max(8, evidence.Height / 4);
		int num2 = Math.Max(2, evidence.Height / 16);
		HashSet<(int, int)> hashSet = new HashSet<(int, int)>();
		for (int num3 = 0; num3 + num <= evidence.Height; num3 += num2)
		{
			hashSet.Add((num3, num3 + num));
		}
		hashSet.Add((Math.Max(0, evidence.Height - num), evidence.Height));
		if (allowFullCanvas)
		{
			hashSet.Add((0, evidence.Height));
		}
		DecorativeEvidenceWindow decorativeEvidenceWindow = null;
		int num4 = Math.Max(64, (int)Math.Ceiling((double)evidence.Cells.Count * 0.12));
		foreach (var item6 in from range in hashSet
			orderby range.Top, range.Bottom
			select range)
		{
			int top = item6.Item1;
			int bottom = item6.Item2;
			List<EvidenceCell> windowCells = evidence.Cells.Where((EvidenceCell cell) => cell.Y >= top && cell.Y < bottom).ToList();
			if (windowCells.Count < num4)
			{
				continue;
			}
			Dictionary<int, int> counts = (from cell in windowCells
				group cell by cell.PaletteIndex).ToDictionary((IGrouping<int, EvidenceCell> group) => group.Key, (IGrouping<int, EvidenceCell> group) => group.Count());
			if (counts.Count < 8)
			{
				continue;
			}
			int num5 = 0;
			int num6 = 0;
			int num7 = 0;
			int num8 = 0;
			double num9 = 0.0;
			foreach (EvidenceCell item7 in windowCells)
			{
				if (dictionary.TryGetValue((item7.X + 1, item7.Y), out var value))
				{
					double num10 = ColorDistance(palette[item7.PaletteIndex], palette[value]);
					num5++;
					num9 += num10;
					if (num10 >= 55.0)
					{
						num7++;
					}
				}
				if (item7.Y + 1 < bottom && dictionary.TryGetValue((item7.X, item7.Y + 1), out var value2))
				{
					double num11 = ColorDistance(palette[item7.PaletteIndex], palette[value2]);
					num6++;
					num9 += num11;
					if (num11 >= 55.0)
					{
						num8++;
					}
				}
			}
			if (num5 < 32 || num6 < 32)
			{
				continue;
			}
			int num12 = num5 + num6;
			double num13 = (double)num7 / (double)num5;
			double num14 = (double)num8 / (double)num6;
			double num15 = (double)(num7 + num8) / (double)num12;
			double num16 = num9 / (double)num12;
			double num17 = Math.Min(num13, num14) / Math.Max(1E-06, Math.Max(num13, num14));
			if (num15 < 0.12 || num16 < 18.0 || num13 < 0.12 || num14 < 0.06 || num17 < 0.35)
			{
				continue;
			}
			List<int> common = (from pair in counts
				where (double)pair.Value / (double)windowCells.Count >= 0.06
				select pair.Key).ToList();
			if (common.Count == 0)
			{
				continue;
			}
			int index = common.MinBy((int candidate) => common.Sum((int other) => (double)counts[other] * ColorDistance(palette[candidate], palette[other])));
			GarmentArtRgb reference = palette[index];
			double referenceHue = RgbToHsl(reference).H;
			double referenceSaturation = HsvSaturation(reference);
			HashSet<int> accentIndices = (from pair in (from pair in counts
					where pair.Value >= 2 && (double)pair.Value / (double)windowCells.Count <= 0.04
					where ColorDistance(palette[pair.Key], reference) >= 70.0
					where Math.Abs(palette[pair.Key].Luma - reference.Luma) >= 0.14
					select pair).Where(delegate(KeyValuePair<int, int> pair)
				{
					double item5 = RgbToHsl(palette[pair.Key]).H;
					double num28 = HsvSaturation(palette[pair.Key]);
					double num29 = Math.Abs(item5 - referenceHue);
					num29 = Math.Min(num29, 360.0 - num29);
					return num29 >= 18.0 || Math.Abs(num28 - referenceSaturation) >= 0.18;
				})
				select pair.Key).ToHashSet();
			if (accentIndices.Count == 0)
			{
				continue;
			}
			Dictionary<(int, int), int> dictionary2 = windowCells.Where((EvidenceCell cell) => accentIndices.Contains(cell.PaletteIndex)).ToDictionary((EvidenceCell cell) => (X: cell.X, Y: cell.Y), (EvidenceCell cell) => cell.PaletteIndex);
			HashSet<(int, int)> hashSet2 = new HashSet<(int, int)>();
			List<List<(int, int)>> list = new List<List<(int, int)>>();
			foreach (var (item, item2) in from point in dictionary2.Keys
				orderby point.Y, point.X
				select point)
			{
				if (!hashSet2.Add((item, item2)))
				{
					continue;
				}
				Queue<(int, int)> queue = new Queue<(int, int)>();
				queue.Enqueue((item, item2));
				List<(int, int)> list2 = new List<(int, int)>();
				while (queue.Count > 0)
				{
					var (num18, num19) = queue.Dequeue();
					list2.Add((num18, num19));
					foreach (var (item3, item4) in CardinalNeighbors(num18, num19))
					{
						if (dictionary2.ContainsKey((item3, item4)) && hashSet2.Add((item3, item4)))
						{
							queue.Enqueue((item3, item4));
						}
					}
				}
				int num20 = list2.Max<(int, int)>(((int X, int Y) point) => point.X) - list2.Min<(int, int)>(((int X, int Y) point) => point.X) + 1;
				int num21 = list2.Max<(int, int)>(((int X, int Y) point) => point.Y) - list2.Min<(int, int)>(((int X, int Y) point) => point.Y) + 1;
				double num22 = (double)Math.Max(num20, num21) / (double)Math.Max(1, Math.Min(num20, num21));
				int count = list2.Count;
				if (count >= 2 && count <= 24 && num20 <= 8 && num21 <= 8 && num22 <= 4.0)
				{
					list.Add(list2);
				}
			}
			int num23 = list.Sum((List<(int X, int Y)> component) => component.Count);
			if (list.Count < 4 || num23 < 12)
			{
				continue;
			}
			int num24 = windowCells.Min((EvidenceCell cell) => cell.X);
			int num25 = windowCells.Max((EvidenceCell cell) => cell.X);
			double[] source = list.Select((List<(int X, int Y)> component) => component.Average(((int X, int Y) point) => point.X)).ToArray();
			double num26 = (source.Max() - source.Min()) / Math.Max(1.0, num25 - num24 + 1);
			if (!(num26 < 0.35))
			{
				double num27 = num15 * 2.0 + num16 / 255.0 + Math.Min((double)num23 / 100.0, 0.25) + num26 * 0.1;
				if (decorativeEvidenceWindow == null || num27 > decorativeEvidenceWindow.Score)
				{
					decorativeEvidenceWindow = new DecorativeEvidenceWindow
					{
						Top = top,
						Bottom = bottom,
						Score = num27,
						FabricReference = reference,
						Components = list
					};
				}
			}
		}
		return decorativeEvidenceWindow;
	}

	public static GarmentArtRgb Shade(GarmentArtRgb color, int shadeStep)
	{
		IReadOnlyList<GarmentArtRgb> readOnlyList = BuildShadeRamp(color);
		return readOnlyList[Math.Clamp(2 + shadeStep, 0, readOnlyList.Count - 1)];
	}

	private static List<GarmentArtRgb> ResolvePalette(GarmentSpec spec)
	{
		List<GarmentArtRgb> list = new List<GarmentArtRgb>();
		foreach (string item in spec.Palette)
		{
			list.Add(TryParseHex(item, out var color) ? color : list.LastOrDefault(new GarmentArtRgb(96, 104, 116)));
		}
		if (list.Count == 0)
		{
			string[] array = new string[3] { spec.PrimaryColor, spec.SecondaryColor, spec.AccentColor };
			for (int i = 0; i < array.Length; i++)
			{
				if (TryParseHex(array[i], out var color2) && !list.Contains(color2))
				{
					list.Add(color2);
				}
			}
			if (list.Count == 0)
			{
				list.Add(new GarmentArtRgb(96, 104, 116));
			}
		}
		return list;
	}

	private static PatternEvidence ReadEvidence(GarmentSpec spec, int paletteCount)
	{
		int patternWidth = spec.PatternWidth;
		int patternHeight = spec.PatternHeight;
		if (patternWidth <= 0 || patternHeight <= 0 || spec.PatternMap.Count < patternWidth * patternHeight)
		{
			return new PatternEvidence
			{
				Width = 0,
				Height = 0,
				BaseIndex = 0
			};
		}
		List<EvidenceCell> list = new List<EvidenceCell>();
		int[] array = new int[Math.Max(1, paletteCount)];
		for (int i = 0; i < patternHeight; i++)
		{
			for (int j = 0; j < patternWidth; j++)
			{
				int num = spec.PatternMap[i * patternWidth + j];
				if (num >= 0 && num < paletteCount && IsOccupied(spec.Blueprint, j, i, patternWidth, patternHeight))
				{
					list.Add(new EvidenceCell(j, i, num));
					array[num]++;
				}
			}
		}
		int num2 = 0;
		for (int k = 1; k < array.Length; k++)
		{
			if (array[k] > array[num2])
			{
				num2 = k;
			}
		}
		return new PatternEvidence
		{
			Width = patternWidth,
			Height = patternHeight,
			Cells = list,
			BaseIndex = num2
		};
	}

	private static bool IsOccupied(GarmentBlueprint? blueprint, int x, int y, int width, int height)
	{
		if (blueprint == null || blueprint.CanvasWidth <= 0 || blueprint.CanvasHeight <= 0 || blueprint.OccupancyMap.Count < blueprint.CanvasWidth * blueprint.CanvasHeight)
		{
			return true;
		}
		int num = Math.Clamp((int)(((double)x + 0.5) * (double)blueprint.CanvasWidth / (double)width), 0, blueprint.CanvasWidth - 1);
		int num2 = Math.Clamp((int)(((double)y + 0.5) * (double)blueprint.CanvasHeight / (double)height), 0, blueprint.CanvasHeight - 1);
		return blueprint.OccupancyMap[num2 * blueprint.CanvasWidth + num] > 0;
	}

	private static List<double> CompileTrustedTierRows(GarmentSpec spec, PatternEvidence evidence, IReadOnlyList<GarmentArtRgb> palette, bool permitsMapStructure)
	{
		if (!IsSkirtLike(spec))
		{
			return new List<double>();
		}
		List<double> list = spec.Blueprint?.Features.Where(delegate(GarmentFeature feature)
		{
			bool flag = feature.Confidence >= 0.6;
			if (flag)
			{
				bool flag2;
				switch (feature.Type.Trim().ToLowerInvariant())
				{
				case "tier":
				case "tier_seam":
				case "ruffle":
				case "horizontal_seam":
					flag2 = true;
					break;
				default:
					flag2 = false;
					break;
				}
				flag = flag2;
			}
			return flag;
		}).Select((GarmentFeature feature) => Math.Clamp(feature.Y, 0.08, 0.94)).OrderBy((double value) => value)
			.ToList() ?? new List<double>();
		if (permitsMapStructure && evidence.Width >= 8 && evidence.Height >= 8)
		{
			int count = palette.Count;
			double[][] array = new double[evidence.Height][];
			int[] array2 = new int[evidence.Height];
			for (int num = 0; num < evidence.Height; num++)
			{
				array[num] = new double[count];
			}
			foreach (EvidenceCell cell in evidence.Cells)
			{
				array[cell.Y][cell.PaletteIndex]++;
				array2[cell.Y]++;
			}
			int num2 = Math.Max(2, evidence.Height / 12);
			List<(int, double)> list2 = new List<(int, double)>();
			for (int num3 = num2; num3 < evidence.Height - num2; num3++)
			{
				int num4 = Math.Max(8, num2 * evidence.Width / 8);
				int num5 = array2.Skip(num3 - num2).Take(num2).Sum();
				int num6 = array2.Skip(num3).Take(num2).Sum();
				if (num5 >= num4 && num6 >= num4)
				{
					double[] array3 = AggregateRows(array, array2, num3 - num2, num3);
					double[] array4 = AggregateRows(array, array2, num3, num3 + num2);
					double num7 = TotalVariation(array3, array4);
					int num8 = DominantIndex(array3);
					int num9 = DominantIndex(array4);
					double num10 = ColorDistance(palette[num8], palette[num9]);
					if (num7 >= 0.34 && (num8 != num9 || num10 >= 24.0))
					{
						list2.Add((num3, num7 + Math.Min(num10 / 255.0, 0.25)));
					}
				}
			}
			int minimumGap = Math.Max(3, evidence.Height / 7);
			foreach (var item2 in from candidate in list2
				orderby candidate.Score descending, candidate.Y
				select candidate)
			{
				int item = item2.Item1;
				double normalized = (double)item / (double)evidence.Height;
				if (!(normalized < 0.12) && !(normalized > 0.9) && !list.Any((double existing) => Math.Abs(existing - normalized) * (double)evidence.Height < (double)minimumGap))
				{
					list.Add(normalized);
					if (list.Count >= 3)
					{
						break;
					}
				}
			}
		}
		return list.OrderBy((double value) => value).Aggregate(new List<double>(), delegate(List<double> rows, double value)
		{
			if (rows.Count != 0)
			{
				if (!(Math.Abs(rows[rows.Count - 1] - value) >= 0.08))
				{
					goto IL_002f;
				}
			}
			rows.Add(value);
			goto IL_002f;
			IL_002f:
			return rows;
		});
	}

	private static bool IsSkirtLike(GarmentSpec spec)
	{
		string text = string.Join(' ', spec.Silhouette, spec.SemanticDescription, spec.Blueprint?.SemanticType ?? "").ToLowerInvariant();
		if (!text.Contains("skirt", StringComparison.Ordinal) && !text.Contains("dress", StringComparison.Ordinal))
		{
			return text.Contains("gown", StringComparison.Ordinal);
		}
		return true;
	}

	private static double[] AggregateRows(double[][] rows, int[] population, int start, int end)
	{
		double[] array = new double[rows[0].Length];
		double num = 0.0;
		for (int i = Math.Max(0, start); i < Math.Min(rows.Length, end); i++)
		{
			if (population[i] != 0)
			{
				for (int j = 0; j < array.Length; j++)
				{
					array[j] += rows[i][j];
				}
				num += (double)population[i];
			}
		}
		if (num > 0.0)
		{
			for (int k = 0; k < array.Length; k++)
			{
				array[k] /= num;
			}
		}
		return array;
	}

	private static double TotalVariation(IReadOnlyList<double> left, IReadOnlyList<double> right)
	{
		double num = 0.0;
		for (int i = 0; i < left.Count; i++)
		{
			num += Math.Abs(left[i] - right[i]);
		}
		return num * 0.5;
	}

	private static int DominantIndex(IReadOnlyList<double> histogram)
	{
		int num = 0;
		for (int i = 1; i < histogram.Count; i++)
		{
			if (histogram[i] > histogram[num])
			{
				num = i;
			}
		}
		return num;
	}

	private static List<GarmentColorBand> CompileBaseBands(PatternEvidence evidence, IReadOnlyList<GarmentArtRgb> palette, GarmentArtRgb baseColor, IReadOnlyList<double> tierRows, bool permitsMapStructure)
	{
		if (!permitsMapStructure || evidence.Width == 0 || tierRows.Count == 0)
		{
			return new List<GarmentColorBand>
			{
				new GarmentColorBand
				{
					Top = 0.0,
					Bottom = 1.0,
					Color = baseColor
				}
			};
		}
		List<double> list = new List<double> { 0.0 };
		list.AddRange(tierRows);
		list.Add(1.0);
		List<GarmentColorBand> list2 = new List<GarmentColorBand>();
		for (int i = 0; i < list.Count - 1; i++)
		{
			double num = list[i];
			double num2 = list[i + 1];
			int num3 = Math.Clamp((int)Math.Floor(num * (double)evidence.Height), 0, evidence.Height - 1);
			int num4 = Math.Clamp((int)Math.Ceiling(num2 * (double)evidence.Height), num3 + 1, evidence.Height);
			int[] array = new int[palette.Count];
			foreach (EvidenceCell cell in evidence.Cells)
			{
				if (cell.Y >= num3 && cell.Y < num4)
				{
					array[cell.PaletteIndex]++;
				}
			}
			GarmentArtRgb color = ((array.Sum() == 0) ? baseColor : WeightedFabricColor(array, palette, baseColor));
			list2.Add(new GarmentColorBand
			{
				Top = num,
				Bottom = num2,
				Color = color
			});
		}
		return list2;
	}

	private static GarmentArtRgb WeightedFabricColor(IReadOnlyList<int> counts, IReadOnlyList<GarmentArtRgb> palette, GarmentArtRgb fallback)
	{
		int total = counts.Sum();
		if (total <= 0)
		{
			return fallback;
		}
		List<int> list = (from index in Enumerable.Range(0, counts.Count)
			where counts[index] > 0 && (double)counts[index] / (double)total >= 0.025
			select index).ToList();
		if (list.Count == 0)
		{
			list = (from index in Enumerable.Range(0, counts.Count)
				where counts[index] > 0
				select index).ToList();
		}
		long num = ((IEnumerable<int>)list).Sum((Func<int, long>)((int index) => counts[index]));
		if (num <= 0)
		{
			return fallback;
		}
		GarmentArtRgb garmentArtRgb = new GarmentArtRgb((byte)Math.Clamp((int)Math.Round((double)list.Sum((int index) => (long)palette[index].R * (long)counts[index]) / (double)num), 0, 255), (byte)Math.Clamp((int)Math.Round((double)list.Sum((int index) => (long)palette[index].G * (long)counts[index]) / (double)num), 0, 255), (byte)Math.Clamp((int)Math.Round((double)list.Sum((int index) => (long)palette[index].B * (long)counts[index]) / (double)num), 0, 255));
		if (fallback.Luma >= 0.2 && garmentArtRgb.Luma < fallback.Luma * 0.72)
		{
			return MixRgb(garmentArtRgb, fallback, 0.55);
		}
		return garmentArtRgb;
	}

	private static (List<GarmentMotifStamp> Stamps, int Retained, int Rejected) CompileFloralMotifs(GarmentSpec spec, PatternEvidence evidence, IReadOnlyList<GarmentArtRgb> palette, GarmentArtRgb baseColor)
	{
		if (evidence.Width == 0 || evidence.Cells.Count == 0)
		{
			return (Stamps: new List<GarmentMotifStamp>(), Retained: 0, Rejected: 0);
		}
		string text = NormalizePattern(spec.Pattern);
		bool flag = ((text == "other" || text == "unknown") ? true : false);
		DecorativeEvidenceWindow decorativeEvidenceWindow = (flag ? FindDecorativeEvidenceWindow(evidence, palette) : null);
		if (flag && decorativeEvidenceWindow == null)
		{
			return (Stamps: new List<GarmentMotifStamp>(), Retained: 0, Rejected: 0);
		}
		Dictionary<(int X, int Y), int> allEvidence = evidence.Cells.ToDictionary((EvidenceCell cell) => (X: cell.X, Y: cell.Y), (EvidenceCell cell) => cell.PaletteIndex);
		int num = 0;
		List<List<(int, int)>> list;
		Dictionary<(int, int), int> dictionary;
		if (decorativeEvidenceWindow != null)
		{
			list = decorativeEvidenceWindow.Components.Select((List<(int X, int Y)> component) => new List<(int, int)>(component)).ToList();
			dictionary = list.SelectMany((List<(int X, int Y)> component) => component).Distinct().ToDictionary(((int X, int Y) point) => point, ((int X, int Y) point) => allEvidence[point]);
		}
		else
		{
			dictionary = evidence.Cells.Where((EvidenceCell cell) => cell.PaletteIndex != evidence.BaseIndex && ColorDistance(palette[cell.PaletteIndex], baseColor) >= 22.0).ToDictionary((EvidenceCell cell) => (X: cell.X, Y: cell.Y), (EvidenceCell cell) => cell.PaletteIndex);
			HashSet<(int, int)> hashSet = new HashSet<(int, int)>();
			list = new List<List<(int, int)>>();
			foreach (var (item, item2) in from point in dictionary.Keys
				orderby point.Y, point.X
				select point)
			{
				if (!hashSet.Add((item, item2)))
				{
					continue;
				}
				Queue<(int, int)> queue = new Queue<(int, int)>();
				queue.Enqueue((item, item2));
				List<(int, int)> list2 = new List<(int, int)>();
				while (queue.Count > 0)
				{
					var (num2, num3) = queue.Dequeue();
					list2.Add((num2, num3));
					foreach (var (item3, item4) in CardinalNeighbors(num2, num3))
					{
						if (dictionary.ContainsKey((item3, item4)) && hashSet.Add((item3, item4)))
						{
							queue.Enqueue((item3, item4));
						}
					}
				}
				if (list2.Count >= 2)
				{
					list.Add(list2);
				}
				else
				{
					num++;
				}
			}
		}
		int num4 = list.Sum((List<(int X, int Y)> component) => component.Count);
		if (num4 == 0)
		{
			return (Stamps: new List<GarmentMotifStamp>(), Retained: 0, Rejected: num);
		}
		Dictionary<int, int> dictionary2 = new Dictionary<int, int>();
		foreach (List<(int, int)> item9 in list)
		{
			foreach (var item10 in item9)
			{
				int item5 = item10.Item1;
				int item6 = item10.Item2;
				int key = dictionary[(item5, item6)];
				dictionary2[key] = dictionary2.GetValueOrDefault(key) + 1;
			}
		}
		List<KeyValuePair<int, int>> list3 = dictionary2.Where((KeyValuePair<int, int> pair) => pair.Value >= 2).ToList();
		List<int> selectedAccentIndices = new List<int>();
		if (list3.Count > 0)
		{
			IEnumerable<KeyValuePair<int, int>> source = list3.Where((KeyValuePair<int, int> pair) => palette[pair.Key].Luma >= baseColor.Luma + 0.06);
			if (!source.Any())
			{
				source = list3;
			}
			int readable = source.MaxBy((KeyValuePair<int, int> pair) => ColorDistance(palette[pair.Key], baseColor) * Math.Sqrt(pair.Value)).Key;
			selectedAccentIndices.Add(readable);
			int item7 = (from pair in list3
				where pair.Key != readable
				orderby palette[pair.Key].Luma descending, ColorDistance(palette[pair.Key], baseColor) descending
				select pair.Key).FirstOrDefault(readable);
			if (!selectedAccentIndices.Contains(item7))
			{
				selectedAccentIndices.Add(item7);
			}
			int item8 = (from pair in list3
				where !selectedAccentIndices.Contains(pair.Key)
				orderby HueDistance(palette[pair.Key], baseColor) descending, (palette[pair.Key].Luma >= baseColor.Luma + 0.06) ? 1 : 0 descending, pair.Value descending, ColorDistance(palette[pair.Key], baseColor) descending
				select pair.Key).FirstOrDefault(readable);
			if (!selectedAccentIndices.Contains(item8))
			{
				selectedAccentIndices.Add(item8);
			}
		}
		List<GarmentArtRgb> list4 = (from index in selectedAccentIndices.Take(3)
			select LiftUnsafeDark(palette[index], baseColor)).ToList();
		if (list4.Count == 0)
		{
			return (Stamps: new List<GarmentMotifStamp>(), Retained: 0, Rejected: num);
		}
		double num5 = (double)num4 / (double)Math.Max(1, evidence.Cells.Count);
		int num6 = ((decorativeEvidenceWindow == null) ? Math.Clamp((int)Math.Round(2.0 + num5 * 5.0), 2, 3) : Math.Clamp(decorativeEvidenceWindow.Components.Count, 3, 5));
		int num7 = ((decorativeEvidenceWindow == null) ? Math.Clamp((int)Math.Round(2.0 + Math.Sqrt((double)num4 / (double)num6)), 5, 6) : Math.Clamp((int)Math.Round(2.0 + Math.Sqrt((double)num4 / (double)num6)), 4, 6));
		double value = ((decorativeEvidenceWindow == null) ? list.SelectMany((List<(int X, int Y)> component) => component).Average(((int X, int Y) point) => ((double)point.Y + 0.5) / (double)evidence.Height) : ((double)(decorativeEvidenceWindow.Top + decorativeEvidenceWindow.Bottom) / (2.0 * (double)evidence.Height)));
		value = Math.Clamp(value, (decorativeEvidenceWindow == null) ? 0.28 : 0.1, (decorativeEvidenceWindow == null) ? 0.72 : 0.9);
		double verticalSpread = ((decorativeEvidenceWindow == null) ? 1.0 : 0.4);
		List<GarmentMotifStamp> list5 = new List<GarmentMotifStamp>();
		AddFacingMotifs(list5, GarmentArtFacing.Front, num6, num7, value, 1.0, list4, verticalSpread);
		AddFacingMotifs(list5, GarmentArtFacing.Left, Math.Max(1, num6 / 2), Math.Max(2, num7 - 1), value, 0.68, list4, verticalSpread);
		AddFacingMotifs(list5, GarmentArtFacing.Right, Math.Max(1, num6 / 2), Math.Max(2, num7 - 1), value, 0.68, list4, verticalSpread);
		AddFacingMotifs(list5, GarmentArtFacing.Back, Math.Max(1, (num6 - 1) / 2), Math.Max(2, num7 - 2), value, 0.52, list4, verticalSpread);
		return (Stamps: list5, Retained: num4, Rejected: num);
	}

	private static void AddFacingMotifs(ICollection<GarmentMotifStamp> output, GarmentArtFacing facing, int count, int motifSize, double centerY, double opacity, IReadOnlyList<GarmentArtRgb> colors, double verticalSpread = 1.0)
	{
		if (count > 0)
		{
			(double, double)[] array = Math.Clamp(count, 1, 5) switch
			{
				1 => new(double, double)[1] { (0.5, centerY) }, 
				2 => new(double, double)[2]
				{
					(0.32, centerY - 0.01),
					(0.68, centerY + 0.14)
				}, 
				3 => new(double, double)[3]
				{
					(0.27, centerY),
					(0.73, centerY + 0.13),
					(0.46, centerY + 0.28)
				}, 
				4 => new(double, double)[4]
				{
					(0.3, centerY - 0.1),
					(0.67, centerY - 0.07),
					(0.42, centerY + 0.12),
					(0.72, centerY + 0.16)
				}, 
				_ => new(double, double)[5]
				{
					(0.22, centerY - 0.08),
					(0.5, centerY - 0.1),
					(0.78, centerY - 0.06),
					(0.35, centerY + 0.12),
					(0.65, centerY + 0.15)
				}, 
			};
			for (int i = 0; i < array.Length; i++)
			{
				output.Add(new GarmentMotifStamp
				{
					Facing = facing,
					X = array[i].Item1,
					Y = Math.Clamp(centerY + (array[i].Item2 - centerY) * verticalSpread, 0.08, 0.92),
					Opacity = opacity,
					Pixels = BuildConnectedFlower(motifSize, colors, i)
				});
			}
		}
	}

	private static IReadOnlyList<GarmentMotifPixel> BuildConnectedFlower(int requestedSize, IReadOnlyList<GarmentArtRgb> colors, int variant)
	{
		(int, int)[] array = ((variant % 2 != 0) ? new(int, int)[8]
		{
			(0, 0),
			(0, 1),
			(1, 0),
			(-1, 0),
			(0, -1),
			(-1, 1),
			(1, 1),
			(-1, -1)
		} : new(int, int)[8]
		{
			(0, 0),
			(1, 0),
			(0, 1),
			(-1, 0),
			(0, -1),
			(1, 1),
			(-1, 1),
			(1, -1)
		});
		int num = Math.Clamp(requestedSize, 2, 8);
		GarmentArtRgb petalColor = colors.MaxBy((GarmentArtRgb garmentArtRgb3) => garmentArtRgb3.Luma);
		GarmentArtRgb centerColor = colors.Where((GarmentArtRgb garmentArtRgb3) => garmentArtRgb3 != petalColor).MinBy((GarmentArtRgb garmentArtRgb3) => garmentArtRgb3.Luma);
		if (centerColor == default(GarmentArtRgb))
		{
			centerColor = colors[0];
		}
		GarmentArtRgb garmentArtRgb = colors.FirstOrDefault((GarmentArtRgb garmentArtRgb3) => garmentArtRgb3 != petalColor && garmentArtRgb3 != centerColor, colors[0]);
		List<GarmentMotifPixel> list = new List<GarmentMotifPixel>(num);
		for (int num2 = 0; num2 < num; num2++)
		{
			(int, int) tuple = array[num2];
			int item = tuple.Item1;
			int item2 = tuple.Item2;
			GarmentArtRgb garmentArtRgb2 = ((num2 > 4) ? garmentArtRgb : ((num2 != 0) ? petalColor : centerColor));
			GarmentArtRgb color = garmentArtRgb2;
			list.Add(new GarmentMotifPixel(item, item2, color));
		}
		return list;
	}

	private static IEnumerable<(int X, int Y)> CardinalNeighbors(int x, int y)
	{
		yield return (X: x - 1, Y: y);
		yield return (X: x + 1, Y: y);
		yield return (X: x, Y: y - 1);
		yield return (X: x, Y: y + 1);
	}

	private static List<GarmentArtRgb> BuildShadeRamp(GarmentArtRgb color)
	{
		(double, double, double) tuple = RgbToHsl(color);
		double h = tuple.Item1;
		double s = tuple.Item2;
		double item = tuple.Item3;
		double num = ((item >= 0.68) ? 0.38 : ((item >= 0.5) ? 0.26 : Math.Min(0.18, item * 0.72)));
		return new double[5]
		{
			Math.Max(num, item * 0.62),
			Math.Max(num + 0.04, item * 0.82),
			item,
			item + (1.0 - item) * 0.2,
			item + (1.0 - item) * 0.38
		}.Select((double value) => HslToRgb(h, s, Math.Clamp(value, 0.0, 1.0))).ToList();
	}

	private static GarmentArtRgb LiftUnsafeDark(GarmentArtRgb color, GarmentArtRgb baseColor)
	{
		if (color.Luma >= 0.16)
		{
			return color;
		}
		var (h, num, _) = RgbToHsl(color);
		var (num2, _, num3) = RgbToHsl(baseColor);
		if (num < 0.08)
		{
			h = num2;
		}
		double l = ((num3 >= 0.65) ? 0.3 : 0.22);
		return HslToRgb(h, Math.Max(0.18, num), l);
	}

	private static bool TryParseHex(string? value, out GarmentArtRgb color)
	{
		color = default(GarmentArtRgb);
		if (string.IsNullOrWhiteSpace(value))
		{
			return false;
		}
		string text = value.Trim().TrimStart('#');
		if (text.Length == 3)
		{
			text = string.Concat(text.Select((char character) => new string(character, 2)));
		}
		if (text.Length != 6 || !int.TryParse(text, NumberStyles.HexNumber, CultureInfo.InvariantCulture, out var result))
		{
			return false;
		}
		color = new GarmentArtRgb((byte)(result >> 16), (byte)(result >> 8), (byte)result);
		return true;
	}

	private static string ResolvePattern(GarmentSpec spec)
	{
		string text = NormalizePattern(spec.Pattern);
		switch (text)
		{
		default:
			return CanonicalPattern(text);
		case "solid":
		case "other":
		case "unknown":
			return spec.Blueprint?.Regions.Where((GarmentRegion region) => region.Width * region.Height >= 0.04).Select((GarmentRegion region) => NormalizePattern(region.Pattern)).Where((string pattern) => !(pattern == "solid") && !(pattern == "other") && !(pattern == "unknown"))
				.GroupBy((string pattern) => CanonicalPattern(pattern))
				.OrderByDescending((IGrouping<string, string> group) => group.Count())
				.ThenBy((IGrouping<string, string> group) => group.Key)
				.Select((IGrouping<string, string> group) => group.Key)
				.FirstOrDefault() ?? CanonicalPattern(text);
		}
	}

	private static string NormalizePattern(string? value)
	{
		if (!string.IsNullOrWhiteSpace(value))
		{
			return value.Trim().ToLowerInvariant().Replace('-', '_');
		}
		return "solid";
	}

	private static string CanonicalPattern(string value)
	{
		if (value.Contains("floral", StringComparison.Ordinal) || value.Contains("flower", StringComparison.Ordinal))
		{
			return "floral";
		}
		if (value.Contains("stripe", StringComparison.Ordinal))
		{
			return "striped";
		}
		if (value.Contains("color_block", StringComparison.Ordinal) || value.Contains("colour_block", StringComparison.Ordinal) || value.Contains("colorblock", StringComparison.Ordinal) || value.Contains("colourblock", StringComparison.Ordinal))
		{
			return "colorblock";
		}
		return value;
	}

	private static double ColorDistance(GarmentArtRgb left, GarmentArtRgb right)
	{
		double num = left.R - right.R;
		double num2 = left.G - right.G;
		double num3 = left.B - right.B;
		return Math.Sqrt(num * num + num2 * num2 + num3 * num3);
	}

	private static double HueDistance(GarmentArtRgb left, GarmentArtRgb right)
	{
		(double H, double S, double L) tuple = RgbToHsl(left);
		double item = tuple.H;
		double item2 = tuple.S;
		(double H, double S, double L) tuple2 = RgbToHsl(right);
		double item3 = tuple2.H;
		double item4 = tuple2.S;
		double num = Math.Abs(item - item3);
		num = Math.Min(num, 360.0 - num);
		return num * (0.25 + Math.Max(item2, item4));
	}

	private static double HsvSaturation(GarmentArtRgb color)
	{
		double num = (double)(int)Math.Max(color.R, Math.Max(color.G, color.B)) / 255.0;
		double num2 = (double)(int)Math.Min(color.R, Math.Min(color.G, color.B)) / 255.0;
		if (!(num <= 1E-06))
		{
			return (num - num2) / num;
		}
		return 0.0;
	}

	private static (double H, double S, double L) RgbToHsl(GarmentArtRgb color)
	{
		double num = (double)(int)color.R / 255.0;
		double num2 = (double)(int)color.G / 255.0;
		double num3 = (double)(int)color.B / 255.0;
		double num4 = Math.Max(num, Math.Max(num2, num3));
		double num5 = Math.Min(num, Math.Min(num2, num3));
		double num6 = (num4 + num5) / 2.0;
		double num7 = num4 - num5;
		if (num7 < 1E-06)
		{
			return (H: 0.0, S: 0.0, L: num6);
		}
		double item = num7 / (1.0 - Math.Abs(2.0 * num6 - 1.0));
		double num8 = ((num4 == num) ? (60.0 * ((num2 - num3) / num7 % 6.0)) : ((num4 != num2) ? (60.0 * ((num - num2) / num7 + 4.0)) : (60.0 * ((num3 - num) / num7 + 2.0))));
		if (num8 < 0.0)
		{
			num8 += 360.0;
		}
		return (H: num8, S: item, L: num6);
	}

	private static GarmentArtRgb HslToRgb(double h, double s, double l)
	{
		double num = (1.0 - Math.Abs(2.0 * l - 1.0)) * s;
		double num2 = num * (1.0 - Math.Abs(h / 60.0 % 2.0 - 1.0));
		double num3 = l - num / 2.0;
		var (num4, num5, num6) = ((h < 60.0) ? (num, num2, 0.0) : ((h < 120.0) ? (num2, num, 0.0) : ((h < 180.0) ? (0.0, num, num2) : ((h < 240.0) ? (0.0, num2, num) : ((!(h < 300.0)) ? (num, 0.0, num2) : (num2, 0.0, num))))));
		return new GarmentArtRgb((byte)Math.Clamp((int)Math.Round((num4 + num3) * 255.0), 0, 255), (byte)Math.Clamp((int)Math.Round((num5 + num3) * 255.0), 0, 255), (byte)Math.Clamp((int)Math.Round((num6 + num3) * 255.0), 0, 255));
	}
}
