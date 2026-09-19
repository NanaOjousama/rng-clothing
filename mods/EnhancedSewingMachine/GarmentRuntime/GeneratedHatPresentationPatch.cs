using System;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Objects;

namespace EnhancedSewingMachine.GarmentRuntime
{
    [HarmonyPatch(typeof(Hat), "get_DisplayName")]
    internal static class GeneratedHatDisplayNamePatch
    {
        [HarmonyPostfix]
        private static void Postfix(Hat __instance, ref string __result)
        {
            string generatedName = FarmerRendererPatch.Host?.GetDisplayName(__instance);
            if (!string.IsNullOrWhiteSpace(generatedName))
                __result = generatedName;
        }
    }

    [HarmonyPatch(
        typeof(Hat),
        nameof(Hat.drawInMenu),
        new Type[]
        {
            typeof(SpriteBatch),
            typeof(Vector2),
            typeof(float),
            typeof(float),
            typeof(float),
            typeof(StackDrawType),
            typeof(Color),
            typeof(bool)
        })]
    internal static class GeneratedHatMenuIconPatch
    {
        [HarmonyPostfix]
        private static void Postfix(
            Hat __instance,
            SpriteBatch spriteBatch,
            Vector2 location,
            float scaleSize,
            float transparency,
            float layerDepth,
            Color color)
        {
            FarmerRendererPatch.Host?.DrawInMenu(
                __instance,
                spriteBatch,
                location,
                scaleSize,
                transparency,
                layerDepth,
                color);
        }
    }
}
