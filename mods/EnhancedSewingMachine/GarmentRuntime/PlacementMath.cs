using System;
using Microsoft.Xna.Framework;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal static class PlacementMath
    {
        public const float VanillaPixelScale = 4f;

        public static float GetDrawScale(float farmerScale, float renderScale)
            => VanillaPixelScale * farmerScale * renderScale;

        public static Vector2 GetVanillaHatPivot(
            Vector2 position,
            Vector2 farmerOrigin,
            Vector2 positionOffset,
            float farmerScale,
            int featureX,
            int featureY,
            int hairstyleOffset,
            int heightOffset,
            bool animationFlip)
        {
            float vanillaScale = VanillaPixelScale * farmerScale;
            float x = (-vanillaScale * 2f)
                + (((animationFlip ? -1 : 1) * featureX) * vanillaScale);
            float y = (-vanillaScale * 4f)
                + featureY * VanillaPixelScale
                + hairstyleOffset
                + VanillaPixelScale
                + heightOffset;
            return position + farmerOrigin + positionOffset + new Vector2(x, y);
        }

        public static Vector2 GetReferenceWorldPoint(
            Vector2 vanillaPivot,
            Vector2 farmerOrigin,
            Vector2 vanillaReferenceAnchor,
            float farmerScale,
            float rotation)
        {
            float vanillaScale = VanillaPixelScale * farmerScale;
            Vector2 delta = (vanillaReferenceAnchor - farmerOrigin) * vanillaScale;
            return vanillaPivot + Rotate(delta, rotation);
        }

        public static Vector2 GetCustomDrawPosition(
            Vector2 referenceWorldPoint,
            int offsetX,
            int offsetY,
            float farmerScale,
            float rotation)
        {
            Vector2 offset = new Vector2(offsetX, offsetY) * (VanillaPixelScale * farmerScale);
            return referenceWorldPoint + Rotate(offset, rotation);
        }

        internal static Vector2 Rotate(Vector2 value, float rotation)
        {
            if (rotation == 0f)
                return value;
            float c = MathF.Cos(rotation);
            float s = MathF.Sin(rotation);
            return new Vector2(value.X * c - value.Y * s, value.X * s + value.Y * c);
        }
    }
}
