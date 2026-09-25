using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using Netcode;
using StardewValley;
using StardewValley.Menus;
using StardewValley.Objects;
using xTile.Dimensions;

namespace PhotoTailor;

internal sealed class TailorMenu : MenuWithInventory
{
	[CompilerGenerated]
	private static class _003C_003EO
	{
		public static highlightThisItem _003C0_003E__highlightAllItems;
	}

	private const int MenuWidth = 960;

	private const int MenuHeight = 640;

	private static readonly Color Ink;

	private static readonly Color MutedInk;

	private readonly ModEntry mod;

	private readonly Texture2D menuTexture;

	private readonly Texture2D tailoringTexture;

	private readonly List<ClickableComponent> equipmentSlots = new List<ClickableComponent>();

	private Rectangle quickButton;

	private Rectangle preciseButton;

	private Rectangle clothSlot;

	private Rectangle previewSlot;

	private Item? clothItem;

	private Texture2D? previewTexture;

	private string selectedFileName = "尚未放入照片";

	private string status = "可先选择快速或精确识别；预览不会消耗材料。";

	private bool busy;

	internal int ClothCount
	{
		get
		{
			Item? obj = clothItem;
			if (!(((obj != null) ? obj.QualifiedItemId : null) == "(O)428"))
			{
				return 0;
			}
			return clothItem.Stack;
		}
	}

	public TailorMenu(ModEntry mod)
		: base((highlightThisItem)null, false, false, 0, 0, 0, (ItemExitBehavior)0, false)
	{
		this.mod = mod;
		menuTexture = Game1.content.Load<Texture2D>("Mods/Robin.PhotoTailor/Menu");
		tailoringTexture = Game1.temporaryContent.Load<Texture2D>("LooseSprites\\tailoring");
		LayoutMenu();
	}

	public void SetStatus(string message, bool isBusy = false)
	{
		status = message;
		busy = isBusy;
	}

	public void SetSelectedImage(string path)
	{
		try
		{
			Texture2D? obj = previewTexture;
			if (obj != null)
			{
				((GraphicsResource)obj).Dispose();
			}
			using FileStream fileStream = File.OpenRead(path);
			previewTexture = Texture2D.FromStream(Game1.graphics.GraphicsDevice, (Stream)fileStream);
			selectedFileName = Path.GetFileName(path);
		}
		catch
		{
			previewTexture = null;
			selectedFileName = Path.GetFileName(path);
		}
	}

	internal bool ConsumeCloth(int amount)
	{
		if (amount <= 0)
		{
			return true;
		}
		if (ClothCount < amount || clothItem == null)
		{
			return false;
		}
		Item? obj = clothItem;
		obj.Stack -= amount;
		if (clothItem.Stack <= 0)
		{
			clothItem = null;
		}
		return true;
	}

	public override bool readyToClose()
	{
		if (!busy)
		{
			return ((MenuWithInventory)this).heldItem == null;
		}
		return false;
	}

	public override void receiveLeftClick(int x, int y, bool playSound = true)
	{
		ClickableTextureComponent upperRightCloseButton = ((IClickableMenu)this).upperRightCloseButton;
		if (upperRightCloseButton != null && ((ClickableComponent)upperRightCloseButton).containsPoint(x, y) && ((IClickableMenu)this).readyToClose())
		{
			((IClickableMenu)this).exitThisMenu(playSound);
		}
		else
		{
			if (HandleClothLeftClick(x, y) || (!busy && HandleEquipmentClick(x, y)))
			{
				return;
			}
			if (((Rectangle)(ref quickButton)).Contains(x, y) || ((Rectangle)(ref preciseButton)).Contains(x, y))
			{
				if (busy || ((MenuWithInventory)this).heldItem != null)
				{
					Game1.playSound("cancel", (int?)null);
					return;
				}
				Game1.playSound("bigSelect", (int?)null);
				RecognitionMode mode = (((Rectangle)(ref preciseButton)).Contains(x, y) ? RecognitionMode.Precise : RecognitionMode.Quick);
				mod.BeginImageSelection(this, mode);
			}
			else if (!busy)
			{
				((MenuWithInventory)this).receiveLeftClick(x, y, playSound);
			}
		}
	}

