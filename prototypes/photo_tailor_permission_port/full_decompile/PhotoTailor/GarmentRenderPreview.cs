using System;
using Microsoft.Xna.Framework;

namespace PhotoTailor;

internal sealed class GarmentRenderPreview
{
	public int ItemIndex { get; }

	public int TemplateIndex { get; }

	public string Category { get; }

	public string Name { get; }

	public string Silhouette { get; }

	public string LogicalGarmentId { get; }

	public string RenderRole { get; }

	public int Width { get; }

	public int Height { get; }

	public Color[] Pixels { get; }

	public bool HasSleeves { get; }

	public int PaletteWidth { get; }

	public int PaletteHeight { get; }

	public Color[] PalettePixels { get; }

	public int ArtworkWidth { get; }

	public int ArtworkHeight { get; }

	public Color[] ArtworkPixels { get; }

	public bool HasPalette => PalettePixels.Length != 0;

	public bool HasArtwork => ArtworkPixels.Length != 0;

	public GarmentRenderPreview(int itemIndex, int templateIndex, GarmentSpec spec, int width, int height, Color[] pixels, bool hasSleeves = true, int paletteWidth = 0, int paletteHeight = 0, Color[]? palettePixels = null, int artworkWidth = 0, int artworkHeight = 0, Color[]? artworkPixels = null)
	{
		ArgumentNullException.ThrowIfNull(spec, "spec");
		ArgumentNullException.ThrowIfNull(pixels, "pixels");
		if (itemIndex < 0)
		{
			throw new ArgumentOutOfRangeException("itemIndex");
		}
		if (width <= 0 || height <= 0 || pixels.Length != width * height)
		{
			throw new ArgumentException("Pixel data doesn't match the declared texture size.", "pixels");
		}
		Color[] array = palettePixels ?? Array.Empty<Color>();
		if (array.Length != 0 && (paletteWidth <= 0 || paletteHeight <= 0 || array.Length != paletteWidth * paletteHeight))
		{
			throw new ArgumentException("Palette data doesn't match the declared palette texture size.", "palettePixels");
		}
		Color[] array2 = artworkPixels ?? Array.Empty<Color>();
		if (array2.Length != 0 && (artworkWidth <= 0 || artworkHeight <= 0 || array2.Length != artworkWidth * artworkHeight))
		{
			throw new ArgumentException("Artwork data doesn't match the declared canonical canvas size.", "artworkPixels");
		}
		ItemIndex = itemIndex;
		TemplateIndex = templateIndex;
		Category = spec.Category;
		Name = spec.Name;
		Silhouette = spec.Silhouette;
		LogicalGarmentId = spec.LogicalGarmentId;
		RenderRole = spec.RenderRole;
		Width = width;
		Height = height;
		Pixels = pixels;
		HasSleeves = hasSleeves;
		PaletteWidth = ((array.Length != 0) ? paletteWidth : 0);
		PaletteHeight = ((array.Length != 0) ? paletteHeight : 0);
		PalettePixels = array;
		ArtworkWidth = ((array2.Length != 0) ? artworkWidth : 0);
		ArtworkHeight = ((array2.Length != 0) ? artworkHeight : 0);
		ArtworkPixels = array2;
	}
}
