using System;
using System.Collections.Generic;

namespace PhotoTailor;

internal static class RecognitionPreviewLayoutEngine
{
	private const int MinimumUsableWidth = 620;

	private const int MinimumUsableHeight = 460;

	internal static RecognitionPreviewLayoutPlan Calculate(int width, int height, int itemCount)
	{
		if (width <= 0)
		{
			throw new ArgumentOutOfRangeException("width");
		}
		if (height <= 0)
		{
			throw new ArgumentOutOfRangeException("height");
		}
		if (itemCount < 0)
		{
			throw new ArgumentOutOfRangeException("itemCount");
		}
		PreviewLayoutRect viewport = new PreviewLayoutRect(0, 0, width, height);
		if (width < 620 || height < 460)
		{
			return BuildConstrained(viewport);
		}
		int num = Math.Clamp(width / 50, 12, 30);
		int gap = Math.Clamp(width / 85, 10, 20);
		int num2 = Math.Clamp(height / 14, 44, 56);
		int buttonY = height - num - num2;
		if (width < 1180 || height < 640)
		{
			return BuildStacked(viewport, num, gap, buttonY, num2, itemCount);
		}
		return BuildWide(viewport, num, gap, buttonY, num2, itemCount);
	}

	private static RecognitionPreviewLayoutPlan BuildWide(PreviewLayoutRect viewport, int margin, int gap, int buttonY, int buttonHeight, int itemCount)
	{
		int width = Math.Clamp((int)Math.Round((double)(viewport.Width - margin * 2) * 0.5), 390, 760);
		PreviewLayoutRect photoPanel = new PreviewLayoutRect(margin, margin, width, buttonY - gap - margin);
		PreviewLayoutRect outputPanel = new PreviewLayoutRect(photoPanel.Right + gap, margin, viewport.Width - margin - photoPanel.Right - gap, buttonY - gap - margin);
		PreviewLayoutRect previewLayoutRect = outputPanel.Inset(16, 56, 16, 34);
		var (outputCells, outputVisibleCapacity) = BuildOutputCells(previewLayoutRect, itemCount, 10);
		var (cancelButton, adjustButton, confirmButton) = BuildButtons(outputPanel.X, outputPanel.Width, buttonY, buttonHeight, 8);
		return new RecognitionPreviewLayoutPlan
		{
			Mode = RecognitionPreviewLayoutMode.Wide,
			Viewport = viewport,
			PhotoPanel = photoPanel,
			PhotoViewport = photoPanel.Inset(16, 56, 16, 16),
			OutputPanel = outputPanel,
			OutputViewport = previewLayoutRect,
			OutputCells = outputCells,
			OutputVisibleCapacity = outputVisibleCapacity,
			CancelButton = cancelButton,
			AdjustButton = adjustButton,
			ConfirmButton = confirmButton
		};
	}

	private static RecognitionPreviewLayoutPlan BuildStacked(PreviewLayoutRect viewport, int margin, int gap, int buttonY, int buttonHeight, int itemCount)
	{
		int width = viewport.Width - margin * 2;
		int height = Math.Clamp((int)Math.Round((double)(buttonY - gap - margin) * 0.48), 180, 330);
		PreviewLayoutRect photoPanel = new PreviewLayoutRect(margin, margin, width, height);
		PreviewLayoutRect outputPanel = new PreviewLayoutRect(margin, photoPanel.Bottom + gap, width, buttonY - gap - (photoPanel.Bottom + gap));
		PreviewLayoutRect previewLayoutRect = outputPanel.Inset(12, 44, 12, 24);
		var (outputCells, outputVisibleCapacity) = BuildOutputCells(previewLayoutRect, itemCount, 8);
		var (cancelButton, adjustButton, confirmButton) = BuildButtons(margin, width, buttonY, buttonHeight, 8);
		return new RecognitionPreviewLayoutPlan
		{
			Mode = RecognitionPreviewLayoutMode.Stacked,
			Viewport = viewport,
			PhotoPanel = photoPanel,
			PhotoViewport = photoPanel.Inset(12, 45, 12, 10),
			OutputPanel = outputPanel,
			OutputViewport = previewLayoutRect,
			OutputCells = outputCells,
			OutputVisibleCapacity = outputVisibleCapacity,
			CancelButton = cancelButton,
			AdjustButton = adjustButton,
			ConfirmButton = confirmButton
		};
	}

	private static RecognitionPreviewLayoutPlan BuildConstrained(PreviewLayoutRect viewport)
	{
		int num = 8;
		int num2 = 6;
		int num3 = Math.Min(42, Math.Max(30, viewport.Height / 8));
		int num4 = Math.Max(num, viewport.Height - num - num3);
		int width = Math.Max(1, viewport.Width - num * 2);
		var (cancelButton, adjustButton, confirmButton) = BuildButtons(num, width, num4, num3, num2);
		return new RecognitionPreviewLayoutPlan
		{
			Mode = RecognitionPreviewLayoutMode.Constrained,
			Viewport = viewport,
			ConstrainedMessage = new PreviewLayoutRect(num, num, width, Math.Max(1, num4 - num2 - num)),
			CancelButton = cancelButton,
			AdjustButton = adjustButton,
			ConfirmButton = confirmButton
		};
	}

	private static (IReadOnlyList<PreviewLayoutRect> Cells, int Capacity) BuildOutputCells(PreviewLayoutRect viewport, int itemCount, int gap)
	{
		if (viewport.IsEmpty)
		{
			return (Cells: Array.Empty<PreviewLayoutRect>(), Capacity: 0);
		}
		int num = Math.Max(1, (viewport.Width + gap) / (220 + gap));
		int num2 = Math.Max(1, (viewport.Height + gap) / (210 + gap));
		int num3 = Math.Max(1, num * num2);
		int num4 = Math.Max(1, (viewport.Width - gap * (num - 1)) / num);
		int num5 = Math.Max(1, Math.Min(210, (viewport.Height - gap * (num2 - 1)) / num2));
		int num6 = Math.Min(itemCount, num3);
		List<PreviewLayoutRect> list = new List<PreviewLayoutRect>(num6);
		for (int i = 0; i < num6; i++)
		{
			int num7 = i / num;
			int num8 = i % num;
			int num9 = num7 * num;
			int num10 = Math.Min(num, num6 - num9);
			int num11 = num10 * num4 + Math.Max(0, num10 - 1) * gap;
			int num12 = viewport.X + Math.Max(0, (viewport.Width - num11) / 2);
			list.Add(new PreviewLayoutRect(num12 + num8 * (num4 + gap), viewport.Y + num7 * (num5 + gap), num4, num5));
		}
		return (Cells: list, Capacity: num3);
	}

	private static (PreviewLayoutRect Cancel, PreviewLayoutRect Adjust, PreviewLayoutRect Confirm) BuildButtons(int x, int width, int y, int height, int gap)
	{
		int num = Math.Max(3, width - gap * 2);
		int num2 = num / 3;
		int num3 = num / 3;
		int width2 = num - num2 - num3;
		PreviewLayoutRect item = new PreviewLayoutRect(x, y, num2, height);
		PreviewLayoutRect item2 = new PreviewLayoutRect(item.Right + gap, y, num3, height);
		return new ValueTuple<PreviewLayoutRect, PreviewLayoutRect, PreviewLayoutRect>(item3: new PreviewLayoutRect(item2.Right + gap, y, width2, height), item1: item, item2: item2);
	}
}