	public override void receiveRightClick(int x, int y, bool playSound = true)
	{
		if (!HandleClothRightClick(x, y) && !busy)
		{
			((MenuWithInventory)this).receiveRightClick(x, y, playSound);
		}
	}

	public override void receiveKeyPress(Keys key)
	{
		//IL_0009: Unknown result type (might be due to invalid IL or missing references)
		if (!busy)
		{
			((IClickableMenu)this).receiveKeyPress(key);
		}
	}

	public override void performHoverAction(int x, int y)
	{
		((MenuWithInventory)this).performHoverAction(x, y);
		ClickableTextureComponent upperRightCloseButton = ((IClickableMenu)this).upperRightCloseButton;
		if (upperRightCloseButton != null)
		{
			upperRightCloseButton.tryHover(x, y, 0.5f);
		}
		if (((Rectangle)(ref clothSlot)).Contains(x, y))
		{
			base.hoveredItem = clothItem;
			base.hoverText = ((clothItem == null) ? $"布料槽：放入 {mod.Config.ClothCost} 块布料" : "缝制时只会消耗所需数量；关闭界面会退回剩余布料。");
			return;
		}
		foreach (ClickableComponent equipmentSlot in equipmentSlots)
		{
			if (equipmentSlot.containsPoint(x, y))
			{
				base.hoveredItem = GetEquippedItem(equipmentSlot.name);
				Item hoveredItem = base.hoveredItem;
				base.hoverText = ((hoveredItem != null) ? hoveredItem.getDescription() : null) ?? EquipmentDisplayName(equipmentSlot.name);
				break;
			}
		}
	}

	public override void gameWindowSizeChanged(Rectangle oldBounds, Rectangle newBounds)
	{
		LayoutMenu();
	}

	protected override void cleanupBeforeExit()
	{
		if (clothItem != null)
		{
			Utility.CollectOrDrop(clothItem, -1);
			clothItem = null;
		}
		Texture2D? obj = previewTexture;
		if (obj != null)
		{
			((GraphicsResource)obj).Dispose();
		}
		previewTexture = null;
		((MenuWithInventory)this).cleanupBeforeExit();
	}

	public override void draw(SpriteBatch b)
	{
		//IL_005c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0061: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_0029: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		//IL_0175: Unknown result type (might be due to invalid IL or missing references)
		if (!Game1.options.showClearBackgrounds)
		{
			Texture2D fadeToBlackRect = Game1.fadeToBlackRect;
			Viewport viewport = Game1.graphics.GraphicsDevice.Viewport;
			b.Draw(fadeToBlackRect, ((Viewport)(ref viewport)).Bounds, Color.Black * 0.68f);
		}
		b.Draw(menuTexture, new Rectangle(((IClickableMenu)this).xPositionOnScreen, ((IClickableMenu)this).yPositionOnScreen, ((IClickableMenu)this).width, ((IClickableMenu)this).height), Color.White);
		DrawPhotoPreview(b);
		DrawClothSlot(b);
		DrawPlayerEquipment(b);
		DrawInformation(b);
		((IClickableMenu)base.inventory).draw(b);
		ClickableTextureComponent upperRightCloseButton = ((IClickableMenu)this).upperRightCloseButton;
		if (upperRightCloseButton != null)
		{
			upperRightCloseButton.draw(b);
		}
		if (!string.IsNullOrWhiteSpace(base.hoverText) && base.hoveredItem == null)
		{
			IClickableMenu.drawHoverText(b, base.hoverText, Game1.smallFont, (((MenuWithInventory)this).heldItem != null) ? 32 : 0, (((MenuWithInventory)this).heldItem != null) ? 32 : 0, -1, (string)null, -1, (string[])null, (Item)null, 0, (string)null, -1, -1, -1, 1f, (CraftingRecipe)null, (IList<Item>)null, (Texture2D)null, (Rectangle?)null, (Color?)null, (Color?)null, 1f, -1, -1);
		}
		else if (base.hoveredItem != null)
		{
			IClickableMenu.drawToolTip(b, base.hoveredItem.getDescription(), base.hoveredItem.DisplayName, base.hoveredItem, ((MenuWithInventory)this).heldItem != null, -1, 0, (string)null, -1, (CraftingRecipe)null, -1, (IList<Item>)null);
		}
		Item heldItem = ((MenuWithInventory)this).heldItem;
		if (heldItem != null)
		{
			heldItem.drawInMenu(b, new Vector2((float)(Game1.getOldMouseX() + 8), (float)(Game1.getOldMouseY() + 8)), 1f);
		}
		if (!Game1.options.hardwareCursor)
		{
			((IClickableMenu)this).drawMouse(b, false, -1);
		}
	}

