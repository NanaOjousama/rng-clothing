using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;
using StardewValley.GameData.Shops;
using StardewValley.Menus;
using StardewValley.Objects;

namespace StardewVisualQCBridge
{
    internal static class FittingProbe
    {
        private static SButton? pendingButton;

        public static void ApplyInput(IModHelper helper)
        {
            if (pendingButton is SButton button)
            {
                helper.Input.Press(button);
                pendingButton = null;
            }
        }

        public static Dictionary<string, object> Run(IModHelper helper, Request request, string root)
        {
            if (!Context.IsWorldReady)
                throw new InvalidOperationException("Load a save first.");
            string action = request.Arg("action") ?? "state";
            switch (action)
            {
                case "sew":
                    if (Game1.activeClickableMenu != null)
                        throw new InvalidOperationException("Close the current menu first.");
                    var machine = ItemRegistry.Create<StardewValley.Object>("(BC)247");
                    machine.Location = Game1.currentLocation;
                    machine.checkForAction(Game1.player);
                    break;
                case "equip":
                    if (Game1.activeClickableMenu != null)
                        throw new InvalidOperationException("Close the current menu first.");
                    var hat = ItemRegistry.Create<Hat>(request.Arg("id"));
                    if (Game1.player.hat.Value != null)
                        Utility.CollectOrDrop(Game1.player.hat.Value);
                    Game1.player.hat.Value = hat;
                    break;
                case "press":
                    var button = Enum.Parse<SButton>(request.Arg("button"));
                    if (button.ToString().StartsWith("Controller") || button == SButton.LeftTrigger
                        || button == SButton.RightTrigger || button.ToString().StartsWith("DPad"))
                    {
                        Game1.options.gamepadControls = true;
                        Game1.options.snappyMenus = true;
                    }
                    pendingButton = button;
                    break;
                case "ingredients":
                    if (Game1.activeClickableMenu is not TailoringMenu tailoring)
                        throw new InvalidOperationException("Open the sewing machine first.");
                    if (tailoring.leftIngredientSpot.item != null || tailoring.rightIngredientSpot.item != null)
                        throw new InvalidOperationException("Ingredient slots must be empty.");
                    tailoring.leftIngredientSpot.item = ItemRegistry.Create("(O)428");
                    tailoring.rightIngredientSpot.item = ItemRegistry.Create("(O)388");
                    helper.Reflection.GetMethod(tailoring, "_ValidateCraft").Invoke();
                    break;
                case "screen":
                    string path = Path.Combine(root, "captures", "fitting-loop", request.Arg("label") + ".png");
                    Directory.CreateDirectory(Path.GetDirectoryName(path));
                    if (!Capture.SaveScreen(path, out string error))
                        throw new InvalidOperationException(error);
                    break;
                case "state":
                    break;
                default:
                    throw new InvalidOperationException("Unknown fitting probe action.");
            }
            var menu = Game1.activeClickableMenu;
            var result = new Dictionary<string, object>
            {
                ["menu"] = menu?.GetType().FullName,
                ["hat"] = Game1.player.hat.Value?.QualifiedItemId,
                ["hat_name"] = Game1.player.hat.Value?.DisplayName,
                ["focus"] = menu?.currentlySnappedComponent?.myID,
                ["components"] = menu?.allClickableComponents?.Select(component => new
                {
                    id = component.myID, bounds = component.bounds, name = component.name
                }).ToArray(),
                ["shop"] = Game1.content.Load<Dictionary<string, ShopData>>("Data/Shops")["SeedShop"]
                    .Items.Where(item => item.Id == "RNGClothing.Fitting/Cap2").ToArray()
            };
            if (menu?.GetType().FullName == "RNGClothingFitting.FittingMenu")
            {
                result["fit"] = helper.Reflection.GetField<object>(menu, "fit").GetValue();
                result["original"] = helper.Reflection.GetField<object>(menu, "original").GetValue();
                result["toast"] = helper.Reflection.GetField<string>(menu, "toast").GetValue();
                result["target"] = helper.Reflection.GetField<object>(menu, "session").GetValue();
            }
            if (menu is TailoringMenu sewing)
            {
                result["left"] = sewing.leftIngredientSpot.item?.QualifiedItemId;
                result["right"] = sewing.rightIngredientSpot.item?.QualifiedItemId;
                result["held"] = sewing.heldItem?.QualifiedItemId;
                result["busy"] = sewing.IsBusy();
            }
            return result;
        }
    }
}
