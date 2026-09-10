using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using FashionSense.Framework.Models.Appearances;
using FashionSense.Framework.Models.Appearances.Hat;
using FsPosition = FashionSense.Framework.Models.Appearances.Generic.Position;

namespace RNGClothingFitting
{
    /// <summary>Talks to Fashion Sense.
    ///
    /// Two different mechanisms, because the two adjustments are different
    /// kinds of thing:
    ///
    ///   HAT position is a property of the loaded model. `HatModel.HeadPosition`
    ///   is public and settable, and Fashion Sense reads it during the draw, so
    ///   assigning it changes what is on screen the very next frame. No patch,
    ///   no texture work, no reload — this is what makes the preview live.
    ///
    ///   DESIGN position is pixels, so it goes through Fashion Sense's own
    ///   public API (`SetAppearanceTexture` / `ResetAppearanceTexture`), which
    ///   is the supported way for another mod to swap an appearance's texture.
    ///
    /// Everything here fails soft. If Fashion Sense moves its internals, the
    /// bridge reports unavailable and the fitting affordance simply never
    /// appears; the sewing machine keeps working exactly as it does in vanilla.
    /// </summary>
    internal sealed class FashionSenseBridge
    {
        private readonly IModHelper helper;
        private readonly IMonitor monitor;
        private readonly IManifest manifest;
        private object textureManager;
        // hat.png parsed once per cap. Without this every single nudge did a
        // disk read plus a GPU texture upload.
        private readonly Dictionary<string, Color[]> pixelCache = new();
        private readonly Dictionary<string, Point> sizeCache = new();

        // Dirty-flag texture updates. Rebuilding a texture is the expensive
        // thing here -- a Color[] pass plus a GPU upload -- and a fitting
        // session is a burst of single-pixel nudges, so the work is deferred to
        // one flush per frame and skipped entirely when the design has not
        // actually moved from what is already on screen.
        private CapSidecar dirtyCap;
        private Fit dirtyFit;
        private readonly Dictionary<string, Point> appliedMotif = new();
        private FashionSense.Framework.Interfaces.API.IApi api;
        private bool probed;

        public FashionSenseBridge(IModHelper helper, IMonitor monitor, IManifest manifest)
        {
            this.helper = helper;
            this.monitor = monitor;
            this.manifest = manifest;
        }

        public bool Available => this.Probe();

        private bool Probe()
        {
            if (this.probed)
                return this.textureManager != null && this.api != null;
            this.probed = true;
            try
            {
                // `textureManager` is an internal static field on a public
                // type. SMAPI's reflection helper is used rather than Harmony:
                // this mod reads FS state, it does not patch FS behaviour.
                this.textureManager = this.helper.Reflection
                    .GetField<object>(typeof(FashionSense.FashionSense), "textureManager", required: false)
                    ?.GetValue();
                this.api = this.helper.ModRegistry
                    .GetApi<FashionSense.Framework.Interfaces.API.IApi>("PeacefulEnd.FashionSense");
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Fashion Sense bridge unavailable: {ex.Message}", LogLevel.Debug);
                this.textureManager = null;
                this.api = null;
            }
            if (this.textureManager == null || this.api == null)
                this.monitor.Log("Fashion Sense bridge unavailable; fitting will stay hidden.", LogLevel.Debug);
            return this.textureManager != null && this.api != null;
        }

        /// <summary>The loaded hat pack behind an item id, or null.</summary>
        public HatContentPack GetHatPack(string itemId)
        {
            if (!this.Available || string.IsNullOrEmpty(itemId))
                return null;
            try
            {
                var pack = this.helper.Reflection
                    .GetMethod(this.textureManager, "GetAppearanceContentPackByItemId", required: false)
                    ?.Invoke<AppearanceContentPack>(itemId);
                return pack as HatContentPack;
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Could not resolve '{itemId}': {ex.Message}", LogLevel.Trace);
                return null;
            }
        }

        /// <summary>Push a fit onto the live models. Takes effect next frame.</summary>
        public void ApplyHat(HatContentPack pack, CapSidecar cap, Fit fit)
        {
            if (pack == null || cap == null || fit == null)
                return;
            Set(pack.FrontHat, cap, fit, "Front");
            Set(pack.RightHat, cap, fit, "Right");
            Set(pack.LeftHat, cap, fit, "Left");
            Set(pack.BackHat, cap, fit, "Back");
        }

