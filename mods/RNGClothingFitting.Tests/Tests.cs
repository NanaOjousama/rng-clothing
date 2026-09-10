using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Xna.Framework;

namespace RNGClothingFitting.Tests
{
    /// <summary>Headless checks over the fitting mod's pure logic.
    ///
    /// These run against the REAL generated sidecar from the installed Cap 2
    /// pack, not a hand-written fixture, so a change to the generator that
    /// breaks the mod's assumptions fails here rather than in game.
    /// </summary>
    internal static class Program
    {
        private static int passed, failed;

        private static void Check(string name, bool ok, string detail = "")
        {
            if (ok) { passed++; Console.WriteLine($"  ok   {name}"); }
            else { failed++; Console.WriteLine($"  FAIL {name}   {detail}"); }
        }

        private static void Eq<T>(string name, T expected, T actual) =>
            Check(name, EqualityComparer<T>.Default.Equals(expected, actual),
                  $"expected {expected}, got {actual}");

        private static int Main()
        {
            string root = Path.GetFullPath(Path.Combine(
                AppContext.BaseDirectory, "../../../../.."));
            string packDir = Path.Combine(root, "test-packs/fashionsense/RNG-Cap2Fit/Hats");
            if (!Directory.Exists(packDir))
            {
                Console.WriteLine($"cannot find the generated pack at {packDir}");
                return 2;
            }

            var caps = Directory.GetDirectories(packDir)
                .Select(d => Path.Combine(d, "fitting.json"))
                .Where(File.Exists)
                .Select(CapSidecar.Load)
                .Where(c => c != null)
                .OrderBy(c => c.ItemId)
                .ToList();
            Console.WriteLine($"loaded {caps.Count} generated cap sidecar(s)\n");

            CapSidecar movable = caps.First(c => c.HasMotif && FitRules.LegalPositionCount(c) > 1);
            CapSidecar fixedMotif = caps.FirstOrDefault(c => c.HasMotif && FitRules.LegalPositionCount(c) == 1);
            CapSidecar plain = caps.First(c => !c.HasMotif);

            Console.WriteLine("SIDECAR");
            Check("every cap parsed", caps.Count >= 4);
            Check("a movable design exists", movable != null);
            Check("an immovable design exists", fixedMotif != null);
            Check("a plain cap exists", plain != null);
            Check("base pixels cover the safe mask",
                  movable.SafeCells.All(c => movable.BasePixels.ContainsKey(c)));
            Check("motif cells start inside the mask",
                  movable.MotifCells.All(c => movable.SafeCells.Contains(c)));

            Console.WriteLine("\nHEAD POSITION (integer-only, inverted once)");
            var fit = new Fit { ItemId = "x" };
            Eq("default is the authored value", new Point(3, -2),
               fit.HeadPosition(new Point(3, -2)));
            fit.HatRight = 1;
            Eq("move right writes X-1", new Point(-1, 0), fit.HeadPosition(Point.Zero));
            fit.HatRight = 0; fit.HatDown = 1;
            Eq("move down writes Y-1", new Point(0, -1), fit.HeadPosition(Point.Zero));
            fit.HatDown = 0;

            Console.WriteLine("\nHAT BOUNDS (refused, never clamped)");
            var f2 = new Fit { ItemId = "x" };
            bool allOk = true;
            for (int i = 0; i < movable.HatRange; i++)
                allOk &= FitRules.TryMoveHat(f2, movable, 1, 0) == MoveResult.Ok;
            Check($"{movable.HatRange} steps right all allowed", allOk);
            Eq("at the range limit", movable.HatRange, f2.HatRight);
            Eq("one more is refused", MoveResult.OutOfRange,
               FitRules.TryMoveHat(f2, movable, 1, 0));
            Eq("and the value did not creep", movable.HatRange, f2.HatRight);

            Console.WriteLine("\nMOTIF MASK (blocked whole, never clipped)");
            var f3 = new Fit { ItemId = "x" };
            Eq("plain cap reports no design", MoveResult.NoMotif,
               FitRules.TryMoveMotif(f3, plain, 1, 0));
            if (fixedMotif != null)
            {
                var f4 = new Fit { ItemId = "x" };
                bool everyMoveRefused = true;
                foreach (var (dx, dy) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
                    everyMoveRefused &= FitRules.TryMoveMotif(f4, fixedMotif, dx, dy)
                                        == MoveResult.OutsideMask;
                Check("an immovable design refuses every direction", everyMoveRefused);
                Check("and its offset is untouched", f4.MotifRight == 0 && f4.MotifDown == 0);
            }
            var f5 = new Fit { ItemId = "x" };
            int legal = 0;
            foreach (var (dx, dy) in new[] { (1, 0), (-1, 0), (0, 1), (0, -1) })
            {
                var probe = new Fit { ItemId = "x" };
                if (FitRules.TryMoveMotif(probe, movable, dx, dy) == MoveResult.Ok)
                    legal++;
            }
            Check("a movable design accepts at least one direction", legal >= 1);
            // no partial application: a refused move leaves every cell alone
            var f6 = new Fit { ItemId = "x", MotifRight = 0, MotifDown = 0 };
            while (FitRules.TryMoveMotif(f6, movable, 1, 0) == MoveResult.Ok) { }
            var placed = FitRules.PlacedMotif(f6, movable).ToList();
            Check("after exhausting travel every cell is still legal",
                  placed.All(c => movable.SafeCells.Contains(c)));
            Eq("cell count is unchanged", movable.MotifCells.Count, placed.Count);

            Console.WriteLine("\nGEOMETRY: screen <-> cell must be exact inverses");
            var geo = new FittingGeometry(100, 50, movable.FrameSize);
            geo.SetCellWindow(FittingGeometry.WindowAroundMask(movable));
            Rectangle win = geo.CellWindow;
            Check("the window covers the whole mask",
                  movable.SafeCells.All(c => win.Contains(c)));
            Check("the window shows the visor row below the mask",
                  win.Bottom > movable.SafeCells.Max(c => c.Y) + 1);
            Check("the window stays inside the frame",
                  win.X >= 0 && win.Y >= 0
                  && win.Right <= movable.FrameSize && win.Bottom <= movable.FrameSize);

            foreach (int scale in new[] { 1, 2, 4 })
            {
                Rectangle room = geo.ReadabilityPreview;
                geo.SetCellSize(Math.Min(scale * 4, geo.MaxCellSize(room.Width, room.Height)));
                bool roundTrip = true, everyPixel = true;
                for (int cy = win.Y; cy < win.Bottom; cy++)
                for (int cx = win.X; cx < win.Right; cx++)
                {
                    var cell = new Point(cx, cy);
                    Rectangle r = geo.CellToScreen(cell);
                    roundTrip &= geo.ScreenToCell(r.X, r.Y) == cell
                                 && geo.ScreenToCell(r.Right - 1, r.Bottom - 1) == cell;
                    for (int py = r.Y; py < r.Bottom && everyPixel; py++)
                    for (int px = r.X; px < r.Right && everyPixel; px++)
                        everyPixel &= geo.ScreenToCell(px, py) == cell;
                }
                Check($"cell<->screen round-trips at {scale}x", roundTrip);
                Check($"every pixel of every cell maps back at {scale}x", everyPixel);

                Rectangle g = geo.MotifGrid;
                Check($"outside the grid returns null at {scale}x",
                      geo.ScreenToCell(g.X - 1, g.Y) == null
                      && geo.ScreenToCell(g.X, g.Y - 1) == null
                      && geo.ScreenToCell(g.Right, g.Y) == null
                      && geo.ScreenToCell(g.X, g.Bottom) == null);

                // The bug the player actually hit: at 2x and 4x the grid grew
                // past its panel and drew over the action buttons.
                Check($"the grid stays inside its panel at {scale}x",
                      g.Width <= room.Width && g.Height <= room.Height,
                      $"grid {g.Width}x{g.Height} vs room {room.Width}x{room.Height}");
                Check($"the grid never reaches the action buttons at {scale}x",
                      !g.Intersects(geo.ResetButton) && !g.Intersects(geo.CancelButton)
                      && !g.Intersects(geo.SaveButton) && !g.Intersects(geo.UndoButton)
                      && !g.Intersects(geo.RedoButton));
                Check($"a cell outside the window has no screen place at {scale}x",
                      !geo.CellVisible(new Point(win.X - 1, win.Y))
                      && !geo.CellVisible(new Point(win.X, win.Bottom)));
            }

            Console.WriteLine("\nGEOMETRY: one source of truth for hit-testing");
            var g2 = new FittingGeometry(100, 50, 20);
            Check("nudge arrows do not overlap each other",
                  !g2.NudgeUp.Intersects(g2.NudgeDown) && !g2.NudgeLeft.Intersects(g2.NudgeRight)
                  && !g2.NudgeUp.Intersects(g2.NudgeLeft));
            Check("action buttons do not overlap",
                  !g2.UndoButton.Intersects(g2.RedoButton)
                  && !g2.RedoButton.Intersects(g2.ResetButton)
                  && !g2.ResetButton.Intersects(g2.CancelButton)
                  && !g2.CancelButton.Intersects(g2.SaveButton));
            Check("tabs do not overlap", !g2.HatTab.Intersects(g2.MotifTab));
            Check("readability buttons do not overlap",
                  !g2.ReadabilityButton(0).Intersects(g2.ReadabilityButton(1))
                  && !g2.ReadabilityButton(1).Intersects(g2.ReadabilityButton(2)));
            Check("everything stays inside the menu",
                  new[] { g2.HatTab, g2.MotifTab, g2.NudgePad, g2.ReadabilityRow,
                          g2.TurnButton, g2.UndoButton, g2.RedoButton, g2.ResetButton,
                          g2.CancelButton, g2.SaveButton, g2.FarmerPreview }
                      .All(r => g2.Bounds.Contains(r)));

            Console.WriteLine("\nUNDO / REDO must restore the exact prior state");
            var hist = new FitHistory();
            var live = new Fit { ItemId = "x" };
            Check("nothing to undo initially", !hist.CanUndo && !hist.CanRedo);
            hist.Capture(FitSnapshot.From(live));
            FitRules.TryMoveHat(live, movable, 1, 0);
            hist.Capture(FitSnapshot.From(live));
            FitRules.TryMoveHat(live, movable, 0, 1);
            Check("two steps recorded", hist.Depth == 2);
            var restored = hist.Undo(FitSnapshot.From(live));
            restored.ApplyTo(live);
            Check("undo lands on the previous state", live.HatRight == 1 && live.HatDown == 0,
                  $"got {live.HatRight},{live.HatDown}");
            var again = hist.Undo(FitSnapshot.From(live));
            again.ApplyTo(live);
            Check("undo again reaches the start", live.HatRight == 0 && live.HatDown == 0);
            var fwd = hist.Redo(FitSnapshot.From(live));
            fwd.ApplyTo(live);
            Check("redo returns to 1,0", live.HatRight == 1 && live.HatDown == 0);
            Check("undo of an empty history is null", new FitHistory().Undo(FitSnapshot.From(live)) == null);

            var h2 = new FitHistory();
            var l2 = new Fit { ItemId = "x" };
            h2.Capture(FitSnapshot.From(l2));
            h2.Capture(FitSnapshot.From(l2));
            Eq("an unchanged capture is discarded", 1, h2.Depth);

            var h3 = new FitHistory();
            var l3 = new Fit { ItemId = "x" };
            for (int i = 0; i < FitHistory.MaxDepth + 20; i++)
            {
                l3.HatRight = i % 3;
                l3.HatDown = i % 2;
                h3.Capture(FitSnapshot.From(l3));
            }
            Check($"history is bounded at {FitHistory.MaxDepth}", h3.Depth <= FitHistory.MaxDepth,
                  $"depth {h3.Depth}");

            var h4 = new FitHistory();
            var l4 = new Fit { ItemId = "x" };
            h4.Capture(FitSnapshot.From(l4));
            l4.HatRight = 2;
            h4.Undo(FitSnapshot.From(l4));
            Check("redo is available after an undo", h4.CanRedo);
            h4.Capture(FitSnapshot.From(l4));
            Check("a new edit clears the redo branch", !h4.CanRedo);

            Console.WriteLine("\nSNAPSHOT round-trips every field");
            var snapA = new FitSnapshot { HatRight = 2, HatDown = -1, MotifRight = 1,
                                          MotifDown = 3, ScaleIndex = 0,
                                          PaintedCells = new uint[] { 7, 9 } };
            Check("clone equals its source", snapA.SameAs(snapA.Clone()));
            var snapB = snapA.Clone();
            snapB.PaintedCells[0] = 8;
            Check("clone is deep, not shared", !snapA.SameAs(snapB));

            Console.WriteLine("\nSYMMETRY: mask wins over mirroring");
            int axis2 = Symmetry.MirrorAxisX2(movable);
            Check("mirror axis derived from the mask, not assumed", axis2 > 0);
            foreach (var c in movable.SafeCells)
                Check($"mirror is an involution at {c.X},{c.Y}",
                      Symmetry.Mirror(movable, Symmetry.Mirror(movable, c)) == c);
            var off = Symmetry.Targets(movable, movable.MotifCells[0], SymmetryMode.Off);
            Eq("symmetry off touches one cell", 1, off.Count);
            foreach (var c in movable.SafeCells)
            {
                var t = Symmetry.Targets(movable, c, SymmetryMode.Vertical);
                Check($"every symmetry target is legal at {c.X},{c.Y}",
                      t.All(p => movable.SafeCells.Contains(p)));
                Check($"targets are unique at {c.X},{c.Y}", t.Distinct().Count() == t.Count);
                Check($"at most two targets at {c.X},{c.Y}", t.Count <= 2);
            }
            var outside = new Point(-5, -5);
            Eq("an illegal cell yields no targets", 0,
               Symmetry.Targets(movable, outside, SymmetryMode.Vertical).Count);

            Console.WriteLine("\nSESSION restores view state, never the garment");
            var sessions = new SessionStore();
            var s1 = sessions.For("a");
            s1.Target = FitTarget.Motif;
            s1.ReadabilityIndex = 0;
            s1.Cursor = new Point(9, 6);
            Check("same item returns the same session", ReferenceEquals(s1, sessions.For("a")));
            Check("a different item gets its own", !ReferenceEquals(s1, sessions.For("b")));
            Eq("target survives", FitTarget.Motif, sessions.For("a").Target);
            Eq("readability survives", 0, sessions.For("a").ReadabilityIndex);
            Eq("cursor survives", new Point(9, 6), sessions.For("a").Cursor.Value);
            Eq("a fresh item defaults to 4x (gameplay scale)", 2, sessions.For("c").ReadabilityIndex);
            Eq("a fresh item defaults to the cap", FitTarget.Hat, sessions.For("c").Target);
            sessions.Clear();
            Eq("clearing resets to defaults", FitTarget.Hat, sessions.For("a").Target);

            Console.WriteLine($"\n{passed} passed, {failed} failed");
            return failed == 0 ? 0 : 1;
        }
    }
}
