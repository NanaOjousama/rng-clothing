using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;
using xTile.Dimensions;

namespace PhotoTailor;

internal sealed class RecognitionPreviewMenu : IClickableMenu
{
	private static readonly Color Ink;

	private static readonly Color MutedInk;

	private static readonly Color[] PreviewCropColors;

	private readonly ModEntry mod;

	private readonly TailorMenu parent;

	private readonly string imagePath;

	private readonly OutfitSpec outfit;

	private readonly List<GarmentCropSelection> selections;

	private readonly RecognitionPreviewResourceSet<Texture2D> resources = new RecognitionPreviewResourceSet<Texture2D>();

	private readonly Texture2D tailoringTextures;

	private readonly OutfitRenderPreview? renderedPreview;

	private RecognitionPreviewLayoutPlan layout;

	private Rectangle confirmButton;

	private Rectangle adjustButton;

	private Rectangle cancelButton;

	private int scrollOffset;

	private bool transitioning;

	private bool disposed;

	private bool PartsReady
	{
		get
		{
			if (renderedPreview != null && outfit.Items.Count > 0 && resources.Parts.Count == outfit.Items.Count)
			{
				return resources.Artworks.Count == outfit.Items.Count;
			}
			return false;
		}
	}

	private bool CanConfirm
	{
		get
		{
			if (PartsReady)
			{
				return layout.IsUsable;
			}
			return false;
		}
	}

	internal RecognitionPreviewMenu(ModEntry mod, TailorMenu parent, string imagePath, OutfitSpec outfit, IReadOnlyList<GarmentCropSelection>? selections = null)
		: base(0, 0, ((Rectangle)(ref Game1.uiViewport)).Width, ((Rectangle)(ref Game1.uiViewport)).Height, false)
	{
		this.mod = mod;
		this.parent = parent;
		this.imagePath = imagePath;
		this.outfit = outfit;
		this.selections = selections?.Select(CloneSelection).ToList() ?? new List<GarmentCropSelection>();
		tailoringTextures = Game1.temporaryContent.Load<Texture2D>("LooseSprites\\tailoring");
		using FileStream fileStream = File.OpenRead(imagePath);
		resources.ReplaceSource(Texture2D.FromStream(Game1.graphics.GraphicsDevice, (Stream)fileStream));
		try
		{
			renderedPreview = mod.PopulateRecognitionPreview(outfit, resources);
		}
		catch (Exception error)
		{
			resources.ReportNonFatalFailure("成品", error);
			mod.LogPreviewWarning("无法创建识别成品预览。", error);
		}
		Layout();
	}

	public override bool readyToClose()
	{
		return false;
	}

	public override void receiveLeftClick(int x, int y, bool playSound = true)
	{
		if (transitioning)
		{
			return;
		}
		if (((Rectangle)(ref confirmButton)).Contains(x, y))
		{
			if (!CanConfirm)
			{
				Game1.playSound("cancel", (int?)null);
				return;
			}
			transitioning = true;
			DisposeResources();
			mod.ConfirmRecognizedOutfit(parent, outfit, renderedPreview);
		}
		else if (((Rectangle)(ref adjustButton)).Contains(x, y))
		{
			PhotoCropMenu activeClickableMenu;
			try
			{
				activeClickableMenu = new PhotoCropMenu(mod, parent, imagePath, (selections.Count > 0) ? selections : null);
			}
			catch (Exception error)
			{
				resources.ReportNonFatalFailure("重新打开照片", error);
				mod.LogPreviewWarning("无法重新打开精确框选页。", error);
				Game1.playSound("cancel", (int?)null);
				return;
			}
			transitioning = true;
			DisposeResources();
			Game1.activeClickableMenu = (IClickableMenu)(object)activeClickableMenu;
			Game1.playSound("bigSelect", (int?)null);
		}
		else if (((Rectangle)(ref cancelButton)).Contains(x, y))
		{
			ReturnToParent();
		}
	}

	public override void receiveScrollWheelAction(int direction)
	{
		if (!transitioning && layout.IsUsable)
		{
			int num = Math.Max(1, layout.OutputVisibleCapacity);
			int max = Math.Max(0, outfit.Items.Count - num);
			scrollOffset = Math.Clamp(scrollOffset + ((direction < 0) ? 1 : (-1)), 0, max);
		}
	}