        private static void Set(HatModel model, CapSidecar cap, Fit fit, string direction)
        {
            if (model == null)
                return;                       // a missing direction draws nothing
            if (!cap.DefaultHeadPosition.TryGetValue(direction, out Point def))
                def = Point.Zero;
            Point p = fit.HeadPosition(def);
            // Replace the Position object rather than mutating it: the model
            // may share one, and a shared mutation would move other packs too.
            model.HeadPosition = new FsPosition { X = p.X, Y = p.Y };
        }

        /// <summary>Put every direction back to the value the generator authored.</summary>
        public void ResetHat(HatContentPack pack, CapSidecar cap)
        {
            this.ApplyHat(pack, cap, new Fit { ItemId = cap.ItemId });
        }

        // --- design pixels -------------------------------------------------

        /// <summary>Redraw the cap's texture with the design at the player's
        /// offset, and hand it to Fashion Sense.
        ///
        /// The safe cells are repainted from the sidecar's BasePixels first, so
        /// the crown the design used to sit on comes back; only then is the
        /// design drawn at its new home. Nothing outside the safe mask is ever
        /// touched, so the visor, the rim and the rest of the author's
        /// construction are untouched by construction, not by promise.
        /// </summary>
        /// <summary>Note that the design needs redrawing, without doing it.
        ///
        /// Cheap and idempotent: call it on every keypress. The actual rebuild
        /// happens once in <see cref="FlushMotif"/>.</summary>
        public void MarkMotifDirty(CapSidecar cap, Fit fit)
        {
            if (cap == null || fit == null || !cap.HasMotif)
                return;
            this.dirtyCap = cap;
            this.dirtyFit = fit;
        }

        /// <summary>Do the deferred rebuild, if there is one worth doing.
        ///
        /// Returns true only when a texture was actually uploaded, so callers
        /// can tell "nothing to do" from "done".</summary>
        public bool FlushMotif()
        {
            if (this.dirtyCap == null || this.dirtyFit == null)
                return false;
            CapSidecar cap = this.dirtyCap;
            Fit fit = this.dirtyFit;
            this.dirtyCap = null;
            this.dirtyFit = null;

            var want = new Point(fit.MotifRight, fit.MotifDown);
            if (this.appliedMotif.TryGetValue(cap.ItemId, out Point have) && have == want)
                return false;                  // already on screen; no work needed

            if (!this.ApplyMotif(cap, fit))
                return false;
            this.appliedMotif[cap.ItemId] = want;
            return true;
        }

        /// <summary>Forget what is on screen, so the next flush rebuilds.
        ///
        /// Needed after a reset or a cancel, where the texture must go back to
        /// the generated art and the cached "already applied" offset would
        /// otherwise suppress the rebuild.</summary>
        public void InvalidateMotif(CapSidecar cap)
        {
            if (cap != null)
            {
                this.appliedMotif.Remove(cap.ItemId);
                if (this.dirtyCap?.ItemId == cap.ItemId)
                {
                    this.dirtyCap = null;
                    this.dirtyFit = null;
                }
            }
        }

        /// <summary>The Front frame as it should look for this fit.
        ///
        /// ONE composition routine, used both by the on-screen grid and by the
        /// texture actually handed to Fashion Sense, so the preview cannot
        /// disagree with the result.
        ///
        /// Safe cells are repainted from the sidecar's BasePixels first, so the
        /// crown the design used to sit on comes back; only then is the design
        /// drawn at its new home. Nothing outside the safe mask is touched, so
        /// the visor, the rim and the rest of the author's construction are
        /// untouched by construction rather than by promise.
        /// </summary>
        public Color[] ComposeFrontFrame(CapSidecar cap, Fit fit)
        {
            if (cap == null)
                return null;
            Color[] atlas = this.LoadPixels(cap, out int w, out int h);
            if (atlas == null)
                return null;
            int n = cap.FrameSize;
            int frame = cap.FrameIndex("Front");
            if (frame < 0)
                return null;
            int originY = frame * n;

            var outp = new Color[n * n];
            for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                int sx = x, sy = y + originY;
                outp[y * n + x] = (sx < w && sy < h) ? atlas[sy * w + sx] : Color.Transparent;
            }
            if (!cap.HasMotif || cap.MotifColor == null || fit == null)
                return outp;