	private void LayoutMenu()
	{
		//IL_0055: Unknown result type (might be due to invalid IL or missing references)
		//IL_005a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0072: Unknown result type (might be due to invalid IL or missing references)
		//IL_0077: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f7: Expected O, but got Unknown
		//IL_0114: Unknown result type (might be due to invalid IL or missing references)
		//IL_011e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0128: Expected O, but got Unknown
		//IL_013d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0147: Unknown result type (might be due to invalid IL or missing references)
		//IL_0151: Expected O, but got Unknown
		//IL_0166: Unknown result type (might be due to invalid IL or missing references)
		//IL_0170: Unknown result type (might be due to invalid IL or missing references)
		//IL_017a: Expected O, but got Unknown
		//IL_018f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a3: Expected O, but got Unknown
		//IL_00da: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e5: Expected O, but got Unknown
		int num = Math.Max(0, ((Rectangle)(ref Game1.uiViewport)).Width / 2 - 480);
		int num2 = Math.Max(0, ((Rectangle)(ref Game1.uiViewport)).Height / 2 - 320);
		((IClickableMenu)this).initialize(num, num2, 960, 640, true);
		previewSlot = new Rectangle(num + 225, num2 + 78, 124, 117);
		clothSlot = new Rectangle(num + 160, num2 + 260, 73, 73);
		quickButton = new Rectangle(num + 653, num2 + 315, 128, 60);
		preciseButton = new Rectangle(num + 790, num2 + 315, 128, 60);
		int num3 = num + 28;
		int num4 = num2 + 408;
		object obj = _003C_003EO._003C0_003E__highlightAllItems;
		if (obj == null)
		{
			highlightThisItem val = InventoryMenu.highlightAllItems;
			_003C_003EO._003C0_003E__highlightAllItems = val;
			obj = (object)val;
		}
		base.inventory = new InventoryMenu(num3, num4, false, (IList<Item>)null, (highlightThisItem)obj, 36, 3, 11, -3, false);
		equipmentSlots.Clear();
		equipmentSlots.Add(new ClickableComponent(new Rectangle(num + 40, num2 + 112, 64, 56), "Hat"));
		equipmentSlots.Add(new ClickableComponent(new Rectangle(num + 40, num2 + 170, 64, 56), "Shirt"));
		equipmentSlots.Add(new ClickableComponent(new Rectangle(num + 40, num2 + 229, 64, 55), "Pants"));
		equipmentSlots.Add(new ClickableComponent(new Rectangle(num + 40, num2 + 287, 64, 55), "Boots"));
	}

