using System;
using System.Text.Json.Serialization;

namespace PhotoTailor;

internal sealed class GeneratedGarment
{
	public int RendererVersion { get; set; }

	public string Id { get; set; } = "";

	public string Category { get; set; } = "";

	public string Name { get; set; } = "";

	public string Description { get; set; } = "";

	public string TextureAsset { get; set; } = "";

	public string TexturePath { get; set; } = "";

	public string? LogicalGarmentId { get; set; }

	public string? ArtworkPath { get; set; }

	public int ArtworkWidth { get; set; }

	public int ArtworkHeight { get; set; }

	public string? PaletteAsset { get; set; }

	public string? PalettePath { get; set; }

	public bool HasSleeves { get; set; } = true;

	[JsonIgnore]
	public string QualifiedItemId => Category switch
	{
		"shirt" => "(S)" + Id, 
		"pants" => "(P)" + Id, 
		"hat" => "(H)" + Id, 
		"boots" => "(B)" + Id, 
		_ => throw new InvalidOperationException("Unsupported category: " + Category), 
	};
}
