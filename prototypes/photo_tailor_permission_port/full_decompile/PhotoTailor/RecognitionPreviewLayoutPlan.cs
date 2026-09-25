using System;
using System.Collections.Generic;

namespace PhotoTailor;

internal sealed class RecognitionPreviewLayoutPlan
{
	internal RecognitionPreviewLayoutMode Mode { get; init; }

	internal bool IsUsable => Mode != RecognitionPreviewLayoutMode.Constrained;

	internal PreviewLayoutRect Viewport { get; init; }

	internal PreviewLayoutRect PhotoPanel { get; init; }

	internal PreviewLayoutRect PhotoViewport { get; init; }

	internal PreviewLayoutRect OutputPanel { get; init; }

	internal PreviewLayoutRect OutputViewport { get; init; }

	internal IReadOnlyList<PreviewLayoutRect> OutputCells { get; init; } = Array.Empty<PreviewLayoutRect>();

	internal int OutputVisibleCapacity { get; init; }

	internal PreviewLayoutRect CancelButton { get; init; }

	internal PreviewLayoutRect AdjustButton { get; init; }

	internal PreviewLayoutRect ConfirmButton { get; init; }

	internal PreviewLayoutRect ConstrainedMessage { get; init; }
}
