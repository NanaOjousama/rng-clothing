using System;
using Microsoft.Xna.Framework;

namespace RNGClothingFitting
{
    /// <summary>Every rectangle the fitting screen uses, in one place.
    ///
    /// Drawing and hit-testing both read from here, so they cannot drift apart.
    /// That is not a theoretical concern: an earlier version of this menu placed
    /// the "Adjust Fit" button by one expression and hit-tested it by another,
    /// and the two disagreed off-screen.
    ///
    /// Rectangles are computed on demand from the menu's origin rather than
    /// cached, so a resize or a UI-scale change cannot leave a stale bound
    /// behind.
    ///
    /// This type also owns the ONLY conversion between screen pixels and motif
    /// cells (<see cref="ScreenToCell"/> / <see cref="CellToScreen"/>). No
    /// coordinate arithmetic belongs anywhere else.
    /// </summary>
    internal sealed class FittingGeometry
    {
        public const int Width = 900;
        public const int Height = 660;

        private const int Pad = 32;
        private const int RowH = 32;

        public int X { get; }
        public int Y { get; }

        /// <summary>Sprite cells across one garment frame (20 for Cap 2).</summary>
        public int FrameSize { get; }

        /// <summary>Screen pixels per sprite cell on the motif grid. Set from
        /// the readability scale so the grid and the preview agree.</summary>
        public int CellSize { get; private set; } = 8;

        /// <summary>Which sprite cells the grid shows, in cell coordinates.
        ///
        /// The whole 20x20 frame does not fit: at 4x that is 320px square, and
        /// it overflowed the panel and covered the action buttons. It is also
        /// not what the player needs -- the design lives on the front crown, so
        /// the grid windows onto the crown and the peak below it and leaves the
        /// rest of the sprite to the farmer preview.
        ///
        /// The window is part of the coordinate contract: ScreenToCell and
        /// CellToScreen both translate through it, so a cell outside the window
        /// has no screen position and vice versa.</summary>
        public Rectangle CellWindow { get; private set; }

        public FittingGeometry(int x, int y, int frameSize)
        {
            this.X = x;
            this.Y = y;
            this.FrameSize = Math.Max(1, frameSize);
            this.CellWindow = new Rectangle(0, 0, this.FrameSize, this.FrameSize);
        }

        /// <summary>Window the grid onto part of the frame.
        ///
        /// Clamped to the frame, so a caller cannot ask for cells that do not
        /// exist.</summary>
        public void SetCellWindow(Rectangle cells)
        {
            int x = Math.Clamp(cells.X, 0, this.FrameSize - 1);
            int y = Math.Clamp(cells.Y, 0, this.FrameSize - 1);
            int w = Math.Clamp(cells.Width, 1, this.FrameSize - x);
            int h = Math.Clamp(cells.Height, 1, this.FrameSize - y);
            this.CellWindow = new Rectangle(x, y, w, h);
        }

        /// <summary>A window around the authored mask, with a little context.
        ///
        /// Derived from the mask so it follows the authored surface instead of
        /// assuming where the crown is.</summary>
        public static Rectangle WindowAroundMask(CapSidecar cap, int margin = 1)
        {
            if (cap == null || cap.SafeCells.Count == 0)
                return new Rectangle(0, 0, 20, 20);
            int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue;
            foreach (var c in cap.SafeCells)
            {
                if (c.X < minX) minX = c.X;
                if (c.X > maxX) maxX = c.X;
                if (c.Y < minY) minY = c.Y;
                if (c.Y > maxY) maxY = c.Y;
            }
            // Extra rows below, so the visor the mask must not touch is visible.
            return new Rectangle(minX - margin, minY - margin,
                                 (maxX - minX + 1) + margin * 2,
                                 (maxY - minY + 1) + margin * 2 + 1);
        }

        public void SetCellSize(int px) => this.CellSize = Math.Max(1, px);

        // --- panels ---------------------------------------------------------

        public Rectangle Bounds => new(this.X, this.Y, Width, Height);

        private int ActionY => this.Y + Height - 40 - 72;

        public Rectangle Title => new(this.X + Pad * 2, this.Y + Pad, 520, 40);
        public Rectangle Subtitle => new(this.X + Pad * 2, this.Y + Pad + 44, 520, 28);

        /// <summary>The worn farmer. Gameplay scale is the authority, so this
        /// is always on screen and never collapsed behind a toggle.</summary>
        public Rectangle FarmerPreview => new(this.X + Pad * 2, this.Y + 120, 288, 300);

        public Rectangle Panel => new(this.X + 400, this.Y + 116, Width - 400 - Pad * 2, 300);

        public Rectangle HatTab => new(this.Panel.X, this.Panel.Y, 200, 68);
        public Rectangle MotifTab => new(this.Panel.X + 216, this.Panel.Y, 200, 68);

        public Rectangle OffsetReadout => new(this.Panel.X, this.Panel.Y + 88, this.Panel.Width, 40);
        public Rectangle Note => new(this.Panel.X, this.Panel.Y + 136, this.Panel.Width, 64);

