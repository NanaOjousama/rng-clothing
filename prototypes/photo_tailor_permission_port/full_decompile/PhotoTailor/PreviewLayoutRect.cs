using System;

namespace PhotoTailor;

internal readonly record struct PreviewLayoutRect(int X, int Y, int Width, int Height)
{
	internal int Right => X + Width;

	internal int Bottom => Y + Height;

	internal bool IsEmpty
	{
		get
		{
			if (Width > 0)
			{
				return Height <= 0;
			}
			return true;
		}
	}

	internal bool Contains(PreviewLayoutRect child)
	{
		if (child.X >= X && child.Y >= Y && child.Right <= Right)
		{
			return child.Bottom <= Bottom;
		}
		return false;
	}

	internal bool Overlaps(PreviewLayoutRect other)
	{
		if (!IsEmpty && !other.IsEmpty && X < other.Right && Right > other.X && Y < other.Bottom)
		{
			return Bottom > other.Y;
		}
		return false;
	}

	internal PreviewLayoutRect Inset(int left, int top, int right, int bottom)
	{
		return new PreviewLayoutRect(X + left, Y + top, Math.Max(0, Width - left - right), Math.Max(0, Height - top - bottom));
	}
}