	public override void receiveKeyPress(Keys key)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0003: Invalid comparison between Unknown and I4
		if ((int)key == 27)
		{
			ReturnToParent();
		}
	}

	public override void gameWindowSizeChanged(Rectangle oldBounds, Rectangle newBounds)
	{
		base.width = ((Rectangle)(ref Game1.uiViewport)).Width;
		base.height = ((Rectangle)(ref Game1.uiViewport)).Height;
		Layout();
	}

	protected override void cleanupBeforeExit()
	{
		DisposeResources();
		((IClickableMenu)this).cleanupBeforeExit();
	}

	public override void draw(SpriteBatch b)
	{
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		//IL_0018: Unknown result type (might be due to invalid IL or missing references)
		//IL_001d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_0050: Unknown result type (might be due to invalid IL or missing references)
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0076: Unknown result type (might be due to invalid IL or missing references)
		Texture2D fadeToBlackRect = Game1.fadeToBlackRect;
		Viewport viewport = Game1.graphics.GraphicsDevice.Viewport;
		b.Draw(fadeToBlackRect, ((Viewport)(ref viewport)).Bounds, Color.Black * 0.82f);
		if (layout.IsUsable)
		{
			DrawUsablePreview(b);
		}
		else
		{
			DrawConstrainedPreview(b);
		}
		DrawButton(b, cancelButton, "取消");
		DrawButton(b, adjustButton, "放大并调整框");
		DrawButton(b, confirmButton, CanConfirm ? "确认缝制" : "预览未就绪", CanConfirm, accent: true);
		if (!Game1.options.hardwareCursor)
		{
			((IClickableMenu)this).drawMouse(b, false, -1);
		}
	}

	private void Layout()
	{
		//IL_0053: Unknown result type (might be due to invalid IL or missing references)
		//IL_0058: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0084: Unknown result type (might be due to invalid IL or missing references)
		base.width = ((Rectangle)(ref Game1.uiViewport)).Width;
		base.height = ((Rectangle)(ref Game1.uiViewport)).Height;
		layout = RecognitionPreviewLayoutEngine.Calculate(base.width, base.height, outfit.Items.Count);
		cancelButton = ToRectangle(layout.CancelButton);
		adjustButton = ToRectangle(layout.AdjustButton);
		confirmButton = ToRectangle(layout.ConfirmButton);
		int max = Math.Max(0, outfit.Items.Count - Math.Max(1, layout.OutputVisibleCapacity));
		scrollOffset = Math.Clamp(scrollOffset, 0, max);
	}

	private void DrawUsablePreview(SpriteBatch b)
	{
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_0023: Unknown result type (might be due to invalid IL or missing references)
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0054: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_0073: Unknown result type (might be due to invalid IL or missing references)
		//IL_007d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0082: Unknown result type (might be due to invalid IL or missing references)
		//IL_0098: Unknown result type (might be due to invalid IL or missing references)
		//IL_009d: Unknown result type (might be due to invalid IL or missing references)
		//IL_009e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_0123: Unknown result type (might be due to invalid IL or missing references)
		//IL_0128: Unknown result type (might be due to invalid IL or missing references)
		//IL_012d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0132: Unknown result type (might be due to invalid IL or missing references)
		//IL_0134: Unknown result type (might be due to invalid IL or missing references)
		//IL_0140: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_018b: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01cc: Unknown result type (might be due to invalid IL or missing references)
		//IL_01dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d6: Unknown result type (might be due to invalid IL or missing references)
		Rectangle val = ToRectangle(layout.PhotoPanel);
		Rectangle val2 = ToRectangle(layout.OutputPanel);
		DrawPanel(b, val);
		DrawPanel(b, val2);
		b.DrawString(Game1.smallFont, "照片与框选", new Vector2((float)(val.X + 16), (float)(val.Y + 12)), Ink);
		b.DrawString(Game1.smallFont, "完整高像素画稿 → 原版缝制结果", new Vector2((float)(val2.X + 16), (float)(val2.Y + 11)), Ink);
		string text = "画稿先完成，再投射到原版动画版型";
		Vector2 val3 = Game1.tinyFont.MeasureString(text);
		if (val3.X + 36f < (float)val2.Width && outfit.Items.Count <= layout.OutputVisibleCapacity)
		{
			b.DrawString(Game1.tinyFont, text, new Vector2((float)((Rectangle)(ref val2)).Right - val3.X - 16f, (float)(val2.Y + 17)), MutedInk);
		}
		Texture2D source = resources.Source;
		if (source != null)
		{
			Rectangle val4 = Fit(source, ToRectangle(layout.PhotoViewport));
			b.Draw(source, val4, Color.White);
			DrawCropBoxes(b, val4);
		}
		DrawOutputPreviews(b);
		string text2 = (PartsReady ? "以上就是确认后获得的衣物；确认前不会扣除布料或金币。" : (resources.NonFatalWarning ?? "衣物小图尚未完成，请返回调整框后重试。"));
		text2 = text2.Replace('\r', ' ').Replace('\n', ' ');
		Vector2 val5 = default(Vector2);
		((Vector2)(ref val5))._002Ector((float)(val2.X + 16), (float)(((Rectangle)(ref val2)).Bottom - Game1.tinyFont.LineSpacing - 8));
		b.DrawString(Game1.tinyFont, TrimToWidth(text2, Math.Max(40, val2.Width - 32)), val5, PartsReady ? MutedInk : Color.DarkRed);
	}

	private void DrawConstrainedPreview(SpriteBatch b)
	{
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_0012: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0049: Unknown result type (might be due to invalid IL or missing references)
		//IL_0053: Unknown result type (might be due to invalid IL or missing references)
		//IL_0058: Unknown result type (might be due to invalid IL or missing references)
		Rectangle val = ToRectangle(layout.ConstrainedMessage);
		DrawPanel(b, val);
		string text = "窗口太小，暂时无法完整显示原版缝纫机式衣物小图。\n请放大游戏窗口，或返回调整框。";
		b.DrawString(Game1.smallFont, Game1.parseText(text, Game1.smallFont, Math.Max(100, val.Width - 32)), new Vector2((float)(val.X + 16), (float)(val.Y + 16)), Ink);
	}

	private void DrawOutputPreviews(SpriteBatch b)
	{
		//IL_001d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0022: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Unknown result type (might be due to invalid IL or missing references)
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_009e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_010f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0128: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0142: Unknown result type (might be due to invalid IL or missing references)
		//IL_0149: Unknown result type (might be due to invalid IL or missing references)
		//IL_0152: Unknown result type (might be due to invalid IL or missing references)
		//IL_0164: Unknown result type (might be due to invalid IL or missing references)
		//IL_016c: Unknown result type (might be due to invalid IL or missing references)
		//IL_03be: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_0465: Unknown result type (might be due to invalid IL or missing references)
		//IL_0470: Unknown result type (might be due to invalid IL or missing references)
		//IL_0475: Unknown result type (might be due to invalid IL or missing references)
		//IL_0198: Unknown result type (might be due to invalid IL or missing references)
		//IL_018e: Unknown result type (might be due to invalid IL or missing references)
		//IL_01af: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0230: Unknown result type (might be due to invalid IL or missing references)
		//IL_0239: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Unknown result type (might be due to invalid IL or missing references)
		//IL_0221: Unknown result type (might be due to invalid IL or missing references)
		//IL_0272: Unknown result type (might be due to invalid IL or missing references)
		//IL_027c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0286: Unknown result type (might be due to invalid IL or missing references)
		//IL_028b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0332: Unknown result type (might be due to invalid IL or missing references)
		//IL_0345: Unknown result type (might be due to invalid IL or missing references)
		//IL_035c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0361: Unknown result type (might be due to invalid IL or missing references)
		if (outfit.Items.Count == 0)
		{
			Rectangle val = ToRectangle(layout.OutputViewport);
			b.DrawString(Game1.tinyFont, "没有识别到衣物，请返回调整框。", new Vector2((float)(val.X + 4), (float)(val.Y + 4)), Color.DarkRed);
			return;
		}
		Rectangle val3 = default(Rectangle);
		Rectangle val4 = default(Rectangle);
		Rectangle val5 = default(Rectangle);
		for (int i = 0; i < layout.OutputCells.Count; i++)
		{
			int num = scrollOffset + i;
			if (num >= outfit.Items.Count)
			{
				break;
			}
			GarmentSpec garmentSpec = outfit.Items[num];
			Rectangle val2 = ToRectangle(layout.OutputCells[i]);
			int lineSpacing = Game1.tinyFont.LineSpacing;
			((Rectangle)(ref val3))._002Ector(val2.X + 3, val2.Y + 2, Math.Max(1, val2.Width - 6), Math.Max(1, val2.Height - lineSpacing - 6));
			int num2 = Math.Min(64, Math.Max(42, val3.Height - 8));
			((Rectangle)(ref val4))._002Ector(((Rectangle)(ref val3)).Right - num2 - 4, ((Rectangle)(ref val3)).Center.Y - num2 / 2, num2, num2);
			int num3 = Math.Max(1, val4.X - val3.X - 7);
			((Rectangle)(ref val5))._002Ector(val3.X, val3.Y, num3, val3.Height);
			b.Draw(Game1.staminaRect, val5, new Color(77, 88, 98));
			if (resources.Artworks.TryGetValue(num, out Texture2D value))
			{
				DrawPixelArtwork(b, value, val5);
			}
			else
			{
				DrawPlaceholder(b, val5, "无画稿");
			}
			b.DrawString(Game1.tinyFont, "画稿", new Vector2((float)(val5.X + 3), (float)(val5.Y + 2)), Color.White * 0.88f);
			b.Draw(tailoringTextures, val4, (Rectangle?)new Rectangle(0, 208, 16, 16), Color.White);
			if (resources.Parts.TryGetValue(num, out Texture2D value2))
			{
				GarmentMenuPreviewRenderer.Draw(b, value2, garmentSpec.Category, val4);
			}
			else
			{
				DrawPlaceholder(b, new Rectangle(val4.X + 5, val4.Y + 5, Math.Max(1, num2 - 10), Math.Max(1, num2 - 10)), "无小图");
			}
			b.DrawString(Game1.tinyFont, "成品", new Vector2((float)(val4.X + 3), (float)(val4.Y + 2)), MutedInk);
			string renderRole = garmentSpec.RenderRole;
			string text = ((renderRole == "upper") ? "上装部件" : ((!(renderRole == "lower")) ? CategoryLabel(garmentSpec.Category) : "下装部件"));
			string value3 = text;
			string text2 = $"{num + 1}. {value3} {garmentSpec.Name}";
			b.DrawString(Game1.tinyFont, TrimToWidth(text2, Math.Max(20, val2.Width - 6)), new Vector2((float)(val2.X + 3), (float)(((Rectangle)(ref val2)).Bottom - lineSpacing - 2)), Ink);
		}
		if (Math.Max(0, outfit.Items.Count - Math.Max(1, layout.OutputVisibleCapacity)) > 0)
		{
			Rectangle val6 = ToRectangle(layout.OutputPanel);
			string text3 = $"滚轮切换  {scrollOffset + 1}–{Math.Min(outfit.Items.Count, scrollOffset + layout.OutputVisibleCapacity)}/{outfit.Items.Count}";
			b.DrawString(Game1.tinyFont, text3, new Vector2((float)(((Rectangle)(ref val6)).Right - 184), (float)(val6.Y + 16)), MutedInk);
		}
	}

	private void DrawCropBoxes(SpriteBatch b, Rectangle image)
	{
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_0022: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0038: Unknown result type (might be due to invalid IL or missing references)
		//IL_0050: Unknown result type (might be due to invalid IL or missing references)
		//IL_006c: Unknown result type (might be due to invalid IL or missing references)
		//IL_008d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_0095: Unknown result type (might be due to invalid IL or missing references)
		//IL_00da: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f1: Unknown result type (might be due to invalid IL or missing references)
		Rectangle val = default(Rectangle);
		for (int i = 0; i < selections.Count; i++)
		{
			GarmentCropSelection garmentCropSelection = selections[i];
			((Rectangle)(ref val))._002Ector(image.X + (int)(garmentCropSelection.Left * (double)image.Width), image.Y + (int)(garmentCropSelection.Top * (double)image.Height), Math.Max(1, (int)((garmentCropSelection.Right - garmentCropSelection.Left) * (double)image.Width)), Math.Max(1, (int)((garmentCropSelection.Bottom - garmentCropSelection.Top) * (double)image.Height)));
			Color val2 = PreviewCropColors[i % PreviewCropColors.Length];
			DrawBorder(b, val, val2, 3);
			b.DrawString(Game1.tinyFont, $"{i + 1} {CategoryLabel(garmentCropSelection.CategoryHint)}", new Vector2((float)(val.X + 4), (float)(val.Y + 3)), val2);
		}
	}

	private void ReturnToParent()
	{
		if (!transitioning)
		{
			transitioning = true;
			DisposeResources();
			parent.SetStatus("已取消识别预览，没有消耗材料。");
			Game1.activeClickableMenu = (IClickableMenu)(object)parent;
			Game1.playSound("bigDeSelect", (int?)null);
		}
	}

	private void DisposeResources()
	{
		if (disposed)
		{
			return;
		}
		disposed = true;
		try
		{
			resources.Dispose();
		}
		catch (Exception error)
		{
			mod.LogPreviewWarning("释放识别预览纹理时发生错误。", error);
		}
	}

	private static Rectangle Fit(Texture2D texture, Rectangle area)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_0058: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		float num = Math.Min((float)area.Width / (float)texture.Width, (float)area.Height / (float)texture.Height);
		int num2 = Math.Max(1, (int)((float)texture.Width * num));
		int num3 = Math.Max(1, (int)((float)texture.Height * num));
		return new Rectangle(((Rectangle)(ref area)).Center.X - num2 / 2, ((Rectangle)(ref area)).Center.Y - num3 / 2, num2, num3);
	}

	private static void DrawPixelArtwork(SpriteBatch batch, Texture2D texture, Rectangle area)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_0070: Unknown result type (might be due to invalid IL or missing references)
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0046: Unknown result type (might be due to invalid IL or missing references)
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f7: Unknown result type (might be due to invalid IL or missing references)
		int num = Math.Min(area.Width / Math.Max(1, texture.Width), area.Height / Math.Max(1, texture.Height));
		Rectangle val = default(Rectangle);
		if (num >= 1)
		{
			int num2 = texture.Width * num;
			int num3 = texture.Height * num;
			((Rectangle)(ref val))._002Ector(((Rectangle)(ref area)).Center.X - num2 / 2, ((Rectangle)(ref area)).Center.Y - num3 / 2, num2, num3);
		}
		else
		{
			float num4 = Math.Min((float)area.Width / (float)texture.Width, (float)area.Height / (float)texture.Height);
			int num5 = Math.Max(1, (int)Math.Floor((float)texture.Width * num4));
			int num6 = Math.Max(1, (int)Math.Floor((float)texture.Height * num4));
			((Rectangle)(ref val))._002Ector(((Rectangle)(ref area)).Center.X - num5 / 2, ((Rectangle)(ref area)).Center.Y - num6 / 2, num5, num6);
		}
		batch.Draw(texture, val, Color.White);
	}

	private static void DrawButton(SpriteBatch b, Rectangle bounds, string label, bool enabled = true, bool accent = false)
	{
		//IL_0042: Unknown result type (might be due to invalid IL or missing references)
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_0058: Unknown result type (might be due to invalid IL or missing references)
		//IL_005d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_006f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0075: Unknown result type (might be due to invalid IL or missing references)
		//IL_008c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0091: Unknown result type (might be due to invalid IL or missing references)
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cc: Unknown result type (might be due to invalid IL or missing references)
		//IL_00dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f7: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_010c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0116: Unknown result type (might be due to invalid IL or missing references)
		Color val = ((!enabled) ? new Color(156, 161, 166) : (accent ? new Color(244, 166, 178) : new Color(255, 246, 224)));
		IClickableMenu.drawTextureBox(b, Game1.menuTexture, new Rectangle(0, 256, 60, 60), bounds.X, bounds.Y, bounds.Width, bounds.Height, val, 1f, true, -1f);
		Vector2 val2 = Game1.smallFont.MeasureString(label);
		float num = Math.Min(1f, (float)(bounds.Width - 10) / Math.Max(1f, val2.X));
		b.DrawString(Game1.smallFont, label, new Vector2((float)((Rectangle)(ref bounds)).Center.X - val2.X * num / 2f, (float)((Rectangle)(ref bounds)).Center.Y - val2.Y * num / 2f), (Color)(enabled ? new Color(68, 51, 65) : Color.DarkGray), 0f, Vector2.Zero, num, (SpriteEffects)0, 1f);
	}

	private static void DrawPanel(SpriteBatch b, Rectangle bounds)
	{
		//IL_0001: Unknown result type (might be due to invalid IL or missing references)
		//IL_0007: Unknown result type (might be due to invalid IL or missing references)
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		IClickableMenu.drawTextureBox(b, bounds.X, bounds.Y, bounds.Width, bounds.Height, Color.White);
	}

	private static void DrawPlaceholder(SpriteBatch b, Rectangle bounds, string label)
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0036: Unknown result type (might be due to invalid IL or missing references)
		//IL_0044: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_006f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0080: Unknown result type (might be due to invalid IL or missing references)
		//IL_008b: Unknown result type (might be due to invalid IL or missing references)
		//IL_009a: Unknown result type (might be due to invalid IL or missing references)
		//IL_009f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a9: Unknown result type (might be due to invalid IL or missing references)
		b.Draw(Game1.staminaRect, bounds, new Color(188, 197, 204));
		Vector2 val = Game1.tinyFont.MeasureString(label);
		float num = Math.Min(1f, Math.Max(0.35f, (float)(bounds.Width - 6) / Math.Max(1f, val.X)));
		b.DrawString(Game1.tinyFont, label, new Vector2((float)((Rectangle)(ref bounds)).Center.X - val.X * num / 2f, (float)((Rectangle)(ref bounds)).Center.Y - val.Y * num / 2f), Color.DarkSlateGray, 0f, Vector2.Zero, num, (SpriteEffects)0, 1f);
	}

	private static Rectangle ToRectangle(PreviewLayoutRect rect)
	{
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		return new Rectangle(rect.X, rect.Y, rect.Width, rect.Height);
	}

	private static string TrimToWidth(string text, int width)
	{
		//IL_000a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0046: Unknown result type (might be due to invalid IL or missing references)
		if (width <= 0 || Game1.tinyFont.MeasureString(text).X <= (float)width)
		{
			return text;
		}
		while (text.Length > 0 && Game1.tinyFont.MeasureString(text + "…").X > (float)width)
		{
			string text2 = text;
			text = text2.Substring(0, text2.Length - 1);
		}
		return text + "…";
	}

	private static void DrawBorder(SpriteBatch b, Rectangle rect, Color color, int thickness)
	{
		//IL_0014: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_008b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0091: Unknown result type (might be due to invalid IL or missing references)
		//IL_0096: Unknown result type (might be due to invalid IL or missing references)
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref rect)).Left, ((Rectangle)(ref rect)).Top, rect.Width, thickness), color);
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref rect)).Left, ((Rectangle)(ref rect)).Bottom - thickness, rect.Width, thickness), color);
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref rect)).Left, ((Rectangle)(ref rect)).Top, thickness, rect.Height), color);
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref rect)).Right - thickness, ((Rectangle)(ref rect)).Top, thickness, rect.Height), color);
	}

	private static GarmentCropSelection CloneSelection(GarmentCropSelection source)
	{
		return new GarmentCropSelection
		{
			Left = source.Left,
			Top = source.Top,
			Right = source.Right,
			Bottom = source.Bottom,
			CategoryHint = source.CategoryHint
		};
	}

	private static string CategoryLabel(string category)
	{
		return category switch
		{
			"shirt" => "上衣", 
			"pants" => "下装", 
			"hat" => "帽子", 
			"boots" => "鞋子", 
			_ => "自动", 
		};
	}

	static RecognitionPreviewMenu()
	{
		//IL_0006: Unknown result type (might be due to invalid IL or missing references)
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0034: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_004c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_0067: Unknown result type (might be due to invalid IL or missing references)
		//IL_006c: Unknown result type (might be due to invalid IL or missing references)
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0084: Unknown result type (might be due to invalid IL or missing references)
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_009c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00af: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b4: Unknown result type (might be due to invalid IL or missing references)
		Ink = new Color(34, 55, 82);
		MutedInk = new Color(91, 73, 93);
		PreviewCropColors = (Color[])(object)new Color[6]
		{
			new Color(72, 216, 180),
			new Color(255, 190, 78),
			new Color(133, 180, 255),
			new Color(240, 126, 190),
			new Color(190, 229, 91),
			new Color(224, 149, 91)
		};
	}
}
