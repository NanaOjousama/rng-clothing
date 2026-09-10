using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;
using StardewValley.Objects;
using StardewValley.GameData.Shops;
using FashionSense.Framework.Models.Appearances.Hat;

namespace RNGClothingFitting
{
    /// <summary>Fitting for generated caps, offered at the vanilla sewing machine.
    ///
    /// The mod is deliberately small and passive. It listens to SMAPI events,
    /// draws one extra button over the tailoring menu when — and only when —
    /// the player is wearing a cap we generated, and opens its own menu when
    /// that button is used. It patches nothing, suppresses no input, and
    /// replaces no vanilla menu, so for every other item and every other player
    /// the sewing machine behaves exactly as it always did.
    /// </summary>
    public sealed class ModEntry : Mod
    {
        private FashionSenseBridge fs;
        private CapCatalog catalog;
        private FitStore store;
        private SessionStore sessions;

        // Deferred opening. A menu is never swapped from inside an input
        // handler: the handler only records the request, and OnUpdateTicked
        // acts on it. Replacing Game1.activeClickableMenu mid-event means the
        // old menu is still mid-dispatch when the new one appears, which is
        // where input-handling mods go wrong.
        private bool openRequested;
        private string openRequestedBy;

        private ClickableComponent fitButton;
        private CapSidecar targetCap;
        private HatContentPack targetPack;

        public override void Entry(IModHelper helper)
        {
            this.catalog = new CapCatalog(this.Monitor);
            this.store = new FitStore(helper);
            this.sessions = new SessionStore();
            this.fs = new FashionSenseBridge(helper, this.Monitor, this.ModManifest);

            helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
            helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
            helper.Events.Display.MenuChanged += this.OnMenuChanged;
            helper.Events.Display.RenderedActiveMenu += this.OnRenderedActiveMenu;
            helper.Events.Input.ButtonPressed += this.OnButtonPressed;
            helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
            helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;
            helper.Events.Content.AssetRequested += this.OnAssetRequested;
        }

        private void OnGameLaunched(object sender, GameLaunchedEventArgs e)
        {
            this.catalog.Scan(this.Helper);
            this.Helper.GameContent.InvalidateCache("Data/Hats");
            this.Helper.GameContent.InvalidateCache("Data/Shops");
        }

        private void OnAssetRequested(object sender, AssetRequestedEventArgs e)
        {
            if (e.NameWithoutLocale.IsEquivalentTo("Data/Hats"))
                e.Edit(asset =>
                {
                    var hats = asset.AsDictionary<string, string>().Data;
                    foreach (var cap in this.catalog.All)
                    {
                        if (!hats.TryGetValue(cap.ItemId, out string data))
                            continue;
                        var fields = data.Split('/');
                        if (fields.Length < 6)
                            continue;
                        fields[1] = this.Helper.Translation.Get("fit.cap.description");
                        fields[5] = this.Helper.Translation.Get("fit.cap.name");
                        hats[cap.ItemId] = string.Join('/', fields);
                    }
                }, AssetEditPriority.Late);
            if (e.NameWithoutLocale.IsEquivalentTo("Data/Shops"))
                e.Edit(asset =>
                {
                    var shops = asset.AsDictionary<string, ShopData>().Data;
                    var caps = this.catalog.All.OrderBy(cap => cap.ItemId)
                        .Select(cap => cap.QualifiedItemId).ToList();
                    if (caps.Count == 0 || !shops.TryGetValue("SeedShop", out var shop))
                        return;
                    shop.Items.Add(new ShopItemData
                    {
                        Id = this.ModManifest.UniqueID + "/Cap2",
                        RandomItemId = caps,
                        Price = 250,
                        AvailableStock = 1
                    });
                });
        }

        /// <summary>Re-apply saved fittings when the save loads.
        ///
        /// The generated pack on disk always holds the authored default, so a
        /// player's adjustment has to be re-applied to the live models each
        /// session. That is what keeps Reset able to recover the original
        /// exactly, and keeps a re-roll of the same seed reproducible.
        /// </summary>
        private void OnSaveLoaded(object sender, SaveLoadedEventArgs e)
        {
            this.RestoreDefaults();
            this.store.Load();
            if (!this.fs.Available)
                return;
            foreach (var entry in this.store.All)
            {
                var cap = this.CapById(entry.Key);
                if (cap == null)
                    continue;
                var pack = this.fs.GetHatPack(cap.ItemId);
                if (pack == null)
                    continue;
                var fit = entry.Value;
                if (fit == null)
                    continue;
                fit.ItemId = entry.Key;
                if (Math.Abs((long)fit.HatRight) > cap.HatRange
                    || Math.Abs((long)fit.HatDown) > cap.HatRange
                    || (cap.HasMotif && FitRules.TryMoveMotif(fit, cap, 0, 0) != MoveResult.Ok))
                    continue;
                this.fs.ApplyHat(pack, cap, fit);
                if (cap.HasMotif && (fit.MotifRight != 0 || fit.MotifDown != 0))
                    this.fs.ApplyMotif(cap, fit);
            }
        }

        private CapSidecar CapById(string itemId) => this.catalog.GetById(itemId);

        // --- the sewing machine hook ---------------------------------------