            foreach (var kv in cap.BasePixels)
                if (kv.Key.X >= 0 && kv.Key.X < n && kv.Key.Y >= 0 && kv.Key.Y < n)
                    outp[kv.Key.Y * n + kv.Key.X] = kv.Value;
            Color mc = cap.MotifColor.Value;
            foreach (var p in FitRules.PlacedMotif(fit, cap))
                if (cap.SafeCells.Contains(p) && p.X >= 0 && p.X < n && p.Y >= 0 && p.Y < n)
                    outp[p.Y * n + p.X] = mc;
            return outp;
        }

        public bool ApplyMotif(CapSidecar cap, Fit fit)
        {
            if (!this.Available || cap == null || !cap.HasMotif || cap.MotifColor == null)
                return false;
            try
            {
                Color[] pixels = this.LoadPixels(cap, out int w, out int h);
                if (pixels == null)
                    return false;

                int frame = cap.FrameIndex("Front");
                if (frame < 0)
                    return false;
                int n = cap.FrameSize;
                int originY = frame * n;

                // Refuse rather than draw outside the mask. Must never happen —
                // FitRules blocks it first — but a texture upload is the wrong
                // place to discover otherwise.
                foreach (var p in FitRules.PlacedMotif(fit, cap))
                    if (!cap.SafeCells.Contains(p))
                        return false;

                Color[] front = this.ComposeFrontFrame(cap, fit);
                if (front == null)
                    return false;
                for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    int dx = x, dy = y + originY;
                    if (dx < w && dy < h)
                        pixels[dy * w + dx] = front[y * n + x];
                }

                var result = this.api.SetAppearanceTexture(
                    cap.AppearanceId, new RawTexture(w, h, pixels), this.manifest,
                    shouldOverridePersist: true);
                return result.Key;
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Could not apply the design offset: {ex.Message}", LogLevel.Warn);
                return false;
            }
        }

        /// <summary>Drop our texture override, restoring the generated art.</summary>
        public void ResetMotif(CapSidecar cap)
        {
            if (!this.Available || cap == null)
                return;
            this.InvalidateMotif(cap);
            try { this.api.ResetAppearanceTexture(cap.AppearanceId, this.manifest); }
            catch (Exception ex)
            {
                this.monitor.Log($"Could not reset the design: {ex.Message}", LogLevel.Trace);
            }
        }

        /// <summary>The pack's art as written by the generator, read off disk.
        ///
        /// Read from the file rather than from the live texture on purpose: the
        /// live one may already carry our own override, and layering an
        /// override on an override would accumulate.
        /// </summary>
        private Color[] LoadPixels(CapSidecar cap, out int w, out int h)
        {
            w = h = 0;
            if (this.pixelCache.TryGetValue(cap.ItemId, out Color[] cached))
            {
                Point size = this.sizeCache[cap.ItemId];
                w = size.X;
                h = size.Y;
                // A copy, because the caller paints over what it gets back.
                return (Color[])cached.Clone();
            }

            string path = cap.TexturePath;
            if (!File.Exists(path))
                return null;
            using var stream = File.OpenRead(path);
            using var tex = Texture2D.FromStream(Game1.graphics.GraphicsDevice, stream);
            w = tex.Width;
            h = tex.Height;
            var data = new Color[w * h];
            tex.GetData(data);
            this.pixelCache[cap.ItemId] = data;
            this.sizeCache[cap.ItemId] = new Point(w, h);
            return (Color[])data.Clone();
        }

        /// <summary>Minimal IRawTextureData so a Color[] can cross the API.</summary>
        private sealed class RawTexture : IRawTextureData
        {
            public int Width { get; }
            public int Height { get; }
            public Color[] Data { get; }
            public RawTexture(int w, int h, Color[] data)
            {
                this.Width = w;
                this.Height = h;
                this.Data = data;
            }
        }
    }
}
