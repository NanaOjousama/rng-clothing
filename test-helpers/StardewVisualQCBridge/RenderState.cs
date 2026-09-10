using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;

namespace StardewVisualQCBridge
{
    /// <summary>Reads what the game is ACTUALLY about to draw.
    ///
    /// Everything here comes from live game state or from the equipped hat's own
    /// content pack, never from a formula reproduced from memory.  The one
    /// derived block is <c>predicted_draw</c>, which recomputes Fashion Sense's
    /// own hat placement arithmetic so the capture can be checked against it —
    /// if the prediction and the measured pixels disagree, the prediction is
    /// what is wrong.
    ///
    /// Fashion Sense hat draw, from DrawManager.DrawAppearance (v7.5.0):
    ///
    ///   screenPos = Position + Origin + PositionOffset + featureOffset
    ///   origin    = Origin + (HeadPosition.X, HeadPosition.Y)
    ///   scale     = model.Scale * DrawTool.Scale          (model.Scale defaults to 4)
    ///   source    = (StartingPosition.X, StartingPosition.Y, HatSize.Width, HatSize.Length)
    ///
    /// and for hats specifically (AppearanceHelpers.GetFeatureOffset):
    ///
    ///   featureOffset.X = -8 + (flip ? -1 : 1) * XFeatureOffset(currentFrame) * 4
    ///   featureOffset.Y = -16 + YFeatureOffset(currentFrame) * 4 + 4 + heightOffset
    ///
    /// Note HeadPosition is applied to the ORIGIN, not the position, so its screen
    /// effect is negative and scaled — not the "+X pixels" our pack README assumed.
    /// </summary>
    internal static class RenderState
    {
        /// <summary>SDV facing: 0 up, 1 right, 2 down, 3 left.  Fashion Sense maps
        /// these to BackHat / RightHat / FrontHat / LeftHat in that order
        /// (HatContentPack.GetHatFromFacingDirection).</summary>
        public static readonly string[] FacingNames = { "back", "right", "front", "left" };

