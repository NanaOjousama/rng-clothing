using System.Collections.Generic;

namespace PhotoTailor;

internal sealed class OutfitRenderPreview
{
	public string OutfitName { get; }

	public IReadOnlyList<GarmentRenderPreview> Items { get; }

	public OutfitRenderPreview(string outfitName, IReadOnlyList<GarmentRenderPreview> items)
	{
		OutfitName = outfitName;
		Items = items;
	}
}
