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

internal sealed class PhotoCropMenu : IClickableMenu
{
	private enum CropDragMode
	{
		None,
		Create,
		Move,
		Pan,
		ResizeLeft,
		ResizeRight,
		ResizeTop,
		ResizeBottom,
		ResizeTopLeft,
		ResizeTopRight,
		ResizeBottomLeft,
		ResizeBottomRight
	}

	private const double MinimumCropSize = 0.025;

	private const int MaximumSelections = 8;

	private static readonly string[] CategoryHints;

	private static readonly Color[] CropColors;

	private readonly ModEntry mod;

	private readonly TailorMenu parent;

	private readonly string imagePath;

	private readonly Texture2D photo;

	private readonly List<GarmentCropSelection> selections;

	private Rectangle canvas;

	private Rectangle toolPanel;

	private Rectangle zoomOutButton;

	private Rectangle zoomInButton;

	private Rectangle resetViewButton;

	private Rectangle addButton;

	private Rectangle deleteButton;

	private Rectangle categoryButton;

	private Rectangle cancelButton;

	private Rectangle analyzeButton;

	private int selectedIndex;

	private float zoom;

	private Vector2 pan;

	private Point dragStart;

	private Vector2 panStart;

	private GarmentCropSelection? dragOriginal;

	private CropDragMode dragMode;

	private bool createArmed;

	private bool busy;

	private bool disposed;

	private string status;

	internal IReadOnlyList<GarmentCropSelection> Selections => selections;

	internal PhotoCropMenu(ModEntry mod, TailorMenu parent, string imagePath, IReadOnlyList<GarmentCropSelection>? initialSelections = null)
	{
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0011: Unknown result type (might be due to invalid IL or missing references)
		zoom = 1f;
		pan = Vector2.Zero;
		status = "拖动画框；选中后可移动，拖边或四角可调整大小。";
		((IClickableMenu)this)._002Ector(0, 0, ((Rectangle)(ref Game1.uiViewport)).Width, ((Rectangle)(ref Game1.uiViewport)).Height, false);
		this.mod = mod;
		this.parent = parent;
		this.imagePath = imagePath;
		using FileStream fileStream = File.OpenRead(imagePath);
		photo = Texture2D.FromStream(Game1.graphics.GraphicsDevice, (Stream)fileStream);
		selections = initialSelections?.Take(8).Select(CloneSelection).ToList() ?? new List<GarmentCropSelection>();
		if (selections.Count == 0)
		{
			selections.Add(new GarmentCropSelection
			{
				Left = 0.04,
				Top = 0.04,
				Right = 0.96,
				Bottom = 0.96,
				CategoryHint = "auto"
			});
		}
		selectedIndex = selections.Count - 1;
		Layout();
	}

	internal void SetAnalysisError(string message)
	{
		busy = false;
		status = message;
		Game1.playSound("cancel", (int?)null);
	}

	internal void PrepareForTransition()
	{
		busy = false;
		DisposePhoto();
	}

	public override bool readyToClose()
	{
		return false;
	}