        public static Dictionary<string, object> Capture(IModHelper helper, Bridge bridge)
        {
            var state = new Dictionary<string, object>
            {
                ["session"] = bridge.SessionId,
                ["timestamp"] = DateTime.Now.ToString("o"),
                ["world_ready"] = Context.IsWorldReady
            };
            if (!Context.IsWorldReady)
                return state;

            Farmer who = Game1.player;
            var sprite = who.FarmerSprite;

            state["farmer"] = new Dictionary<string, object>
            {
                ["name"] = who.Name,
                ["facing_direction"] = who.FacingDirection,
                ["facing_name"] = Facing(who.FacingDirection),
                ["current_frame"] = sprite.CurrentFrame,
                ["animation_frame_flip"] = sprite.CurrentAnimationFrame.flip,
                ["animation_frame_index"] = sprite.CurrentAnimationFrame.frame,
                ["source_rect"] = Rect(sprite.SourceRect),
                ["world_position"] = new { X = who.Position.X, Y = who.Position.Y },
                ["tile"] = new { X = who.TilePoint.X, Y = who.TilePoint.Y },
                ["location"] = who.currentLocation?.NameOrUniqueName ?? "",
                ["hairstyle"] = who.hair.Value,
                ["hair_color"] = Col(who.hairstyleColor.Value),
                ["skin"] = who.skin.Value,
                ["is_male"] = who.IsMale,
                ["swimming"] = who.swimming.Value,
                ["is_moving"] = who.isMoving()
            };

            state["view"] = new Dictionary<string, object>
            {
                ["zoom_level"] = Game1.options.zoomLevel,
                ["ui_scale"] = Game1.options.uiScale,
                ["viewport"] = new { Game1.viewport.X, Game1.viewport.Y, Game1.viewport.Width, Game1.viewport.Height },
                ["backbuffer"] = new
                {
                    Width = Game1.graphics.GraphicsDevice.PresentationParameters.BackBufferWidth,
                    Height = Game1.graphics.GraphicsDevice.PresentationParameters.BackBufferHeight
                }
            };

            // --- the hat -----------------------------------------------------
            var hat = new Dictionary<string, object>();
            string fsHatId = null;
            if (who.modData.TryGetValue("FashionSense.CustomHat.Id", out string id) && !string.IsNullOrWhiteSpace(id))
                fsHatId = id;

            hat["fashion_sense_id"] = fsHatId ?? "";
            hat["is_fashion_sense"] = fsHatId != null;
            hat["vanilla_hat"] = who.hat.Value?.QualifiedItemId ?? "";
            hat["vanilla_hat_name"] = who.hat.Value?.DisplayName ?? "";

            if (fsHatId != null)
            {
                var model = HatPacks.ResolveModel(fsHatId, who.FacingDirection);
                if (model != null)
                {
                    hat["pack_id"] = model.PackId;
                    hat["appearance_name"] = model.AppearanceName;
                    hat["texture_path"] = model.TexturePath;
                    hat["direction_model"] = model.DirectionKey;
                    hat["source_rectangle"] = new
                    {
                        X = model.StartX,
                        Y = model.StartY,
                        Width = model.Width,
                        Height = model.Height
                    };
                    hat["native_frame_size"] = new { model.Width, Length = model.Height };
                    hat["scale"] = model.Scale;
                    hat["head_position"] = new { X = model.HeadX, Y = model.HeadY };
                    hat["hide_hair"] = model.HideHair;
                    hat["flipped"] = model.Flipped;
                    hat["disable_grayscale"] = model.DisableGrayscale;

                    // Fashion Sense's own arithmetic, recomputed for cross-check.
                    bool flip = sprite.CurrentAnimationFrame.flip;
                    int heightOffset = HeightOffset(who);
                    float fx = -8 + (flip ? -1 : 1) * XFeatureOffset(sprite.CurrentFrame) * 4;
                    float fy = -16 + YFeatureOffset(sprite.CurrentFrame) * 4 + 4 + heightOffset;
                    hat["predicted_draw"] = new Dictionary<string, object>
                    {
                        ["feature_offset"] = new { X = fx, Y = fy },
                        ["height_offset"] = heightOffset,
                        ["origin_shift_head_position"] = new { X = model.HeadX, Y = model.HeadY },
                        ["effective_scale"] = model.Scale,
                        ["flip_from_animation_frame"] = flip,
                        ["note"] = "HeadPosition is added to the sprite ORIGIN, so it moves the "
                                 + "hat by -HeadPosition * scale on screen."
                    };
                }
                else
                    hat["resolve_error"] = "could not resolve the hat model from disk";
            }
            state["hat"] = hat;
            return state;
        }

        public static string Facing(int direction)
            => direction >= 0 && direction < 4 ? FacingNames[direction] : "unknown";

        public static int FacingFromName(string name)
        {
            switch ((name ?? "").Trim().ToLowerInvariant())
            {
                case "back": case "up": case "0": return 0;
                case "right": case "1": return 1;
                case "front": case "down": case "2": return 2;
                case "left": case "3": return 3;
                default: return -1;
            }
        }

        /// <summary>FarmerRenderer's per-frame head bob. Mirrors the vanilla tables
        /// Fashion Sense reads; if the game ever changes them the capture, not this,
        /// is the authority.</summary>
        public static int XFeatureOffset(int currentFrame)
        {
            try { return FarmerRenderer.featureXOffsetPerFrame[currentFrame]; }
            catch { return 0; }
        }

        public static int YFeatureOffset(int currentFrame)
        {
            try { return FarmerRenderer.featureYOffsetPerFrame[currentFrame]; }
            catch { return 0; }
        }

        public static int HeightOffset(Farmer who)
        {
            try { return who.FarmerRenderer.heightOffset.Value; }
            catch { return 0; }
        }

        private static object Rect(Rectangle r) => new { r.X, r.Y, r.Width, r.Height };
        private static object Col(Color c) => new { c.R, c.G, c.B, c.A };
    }
}
