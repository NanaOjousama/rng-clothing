using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Xna.Framework;
using Newtonsoft.Json.Linq;

namespace RNGClothingFitting
{
    /// <summary>The generator's `fitting.json` sidecar for one generated cap.
    ///
    /// Fashion Sense ignores unknown files in a pack folder, so this rides
    /// along beside hat.json. It carries the three things this mod cannot
    /// recover on its own:
    ///
    ///   * the authored default HeadPosition per direction, so Reset restores
    ///     the generated default EXACTLY rather than assuming {0,0};
    ///   * the safe mask, so the mod enforces the same per-pixel rule the
    ///     generator enforced instead of re-deriving it and drifting;
    ///   * BasePixels — what each safe cell looks like with no design on it.
    ///     Moving a design means repainting the cells it left behind, and only
    ///     the generator knows what was underneath.
    /// </summary>
    internal sealed class CapSidecar
    {
        public string PackDirectory;
        public string AppearanceId;
        public string ItemId;
        public string QualifiedItemId => "(H)" + this.ItemId;
        public string Base;
        public int FrameSize = 20;
        public string[] Directions = { "Front", "Right", "Left", "Back" };

        public int HatRange = 3;
        public Dictionary<string, Point> DefaultHeadPosition = new();

        public string MotifId = "plain";
        public List<Point> MotifCells = new();
        public Color? MotifColor;
        public HashSet<Point> SafeCells = new();
        public Dictionary<Point, Color> BasePixels = new();

        public bool HasMotif => this.MotifId != "plain" && this.MotifCells.Count > 0;
        public string TexturePath => Path.Combine(this.PackDirectory, "hat.png");

        public static CapSidecar Load(string path)
        {
            var o = JObject.Parse(File.ReadAllText(path));
            if (o.Value<int?>("format") != 1 || o.Value<bool?>("player_fitting") != true)
                return null;                 // a format we do not understand

            var s = new CapSidecar
            {
                PackDirectory = Path.GetDirectoryName(path),
                AppearanceId = o.Value<string>("appearance_id"),
                ItemId = o.Value<string>("item_id"),
                Base = o.Value<string>("base")
            };
            if (s.Base != "cap2" || string.IsNullOrWhiteSpace(s.ItemId) || string.IsNullOrWhiteSpace(s.AppearanceId))
                return null;

            if (o["frame"] is JObject fr)
            {
                s.FrameSize = fr.Value<int?>("size") ?? 20;
                if (fr["directions"] is JArray da && da.Count == 4)
                    s.Directions = da.Select(t => t.ToString()).ToArray();
            }

            if (o["hat"] is JObject hat)
            {
                s.HatRange = hat.Value<int?>("range") ?? 3;
                if (hat["default_head_position"] is JObject dhp)
                    foreach (var p in dhp.Properties())
                        s.DefaultHeadPosition[p.Name] = new Point(
                            p.Value.Value<int>("X"), p.Value.Value<int>("Y"));
            }

            if (o["motif"] is JObject m)
            {
                s.MotifId = m.Value<string>("id") ?? "plain";
                s.MotifCells = ReadPoints(m["cells"]);
                s.SafeCells = new HashSet<Point>(ReadPoints(m["safe_cells"]));
                if (m["colour"] is JArray c && c.Count >= 3)
                    s.MotifColor = new Color(c[0].Value<int>(), c[1].Value<int>(), c[2].Value<int>());
                if (m["base_pixels"] is JObject bp)
                {
                    foreach (var p in bp.Properties())
                    {
                        var bits = p.Name.Split(',');
                        if (bits.Length != 2
                            || !int.TryParse(bits[0], out int x)
                            || !int.TryParse(bits[1], out int y)
                            || p.Value is not JArray v || v.Count < 4)
                            continue;
                        s.BasePixels[new Point(x, y)] = new Color(
                            v[0].Value<int>(), v[1].Value<int>(),
                            v[2].Value<int>(), v[3].Value<int>());
                    }
                }
            }
            return s;
        }

        private static List<Point> ReadPoints(JToken t)
        {
            var list = new List<Point>();
            if (t is JArray arr)
                foreach (var e in arr)
                    if (e is JArray p && p.Count >= 2)
                        list.Add(new Point(p[0].Value<int>(), p[1].Value<int>()));
            return list;
        }

        /// <summary>Index of a direction in the stacked atlas, or -1.</summary>
        public int FrameIndex(string direction) => Array.IndexOf(this.Directions, direction);
    }