	public override void receiveLeftClick(int x, int y, bool playSound = true)
	{
		//IL_0132: Unknown result type (might be due to invalid IL or missing references)
		//IL_0137: Unknown result type (might be due to invalid IL or missing references)
		//IL_021c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0221: Unknown result type (might be due to invalid IL or missing references)
		//IL_0240: Unknown result type (might be due to invalid IL or missing references)
		//IL_0245: Unknown result type (might be due to invalid IL or missing references)
		//IL_024a: Unknown result type (might be due to invalid IL or missing references)
		//IL_024f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0265: Unknown result type (might be due to invalid IL or missing references)
		//IL_026a: Unknown result type (might be due to invalid IL or missing references)
		//IL_02f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_02f7: Unknown result type (might be due to invalid IL or missing references)
		//IL_02fc: Unknown result type (might be due to invalid IL or missing references)
		//IL_030a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0318: Unknown result type (might be due to invalid IL or missing references)
		//IL_0326: Unknown result type (might be due to invalid IL or missing references)
		//IL_0334: Unknown result type (might be due to invalid IL or missing references)
		//IL_0392: Unknown result type (might be due to invalid IL or missing references)
		if (busy)
		{
			Game1.playSound("cancel", (int?)null);
			return;
		}
		if (((Rectangle)(ref cancelButton)).Contains(x, y))
		{
			ReturnToParent("已取消精确识别，没有消耗材料。");
			return;
		}
		if (((Rectangle)(ref analyzeButton)).Contains(x, y))
		{
			if (selections.Count == 0)
			{
				status = "请至少框选一件衣物。";
				Game1.playSound("cancel", (int?)null);
				return;
			}
			busy = true;
			status = "正在逐个分析所选衣物，照片不会上传。";
			Game1.playSound("bigSelect", (int?)null);
			mod.BeginPreciseRecognition(this, parent, imagePath, selections.Select(CloneSelection).ToList());
			return;
		}
		if (((Rectangle)(ref zoomOutButton)).Contains(x, y))
		{
			ChangeZoom(-0.25f);
			return;
		}
		if (((Rectangle)(ref zoomInButton)).Contains(x, y))
		{
			ChangeZoom(0.25f);
			return;
		}
		if (((Rectangle)(ref resetViewButton)).Contains(x, y))
		{
			zoom = 1f;
			pan = Vector2.Zero;
			status = "视图已恢复；衣物框不会改变。";
			Game1.playSound("smallSelect", (int?)null);
			return;
		}
		if (((Rectangle)(ref addButton)).Contains(x, y))
		{
			if (selections.Count >= 8)
			{
				status = $"一次最多框选 {8} 件衣物。";
				Game1.playSound("cancel", (int?)null);
			}
			else
			{
				createArmed = true;
				status = "请在图片上拖出一个新的衣物框。";
				Game1.playSound("smallSelect", (int?)null);
			}
			return;
		}
		if (((Rectangle)(ref deleteButton)).Contains(x, y))
		{
			DeleteSelected();
			return;
		}
		if (((Rectangle)(ref categoryButton)).Contains(x, y))
		{
			CycleCategoryHint();
			return;
		}
		Rectangle image = ImageDestination();
		if (!((Rectangle)(ref canvas)).Contains(x, y) || !((Rectangle)(ref image)).Contains(x, y))
		{
			return;
		}
		dragStart = new Point(x, y);
		KeyboardState state = Keyboard.GetState();
		if (((KeyboardState)(ref state)).IsKeyDown((Keys)32))
		{
			dragMode = CropDragMode.Pan;
			panStart = pan;
			status = "正在平移放大的照片。";
		}
		else if (createArmed || selections.Count == 0)
		{
			if (selections.Count >= 8)
			{
				createArmed = false;
				status = $"一次最多框选 {8} 件衣物。";
				Game1.playSound("cancel", (int?)null);
			}
			else
			{
				Vector2 val = ScreenToNormalized(x, y, image);
				selections.Add(new GarmentCropSelection
				{
					Left = val.X,
					Top = val.Y,
					Right = val.X,
					Bottom = val.Y,
					CategoryHint = "auto"
				});
				selectedIndex = selections.Count - 1;
				dragOriginal = CloneSelection(selections[selectedIndex]);
				dragMode = CropDragMode.Create;
				createArmed = false;
			}
		}
		else
		{
			var (num, cropDragMode) = HitTestSelections(x, y, image);
			if (num >= 0)
			{
				selectedIndex = num;
				dragMode = cropDragMode;
				dragOriginal = CloneSelection(selections[num]);
				status = ((cropDragMode == CropDragMode.Move) ? "拖动衣物框；拖边或四角可以调整大小。" : "正在调整衣物框大小。");
				Game1.playSound("smallSelect", (int?)null);
			}
			else
			{
				createArmed = true;
				((IClickableMenu)this).receiveLeftClick(x, y, false);
			}
		}
	}

