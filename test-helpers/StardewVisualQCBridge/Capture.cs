using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;

namespace StardewVisualQCBridge
{
    /// <summary>Two kinds of capture, and the difference matters.
    ///
    ///   SCREEN   the actual backbuffer — literally the pixels the player sees,
    ///            background, lighting and all.  This is the AUTHORITY.
    ///
    ///   ISOLATED the farmer drawn to an offscreen target through
    ///            FarmerRenderer.draw, which Fashion Sense prefixes.  It is the
    ///            same renderer and the same Fashion Sense pipeline, just without
    ///            a world behind it, so alpha is meaningful and measurement is
    ///            exact.  It is NOT a synthetic composite: no part of the farmer
    ///            or the hat is reconstructed here.
    ///
    /// The isolated pass is also taken twice — with the hat and with the hat
    /// cleared — so the hat's real drawn pixels can be recovered by difference.
    /// That is what makes seating, face intrusion and hair relationship
    /// measurable at all.
    /// </summary>
    internal static class Capture
    {
        public const int TargetSize = 256;

        public static void SavePng(Texture2D texture, string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            using var stream = File.Create(path);
            texture.SaveAsPng(stream, texture.Width, texture.Height);
        }

        /// <summary>The real backbuffer. Must be called after the frame is drawn.</summary>
        public static bool SaveScreen(string path, out string error)
        {
            error = null;
            try
            {
                GraphicsDevice device = Game1.graphics.GraphicsDevice;
                int w = device.PresentationParameters.BackBufferWidth;
                int h = device.PresentationParameters.BackBufferHeight;
                var data = new Color[w * h];
                device.GetBackBufferData(data);
                using var tex = new Texture2D(device, w, h);
                tex.SetData(data);
                SavePng(tex, path);
                return true;
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return false;
            }
        }

        /// <summary>Crop of the screen around the farmer.
        ///
        /// The anchor is <see cref="Farmer.getLocalPosition"/> scaled by the zoom,
        /// which is what the world SpriteBatch actually uses.  An earlier version
        /// derived it from Game1.viewport and Player.Position and landed on a
        /// piece of furniture, so <see cref="ScreenAnchors"/> also reports the
        /// candidates and the measured result — a wrong crop must be visible in
        /// the JSON, not silently wrong in a PNG.
        /// </summary>
        public static bool SaveHeadCrop(string outPath, out string error,
            out Dictionary<string, object> debug)
        {
            error = null;
            debug = ScreenAnchors();
            try
            {
                GraphicsDevice device = Game1.graphics.GraphicsDevice;
                int w = device.PresentationParameters.BackBufferWidth;
                int h = device.PresentationParameters.BackBufferHeight;
                var data = new Color[w * h];
                device.GetBackBufferData(data);

                float zoom = Game1.options.zoomLevel;
                Vector2 local = Game1.player.getLocalPosition(Game1.viewport);
                // getLocalPosition is the sprite's draw origin in world pixels;
                // the head sits about one tile above it, and the sprite is 64 wide.
                int cx = (int)((local.X + 32f) * zoom);
                int cy = (int)((local.Y - 40f) * zoom);
                int half = (int)(64 * zoom);

                int x0 = Math.Max(0, cx - half), y0 = Math.Max(0, cy - half);
                int x1 = Math.Min(w, cx + half), y1 = Math.Min(h, cy + half);
                int cw = Math.Max(1, x1 - x0), chh = Math.Max(1, y1 - y0);
                debug["crop"] = new { x = x0, y = y0, width = cw, height = chh };

                var crop = new Color[cw * chh];
                for (int y = 0; y < chh; y++)
                    Array.Copy(data, (y0 + y) * w + x0, crop, y * cw, cw);
                using var tex = new Texture2D(device, cw, chh);
                tex.SetData(crop);
                SavePng(tex, outPath);
                return true;
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return false;
            }
        }

        /// <summary>Every candidate for "where is the farmer on screen", so the
        /// crop can be calibrated from one capture instead of guessed again.</summary>
        public static Dictionary<string, object> ScreenAnchors()
        {
            var d = new Dictionary<string, object>();
            try
            {
                float zoom = Game1.options.zoomLevel;
                Vector2 local = Game1.player.getLocalPosition(Game1.viewport);
                Vector2 g2l = Game1.GlobalToLocal(Game1.viewport, Game1.player.Position);
                d["zoom"] = zoom;
                d["ui_scale"] = Game1.options.uiScale;
                d["get_local_position"] = new { local.X, local.Y };
                d["get_local_position_scaled"] = new { X = local.X * zoom, Y = local.Y * zoom };
                d["global_to_local"] = new { g2l.X, g2l.Y };
                d["global_to_local_scaled"] = new { X = g2l.X * zoom, Y = g2l.Y * zoom };
                d["player_position"] = new { Game1.player.Position.X, Game1.player.Position.Y };
                d["viewport"] = new { Game1.viewport.X, Game1.viewport.Y, Game1.viewport.Width, Game1.viewport.Height };
            }
            catch (Exception ex) { d["error"] = ex.Message; }
            return d;
        }

