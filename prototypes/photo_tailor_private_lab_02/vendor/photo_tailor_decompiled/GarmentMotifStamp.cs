using System;
using System.Collections.Generic;

namespace PhotoTailor;

internal sealed class GarmentMotifStamp
{
	public GarmentArtFacing Facing { get; init; }

	public double X { get; init; }

	public double Y { get; init; }

	public double Opacity { get; init; } = 1.0;

	public IReadOnlyList<GarmentMotifPixel> Pixels { get; init; } = Array.Empty<GarmentMotifPixel>();
}