	private void DrawPhotoPreview(SpriteBatch b)
	{
		//IL_00cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_0101: Unknown result type (might be due to invalid IL or missing references)
		//IL_010c: Unknown result type (might be due to invalid IL or missing references)
		//IL_011a: Unknown result type (might be due to invalid IL or missing references)
		//IL_011f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0129: Unknown result type (might be due to invalid IL or missing references)
		//IL_0083: Unknown result type (might be due to invalid IL or missing references)
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b4: Unknown result type (might be due to invalid IL or missing references)
		if (previewTexture != null)
		{
			float num = Math.Min((float)previewSlot.Width / (float)previewTexture.Width, (float)previewSlot.Height / (float)previewTexture.Height);
			int num2 = Math.Max(1, (int)Math.Round((float)previewTexture.Width * num));
			int num3 = Math.Max(1, (int)Math.Round((float)previewTexture.Height * num));
			Rectangle val = default(Rectangle);
			((Rectangle)(ref val))._002Ector(((Rectangle)(ref previewSlot)).Center.X - num2 / 2, ((Rectangle)(ref previewSlot)).Center.Y - num3 / 2, num2, num3);
			b.Draw(previewTexture, val, Color.White);
		}
		else
		{
			string text = "照片";
			Vector2 val2 = Game1.smallFont.MeasureString(text);
			b.DrawString(Game1.smallFont, text, new Vector2((float)((Rectangle)(ref previewSlot)).Center.X - val2.X / 2f, (float)((Rectangle)(ref previewSlot)).Center.Y - val2.Y / 2f), Color.White * 0.72f);
		}
	}

	private void DrawClothSlot(SpriteBatch b)
	{
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		//IL_005b: Unknown result type (might be due to invalid IL or missing references)
		//IL_006d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Unknown result type (might be due to invalid IL or missing references)
		//IL_008b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0096: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		if (clothItem != null)
		{
			clothItem.drawInMenu(b, new Vector2((float)(clothSlot.X + 5), (float)(clothSlot.Y + 5)), 0.98f, 1f, 0.98f, (StackDrawType)1, Color.White, true);
			return;
		}
		Vector2 val = Game1.tinyFont.MeasureString("布料");
		b.DrawString(Game1.tinyFont, "布料", new Vector2((float)((Rectangle)(ref clothSlot)).Center.X - val.X / 2f, (float)((Rectangle)(ref clothSlot)).Center.Y - val.Y / 2f), new Color(141, 78, 48) * 0.55f);
	}

	private void DrawPlayerEquipment(SpriteBatch b)
	{
		//IL_001f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0084: Unknown result type (might be due to invalid IL or missing references)
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_0120: Unknown result type (might be due to invalid IL or missing references)
		//IL_0122: Unknown result type (might be due to invalid IL or missing references)
		//IL_0123: Unknown result type (might be due to invalid IL or missing references)
		//IL_0124: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0101: Unknown result type (might be due to invalid IL or missing references)
		//IL_0180: Unknown result type (might be due to invalid IL or missing references)
		//IL_0185: Unknown result type (might be due to invalid IL or missing references)
		//IL_0198: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01df: Unknown result type (might be due to invalid IL or missing references)
		//IL_0155: Unknown result type (might be due to invalid IL or missing references)
		//IL_015a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0160: Unknown result type (might be due to invalid IL or missing references)
		//IL_016a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0110: Unknown result type (might be due to invalid IL or missing references)
		//IL_0115: Unknown result type (might be due to invalid IL or missing references)
		//IL_0119: Unknown result type (might be due to invalid IL or missing references)
		//IL_011e: Unknown result type (might be due to invalid IL or missing references)
		Game1.player.FarmerRenderer.drawMiniPortrat(b, new Vector2((float)(((IClickableMenu)this).xPositionOnScreen + 38), (float)(((IClickableMenu)this).yPositionOnScreen + 29)), 0.91f, 4f, 2, Game1.player, 1f);
		foreach (ClickableComponent equipmentSlot in equipmentSlots)
		{
			Item equippedItem = GetEquippedItem(equipmentSlot.name);
			if (equippedItem != null)
			{
				equippedItem.drawInMenu(b, new Vector2((float)(equipmentSlot.bounds.X + 5), (float)(equipmentSlot.bounds.Y + 1)), 0.82f, 1f, 0.91f, (StackDrawType)0, Color.White, true);
				continue;
			}
			Rectangle val = (Rectangle)(equipmentSlot.name switch
			{
				"Hat" => new Rectangle(48, 208, 16, 16), 
				"Shirt" => new Rectangle(32, 208, 16, 16), 
				"Pants" => new Rectangle(16, 208, 16, 16), 
				_ => Rectangle.Empty, 
			});
			if (val != Rectangle.Empty)
			{
				b.Draw(tailoringTexture, new Rectangle(equipmentSlot.bounds.X + 6, equipmentSlot.bounds.Y + 1, 52, 52), (Rectangle?)val, Color.White * 0.65f);
				continue;
			}
			Vector2 val2 = Game1.smallFont.MeasureString("鞋");
			b.DrawString(Game1.smallFont, "鞋", new Vector2((float)((Rectangle)(ref equipmentSlot.bounds)).Center.X - val2.X / 2f, (float)((Rectangle)(ref equipmentSlot.bounds)).Center.Y - val2.Y / 2f), Color.White * 0.62f);
		}
	}

