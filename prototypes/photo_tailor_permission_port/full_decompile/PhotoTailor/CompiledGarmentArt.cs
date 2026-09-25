using System;
using System.Collections.Generic;
using System.Linq;

namespace PhotoTailor;

internal sealed class CompiledGarmentArt
{
	private readonly IReadOnlyList<GarmentColorBand> bands;

	public string Pattern { get; }

	public GarmentArtRgb BaseColor { get; }

	public IReadOnlyList<GarmentArtRgb> ShadeRamp { get; }

	public IReadOnlyList<GarmentColorBand> BaseBands { get; }

	public IReadOnlyList<double> TrustedTierRows { get; }

	public IReadOnlyList<GarmentMotifStamp> MotifStamps { get; }

	public int RetainedEvidencePixels { get; }

	public int RejectedIsolatedPixels { get; }

	public CanonicalGarmentCanvas CanonicalCanvas { get; }

	public double ArtworkTop { get; }

	public double ArtworkBottom { get; }

	public bool HasTrustedStructure
	{
		get
		{
			if (TrustedTierRows.Count <= 0 && MotifStamps.Count <= 0)
			{
				return BaseBands.Count > 1;
			}
			return true;
		}
	}

	internal CompiledGarmentArt(string pattern, GarmentArtRgb baseColor, IReadOnlyList<GarmentArtRgb> shadeRamp, IReadOnlyList<GarmentColorBand> baseBands, IReadOnlyList<double> trustedTierRows, IReadOnlyList<GarmentMotifStamp> motifStamps, int retainedEvidencePixels, int rejectedIsolatedPixels, CanonicalGarmentCanvas canonicalCanvas, double artworkTop, double artworkBottom)
	{
		Pattern = pattern;
		BaseColor = baseColor;
		ShadeRamp = shadeRamp;
		bands = baseBands;
		BaseBands = baseBands;
		TrustedTierRows = trustedTierRows;
		MotifStamps = motifStamps;
		RetainedEvidencePixels = retainedEvidencePixels;
		RejectedIsolatedPixels = rejectedIsolatedPixels;
		CanonicalCanvas = canonicalCanvas;
		ArtworkTop = artworkTop;
		ArtworkBottom = artworkBottom;
	}

	public GarmentArtRgb SampleBase(double u, double v, int shadeStep = 0)
	{
		double y = Math.Clamp(v, 0.0, 1.0);
		return GarmentArtCompiler.Shade(bands.FirstOrDefault((GarmentColorBand band) => y >= band.Top && y <= band.Bottom)?.Color ?? BaseColor, shadeStep);
	}

	public IReadOnlyList<GarmentMotifStamp> MotifsFor(GarmentArtFacing facing)
	{
		return MotifStamps.Where((GarmentMotifStamp stamp) => stamp.Facing == facing).ToList();
	}

	public GarmentArtRgb SampleProjection(GarmentArtFacing facing, double u, double v, double footprintU = 0.0, double footprintV = 0.0)
	{
		return CanonicalCanvas.SampleProjection(facing, ArtworkTop, ArtworkBottom, u, v, SampleBase(u, ArtworkTop + v * Math.Max(0.001, ArtworkBottom - ArtworkTop)), footprintU, footprintV);
	}

	internal CompiledGarmentArt WithArtworkRange(double artworkTop, double artworkBottom)
	{
		return new CompiledGarmentArt(Pattern, BaseColor, ShadeRamp, BaseBands, TrustedTierRows, MotifStamps, RetainedEvidencePixels, RejectedIsolatedPixels, CanonicalCanvas, Math.Clamp(artworkTop, 0.0, 0.999), Math.Clamp(artworkBottom, Math.Clamp(artworkTop, 0.0, 0.999) + 0.001, 1.0));
	}
}
