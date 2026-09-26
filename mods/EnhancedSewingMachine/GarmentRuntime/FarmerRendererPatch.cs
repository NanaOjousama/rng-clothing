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
        internal static StardewValley.Objects.Hat WorldPreviewHat { get; private set; }

        internal static void SetWorldPreview(StardewValley.Objects.Hat hat)
            => WorldPreviewHat = hat;

        internal static void ClearWorldPreview()
            => WorldPreviewHat = null;

        [HarmonyPrefix]
        private static void Prefix(Farmer who, out StardewValley.Objects.Hat __state)
        {
            __state = null;
            if (who == null || who != Game1.player || WorldPreviewHat == null)
                return;

            __state = who.hat.Value;
            who.hat.Value = WorldPreviewHat;
        }

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
            NetInt ___heightOffset,
            StardewValley.Objects.Hat __state)
        {
            Host?.Draw(
                b, facingDirection, who, position, origin, scale,
                currentFrame, rotation, overrideColor, layerDepth,
                ___positionOffset, ___heightOffset?.Value ?? 0);

            if (who == Game1.player && WorldPreviewHat != null)
                who.hat.Value = __state;
        }
    }
}
