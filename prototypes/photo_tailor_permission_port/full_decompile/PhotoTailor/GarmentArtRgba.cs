namespace PhotoTailor;

internal readonly record struct GarmentArtRgba(byte R, byte G, byte B, byte A)
{
	internal GarmentArtRgb Rgb => new GarmentArtRgb(R, G, B);

	internal static readonly GarmentArtRgba Transparent = new GarmentArtRgba(0, 0, 0, 0);
}