        /// <summary>Draw the farmer offscreen through the real (Fashion-Sense-patched)
        /// FarmerRenderer. Returns the pixel buffer as well as writing the PNG.</summary>
        public static Color[] SaveIsolated(string path, out int width, out int height, out string error)
        {
            width = height = TargetSize;
            error = null;
            RenderTarget2D target = null;
            var device = Game1.graphics.GraphicsDevice;
            RenderTargetBinding[] previous = null;
            try
            {
                previous = device.GetRenderTargets();
                target = new RenderTarget2D(device, TargetSize, TargetSize, false,
                    device.PresentationParameters.BackBufferFormat, DepthFormat.Depth24);
                device.SetRenderTarget(target);
                device.Clear(Color.Transparent);

                var batch = new SpriteBatch(device);
                batch.Begin(SpriteSortMode.FrontToBack, BlendState.AlphaBlend, SamplerState.PointClamp,
                    null, null, null, Matrix.Identity);

                Farmer who = Game1.player;
                // 4x sprite is 64x128; centre the head in the target.
                var position = new Vector2(TargetSize / 2f - 32f, TargetSize / 2f - 80f);
                who.FarmerRenderer.draw(
                    batch,
                    who.FarmerSprite.CurrentAnimationFrame,
                    who.FarmerSprite.CurrentFrame,
                    who.FarmerSprite.SourceRect,
                    position,
                    Vector2.Zero,
                    0.8f,
                    who.FacingDirection,
                    Color.White,
                    0f,
                    1f,
                    who);

                batch.End();
                batch.Dispose();

                var data = new Color[TargetSize * TargetSize];
                target.GetData(data);

                device.SetRenderTargets(previous);
                using (var tex = new Texture2D(device, TargetSize, TargetSize))
                {
                    tex.SetData(data);
                    SavePng(tex, path);
                }
                return data;
            }
            catch (Exception ex)
            {
                error = ex.Message;
                try { if (previous != null) device.SetRenderTargets(previous); } catch { }
                return null;
            }
            finally
            {
                target?.Dispose();
            }
        }

        /// <summary>Alpha bounding box of a buffer, or null when nothing was drawn.</summary>
        public static Dictionary<string, object> AlphaBounds(Color[] data, int w, int h, byte threshold = 8)
        {
            int minX = int.MaxValue, minY = int.MaxValue, maxX = int.MinValue, maxY = int.MinValue, count = 0;
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    if (data[y * w + x].A <= threshold)
                        continue;
                    count++;
                    if (x < minX) minX = x;
                    if (y < minY) minY = y;
                    if (x > maxX) maxX = x;
                    if (y > maxY) maxY = y;
                }
            }
            if (count == 0)
                return null;
            return new Dictionary<string, object>
            {
                ["x"] = minX,
                ["y"] = minY,
                ["width"] = maxX - minX + 1,
                ["height"] = maxY - minY + 1,
                ["pixels"] = count
            };
        }

        /// <summary>The hat's real drawn footprint: pixels the hat itself
        /// draws, and nothing else.
        ///
        /// A hat can also REMOVE pixels — HideHair and UseBaldHead delete the
        /// hairstyle, and any hat can cover hair that stuck out further than
        /// the hat does. Those pixels differ between the two passes but are
        /// not part of the hat.
        ///
        /// This used to paint them opaque magenta as a sentinel, which
        /// corrupted the isolated frame: every downstream measurement counts
        /// alpha, so a removal was indistinguishable from hat art. A whole
        /// capture session was invalidated that way, with 16 of 64 frames
        /// carrying magenta that read as hat footprint.
        ///
        /// Removals are now transparent in the image and reported separately,
        /// so `hatonly` means exactly what its name says regardless of which
        /// hair flags the appearance sets.</summary>
        public static Color[] Difference(Color[] withHat, Color[] without, int w, int h, out int changed, out int removed)
        {
            var diff = new Color[w * h];
            changed = 0;
            removed = 0;
            for (int i = 0; i < diff.Length; i++)
            {
                Color a = withHat[i], b = without[i];
                if (a.A != b.A || a.R != b.R || a.G != b.G || a.B != b.B)
                {
                    if (a.A > 0)
                    {
                        diff[i] = a;          // the hat drew here
                        changed++;
                    }
                    else
                    {
                        diff[i] = Color.Transparent;   // the hat removed something
                        removed++;
                    }
                }
                else
                    diff[i] = Color.Transparent;
            }
            return diff;
        }

        public static void SaveBuffer(Color[] data, int w, int h, string path)
        {
            using var tex = new Texture2D(Game1.graphics.GraphicsDevice, w, h);
            tex.SetData(data);
            SavePng(tex, path);
        }
    }
}