	public override void leftClickHeld(int x, int y)
	{
		//IL_001c: Unknown result type (might be due to invalid IL or missing references)
		//IL_003d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0042: Unknown result type (might be due to invalid IL or missing references)
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_0079: Unknown result type (might be due to invalid IL or missing references)
		//IL_007e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0093: Unknown result type (might be due to invalid IL or missing references)
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_0099: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_0109: Unknown result type (might be due to invalid IL or missing references)
		//IL_0126: Unknown result type (might be due to invalid IL or missing references)
		//IL_0143: Unknown result type (might be due to invalid IL or missing references)
		//IL_0233: Unknown result type (might be due to invalid IL or missing references)
		//IL_0288: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0329: Unknown result type (might be due to invalid IL or missing references)
		if (busy || dragMode == CropDragMode.None)
		{
			return;
		}
		if (dragMode == CropDragMode.Pan)
		{
			pan = panStart + new Vector2((float)(x - dragStart.X), (float)(y - dragStart.Y));
			ClampPan();
		}
		else
		{
			if (selectedIndex < 0 || selectedIndex >= selections.Count || dragOriginal == null)
			{
				return;
			}
			Rectangle image = ImageDestination();
			GarmentCropSelection garmentCropSelection = selections[selectedIndex];
			Vector2 val = ScreenToNormalized(x, y, image);
			Vector2 val2 = ScreenToNormalized(dragStart.X, dragStart.Y, image);
			double num = val.X - val2.X;
			double num2 = val.Y - val2.Y;
			if (dragMode == CropDragMode.Create)
			{
				garmentCropSelection.Left = Math.Min(dragOriginal.Left, val.X);
				garmentCropSelection.Top = Math.Min(dragOriginal.Top, val.Y);
				garmentCropSelection.Right = Math.Max(dragOriginal.Left, val.X);
				garmentCropSelection.Bottom = Math.Max(dragOriginal.Top, val.Y);
				return;
			}
			if (dragMode == CropDragMode.Move)
			{
				double num3 = dragOriginal.Right - dragOriginal.Left;
				double num4 = dragOriginal.Bottom - dragOriginal.Top;
				garmentCropSelection.Left = Math.Clamp(dragOriginal.Left + num, 0.0, 1.0 - num3);
				garmentCropSelection.Top = Math.Clamp(dragOriginal.Top + num2, 0.0, 1.0 - num4);
				garmentCropSelection.Right = garmentCropSelection.Left + num3;
				garmentCropSelection.Bottom = garmentCropSelection.Top + num4;
				return;
			}
			CropDragMode cropDragMode = dragMode;
			if ((cropDragMode == CropDragMode.ResizeLeft || cropDragMode == CropDragMode.ResizeTopLeft || cropDragMode == CropDragMode.ResizeBottomLeft) ? true : false)
			{
				garmentCropSelection.Left = Math.Clamp(val.X, 0.0, dragOriginal.Right - 0.025);
			}
			cropDragMode = dragMode;
			if ((cropDragMode == CropDragMode.ResizeRight || cropDragMode == CropDragMode.ResizeTopRight || cropDragMode == CropDragMode.ResizeBottomRight) ? true : false)
			{
				garmentCropSelection.Right = Math.Clamp(val.X, dragOriginal.Left + 0.025, 1.0);
			}
			cropDragMode = dragMode;
			if ((cropDragMode == CropDragMode.ResizeTop || (uint)(cropDragMode - 8) <= 1u) ? true : false)
			{
				garmentCropSelection.Top = Math.Clamp(val.Y, 0.0, dragOriginal.Bottom - 0.025);
			}
			cropDragMode = dragMode;
			if ((cropDragMode == CropDragMode.ResizeBottom || (uint)(cropDragMode - 10) <= 1u) ? true : false)
			{
				garmentCropSelection.Bottom = Math.Clamp(val.Y, dragOriginal.Top + 0.025, 1.0);
			}
		}
	}

	public override void releaseLeftClick(int x, int y)
	{
		if (dragMode == CropDragMode.Create && selectedIndex >= 0 && selectedIndex < selections.Count)
		{
			GarmentCropSelection garmentCropSelection = selections[selectedIndex];
			if (garmentCropSelection.Right - garmentCropSelection.Left < 0.025 || garmentCropSelection.Bottom - garmentCropSelection.Top < 0.025)
			{
				selections.RemoveAt(selectedIndex);
				selectedIndex = selections.Count - 1;
				status = "衣物框太小，已经取消。";
				Game1.playSound("cancel", (int?)null);
			}
			else
			{
				status = "衣物框已添加；可选择类型，或继续新增衣物框。";
				Game1.playSound("coin", (int?)null);
			}
		}
		dragMode = CropDragMode.None;
		dragOriginal = null;
	}

	public override void receiveRightClick(int x, int y, bool playSound = true)
	{
		//IL_000a: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		if (!busy)
		{
			Rectangle image = ImageDestination();
			int item = HitTestSelections(x, y, image).Index;
			if (item >= 0)
			{
				selectedIndex = item;
				DeleteSelected();
			}
		}
	}

	public override void receiveScrollWheelAction(int direction)
	{
		if (!busy)
		{
			ChangeZoom((direction > 0) ? 0.25f : (-0.25f));
		}
	}