    /// <summary>A player's adjustment for one cap, in SCREEN directions.
    ///
    /// Right and down are positive, which is what the player sees. Fashion
    /// Sense's HeadPosition runs the OTHER way — HeadPosition X+1 draws the hat
    /// 4px LEFT and Y+1 draws it 4px UP — and that inversion is applied in
    /// exactly one place, <see cref="HeadPosition"/>, so nothing else in this
    /// mod has to know about it.
    ///
    /// One step is one sprite pixel = 4 screen pixels at the default Scale of
    /// 4. Half steps are not offered: HeadPosition is `int X, int Y`, and a
    /// fractional value makes Fashion Sense silently skip drawing the hat
    /// while still listing the appearance. That was measured, not assumed.
    /// </summary>
    internal sealed class Fit
    {
        public const int ScreenPixelsPerStep = 4;

        public string ItemId;
        public int HatRight, HatDown;
        public int MotifRight, MotifDown;

        public bool IsDefault => this.HatRight == 0 && this.HatDown == 0
                                 && this.MotifRight == 0 && this.MotifDown == 0;

        public Fit Clone() => (Fit)this.MemberwiseClone();

        /// <summary>The authored default plus the player's delta, inverted.</summary>
        public Point HeadPosition(Point authoredDefault)
        {
            return new Point(authoredDefault.X - this.HatRight,
                             authoredDefault.Y - this.HatDown);
        }

        public void ResetHat() { this.HatRight = this.HatDown = 0; }
        public void ResetMotif() { this.MotifRight = this.MotifDown = 0; }
        public void ResetAll() { this.ResetHat(); this.ResetMotif(); }
    }

    /// <summary>Whether a proposed nudge is allowed, and why not if it isn't.</summary>
    internal enum MoveResult { Ok, OutOfRange, OutsideMask, NoMotif }

    internal static class FitRules
    {
        /// <summary>Hat movement is deliberately bounded: fitting is nudging,
        /// not relocating. A move past the edge is REFUSED, not clamped to
        /// something the player did not ask for.</summary>
        public static MoveResult TryMoveHat(Fit fit, CapSidecar cap, int dx, int dy)
        {
            int nx = fit.HatRight + dx, ny = fit.HatDown + dy;
            if (Math.Abs(nx) > cap.HatRange || Math.Abs(ny) > cap.HatRange)
                return MoveResult.OutOfRange;
            fit.HatRight = nx;
            fit.HatDown = ny;
            return MoveResult.Ok;
        }

        /// <summary>Every cell of the SHIFTED design must be legal.
        ///
        /// A design that would leave the safe mask is blocked WHOLE — never
        /// clipped, never deformed, never partly moved — because half a mark is
        /// a different mark. The mask is per-pixel, exactly as authored; this
        /// mod does not widen it.</summary>
        public static MoveResult TryMoveMotif(Fit fit, CapSidecar cap, int dx, int dy)
        {
            if (!cap.HasMotif)
                return MoveResult.NoMotif;
            int nx = fit.MotifRight + dx, ny = fit.MotifDown + dy;
            foreach (var c in cap.MotifCells)
                if (!cap.SafeCells.Contains(new Point(c.X + nx, c.Y + ny)))
                    return MoveResult.OutsideMask;
            fit.MotifRight = nx;
            fit.MotifDown = ny;
            return MoveResult.Ok;
        }

        /// <summary>How many whole-pixel positions this design could legally
        /// occupy, counting its current one.
        ///
        /// Worth knowing up front: the safe mask is small and some marks nearly
        /// fill it, so a design can have exactly ONE legal position. Telling the
        /// player that is far better than refusing every key they press.</summary>
        public static int LegalPositionCount(CapSidecar cap)
        {
            if (cap == null || !cap.HasMotif)
                return 0;
            int n = 0;
            for (int dy = -cap.FrameSize; dy <= cap.FrameSize; dy++)
            for (int dx = -cap.FrameSize; dx <= cap.FrameSize; dx++)
            {
                bool ok = true;
                foreach (var c in cap.MotifCells)
                    if (!cap.SafeCells.Contains(new Point(c.X + dx, c.Y + dy)))
                    { ok = false; break; }
                if (ok) n++;
            }
            return n;
        }

        /// <summary>Where the design's cells sit after the player's offset.</summary>
        public static IEnumerable<Point> PlacedMotif(Fit fit, CapSidecar cap)
        {
            foreach (var c in cap.MotifCells)
                yield return new Point(c.X + fit.MotifRight, c.Y + fit.MotifDown);
        }
    }
}
