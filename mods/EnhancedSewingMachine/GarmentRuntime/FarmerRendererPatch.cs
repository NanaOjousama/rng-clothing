using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Netcode;
using StardewValley;

namespace EnhancedSewingMachine.GarmentRuntime
{
    [HarmonyPatch(typeof(FarmerRenderer), nameof(FarmerRenderer.drawHairAndAccesories))]
    internal static class FarmerRendererPatch
    {
        internal static GarmentRuntimeHost Host { get; set; }

        [HarmonyPostfix]
        private static void Postfix(
            SpriteBatch b,
            int facingDirection,
            Farmer who,
            Vector2 position,
            Vector2 origin,
            float scale,
            int currentFrame,
            float rotation,
            Color overrideColor,
            float layerDepth,
            Vector2 ___positionOffset,
            NetInt ___heightOffset)
        {
            Host?.Draw(
                b, facingDirection, who, position, origin, scale,
                currentFrame, rotation, overrideColor, layerDepth,
                ___positionOffset, ___heightOffset?.Value ?? 0);
        }
    }
}
