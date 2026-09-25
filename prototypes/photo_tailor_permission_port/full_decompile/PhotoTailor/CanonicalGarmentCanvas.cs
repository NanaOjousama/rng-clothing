using System;
using System.Collections.Generic;

namespace PhotoTailor;

internal sealed class CanonicalGarmentCanvas
{
	internal const int PortraitWidth = 64;

	internal const int PortraitHeight = 96;

	private readonly GarmentArtRgba[] basePixels;

	private readonly GarmentArtRgba[] projectionOverlayPixels;

	private readonly GarmentProjectionScope[] projectionScopes;

	internal int Width => 64;

	internal int Height => 96;

	internal IReadOnlyList<GarmentArtRgba> Pixels { get; }

	internal IReadOnlyList<GarmentCanvasRegion> RegionMap { get; }

	internal IReadOnlyList<GarmentProjectionScope> ProjectionScopes => projectionScopes;

	internal int ContentLeft { get; }

	internal int ContentTop { get; }

	internal int ContentRight { get; }

	internal int ContentBottom { get; }

	internal CanonicalGarmentCanvas(GarmentArtRgba[] pixels, GarmentArtRgba[] basePixels, GarmentArtRgba[] projectionOverlayPixels, GarmentProjectionScope[] projectionScopes, GarmentCanvasRegion[] regionMap, int contentLeft, int contentTop, int contentRight, int contentBottom)
	{
		int num = 6144;
		if (pixels.Length != num || basePixels.Length != num || projectionOverlayPixels.Length != num || projectionScopes.Length != num || regionMap.Length != num)
		{
			throw new ArgumentException("Canonical garment canvas data has an invalid size.");
		}
		Pixels = pixels;
		this.basePixels = basePixels;
		this.projectionOverlayPixels = projectionOverlayPixels;
		this.projectionScopes = projectionScopes;
		RegionMap = regionMap;
		ContentLeft = Math.Clamp(contentLeft, 0, 63);
		ContentTop = Math.Clamp(contentTop, 0, 95);
		ContentRight = Math.Clamp(contentRight, ContentLeft, 63);
		ContentBottom = Math.Clamp(contentBottom, ContentTop, 95);
	}

	internal GarmentArtRgb SampleProjection(GarmentArtFacing facing, double artworkTop, double artworkBottom, double u, double v, GarmentArtRgb fallback, double footprintU = 0.0, double footprintV = 0.0)
	{
		double num = Math.Clamp(artworkTop, 0.0, 0.999);
		double num2 = Math.Clamp(artworkBottom, num + 0.001, 1.0);
		double num3 = num + Math.Clamp(v, 0.0, 1.0) * (num2 - num);
		double num4 = facing switch
		{
			GarmentArtFacing.Right => 0.45 + Math.Clamp(u, 0.0, 1.0) * 0.55, 
			GarmentArtFacing.Left => 0.55 - Math.Clamp(u, 0.0, 1.0) * 0.55, 
			GarmentArtFacing.Back => 1.0 - Math.Clamp(u, 0.0, 1.0), 
			_ => Math.Clamp(u, 0.0, 1.0), 
		};
		int x = ContentLeft + (int)Math.Round(num4 * (double)Math.Max(0, ContentRight - ContentLeft));
		int y = ContentTop + (int)Math.Round(num3 * (double)Math.Max(0, ContentBottom - ContentTop));
		int radiusX = Math.Clamp((int)Math.Ceiling(Math.Max(0.0, footprintU) * (double)Math.Max(1, ContentRight - ContentLeft) * 0.5), 0, 6);
		int radiusY = Math.Clamp((int)Math.Ceiling(Math.Max(0.0, footprintV) * (double)Math.Max(1, ContentBottom - ContentTop) * 0.5), 0, 8);
		if (TrySampleScopedDetail(facing, x, y, radiusX, radiusY, out var color))
		{
			return color;
		}
		if (TrySampleNearestOpaque(facing, x, y, out var color2))
		{
			return color2;
		}
		return fallback;
	}

	private bool TrySampleScopedDetail(GarmentArtFacing facing, int x, int y, int radiusX, int radiusY, out GarmentArtRgb color)
	{
		int num = int.MaxValue;
		int num2 = -1;
		for (int i = Math.Max(ContentTop, y - radiusY); i <= Math.Min(ContentBottom, y + radiusY); i++)
		{
			for (int j = Math.Max(ContentLeft, x - radiusX); j <= Math.Min(ContentRight, x + radiusX); j++)
			{
				int num3 = i * 64 + j;
				if (IsScopeVisible(projectionScopes[num3], facing) && projectionOverlayPixels[num3].A >= 16)
				{
					int num4 = Math.Abs(j - x) + Math.Abs(i - y);
					if (num4 < num)
					{
						num = num4;
						num2 = num3;
					}
				}
			}
		}
		if (num2 >= 0)
		{
			color = projectionOverlayPixels[num2].Rgb;
			return true;
		}
		color = default(GarmentArtRgb);
		return false;
	}

	private bool TrySampleNearestOpaque(GarmentArtFacing facing, int x, int y, out GarmentArtRgb color)
	{
		x = Math.Clamp(x, ContentLeft, ContentRight);
		y = Math.Clamp(y, ContentTop, ContentBottom);
		GarmentArtRgba garmentArtRgba = ResolveProjectionPixel(y * 64 + x, facing);
		if (garmentArtRgba.A >= 16)
		{
			color = garmentArtRgba.Rgb;
			return true;
		}
		for (int i = 1; i <= 12; i++)
		{
			for (int j = -i; j <= i; j++)
			{
				int[] array = new int[2]
				{
					y - i,
					y + i
				};
				foreach (int num in array)
				{
					int num2 = x + j;
					if (num2 >= ContentLeft && num2 <= ContentRight && num >= ContentTop && num <= ContentBottom)
					{
						GarmentArtRgba garmentArtRgba2 = ResolveProjectionPixel(num * 64 + num2, facing);
						if (garmentArtRgba2.A >= 16)
						{
							color = garmentArtRgba2.Rgb;
							return true;
						}
					}
				}
			}
			for (int l = -i + 1; l < i; l++)
			{
				int[] array = new int[2]
				{
					x - i,
					x + i
				};
				foreach (int num3 in array)
				{
					int num4 = y + l;
					if (num3 >= ContentLeft && num3 <= ContentRight && num4 >= ContentTop && num4 <= ContentBottom)
					{
						GarmentArtRgba garmentArtRgba3 = ResolveProjectionPixel(num4 * 64 + num3, facing);
						if (garmentArtRgba3.A >= 16)
						{
							color = garmentArtRgba3.Rgb;
							return true;
						}
					}
				}
			}
		}
		color = default(GarmentArtRgb);
		return false;
	}

	private GarmentArtRgba ResolveProjectionPixel(int index, GarmentArtFacing facing)
	{
		if (!IsScopeVisible(projectionScopes[index], facing) || projectionOverlayPixels[index].A < 16)
		{
			return basePixels[index];
		}
		return projectionOverlayPixels[index];
	}

	private static bool IsScopeVisible(GarmentProjectionScope scope, GarmentArtFacing facing)
	{
		return scope switch
		{
			GarmentProjectionScope.AllFacings => true, 
			GarmentProjectionScope.FrontOnly => facing == GarmentArtFacing.Front, 
			_ => false, 
		};
	}
}
