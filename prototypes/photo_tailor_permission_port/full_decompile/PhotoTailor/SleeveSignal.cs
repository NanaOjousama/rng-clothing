using System.Collections.Generic;

namespace PhotoTailor;

internal sealed record SleeveSignal(List<string> Palette, List<int> PatternMap, int PatternWidth, int PatternHeight)
{
	public static SleeveSignal Empty { get; } = new SleeveSignal(new List<string>(), new List<int>(), 0, 0);
}