	private void DrawInformation(SpriteBatch b)
	{
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_002f: Unknown result type (might be due to invalid IL or missing references)
		//IL_005d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_00da: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_0142: Unknown result type (might be due to invalid IL or missing references)
		//IL_0150: Unknown result type (might be due to invalid IL or missing references)
		//IL_019c: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0207: Unknown result type (might be due to invalid IL or missing references)
		//IL_020c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0243: Unknown result type (might be due to invalid IL or missing references)
		//IL_0251: Unknown result type (might be due to invalid IL or missing references)
		//IL_025b: Unknown result type (might be due to invalid IL or missing references)
		//IL_029d: Unknown result type (might be due to invalid IL or missing references)
		//IL_02a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ac: Unknown result type (might be due to invalid IL or missing references)
		int num = ((IClickableMenu)this).xPositionOnScreen + 651;
		int num2 = 275;
		b.DrawString(Game1.dialogueFont, "照片裁缝", new Vector2((float)num, (float)(((IClickableMenu)this).yPositionOnScreen + 42)), Ink);
		string text = "快速识别会自动分析；精确识别可放大并框选多件衣物。预览免费，确认缝制才扣材料。";
		b.DrawString(Game1.smallFont, Game1.parseText(text, Game1.smallFont, num2), new Vector2((float)num, (float)(((IClickableMenu)this).yPositionOnScreen + 92)), MutedInk);
		b.DrawString(Game1.smallFont, $"材料槽 {ClothCount}/{mod.Config.ClothCost} 块布料", new Vector2((float)num, (float)(((IClickableMenu)this).yPositionOnScreen + 191)), Ink);
		b.DrawString(Game1.smallFont, $"金币 {mod.Config.GoldCost:N0}g", new Vector2((float)num, (float)(((IClickableMenu)this).yPositionOnScreen + 221)), new Color(141, 78, 48));
		string text2 = (busy ? (status + BusyDots()) : status);
		b.DrawString(Game1.tinyFont, Game1.parseText(text2, Game1.tinyFont, num2), new Vector2((float)num, (float)(((IClickableMenu)this).yPositionOnScreen + 253)), MutedInk);
		string label = (busy ? "识别中" : "快速识别");
		string label2 = (busy ? "请稍候" : "精确识别");
		Color color = (Color)(busy ? Color.Gray : new Color(105, 46, 61));
		DrawCenteredButtonLabel(b, label, quickButton, color);
		DrawCenteredButtonLabel(b, label2, preciseButton, color);
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref quickButton)).Right + 3, quickButton.Y + 9, 3, quickButton.Height - 18), new Color(163, 83, 101) * 0.6f);
		if (previewTexture != null)
		{
			string text3 = Game1.parseText(selectedFileName, Game1.tinyFont, 230);
			b.DrawString(Game1.tinyFont, text3, new Vector2((float)(num + 8), (float)(((IClickableMenu)this).yPositionOnScreen + 382)), MutedInk * 0.85f);
		}
	}

	private bool HandleEquipmentClick(int x, int y)
	{
		//IL_0128: Unknown result type (might be due to invalid IL or missing references)
		//IL_01aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b0: Invalid comparison between Unknown and I4
		ClickableComponent val = equipmentSlots.FirstOrDefault((ClickableComponent component) => component.containsPoint(x, y));
		if (val == null)
		{
			return false;
		}
		switch (val.name)
		{
		case "Hat":
			if (((MenuWithInventory)this).heldItem == null)
			{
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Hat>((Hat)null, Game1.player.hat);
			}
			else
			{
				Item heldItem4 = ((MenuWithInventory)this).heldItem;
				Hat val5 = (Hat)(object)((heldItem4 is Hat) ? heldItem4 : null);
				if (val5 == null)
				{
					return RejectEquipment();
				}
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Hat>(val5, Game1.player.hat);
			}
			Game1.playSound("grassyStep", (int?)null);
			break;
		case "Shirt":
			if (((MenuWithInventory)this).heldItem == null)
			{
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Clothing>((Clothing)null, Game1.player.shirtItem);
			}
			else
			{
				Item heldItem2 = ((MenuWithInventory)this).heldItem;
				Clothing val3 = (Clothing)(object)((heldItem2 is Clothing) ? heldItem2 : null);
				if (val3 == null || (int)((NetFieldBase<ClothesType, NetEnum<ClothesType>>)(object)val3.clothesType).Value != 0)
				{
					return RejectEquipment();
				}
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Clothing>(val3, Game1.player.shirtItem);
			}
			Game1.playSound("sandyStep", (int?)null);
			break;
		case "Pants":
			if (((MenuWithInventory)this).heldItem == null)
			{
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Clothing>((Clothing)null, Game1.player.pantsItem);
			}
			else
			{
				Item heldItem3 = ((MenuWithInventory)this).heldItem;
				Clothing val4 = (Clothing)(object)((heldItem3 is Clothing) ? heldItem3 : null);
				if (val4 == null || (int)((NetFieldBase<ClothesType, NetEnum<ClothesType>>)(object)val4.clothesType).Value != 1)
				{
					return RejectEquipment();
				}
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Clothing>(val4, Game1.player.pantsItem);
			}
			Game1.playSound("sandyStep", (int?)null);
			break;
		case "Boots":
			if (((MenuWithInventory)this).heldItem == null)
			{
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Boots>((Boots)null, Game1.player.boots);
			}
			else
			{
				Item heldItem = ((MenuWithInventory)this).heldItem;
				Boots val2 = (Boots)(object)((heldItem is Boots) ? heldItem : null);
				if (val2 == null)
				{
					return RejectEquipment();
				}
				((MenuWithInventory)this).heldItem = (Item)(object)Game1.player.Equip<Boots>(val2, Game1.player.boots);
			}
			Game1.playSound("sandyStep", (int?)null);
			break;
		}
		Game1.player.FarmerRenderer.MarkSpriteDirty();
		return true;
	}

	private bool HandleClothLeftClick(int x, int y)
	{
		if (!((Rectangle)(ref clothSlot)).Contains(x, y))
		{
			return false;
		}
		if (busy)
		{
			Game1.playSound("cancel", (int?)null);
			return true;
		}
		if (((MenuWithInventory)this).heldItem == null)
		{
			if (clothItem == null)
			{
				Game1.playSound("cancel", (int?)null);
				return true;
			}
			((MenuWithInventory)this).heldItem = clothItem;
			clothItem = null;
			status = "布料已取回。放入布料后才能开始缝制。";
			Game1.playSound("dwop", (int?)null);
			return true;
		}
		if (((MenuWithInventory)this).heldItem.QualifiedItemId != "(O)428")
		{
			status = "这个材料槽只接受布料。";
			Game1.playSound("cancel", (int?)null);
			return true;
		}
		Item heldItem = ((MenuWithInventory)this).heldItem;
		Item heldItem2 = clothItem;
		clothItem = heldItem;
		((MenuWithInventory)this).heldItem = heldItem2;
		status = "布料已放入。现在可以选择穿搭照片。";
		Game1.playSound("dwop", (int?)null);
		return true;
	}

	private bool HandleClothRightClick(int x, int y)
	{
		if (!((Rectangle)(ref clothSlot)).Contains(x, y))
		{
			return false;
		}
		if (busy)
		{
			Game1.playSound("cancel", (int?)null);
			return true;
		}
		if (((MenuWithInventory)this).heldItem == null && clothItem != null)
		{
			((MenuWithInventory)this).heldItem = clothItem.getOne();
			((MenuWithInventory)this).heldItem.Stack = 1;
			Item? obj = clothItem;
			int stack = obj.Stack;
			obj.Stack = stack - 1;
			if (clothItem.Stack <= 0)
			{
				clothItem = null;
			}
			status = ((clothItem == null) ? "布料已取回。放入布料后才能开始缝制。" : "已从材料槽取回一块布料。");
			Game1.playSound("dwop", (int?)null);
			return true;
		}
		Item heldItem = ((MenuWithInventory)this).heldItem;
		if (((heldItem != null) ? heldItem.QualifiedItemId : null) == "(O)428" && clothItem == null)
		{
			clothItem = ((MenuWithInventory)this).heldItem.getOne();
			clothItem.Stack = 1;
			Item heldItem2 = ((MenuWithInventory)this).heldItem;
			int stack = heldItem2.Stack;
			heldItem2.Stack = stack - 1;
			if (((MenuWithInventory)this).heldItem.Stack <= 0)
			{
				((MenuWithInventory)this).heldItem = null;
			}
			status = "布料已放入。现在可以选择穿搭照片。";
			Game1.playSound("dwop", (int?)null);
			return true;
		}
		if (((MenuWithInventory)this).heldItem != null && ((MenuWithInventory)this).heldItem.QualifiedItemId != "(O)428")
		{
			status = "这个材料槽只接受布料。";
		}
		Game1.playSound("cancel", (int?)null);
		return true;
	}

	private static bool RejectEquipment()
	{
		Game1.playSound("cancel", (int?)null);
		return true;
	}

	private static Item? GetEquippedItem(string name)
	{
		return (Item?)(name switch
		{
			"Hat" => ((NetFieldBase<Hat, NetRef<Hat>>)(object)Game1.player.hat).Value, 
			"Shirt" => ((NetFieldBase<Clothing, NetRef<Clothing>>)(object)Game1.player.shirtItem).Value, 
			"Pants" => ((NetFieldBase<Clothing, NetRef<Clothing>>)(object)Game1.player.pantsItem).Value, 
			"Boots" => ((NetFieldBase<Boots, NetRef<Boots>>)(object)Game1.player.boots).Value, 
			_ => null, 
		});
	}

	private static string EquipmentDisplayName(string name)
	{
		return name switch
		{
			"Hat" => "帽子槽", 
			"Shirt" => "上衣槽", 
			"Pants" => "裤装槽", 
			"Boots" => "鞋子槽", 
			_ => "装备槽", 
		};
	}

	private static string BusyDots()
	{
		return new string('.', (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 400.0) % 4);
	}

	private static void DrawCenteredButtonLabel(SpriteBatch b, string label, Rectangle bounds, Color color)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0011: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0046: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_0071: Unknown result type (might be due to invalid IL or missing references)
		//IL_0076: Unknown result type (might be due to invalid IL or missing references)
		//IL_007c: Unknown result type (might be due to invalid IL or missing references)
		Vector2 val = Game1.smallFont.MeasureString(label);
		float num = Math.Min(1f, (float)(bounds.Width - 10) / Math.Max(1f, val.X));
		b.DrawString(Game1.smallFont, label, new Vector2((float)((Rectangle)(ref bounds)).Center.X - val.X * num / 2f, (float)((Rectangle)(ref bounds)).Center.Y - val.Y * num / 2f), color, 0f, Vector2.Zero, num, (SpriteEffects)0, 1f);
	}

	static TailorMenu()
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		Ink = new Color(34, 55, 82);
		MutedInk = new Color(61, 88, 117);
	}
}
