using System.Collections.Generic;
using Microsoft.Xna.Framework;

namespace RNGClothingFitting
{
    internal enum SymmetryMode { Off, Vertical }

    /// <summary>Mirroring for cell edits, as a wrapper rather than a mode.
    ///
    /// The shape borrowed from Cheerful Pixels is that an edit is applied once
    /// per mirrored position by a wrapper around the single-cell operation,
    /// instead of every tool learning about symmetry. Vertical is the only mode
    /// offered because it is the only one a cap logo wants: a centred mark on
    /// the front crown.
    ///
    /// THE MASK STILL WINS. A mirrored cell that falls outside the safe mask is
    /// dropped, never forced — mirroring must not become a way to paint on the
    /// visor. That means an asymmetric mask legitimately produces a partial
    /// mirror, which is correct: the alternative is drawing outside the legal
    /// surface.
    ///
    /// Nothing calls this yet; no pixel editing exists. It is implemented and
    /// tested now so the masked editor can adopt it without inventing the rule
    /// at that point.
    /// </summary>
    internal static class Symmetry
    {
        /// <summary>The mask's vertical axis of reflection, doubled to stay in
        /// integers. Derived from the mask itself, not hardcoded, so it follows
        /// the authored surface rather than assuming the sprite's centre.</summary>
        public static int MirrorAxisX2(CapSidecar cap)
        {
            if (cap == null || cap.SafeCells.Count == 0)
                return 0;
            int min = int.MaxValue, max = int.MinValue;
            foreach (var c in cap.SafeCells)
            {
                if (c.X < min) min = c.X;
                if (c.X > max) max = c.X;
            }
            return min + max;                  // mirror of x is (min+max) - x
        }

        public static Point Mirror(CapSidecar cap, Point cell)
            => new(MirrorAxisX2(cap) - cell.X, cell.Y);

        /// <summary>Every cell one edit should touch, mirrored and filtered.
        ///
        /// Always includes the original cell (when legal), plus its reflection
        /// when symmetry is on AND that reflection is inside the mask. Cells are
        /// de-duplicated, so a cell sitting on the axis is returned once.</summary>
        public static List<Point> Targets(CapSidecar cap, Point cell, SymmetryMode mode)
        {
            var result = new List<Point>(2);
            if (cap == null)
                return result;
            if (cap.SafeCells.Contains(cell))
                result.Add(cell);
            if (mode == SymmetryMode.Vertical)
            {
                Point m = Mirror(cap, cell);
                if (m != cell && cap.SafeCells.Contains(m))
                    result.Add(m);
            }
            return result;
        }
    }
}