        private void OnMenuChanged(object sender, MenuChangedEventArgs e)
        {
            this.fitButton = null;
            this.targetCap = null;
            this.targetPack = null;

            if (e.NewMenu is not TailoringMenu menu)
                return;
            if (!this.fs.Available || this.catalog.Count == 0)
                return;                        // fail open: vanilla, untouched

            // The cap being worn is the fitting target. That needs no ingredient
            // slot, works with hats the tailoring menu would not accept anyway,
            // and means the preview shows the very thing being changed.
            var cap = this.catalog.Get(Game1.player.hat.Value);
            if (cap == null)
                return;                        // not one of ours — stay out of the way
            var pack = this.fs.GetHatPack(cap.ItemId);
            if (pack == null)
                return;

            this.targetCap = cap;
            this.targetPack = pack;
            this.fitButton = new ClickableComponent(
                this.ButtonBounds(menu), "rng_fit");
        }

        private Rectangle ButtonBounds(IClickableMenu menu)
        {
            // Beside the menu when there is room for it, tucked inside the
            // top-right corner when there is not. On a Steam Deck's 1280x800 the
            // outside position falls off the screen entirely.
            int x = menu.xPositionOnScreen + menu.width + 8;
            int y = Math.Max(0, menu.yPositionOnScreen + 32);
            if (x + 260 > Game1.uiViewport.Width)
            {
                x = Math.Max(0, menu.xPositionOnScreen + menu.width - 260);
                y = Math.Max(0, menu.yPositionOnScreen - 96);
            }
            return new Rectangle(x, y, 260, 88);
        }

        private void OnRenderedActiveMenu(object sender, RenderedActiveMenuEventArgs e)
        {
            if (this.fitButton == null || Game1.activeClickableMenu is not TailoringMenu menu)
                return;
            this.fitButton.bounds = this.ButtonBounds(menu);
            var bounds = this.fitButton.bounds;
            IClickableMenu.drawTextureBox(e.SpriteBatch, bounds.X, bounds.Y,
                                          bounds.Width, bounds.Height, Color.White);
            Utility.drawTextWithShadow(
                e.SpriteBatch, this.Helper.Translation.Get("fit.button"), Game1.smallFont,
                new Vector2(bounds.X + 16, bounds.Y + 12),
                Game1.textColor);
            Utility.drawTextWithShadow(
                e.SpriteBatch, this.Helper.Translation.Get("fit.entry.hint"), Game1.smallFont,
                new Vector2(bounds.X + 16, bounds.Y + 44),
                Game1.textColor);
            // The tailoring menu draws its own cursor; ours would double it.
        }

        private void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            if (this.fitButton == null || Game1.activeClickableMenu is not TailoringMenu menu)
                return;
            if (menu.IsBusy())
                return;                        // never interrupt a stitch in progress

            this.fitButton.bounds = this.ButtonBounds(menu);
            Vector2 cursor = e.Cursor.GetScaledScreenPixels();
            bool clicked = e.Button == SButton.MouseLeft
                           && this.fitButton.containsPoint((int)cursor.X, (int)cursor.Y);
            // A controller shortcut, so the button is not mouse-only.
            bool shortcut = e.Button == SButton.LeftTrigger || e.Button == SButton.F;

            if (!clicked && !shortcut)
                return;

            // Suppress ONLY this press, on this frame — never a global block.
            this.Helper.Input.Suppress(e.Button);
            this.RequestOpen(clicked ? "click" : "button");
        }

        /// <summary>Ask for the fitting screen. Does not open it.</summary>
        private void RequestOpen(string by)
        {
            if (this.openRequested)
                return;
            this.openRequested = true;
            this.openRequestedBy = by;
        }

        /// <summary>Honour a pending request, one tick after it was made.</summary>
        private void OnUpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            if (!this.openRequested)
                return;
            this.openRequested = false;
            string by = this.openRequestedBy;
            this.openRequestedBy = null;

            // Re-check everything: a tick has passed, and the menu or the worn
            // hat could have changed in it.
            if (Game1.activeClickableMenu is not TailoringMenu menu || menu.IsBusy())
                return;
            if (this.targetCap == null || this.targetPack == null)
                return;
            var worn = this.catalog.Get(Game1.player.hat.Value);
            if (worn?.ItemId != this.targetCap.ItemId || menu.heldItem != null)
                return;

            this.Monitor.Log($"Opening fitting for {this.targetCap.ItemId} (via {by}).",
                             LogLevel.Trace);
            Game1.playSound("bigSelect");
            Game1.activeClickableMenu = new FittingMenu(
                this.Helper, this.fs, this.store,
                this.sessions.For(this.targetCap.ItemId),
                this.targetCap, this.targetPack, menu);
        }

        private void OnReturnedToTitle(object sender, ReturnedToTitleEventArgs e)
        {
            this.RestoreDefaults();
            this.sessions.Clear();
            this.openRequested = false;
            this.fitButton = null;
            this.targetCap = null;
            this.targetPack = null;
        }

        private void RestoreDefaults()
        {
            if (!this.fs.Available)
                return;
            foreach (var cap in this.catalog.All)
            {
                this.fs.ResetHat(this.fs.GetHatPack(cap.ItemId), cap);
                if (cap.HasMotif)
                    this.fs.ResetMotif(cap);
            }
        }
    }
}