	public override void receiveKeyPress(Keys key)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0003: Invalid comparison between Unknown and I4
		//IL_0022: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Invalid comparison between Unknown and I4
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_0029: Invalid comparison between Unknown and I4
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_003e: Invalid comparison between Unknown and I4
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_0046: Invalid comparison between Unknown and I4
		//IL_005d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0060: Invalid comparison between Unknown and I4
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_0068: Invalid comparison between Unknown and I4
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0082: Invalid comparison between Unknown and I4
		//IL_009a: Unknown result type (might be due to invalid IL or missing references)
		//IL_009d: Invalid comparison between Unknown and I4
		//IL_008f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b8: Invalid comparison between Unknown and I4
		//IL_00aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d3: Invalid comparison between Unknown and I4
		//IL_00c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ee: Invalid comparison between Unknown and I4
		//IL_00e0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f3: Invalid comparison between Unknown and I4
		//IL_0114: Unknown result type (might be due to invalid IL or missing references)
		//IL_0117: Unknown result type (might be due to invalid IL or missing references)
		if ((int)key == 27)
		{
			if (!busy)
			{
				ReturnToParent("已取消精确识别，没有消耗材料。");
			}
		}
		else if (!busy)
		{
			if (((int)key == 8 || (int)key == 46) ? true : false)
			{
				DeleteSelected();
			}
			else if (((int)key == 107 || (int)key == 187) ? true : false)
			{
				ChangeZoom(0.25f);
			}
			else if (((int)key == 109 || (int)key == 189) ? true : false)
			{
				ChangeZoom(-0.25f);
			}
			else if ((int)key == 37)
			{
				PanBy(new Vector2(36f, 0f));
			}
			else if ((int)key == 39)
			{
				PanBy(new Vector2(-36f, 0f));
			}
			else if ((int)key == 38)
			{
				PanBy(new Vector2(0f, 36f));
			}
			else if ((int)key == 40)
			{
				PanBy(new Vector2(0f, -36f));
			}
			else if ((int)key >= 49 && (int)key <= 53 && selectedIndex >= 0)
			{
				selections[selectedIndex].CategoryHint = CategoryHints[key - 49];
			}
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
		DisposePhoto();
		((IClickableMenu)this).cleanupBeforeExit();
	}

	public override void draw(SpriteBatch b)
	{
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		//IL_0018: Unknown result type (might be due to invalid IL or missing references)
		//IL_001d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ad: Unknown result type (might be due to invalid IL or missing references)
		//IL_00df: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_012d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0138: Unknown result type (might be due to invalid IL or missing references)
		//IL_0149: Unknown result type (might be due to invalid IL or missing references)
		//IL_015d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0169: Unknown result type (might be due to invalid IL or missing references)
		//IL_017a: Unknown result type (might be due to invalid IL or missing references)
		//IL_018c: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01be: Unknown result type (might be due to invalid IL or missing references)
		Texture2D fadeToBlackRect = Game1.fadeToBlackRect;
		Viewport viewport = Game1.graphics.GraphicsDevice.Viewport;
		b.Draw(fadeToBlackRect, ((Viewport)(ref viewport)).Bounds, Color.Black * 0.88f);
		Rectangle val = ImageDestination();
		b.Draw(photo, val, Color.White);
		b.Draw(Game1.staminaRect, new Rectangle(0, 0, base.width, ((Rectangle)(ref canvas)).Top), new Color(24, 39, 60));
		b.Draw(Game1.staminaRect, new Rectangle(0, ((Rectangle)(ref canvas)).Bottom, base.width, base.height - ((Rectangle)(ref canvas)).Bottom), new Color(24, 39, 60));
		b.Draw(Game1.staminaRect, new Rectangle(0, ((Rectangle)(ref canvas)).Top, ((Rectangle)(ref canvas)).Left, canvas.Height), new Color(24, 39, 60));
		b.Draw(Game1.staminaRect, new Rectangle(((Rectangle)(ref canvas)).Right, ((Rectangle)(ref canvas)).Top, base.width - ((Rectangle)(ref canvas)).Right, canvas.Height), new Color(24, 39, 60));
		b.Draw(Game1.staminaRect, toolPanel, new Color(226, 239, 246));
		DrawBorder(b, canvas, new Color(94, 153, 194), 4);
		for (int i = 0; i < selections.Count; i++)
		{
			DrawSelection(b, i, val);
		}
		b.DrawString(Game1.dialogueFont, "精确识别：放大并框选衣物", new Vector2(38f, 13f), Color.White);
		DrawTools(b);
		if (!Game1.options.hardwareCursor)
		{
			((IClickableMenu)this).drawMouse(b, false, -1);
		}
	}

