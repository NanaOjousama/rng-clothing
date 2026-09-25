namespace PhotoTailor;

internal readonly record struct GarmentArtRgb(byte R, byte G, byte B)
{
	public double Luma => ((double)(int)R * 0.2126 + (double)(int)G * 0.7152 + (double)(int)B * 0.0722) / 255.0;

	public string ToHex()
	{
		return $"#{R:X2}{G:X2}{B:X2}";
	}
}