        /// <summary>The four nudge arrows, as real focusable buttons so d-pad
        /// snapping and a mouse both reach them. The left stick also nudges,
        /// but nothing depends on the stick alone.</summary>
        public Rectangle NudgePad => new(this.Panel.X, this.Panel.Y + 204, 192, 192);

        public Rectangle NudgeUp => this.PadCell(1, 0);
        public Rectangle NudgeDown => this.PadCell(1, 2);
        public Rectangle NudgeLeft => this.PadCell(0, 1);
        public Rectangle NudgeRight => this.PadCell(2, 1);

        private Rectangle PadCell(int cx, int cy)
        {
            Rectangle p = this.NudgePad;
            int s = p.Width / 3;
            return new Rectangle(p.X + cx * s, p.Y + cy * s, s, s);
        }

        // --- readability strip ---------------------------------------------

        /// <summary>1x / 2x / 4x buttons. The sprite is judged at the size it
        /// will actually be seen, rather than only zoomed in.</summary>
        public Rectangle ReadabilityRow => new(this.Panel.X + 224, this.Panel.Y + 204, 240, 56);

        public Rectangle ReadabilityButton(int index) =>
            new(this.ReadabilityRow.X + index * 80, this.ReadabilityRow.Y, 72, 56);

        /// <summary>Where the windowed frame is drawn at the chosen scale.
        /// The grid is clamped to fit inside this, so no zoom can overflow it.</summary>
        public Rectangle ReadabilityPreview
        {
            get
            {
                int top = this.Panel.Y + 268;
                // Stop clear of the action bar. Deriving the height instead of
                // hardcoding it is what stops the panel growing into the
                // buttons when the menu is resized.
                int bottom = this.ActionY - 16;
                return new Rectangle(this.Panel.X + 224, top, 232, Math.Max(48, bottom - top));
            }
        }

        // --- motif grid (read-only today; the future editor's surface) ------

        /// <summary>The zoomed sprite grid. Read-only for now: it shows the
        /// crown, the safe mask and where the design sits. The future masked
        /// editor draws its cursor into this same rectangle, through the same
        /// two conversion methods, so the mapping is proven before it is
        /// depended on.</summary>
        public Rectangle MotifGrid
        {
            get
            {
                Rectangle r = this.ReadabilityPreview;
                return new Rectangle(r.X, r.Y,
                                     this.CellSize * this.CellWindow.Width,
                                     this.CellSize * this.CellWindow.Height);
            }
        }

        /// <summary>The largest cell size that keeps the grid inside its panel.
        ///
        /// The readability buttons ask for 1x / 2x / 4x; this is what stops a
        /// request the panel cannot hold from drawing over the action buttons.
        /// The menu reports the scale it actually got, so the label never claims
        /// a zoom that was not honoured.</summary>
        public int MaxCellSize(int availableWidth, int availableHeight)
        {
            int byW = availableWidth / Math.Max(1, this.CellWindow.Width);
            int byH = availableHeight / Math.Max(1, this.CellWindow.Height);
            return Math.Max(1, Math.Min(byW, byH));
        }

        /// <summary>Screen pixel to sprite cell. Null when outside the grid.
        ///
        /// The single authoritative mapping in one direction.</summary>
        public Point? ScreenToCell(int screenX, int screenY)
        {
            Rectangle g = this.MotifGrid;
            if (!g.Contains(screenX, screenY))
                return null;
            int cx = (screenX - g.X) / this.CellSize;
            int cy = (screenY - g.Y) / this.CellSize;
            if (cx < 0 || cy < 0
                || cx >= this.CellWindow.Width || cy >= this.CellWindow.Height)
                return null;                       // guards the bottom/right edge
            return new Point(this.CellWindow.X + cx, this.CellWindow.Y + cy);
        }

        /// <summary>Sprite cell to the screen rectangle it occupies.
        ///
        /// The exact inverse of <see cref="ScreenToCell"/>: every pixel of the
        /// returned rectangle maps back to the cell that produced it.</summary>
        public Rectangle CellToScreen(Point cell)
        {
            Rectangle g = this.MotifGrid;
            return new Rectangle(g.X + (cell.X - this.CellWindow.X) * this.CellSize,
                                 g.Y + (cell.Y - this.CellWindow.Y) * this.CellSize,
                                 this.CellSize, this.CellSize);
        }

        /// <summary>Is this cell shown by the grid at all?</summary>
        public bool CellVisible(Point cell) => this.CellWindow.Contains(cell);

        // --- action bar -----------------------------------------------------



        public Rectangle TurnButton => new(this.X + Pad * 2, this.ActionY, 150, 64);
        public Rectangle UndoButton => new(this.X + 224, this.ActionY, 110, 64);
        public Rectangle RedoButton => new(this.X + 342, this.ActionY, 110, 64);
        public Rectangle ResetButton => new(this.X + 460, this.ActionY, 130, 64);

        public Rectangle CancelButton => new(this.X + 608, this.ActionY, 110, 64);
        public Rectangle SaveButton => new(this.X + 736, this.ActionY, 100, 64);

        public Rectangle Toast => new(this.X, this.Y + Height - 118, Width, RowH);
    }
}