	private void Layout()
	{
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		//IL_005b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0090: Unknown result type (might be due to invalid IL or missing references)
		//IL_0095: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d3: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_0101: Unknown result type (might be due to invalid IL or missing references)
		//IL_0106: Unknown result type (might be due to invalid IL or missing references)
		//IL_0118: Unknown result type (might be due to invalid IL or missing references)
		//IL_011d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0132: Unknown result type (might be due to invalid IL or missing references)
		//IL_0137: Unknown result type (might be due to invalid IL or missing references)
		//IL_0156: Unknown result type (might be due to invalid IL or missing references)
		//IL_015b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0177: Unknown result type (might be due to invalid IL or missing references)
		//IL_017c: Unknown result type (might be due to invalid IL or missing references)
		base.width = ((Rectangle)(ref Game1.uiViewport)).Width;
		base.height = ((Rectangle)(ref Game1.uiViewport)).Height;
		int num = Math.Max(690, base.width - 250 - 24);
		toolPanel = new Rectangle(num, 54, 250, Math.Max(540, base.height - 92));
		canvas = new Rectangle(34, 62, Math.Max(620, ((Rectangle)(ref toolPanel)).Left - 54), Math.Max(500, base.height - 102));
		int num2 = ((Rectangle)(ref toolPanel)).Left + 15;
		int num3 = ((Rectangle)(ref toolPanel)).Top + 52;
		zoomOutButton = new Rectangle(num2, num3, 64, 44);
		zoomInButton = new Rectangle(num2 + 72, num3, 64, 44);
		resetViewButton = new Rectangle(num2 + 144, num3, 76, 44);
		addButton = new Rectangle(num2, num3 + 62, 220, 46);
		deleteButton = new Rectangle(num2, num3 + 116, 220, 46);
		categoryButton = new Rectangle(num2, num3 + 170, 220, 48);
		cancelButton = new Rectangle(num2, ((Rectangle)(ref toolPanel)).Bottom - 128, 220, 48);
		analyzeButton = new Rectangle(num2, ((Rectangle)(ref toolPanel)).Bottom - 70, 220, 54);
		ClampPan();
	}

	private void DrawTools(SpriteBatch b)
	{
		//IL_0072: Unknown result type (might be due to invalid IL or missing references)
		//IL_007d: Unknown result type (might be due to invalid IL or missing references)
		//IL_008a: Unknown result type (might be due to invalid IL or missing references)
		//IL_009e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0147: Unknown result type (might be due to invalid IL or missing references)
		//IL_0196: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_020b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0227: Unknown result type (might be due to invalid IL or missing references)
		int num = ((Rectangle)(ref toolPanel)).Left + 15;
		b.DrawString(Game1.smallFont, $"照片 {photo.Width}×{photo.Height}", new Vector2((float)num, (float)(((Rectangle)(ref toolPanel)).Top + 13)), new Color(34, 55, 82));
		DrawButton(b, zoomOutButton, "缩小");
		DrawButton(b, zoomInButton, "放大");
		DrawButton(b, resetViewButton, "100%");
		DrawButton(b, addButton, createArmed ? "请拖出新框" : "新增衣物框");
		DrawButton(b, deleteButton, "删除选中框", selectedIndex >= 0);
		string text = ((selectedIndex >= 0 && selectedIndex < selections.Count) ? CategoryLabel(selections[selectedIndex].CategoryHint) : "未选择衣物框");
		DrawButton(b, categoryButton, "框类型：" + text, selectedIndex >= 0);
		string text2 = "操作：\n• 滚轮放大/缩小\n• 框内拖动可移动\n• 拖边或四角可缩放\n• 空格+拖动可平移\n• 右键可删除框\n• 每件衣物单独一个框";
		b.DrawString(Game1.smallFont, Game1.parseText(text2, Game1.smallFont, 218), new Vector2((float)num, (float)(((Rectangle)(ref categoryButton)).Bottom + 18)), new Color(61, 88, 117));
		string text3 = (busy ? (status + BusyDots()) : status);
		b.DrawString(Game1.tinyFont, Game1.parseText(text3, Game1.tinyFont, 218), new Vector2((float)num, (float)(((Rectangle)(ref cancelButton)).Top - 76)), new Color(91, 73, 93));
		DrawButton(b, cancelButton, "返回缝纫机", !busy);
		DrawButton(b, analyzeButton, busy ? "正在识别" : $"预览识别结果（{selections.Count}/{8}）", !busy && selections.Count > 0, accent: true);
	}

