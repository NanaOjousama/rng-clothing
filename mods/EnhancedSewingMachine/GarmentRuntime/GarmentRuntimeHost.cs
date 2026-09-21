using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Netcode;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Objects;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal sealed class GarmentRuntimeHost
    {
        public const string LegacyProofGarmentId = "dev.proof32";

        private readonly IModHelper helper;
        private readonly IMonitor monitor;
        private readonly Dictionary<string, Texture2D> textureCache = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> failedTexturePaths = new(StringComparer.OrdinalIgnoreCase);
        private readonly HashSet<string> warnedRenderFailures = new(StringComparer.Ordinal);
        private readonly HashSet<string> warnedDigestDrift = new(StringComparer.Ordinal);

        public GarmentRuntimeHost(IModHelper helper, IMonitor monitor)
        {
            this.helper = helper;
            this.monitor = monitor;
            this.Registry = new GarmentRegistry(helper, monitor);
            this.Items = new GarmentItemService(this.Registry, monitor);
        }

        public GarmentRegistry Registry { get; }
        public GarmentItemService Items { get; }
        public void Load()
        {
            this.textureCache.Clear();
            this.failedTexturePaths.Clear();
            this.warnedRenderFailures.Clear();
            this.warnedDigestDrift.Clear();
            this.Registry.Load();
        }

        public Hat CreateHat(string garmentId, long seed)
            => this.Items.CreateHat(garmentId, seed);

        public bool TryReadInstance(Hat hat, out GarmentInstanceData instance)
            => this.Items.TryRead(hat, out instance);

        public void WriteInstance(Hat hat, GarmentInstanceData instance)
            => this.Items.Write(hat, instance);

        public string GetDisplayName(Hat hat)
        {
            if (!this.Items.TryRead(hat, out GarmentInstanceData instance))
                return null;

            string family = (instance.Family ?? instance.Construction ?? "").Trim().ToLowerInvariant();
            string key = family switch
            {
                "felt_hat" => "garment.family.felt_hat",
                "knit_cap" => "garment.family.knit_cap",
                "soft_cap" => "garment.family.soft_cap",
                "wide_brim_hat" => "garment.family.wide_brim_hat",
                _ => "carrier.hat.name"
            };
            return this.helper.Translation.Get(key);
        }

        public void DrawInMenu(
            Hat hat,
            SpriteBatch batch,
            Vector2 location,
            float scaleSize,
            float transparency,
            float layerDepth,
            Color color)
        {
            if (batch == null || !this.TryResolveRender(hat, out GarmentRenderSnapshot render, out Texture2D texture))
                return;

            DirectionFrame frame = render.Resolve(2);
            if (frame == null)
                return;

            var source = new Rectangle(frame.SourceX, frame.SourceY, render.FrameWidth, render.FrameHeight);
            int maxDimension = Math.Max(render.FrameWidth, render.FrameHeight);
            float fitScale = Math.Max(1, 64 / Math.Max(1, maxDimension));
            float drawScale = fitScale * scaleSize;
            Vector2 center = location + new Vector2(32f, 32f);
            Vector2 origin = new Vector2(
                render.FrameWidth / 2f,
                render.FrameHeight / 2f);

            batch.Draw(
                texture,
                center,
                source,
                color * transparency,
                0f,
                origin,
                drawScale,
                frame.FlipX ? SpriteEffects.FlipHorizontally : SpriteEffects.None,
                layerDepth + 0.0001f);
        }

        public void Draw(
            SpriteBatch batch,
            int facingDirection,
            Farmer who,
            Vector2 position,
            Vector2 farmerOrigin,
            float farmerScale,
            int currentFrame,
            float rotation,
            Color overrideColor,
            float layerDepth,
            Vector2 positionOffset,
            int heightOffset)
        {
            if (batch == null || who == null || who.bathingClothes.Value)
                return;

            Hat hat = who.hat.Value;
            if (!GarmentCarrier.IsCarrier(hat))
                return;

            if (!this.TryResolveRender(hat, out GarmentRenderSnapshot render, out Texture2D texture))
                return;

            DirectionFrame frame = render.Resolve(facingDirection);
            if (frame == null)
                return;
            if (currentFrame < 0 || currentFrame >= FarmerRenderer.featureXOffsetPerFrame.Length
                || currentFrame >= FarmerRenderer.featureYOffsetPerFrame.Length)
                return;

            int featureX = FarmerRenderer.featureXOffsetPerFrame[currentFrame];
            int featureY = FarmerRenderer.featureYOffsetPerFrame[currentFrame];
            int hairIndex = Math.Abs(who.hair.Value % FarmerRenderer.hairstyleHatOffset.Length);
            int hairstyleOffset = hat.ignoreHairstyleOffset.Value
                ? 0
                : FarmerRenderer.hairstyleHatOffset[hairIndex];
            bool animationFlip = who.FarmerSprite != null && who.FarmerSprite.CurrentAnimationFrame.flip;

            Vector2 vanillaPivot = PlacementMath.GetVanillaHatPivot(
                position, farmerOrigin, positionOffset, farmerScale,
                featureX, featureY, hairstyleOffset, heightOffset, animationFlip);

            Vector2 referenceWorld = PlacementMath.GetReferenceWorldPoint(
                vanillaPivot,
                farmerOrigin,
                new Vector2(render.VanillaReferenceAnchor.X, render.VanillaReferenceAnchor.Y),
                farmerScale,
                rotation);

            int fitX = 0;
            int fitY = 0;
            float fitScale = 1f;
            if (this.Items.TryRead(hat, out GarmentInstanceData liveInstance))
            {
                fitX = liveInstance.GetFitOffsetX(facingDirection);
                fitY = liveInstance.GetFitOffsetY(facingDirection);
                fitScale = Math.Clamp(liveInstance.GetFitScale(facingDirection), 0.85f, 1.25f);
            }

            Vector2 drawPosition = PlacementMath.GetCustomDrawPosition(
                referenceWorld,
                frame.OffsetX + fitX,
                frame.OffsetY + fitY,
                farmerScale,
                rotation);

            var source = new Rectangle(frame.SourceX, frame.SourceY, render.FrameWidth, render.FrameHeight);
            // Scale around the authored frame anchor. Because drawPosition is the
            // anchor point and SpriteBatch receives frame.AnchorX/Y as origin,
            // changing scale cannot move the anchor off the farmer's head.
            float drawScale = PlacementMath.GetDrawScale(farmerScale, render.RenderScale) * fitScale;
            Color color = hat.isPrismatic.Value ? Utility.GetPrismaticColor() : overrideColor;
            SpriteEffects effects = frame.FlipX ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
            float depth = FarmerRenderer.GetLayerDepth(layerDepth, FarmerRenderer.FarmerSpriteLayers.Hat);

            batch.Draw(
                texture,
                drawPosition,
                source,
                color,
                rotation,
                new Vector2(frame.AnchorX, frame.AnchorY),
                drawScale,
                effects,
                depth);
        }

        private bool TryResolveRender(Hat hat, out GarmentRenderSnapshot render, out Texture2D texture)
        {
            render = null;
            texture = null;

            if (this.Items.TryRead(hat, out GarmentInstanceData instance))
            {
                render = instance.Render;

                if (this.Registry.TryGet(instance.GarmentId, out RegisteredGarment current)
                    && !string.IsNullOrWhiteSpace(render?.AppearanceDigest)
                    && !string.IsNullOrWhiteSpace(current.AppearanceDigest)
                    && !string.Equals(render.AppearanceDigest, current.AppearanceDigest, StringComparison.OrdinalIgnoreCase))
                {
                    string driftKey = instance.GarmentId + "|" + render.AppearanceDigest + "|" + current.AppearanceDigest;
                    if (this.warnedDigestDrift.Add(driftKey))
                    {
                        this.monitor.Log(
                            $"Garment '{instance.GarmentId}' was created from appearance digest {render.AppearanceDigest} " +
                            $"but the installed definition is now {current.AppearanceDigest}. The saved render snapshot is kept; " +
                            $"production generated assets should use immutable paths.",
                            LogLevel.Warn);
                    }
                }
            }
            else if (hat.QualifiedItemId == GarmentCarrier.LegacyProofQualifiedId
                && this.Registry.TryGet(LegacyProofGarmentId, out RegisteredGarment legacy))
            {
                // Compatibility only for the Phase 1 proof item that may already exist in a dev save.
                render = legacy.Definition.ToSnapshot(legacy.AppearanceDigest);
                texture = legacy.Texture;
            }
            else
            {
                return false;
            }

            if (render == null || string.IsNullOrWhiteSpace(render.WornTexture))
                return false;

            texture ??= this.GetTexture(render.WornTexture);
            if (texture == null)
                return false;

            if (!render.TryValidate(texture.Width, texture.Height, out string error))
            {
                string garmentId = hat.modData.TryGetValue(GarmentInstanceKeys.GarmentId, out string value)
                    ? value
                    : "unknown";
                string key = garmentId + "|" + error;
                if (this.warnedRenderFailures.Add(key))
                    this.monitor.Log($"Garment instance '{garmentId}' failed render validation: {error}", LogLevel.Warn);
                return false;
            }

            return true;
        }

        private Texture2D GetTexture(string path)
        {
            if (this.textureCache.TryGetValue(path, out Texture2D cached))
                return cached;
            if (this.failedTexturePaths.Contains(path))
                return null;

            try
            {
                Texture2D texture = this.helper.ModContent.Load<Texture2D>(path);
                this.textureCache[path] = texture;
                return texture;
            }
            catch (Exception ex)
            {
                this.failedTexturePaths.Add(path);
                this.monitor.Log($"Garment texture '{path}' failed to load; affected items will fail open. {ex.Message}", LogLevel.Error);
                return null;
            }
        }
    }
}