	private void DrawSelection(SpriteBatch b, int index, Rectangle image)
	{
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_0018: Unknown result type (might be due to invalid IL or missing references)
		//IL_001d: Unknown result type (might be due to invalid IL or missing references)
		//IL_001e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0044: Unknown result type (might be due to invalid IL or missing references)
		//IL_004b: Unknown result type (might be due to invalid IL or missing references)
		//IL_004c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0062: Unknown result type (might be due to invalid IL or missing references)
		//IL_006d: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0105: Unknown result type (might be due to invalid IL or missing references)
		//IL_0119: Unknown result type (might be due to invalid IL or missing references)
		//IL_011b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0121: Unknown result type (might be due to invalid IL or missing references)
		//IL_0132: Unknown result type (might be due to invalid IL or missing references)
		//IL_013c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0146: Unknown result type (might be due to invalid IL or missing references)
		//IL_0151: Unknown result type (might be due to invalid IL or missing references)
		//IL_0165: Unknown result type (might be due to invalid IL or missing references)
		//IL_0176: Unknown result type (might be due to invalid IL or missing references)
		//IL_017b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0183: Unknown result type (might be due to invalid IL or missing references)
		//IL_018c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Unknown result type (might be due to invalid IL or missing references)
		//IL_019e: Unknown result type (might be due to invalid IL or missing references)
		Rectangle val = Rectangle.Intersect(SelectionToScreen(selections[index], image), canvas);
		if (val.Width <= 0 || val.Height <= 0)
		{
			return;
		}
		Color val2 = CropColors[index % CropColors.Length];
		b.Draw(Game1.staminaRect, val, val2 * ((index == selectedIndex) ? 0.19f : 0.11f));
		DrawBorder(b, val, val2, (index == selectedIndex) ? 4 : 2);
		string text = $"{index + 1}  {CategoryLabel(selections[index].CategoryHint)}";
		Vector2 val3 = Game1.tinyFont.MeasureString(text);
		Rectangle val4 = default(Rectangle);
		((Rectangle)(ref val4))._002Ector(((Rectangle)(ref val)).Left, Math.Max(((Rectangle)(ref canvas)).Top, ((Rectangle)(ref val)).Top - (int)val3.Y - 8), (int)val3.X + 14, (int)val3.Y + 7);
		b.Draw(Game1.staminaRect, val4, val2 * 0.94f);
		b.DrawString(Game1.tinyFont, text, new Vector2((float)(val4.X + 7), (float)(val4.Y + 3)), new Color(26, 37, 52));
		if (index == selectedIndex)
		{
			Point[] array = CornerPoints(val);
			foreach (Point val5 in array)
			{
				b.Draw(Game1.staminaRect, new Rectangle(val5.X - 6, val5.Y - 6, 12, 12), Color.White);
			}
		}
	}

	private void DrawButton(SpriteBatch b, Rectangle bounds, string label, bool enabled = true, bool accent = false)
	{
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_0059: Unknown result type (might be due to invalid IL or missing references)
		//IL_005e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_006a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0070: Unknown result type (might be due to invalid IL or missing references)
		//IL_0076: Unknown result type (might be due to invalid IL or missing references)
		//IL_008d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_0098: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_002d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0017: Unknown result type (might be due to invalid IL or missing references)
		//IL_0111: Unknown result type (might be due to invalid IL or missing references)
		//IL_0104: Unknown result type (might be due to invalid IL or missing references)
		//IL_011b: Unknown result type (might be due to invalid IL or missing references)
		Color val = ((!enabled) ? new Color(150, 157, 164) : (accent ? new Color(244, 166, 178) : new Color(255, 246, 224)));
		IClickableMenu.drawTextureBox(b, Game1.menuTexture, new Rectangle(0, 256, 60, 60), bounds.X, bounds.Y, bounds.Width, bounds.Height, val, 1f, true, -1f);
		Vector2 val2 = Game1.smallFont.MeasureString(label);
		float num = Math.Min(1f, (float)(bounds.Width - 12) / Math.Max(1f, val2.X));
		Vector2 val3 = default(Vector2);
		((Vector2)(ref val3))._002Ector((float)((Rectangle)(ref bounds)).Center.X - val2.X * num / 2f, (float)((Rectangle)(ref bounds)).Center.Y - val2.Y * num / 2f);
		b.DrawString(Game1.smallFont, label, val3, (Color)(enabled ? new Color(68, 51, 65) : Color.DarkGray), 0f, Vector2.Zero, num, (SpriteEffects)0, 1f);
	}

	private (int Index, CropDragMode Mode) HitTestSelections(int x, int y, Rectangle image)
	{
		//IL_002d: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0070: Unknown result type (might be due to invalid IL or missing references)
		//IL_0071: Unknown result type (might be due to invalid IL or missing references)
		if (selectedIndex >= 0 && selectedIndex < selections.Count)
		{
			CropDragMode cropDragMode = HitTestRect(SelectionToScreen(selections[selectedIndex], image), x, y);
			if (cropDragMode != CropDragMode.None)
			{
				return (Index: selectedIndex, Mode: cropDragMode);
			}
		}
		for (int num = selections.Count - 1; num >= 0; num--)
		{
			if (num != selectedIndex)
			{
				CropDragMode cropDragMode2 = HitTestRect(SelectionToScreen(selections[num], image), x, y);
				if (cropDragMode2 != CropDragMode.None)
				{
					return (Index: num, Mode: cropDragMode2);
				}
			}
		}
		return (Index: -1, Mode: CropDragMode.None);
	}

	private static CropDragMode HitTestRect(Rectangle rect, int x, int y)
	{
		bool flag = Math.Abs(x - ((Rectangle)(ref rect)).Left) <= 11;
		bool flag2 = Math.Abs(x - ((Rectangle)(ref rect)).Right) <= 11;
		bool flag3 = Math.Abs(y - ((Rectangle)(ref rect)).Top) <= 11;
		bool flag4 = Math.Abs(y - ((Rectangle)(ref rect)).Bottom) <= 11;
		bool flag5 = x >= ((Rectangle)(ref rect)).Left - 11 && x <= ((Rectangle)(ref rect)).Right + 11;
		bool flag6 = y >= ((Rectangle)(ref rect)).Top - 11 && y <= ((Rectangle)(ref rect)).Bottom + 11;
		if (flag & flag3)
		{
			return CropDragMode.ResizeTopLeft;
		}
		if (flag2 & flag3)
		{
			return CropDragMode.ResizeTopRight;
		}
		if (flag & flag4)
		{
			return CropDragMode.ResizeBottomLeft;
		}
		if (flag2 & flag4)
		{
			return CropDragMode.ResizeBottomRight;
		}
		if (flag & flag6)
		{
			return CropDragMode.ResizeLeft;
		}
		if (flag2 & flag6)
		{
			return CropDragMode.ResizeRight;
		}
		if (flag3 & flag5)
		{
			return CropDragMode.ResizeTop;
		}
		if (flag4 & flag5)
		{
			return CropDragMode.ResizeBottom;
		}
		if (!((Rectangle)(ref rect)).Contains(x, y))
		{
			return CropDragMode.None;
		}
		return CropDragMode.Move;
	}

	private Rectangle ImageDestination()
	{
		//IL_007d: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		float num = Math.Min((float)canvas.Width / (float)photo.Width, (float)canvas.Height / (float)photo.Height) * zoom;
		int num2 = Math.Max(1, (int)Math.Round((float)photo.Width * num));
		int num3 = Math.Max(1, (int)Math.Round((float)photo.Height * num));
		return new Rectangle(((Rectangle)(ref canvas)).Center.X - num2 / 2 + (int)Math.Round(pan.X), ((Rectangle)(ref canvas)).Center.Y - num3 / 2 + (int)Math.Round(pan.Y), num2, num3);
	}

	private static Rectangle SelectionToScreen(GarmentCropSelection selection, Rectangle image)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_0044: Unknown result type (might be due to invalid IL or missing references)
		//IL_0065: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Unknown result type (might be due to invalid IL or missing references)
		return new Rectangle(image.X + (int)Math.Round(selection.Left * (double)image.Width), image.Y + (int)Math.Round(selection.Top * (double)image.Height), Math.Max(1, (int)Math.Round((selection.Right - selection.Left) * (double)image.Width)), Math.Max(1, (int)Math.Round((selection.Bottom - selection.Top) * (double)image.Height)));
	}

	private static Vector2 ScreenToNormalized(int x, int y, Rectangle image)
	{
		//IL_0001: Unknown result type (might be due to invalid IL or missing references)
		//IL_000a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_0030: Unknown result type (might be due to invalid IL or missing references)
		//IL_004c: Unknown result type (might be due to invalid IL or missing references)
		return new Vector2(Math.Clamp((float)(x - image.X) / (float)Math.Max(1, image.Width), 0f, 1f), Math.Clamp((float)(y - image.Y) / (float)Math.Max(1, image.Height), 0f, 1f));
	}

	private void ChangeZoom(float delta)
	{
		zoom = Math.Clamp(zoom + delta, 1f, 5f);
		ClampPan();
		status = $"当前缩放 {zoom * 100f:0}%；按住空格拖动可平移。";
		Game1.playSound("smallSelect", (int?)null);
	}

	private void PanBy(Vector2 delta)
	{
		//IL_0002: Unknown result type (might be due to invalid IL or missing references)
		//IL_0007: Unknown result type (might be due to invalid IL or missing references)
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		//IL_000d: Unknown result type (might be due to invalid IL or missing references)
		pan += delta;
		ClampPan();
	}

	private void ClampPan()
	{
		if (photo != null && canvas.Width > 0)
		{
			float num = Math.Min((float)canvas.Width / (float)photo.Width, (float)canvas.Height / (float)photo.Height);
			float num2 = (float)photo.Width * num * zoom;
			float num3 = (float)photo.Height * num * zoom;
			float num4 = Math.Max(0f, (num2 - (float)canvas.Width) / 2f);
			float num5 = Math.Max(0f, (num3 - (float)canvas.Height) / 2f);
			pan.X = Math.Clamp(pan.X, 0f - num4, num4);
			pan.Y = Math.Clamp(pan.Y, 0f - num5, num5);
		}
	}

	private void CycleCategoryHint()
	{
		if (selectedIndex >= 0 && selectedIndex < selections.Count)
		{
			string categoryHint = selections[selectedIndex].CategoryHint;
			int num = Array.IndexOf(CategoryHints, categoryHint);
			selections[selectedIndex].CategoryHint = CategoryHints[(num + 1 + CategoryHints.Length) % CategoryHints.Length];
			status = $"衣物框 {selectedIndex + 1} 将按“{CategoryLabel(selections[selectedIndex].CategoryHint)}”识别。";
			Game1.playSound("smallSelect", (int?)null);
		}
	}

	private void DeleteSelected()
	{
		if (selectedIndex < 0 || selectedIndex >= selections.Count)
		{
			Game1.playSound("cancel", (int?)null);
			return;
		}
		selections.RemoveAt(selectedIndex);
		selectedIndex = Math.Min(selectedIndex, selections.Count - 1);
		status = ((selections.Count == 0) ? "所有衣物框已删除；点击“新增衣物框”重新框选。" : "选中的衣物框已删除。");
		Game1.playSound("trashcan", (int?)null);
	}

	private void ReturnToParent(string message)
	{
		DisposePhoto();
		parent.SetStatus(message);
		Game1.activeClickableMenu = (IClickableMenu)(object)parent;
		Game1.playSound("bigDeSelect", (int?)null);
	}

	private void DisposePhoto()
	{
		if (!disposed)
		{
			disposed = true;
			((GraphicsResource)photo).Dispose();
		}
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

	private static string CategoryLabel(string hint)
	{
		return hint switch
		{
			"shirt" => "上衣", 
			"pants" => "下装", 
			"hat" => "帽子", 
			"boots" => "鞋子", 
			_ => "自动判断", 
		};
	}

	private static Point[] CornerPoints(Rectangle rect)
	{
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0030: Unknown result type (might be due to invalid IL or missing references)
		//IL_0035: Unknown result type (might be due to invalid IL or missing references)
		//IL_004a: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_0069: Unknown result type (might be due to invalid IL or missing references)
		return (Point[])(object)new Point[4]
		{
			new Point(((Rectangle)(ref rect)).Left, ((Rectangle)(ref rect)).Top),
			new Point(((Rectangle)(ref rect)).Right, ((Rectangle)(ref rect)).Top),
			new Point(((Rectangle)(ref rect)).Left, ((Rectangle)(ref rect)).Bottom),
			new Point(((Rectangle)(ref rect)).Right, ((Rectangle)(ref rect)).Bottom)
		};
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

	private static string BusyDots()
	{
		return new string('.', (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 400.0) % 4);
	}

	static PhotoCropMenu()
	{
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_004c: Unknown result type (might be due to invalid IL or missing references)
		//IL_005f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		//IL_007a: Unknown result type (might be due to invalid IL or missing references)
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0092: Unknown result type (might be due to invalid IL or missing references)
		//IL_0097: Unknown result type (might be due to invalid IL or missing references)
		//IL_00aa: Unknown result type (might be due to invalid IL or missing references)
		//IL_00af: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c7: Unknown result type (might be due to invalid IL or missing references)
		CategoryHints = new string[5] { "auto", "shirt", "pants", "hat", "boots" };
		CropColors = (Color[])(object)new Color[6]
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
