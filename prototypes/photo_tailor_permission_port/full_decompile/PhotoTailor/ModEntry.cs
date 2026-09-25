using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.GameData;
using StardewValley.GameData.BigCraftables;
using StardewValley.GameData.Pants;
using StardewValley.GameData.Shirts;
using StardewValley.GameData.Shops;
using StardewValley.Menus;

namespace PhotoTailor;

public sealed class ModEntry : Mod
{
	internal const string MachineId = "Robin.PhotoTailor_Machine";

	internal const string MachineQualifiedId = "(BC)Robin.PhotoTailor_Machine";

	private const string MachineTextureAsset = "Mods/Robin.PhotoTailor/Machine";

	internal const string MenuTextureAsset = "Mods/Robin.PhotoTailor/Menu";

	private readonly ConcurrentQueue<Action> mainThreadActions = new ConcurrentQueue<Action>();

	private readonly List<GeneratedGarment> generated = new List<GeneratedGarment>();

	private readonly object catalogLock = new object();

	private SpriteRenderer renderer;

	private LocalOutfitAnalyzer analyzer;

	private string catalogPath;

	private long analysisRequestId;

	internal ModConfig Config { get; private set; } = new ModConfig();

	public override void Entry(IModHelper helper)
	{
		Config = helper.ReadConfig<ModConfig>();
		if (Config.ConfigVersion < 2)
		{
			Config.ConfigVersion = 2;
			Config.ClothCost = 1;
			Config.GoldCost = 2000;
			helper.WriteConfig<ModConfig>(Config);
		}
		catalogPath = Path.Combine(helper.DirectoryPath, "generated", "index.json");
		LoadCatalog();
		SemanticRetriever retriever = new SemanticRetriever(helper.DirectoryPath);
		renderer = new SpriteRenderer(helper.DirectoryPath, retriever);
		analyzer = new LocalOutfitAnalyzer(helper.DirectoryPath);
		helper.Events.Content.AssetRequested += OnAssetRequested;
		helper.Events.Input.ButtonPressed += OnButtonPressed;
		helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
		helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
		helper.ConsoleCommands.Add("phototailor_give_machine", "Give yourself the Photo Tailor machine.", (Action<string, string[]>)OnGiveMachineCommand);
		helper.ConsoleCommands.Add("phototailor_demo", "Generate the striped-shirt fixture without charging resources.", (Action<string, string[]>)OnDemoCommand);
	}

	private void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
	{
		if (e.NameWithoutLocale.IsEquivalentTo("Mods/Robin.PhotoTailor/Machine", false))
		{
			e.LoadFromModFile<Texture2D>("assets/photo_tailor_machine.png", (AssetLoadPriority)int.MaxValue);
			return;
		}
		if (e.NameWithoutLocale.IsEquivalentTo("Mods/Robin.PhotoTailor/Menu", false))
		{
			e.LoadFromModFile<Texture2D>("assets/photo_tailor_ui_hd.png", (AssetLoadPriority)int.MaxValue);
			return;
		}
		string text = null;
		lock (catalogLock)
		{
			GeneratedGarment generatedGarment = generated.FirstOrDefault((GeneratedGarment item) => e.NameWithoutLocale.IsEquivalentTo(item.TextureAsset, false) || (item.PaletteAsset != null && e.NameWithoutLocale.IsEquivalentTo(item.PaletteAsset, false)));
			if (generatedGarment != null)
			{
				text = (e.NameWithoutLocale.IsEquivalentTo(generatedGarment.TextureAsset, false) ? generatedGarment.TexturePath : generatedGarment.PalettePath);
			}
		}
		if (text != null)
		{
			e.LoadFromModFile<Texture2D>(text, (AssetLoadPriority)int.MaxValue);
		}
		else if (e.NameWithoutLocale.IsEquivalentTo("Data/BigCraftables", false))
		{
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				//IL_0010: Unknown result type (might be due to invalid IL or missing references)
				//IL_0015: Unknown result type (might be due to invalid IL or missing references)
				//IL_0020: Unknown result type (might be due to invalid IL or missing references)
				//IL_002b: Unknown result type (might be due to invalid IL or missing references)
				//IL_0036: Unknown result type (might be due to invalid IL or missing references)
				//IL_004c: Unknown result type (might be due to invalid IL or missing references)
				//IL_0053: Unknown result type (might be due to invalid IL or missing references)
				//IL_005a: Unknown result type (might be due to invalid IL or missing references)
				//IL_0061: Unknown result type (might be due to invalid IL or missing references)
				//IL_0068: Unknown result type (might be due to invalid IL or missing references)
				//IL_0073: Unknown result type (might be due to invalid IL or missing references)
				//IL_007f: Expected O, but got Unknown
				((IAssetData<IDictionary<string, BigCraftableData>>)(object)asset.AsDictionary<string, BigCraftableData>()).Data["Robin.PhotoTailor_Machine"] = new BigCraftableData
				{
					Name = "Photo Tailor",
					DisplayName = "照片裁缝",
					Description = "把穿搭照片转译成星露谷原版画风服装的缝纫机。",
					Price = Config.MachinePrice,
					Fragility = 0,
					CanBePlacedIndoors = true,
					CanBePlacedOutdoors = true,
					IsLamp = false,
					Texture = "Mods/Robin.PhotoTailor/Machine",
					SpriteIndex = 0
				};
			}, (AssetEditPriority)0, (string)null);
		}
		else if (e.NameWithoutLocale.IsEquivalentTo("Data/Shops", false))
		{
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				//IL_0062: Unknown result type (might be due to invalid IL or missing references)
				//IL_0067: Unknown result type (might be due to invalid IL or missing references)
				//IL_0072: Unknown result type (might be due to invalid IL or missing references)
				//IL_007d: Unknown result type (might be due to invalid IL or missing references)
				//IL_0093: Unknown result type (might be due to invalid IL or missing references)
				//IL_009a: Unknown result type (might be due to invalid IL or missing references)
				//IL_00a1: Unknown result type (might be due to invalid IL or missing references)
				//IL_00a8: Unknown result type (might be due to invalid IL or missing references)
				//IL_00af: Unknown result type (might be due to invalid IL or missing references)
				//IL_00bb: Expected O, but got Unknown
				if (((IAssetData<IDictionary<string, ShopData>>)(object)asset.AsDictionary<string, ShopData>()).Data.TryGetValue("SeedShop", out var value))
				{
					ShopData val = value;
					if (val.Items == null)
					{
						val.Items = new List<ShopItemData>();
					}
					if (!value.Items.Any((ShopItemData item) => ((GenericSpawnItemData)item).Id == "Robin.PhotoTailor_Machine"))
					{
						value.Items.Add(new ShopItemData
						{
							Id = "Robin.PhotoTailor_Machine",
							ItemId = "(BC)Robin.PhotoTailor_Machine",
							Price = Config.MachinePrice,
							AvailableStock = -1,
							MinStack = 1,
							MaxStack = 1,
							Quality = 0,
							IgnoreShopPriceModifiers = true
						});
					}
				}
			}, (AssetEditPriority)0, (string)null);
		}
		else if (e.NameWithoutLocale.IsEquivalentTo("Data/Shirts", false))
		{
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				//IL_0036: Unknown result type (might be due to invalid IL or missing references)
				//IL_003b: Unknown result type (might be due to invalid IL or missing references)
				//IL_0047: Unknown result type (might be due to invalid IL or missing references)
				//IL_0053: Unknown result type (might be due to invalid IL or missing references)
				//IL_005f: Unknown result type (might be due to invalid IL or missing references)
				//IL_006a: Unknown result type (might be due to invalid IL or missing references)
				//IL_0076: Unknown result type (might be due to invalid IL or missing references)
				//IL_007d: Unknown result type (might be due to invalid IL or missing references)
				//IL_0084: Unknown result type (might be due to invalid IL or missing references)
				//IL_008b: Unknown result type (might be due to invalid IL or missing references)
				//IL_0092: Unknown result type (might be due to invalid IL or missing references)
				//IL_009e: Unknown result type (might be due to invalid IL or missing references)
				//IL_00aa: Expected O, but got Unknown
				IDictionary<string, ShirtData> data = ((IAssetData<IDictionary<string, ShirtData>>)(object)asset.AsDictionary<string, ShirtData>()).Data;
				foreach (GeneratedGarment item in Snapshot("shirt"))
				{
					data[item.Id] = new ShirtData
					{
						Name = item.Name,
						DisplayName = item.Name,
						Description = item.Description,
						Price = 1000,
						Texture = item.TextureAsset,
						SpriteIndex = 0,
						DefaultColor = null,
						CanBeDyed = false,
						IsPrismatic = false,
						HasSleeves = item.HasSleeves,
						CanChooseDuringCharacterCustomization = false
					};
				}
			}, (AssetEditPriority)0, (string)null);
		}
		else if (e.NameWithoutLocale.IsEquivalentTo("Data/Pants", false))
		{
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				//IL_0033: Unknown result type (might be due to invalid IL or missing references)
				//IL_0038: Unknown result type (might be due to invalid IL or missing references)
				//IL_0044: Unknown result type (might be due to invalid IL or missing references)
				//IL_0050: Unknown result type (might be due to invalid IL or missing references)
				//IL_005c: Unknown result type (might be due to invalid IL or missing references)
				//IL_0067: Unknown result type (might be due to invalid IL or missing references)
				//IL_0073: Unknown result type (might be due to invalid IL or missing references)
				//IL_007a: Unknown result type (might be due to invalid IL or missing references)
				//IL_0085: Unknown result type (might be due to invalid IL or missing references)
				//IL_008c: Unknown result type (might be due to invalid IL or missing references)
				//IL_0093: Unknown result type (might be due to invalid IL or missing references)
				//IL_009f: Expected O, but got Unknown
				IDictionary<string, PantsData> data = ((IAssetData<IDictionary<string, PantsData>>)(object)asset.AsDictionary<string, PantsData>()).Data;
				foreach (GeneratedGarment item2 in Snapshot("pants"))
				{
					data[item2.Id] = new PantsData
					{
						Name = item2.Name,
						DisplayName = item2.Name,
						Description = item2.Description,
						Price = 1000,
						Texture = item2.TextureAsset,
						SpriteIndex = 0,
						DefaultColor = "White",
						CanBeDyed = false,
						IsPrismatic = false,
						CanChooseDuringCharacterCustomization = false
					};
				}
			}, (AssetEditPriority)0, (string)null);
		}
		else if (e.NameWithoutLocale.IsEquivalentTo("Data/Hats", false))
		{
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				IDictionary<string, string> data = ((IAssetData<IDictionary<string, string>>)(object)asset.AsDictionary<string, string>()).Data;
				foreach (GeneratedGarment item3 in Snapshot("hat"))
				{
					data[item3.Id] = $"{SafeSlash(item3.Name)}/{SafeSlash(item3.Description)}/true/true//{SafeSlash(item3.Name)}/0/{item3.TextureAsset}";
				}
			}, (AssetEditPriority)0, (string)null);
		}
		else
		{
			if (!e.NameWithoutLocale.IsEquivalentTo("Data/Boots", false))
			{
				return;
			}
			e.Edit((Action<IAssetData>)delegate(IAssetData asset)
			{
				IDictionary<string, string> data = ((IAssetData<IDictionary<string, string>>)(object)asset.AsDictionary<string, string>()).Data;
				foreach (GeneratedGarment item4 in Snapshot("boots"))
				{
					data[item4.Id] = $"{SafeSlash(item4.Name)}/{SafeSlash(item4.Description)}/100/1/1/0/{SafeSlash(item4.Name)}/{item4.PaletteAsset}/0/{item4.TextureAsset}";
				}
			}, (AssetEditPriority)0, (string)null);
		}
	}

	private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
	{
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0031: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0078: Unknown result type (might be due to invalid IL or missing references)
		if (Context.IsWorldReady && Game1.activeClickableMenu == null && SButtonExtensions.IsActionButton(e.Button))
		{
			Vector2 grabTile = ((Mod)this).Helper.Input.GetCursorPosition().GrabTile;
			Object val = default(Object);
			if (Game1.currentLocation.Objects.TryGetValue(grabTile, ref val) && (!(((Item)val).QualifiedItemId != "(BC)Robin.PhotoTailor_Machine") || !(((Item)val).ItemId != "Robin.PhotoTailor_Machine")))
			{
				((Mod)this).Helper.Input.Suppress(e.Button);
				Game1.playSound("bigSelect", (int?)null);
				Game1.activeClickableMenu = (IClickableMenu)(object)new TailorMenu(this);
			}
		}
	}

	internal void BeginImageSelection(TailorMenu menu, RecognitionMode mode)
	{
		string text;
		try
		{
			text = WindowsFilePicker.PickImage();
		}
		catch (Exception ex)
		{
			menu.SetStatus(ex.Message);
			return;
		}
		if (string.IsNullOrWhiteSpace(text))
		{
			menu.SetStatus("已取消选择，没有消耗任何材料。");
			return;
		}
		menu.SetSelectedImage(text);
		if (mode == RecognitionMode.Precise)
		{
			try
			{
				PhotoCropMenu activeClickableMenu = new PhotoCropMenu(this, menu, text);
				menu.SetStatus("已进入精确识别；预览阶段不会消耗材料。");
				Game1.activeClickableMenu = (IClickableMenu)(object)activeClickableMenu;
				return;
			}
			catch (Exception ex2)
			{
				((Mod)this).Monitor.Log(ex2.ToString(), (LogLevel)4);
				menu.SetStatus("无法打开大图预览：" + ex2.Message);
				Game1.playSound("cancel", (int?)null);
				return;
			}
		}
		BeginQuickRecognition(menu, text);
	}

	private void BeginQuickRecognition(TailorMenu menu, string path)
	{
		long requestId = Interlocked.Increment(ref analysisRequestId);
		menu.SetStatus("正在快速识别并准备预览……照片不会上传。", isBusy: true);
		Task.Run(delegate
		{
			try
			{
				OutfitSpec spec = analyzer.Analyze(path);
				mainThreadActions.Enqueue(delegate
				{
					if (requestId == Volatile.Read(in analysisRequestId) && (object)Game1.activeClickableMenu == menu)
					{
						if (spec.Items.Count == 0)
						{
							menu.SetStatus("快速识别没有找到衣物。请使用“精确识别”放大并框选衣物。");
							Game1.playSound("cancel", (int?)null);
						}
						else
						{
							menu.SetStatus("快速识别完成；确认预览后才会消耗材料。");
							try
							{
								Game1.activeClickableMenu = (IClickableMenu)(object)new RecognitionPreviewMenu(this, menu, path, spec);
							}
							catch (Exception ex4)
							{
								((Mod)this).Monitor.Log(ex4.ToString(), (LogLevel)4);
								menu.SetStatus("无法打开识别预览：" + ex4.Message);
								Game1.playSound("cancel", (int?)null);
								return;
							}
							Game1.playSound("newArtifact", (int?)null);
						}
					}
				});
			}
			catch (Exception ex)
			{
				Exception ex2 = ex;
				Exception ex3 = ex2;
				((Mod)this).Monitor.Log(ex3.ToString(), (LogLevel)4);
				mainThreadActions.Enqueue(delegate
				{
					if (requestId == Volatile.Read(in analysisRequestId) && (object)Game1.activeClickableMenu == menu)
					{
						menu.SetStatus(ex3.Message);
					}
				});
			}
		});
	}

	internal void BeginPreciseRecognition(PhotoCropMenu cropMenu, TailorMenu parent, string path, IReadOnlyList<GarmentCropSelection> selections)
	{
		long requestId = Interlocked.Increment(ref analysisRequestId);
		Task.Run(delegate
		{
			try
			{
				OutfitSpec spec = analyzer.Analyze(path, selections);
				mainThreadActions.Enqueue(delegate
				{
					if (requestId == Volatile.Read(in analysisRequestId) && (object)Game1.activeClickableMenu == cropMenu)
					{
						if (spec.Items.Count == 0)
						{
							cropMenu.SetAnalysisError("这些框里没有识别到衣物，请扩大衣物框或指定框类型。");
						}
						else
						{
							RecognitionPreviewMenu activeClickableMenu;
							try
							{
								activeClickableMenu = new RecognitionPreviewMenu(this, parent, path, spec, selections);
							}
							catch (Exception ex4)
							{
								((Mod)this).Monitor.Log(ex4.ToString(), (LogLevel)4);
								cropMenu.SetAnalysisError("无法打开识别预览：" + ex4.Message);
								return;
							}
							cropMenu.PrepareForTransition();
							parent.SetStatus("精确识别完成；确认预览后才会消耗材料。");
							Game1.activeClickableMenu = (IClickableMenu)(object)activeClickableMenu;
							Game1.playSound("newArtifact", (int?)null);
						}
					}
				});
			}
			catch (Exception ex)
			{
				Exception ex2 = ex;
				Exception ex3 = ex2;
				((Mod)this).Monitor.Log(ex3.ToString(), (LogLevel)4);
				mainThreadActions.Enqueue(delegate
				{
					if (requestId == Volatile.Read(in analysisRequestId) && (object)Game1.activeClickableMenu == cropMenu)
					{
						cropMenu.SetAnalysisError(ex3.Message);
					}
				});
			}
		});
	}

	internal void ConfirmRecognizedOutfit(TailorMenu parent, OutfitSpec spec, OutfitRenderPreview preparedPreview)
	{
		Interlocked.Increment(ref analysisRequestId);
		Game1.activeClickableMenu = (IClickableMenu)(object)parent;
		parent.SetStatus("正在按预览结果缝制……", isBusy: true);
		CompleteGeneration(spec, parent, chargeResources: true, preparedPreview);
	}

	internal OutfitRenderPreview PopulateRecognitionPreview(OutfitSpec spec, RecognitionPreviewResourceSet<Texture2D> resources)
	{
		OutfitRenderPreview outfitRenderPreview = renderer.Preview(spec);
		GarmentMenuPreviewRenderer.Populate(outfitRenderPreview, resources, Game1.graphics.GraphicsDevice);
		return outfitRenderPreview;
	}

	internal void LogPreviewWarning(string message, Exception error)
	{
		((Mod)this).Monitor.Log($"{message}\n{error}", (LogLevel)3);
	}

	private void CompleteGeneration(OutfitSpec spec, TailorMenu? menu, bool chargeResources, OutfitRenderPreview? preparedPreview = null)
	{
		bool flag = false;
		try
		{
			if (spec.Items.Count == 0)
			{
				throw new InvalidOperationException("没有识别到可生成的衣物。");
			}
			if (chargeResources && !CanAfford(menu, out string reason, spec.Items.Count))
			{
				throw new InvalidOperationException(reason);
			}
			if (!chargeResources && Game1.player.freeSpotsInInventory() < spec.Items.Count)
			{
				throw new InvalidOperationException($"背包至少需要 {spec.Items.Count} 个空位。");
			}
			string suffix = $"{DateTime.UtcNow:yyyyMMddHHmmss}_{Guid.NewGuid():N}".Substring(0, 23);
			bool usePrepared = preparedPreview != null && preparedPreview.Items.Count == spec.Items.Count;
			List<GeneratedGarment> list = spec.Items.Select(delegate(GarmentSpec item, int index)
			{
				string uniqueSuffix = GarmentOutputPlanner.BuildRenderSuffix(suffix, index);
				return (!usePrepared) ? renderer.Render(item, uniqueSuffix) : renderer.RenderPrepared(item, uniqueSuffix, preparedPreview.Items[index]);
			}).ToList();
			lock (catalogLock)
			{
				generated.AddRange(list);
				SaveCatalog();
			}
			InvalidateGeneratedAssets();
			List<Item> list2 = new List<Item>(list.Count);
			foreach (GeneratedGarment item in list)
			{
				Item val = ItemRegistry.Create(item.QualifiedItemId, 1, 0, true);
				if (val == null)
				{
					throw new InvalidOperationException("游戏没有注册生成的衣物（" + CategoryName(item.Category) + "）。请重新打开缝纫界面后再试。");
				}
				list2.Add(val);
			}
			if (chargeResources)
			{
				DeductCost(menu);
				flag = true;
			}
			int num = 0;
			foreach (Item item2 in list2)
			{
				Item val2 = Game1.player.addItemToInventory(item2);
				if (val2 != null)
				{
					num++;
					Utility.CollectOrDrop(val2, -1);
				}
			}
			Game1.playSound("coin", (int?)null);
			string text = string.Join("、", list.Select((GeneratedGarment item) => CategoryName(item.Category)));
			string text2 = ((num == 0) ? "物品已经放入背包。" : $"{num} 件因背包临时变满而放在角色脚边，其余已放入背包。");
			menu?.SetStatus("缝制完成：" + text + "。" + text2);
			((Mod)this).Monitor.Log("Generated outfit '" + spec.OutfitName + "': " + string.Join(", ", list.Select((GeneratedGarment item) => item.QualifiedItemId)), (LogLevel)2);
		}
		catch (Exception ex)
		{
			((Mod)this).Monitor.Log(ex.ToString(), (LogLevel)4);
			string text3 = (flag ? "材料已经扣除，请查看 SMAPI 日志。" : "本次不会扣除材料。");
			menu?.SetStatus("生成失败：" + ex.Message + "\n" + text3);
			Game1.playSound("cancel", (int?)null);
		}
	}

	private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
	{
		Action result;
		while (mainThreadActions.TryDequeue(out result))
		{
			result();
		}
	}

	private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
	{
		bool flag = false;
		int num = 0;
		lock (catalogLock)
		{
			foreach (GeneratedGarment item in generated)
			{
				string path = Path.Combine(((Mod)this).Helper.DirectoryPath, "generated", item.Id + ".spec.json");
				if (!File.Exists(path))
				{
					continue;
				}
				try
				{
					string json = File.ReadAllText(path);
					int schemaVersion = GeneratedGarmentMigrationPolicy.ReadSchemaVersion(json);
					GarmentSpec garmentSpec = null;
					if (item.RendererVersion >= 11)
					{
						continue;
					}
					if (!GeneratedGarmentMigrationPolicy.ShouldRerender(item.RendererVersion, 11, schemaVersion))
					{
						num++;
						continue;
					}
					if (garmentSpec == null)
					{
						garmentSpec = JsonSerializer.Deserialize<GarmentSpec>(json);
					}
					if (garmentSpec != null)
					{
						renderer.RerenderExisting(garmentSpec, item);
						item.RendererVersion = 11;
						flag = true;
					}
				}
				catch (Exception value)
				{
					((Mod)this).Monitor.Log($"Couldn't migrate generated garment '{item.Id}': {value}", (LogLevel)3);
				}
			}
			if (flag)
			{
				SaveCatalog();
			}
		}
		if (num > 0)
		{
			((Mod)this).Monitor.Log($"Preserved {num} legacy generated garment(s) without rerendering; " + "their pre-v2 specs don't carry the blueprint contract required by the current renderer.", (LogLevel)1);
		}
		if (flag)
		{
			InvalidateGeneratedAssets();
			((Mod)this).Monitor.Log($"Migrated older generated clothing to renderer v{11}.", (LogLevel)2);
		}
	}

	private bool CanAfford(TailorMenu? menu, out string reason, int requiredSlots)
	{
		int num = menu?.ClothCount ?? ((IEnumerable<Item>)Game1.player.Items).Where((Item item) => ((item != null) ? item.QualifiedItemId : null) == "(O)428").Sum((Item item) => item.Stack);
		if (num < Config.ClothCost)
		{
			reason = ((menu == null) ? $"布料不足：需要 {Config.ClothCost} 个，目前只有 {num} 个。" : $"请先在左侧材料槽放入 {Config.ClothCost} 块布料。");
			return false;
		}
		if (Game1.player.Money < Config.GoldCost)
		{
			reason = $"金币不足：需要 {Config.GoldCost:N0}g。";
			return false;
		}
		if (Game1.player.freeSpotsInInventory() < requiredSlots)
		{
			reason = $"背包至少需要 {requiredSlots} 个空位。";
			return false;
		}
		reason = "";
		return true;
	}

	private void DeductCost(TailorMenu? menu)
	{
		if (menu != null)
		{
			if (!menu.ConsumeCloth(Config.ClothCost))
			{
				throw new InvalidOperationException("材料槽里的布料不足，本次不会扣除金币。");
			}
		}
		else
		{
			int num = Config.ClothCost;
			for (int i = 0; i < Game1.player.Items.Count; i++)
			{
				if (num <= 0)
				{
					break;
				}
				Item val = Game1.player.Items[i];
				if (!(((val != null) ? val.QualifiedItemId : null) != "(O)428"))
				{
					int num2 = Math.Min(val.Stack, num);
					val.Stack -= num2;
					num -= num2;
					if (val.Stack <= 0)
					{
						Game1.player.Items[i] = null;
					}
				}
			}
		}
		Farmer player = Game1.player;
		player.Money -= Config.GoldCost;
	}

	private void InvalidateGeneratedAssets()
	{
		string[] array = new string[4] { "Data/Shirts", "Data/Pants", "Data/Hats", "Data/Boots" };
		foreach (string text in array)
		{
			((Mod)this).Helper.GameContent.InvalidateCache(text);
		}
		ItemRegistry.ResetCache();
	}

	private List<GeneratedGarment> Snapshot(string category)
	{
		lock (catalogLock)
		{
			return generated.Where((GeneratedGarment item) => item.Category == category).ToList();
		}
	}

	private void LoadCatalog()
	{
		Directory.CreateDirectory(Path.GetDirectoryName(catalogPath));
		if (!File.Exists(catalogPath))
		{
			return;
		}
		try
		{
			List<GeneratedGarment> list = JsonSerializer.Deserialize<List<GeneratedGarment>>(File.ReadAllText(catalogPath));
			if (list != null)
			{
				generated.AddRange(list);
			}
		}
		catch (Exception value)
		{
			((Mod)this).Monitor.Log($"Couldn't read generated clothing catalog: {value}", (LogLevel)4);
		}
	}

	private void SaveCatalog()
	{
		string contents = JsonSerializer.Serialize(generated, new JsonSerializerOptions
		{
			WriteIndented = true
		});
		string text = catalogPath + ".tmp";
		File.WriteAllText(text, contents);
		File.Move(text, catalogPath, overwrite: true);
	}

	private void OnGiveMachineCommand(string command, string[] args)
	{
		if (!Context.IsWorldReady)
		{
			((Mod)this).Monitor.Log("Load a save first.", (LogLevel)3);
			return;
		}
		Item val = ItemRegistry.Create("(BC)Robin.PhotoTailor_Machine", 1, 0, true);
		Game1.player.addItemToInventoryBool(val, false);
	}

	private void OnDemoCommand(string command, string[] args)
	{
		if (!Context.IsWorldReady)
		{
			((Mod)this).Monitor.Log("Load a save first.", (LogLevel)3);
			return;
		}
		OutfitSpec spec = new OutfitSpec
		{
			OutfitName = "Mint Shadow Stripes",
			Items = new List<GarmentSpec>
			{
				new GarmentSpec
				{
					Category = "shirt",
					Name = "Mint Shadow Striped Shirt",
					SemanticDescription = "black mint green gray white horizontal striped short sleeve t-shirt",
					PrimaryColor = "#202427",
					SecondaryColor = "#45B98A",
					AccentColor = "#E7E9E7",
					Palette = new List<string> { "#202427", "#45B98A", "#E7E9E7", "#697775", "#B9C6C0", "#2D6E59", "#111719", "#78CFAE", "#9BAAA5" },
					PatternWidth = 12,
					PatternHeight = 12,
					PatternMap = Enumerable.Range(0, 144).Select(delegate(int index)
					{
						int num = index % 12;
						int num2 = index / 12;
						int num3 = (new int[12]
						{
							6, 0, 3, 2, 4, 0, 1, 7, 5, 0,
							8, 2
						})[num2];
						if ((num + num2 * 3) % 11 == 0)
						{
							int num4;
							switch (num3)
							{
							case 0:
							case 6:
								num4 = 3;
								break;
							case 1:
							case 7:
								num4 = 5;
								break;
							case 2:
							case 4:
							case 8:
								num4 = 4;
								break;
							default:
								num4 = num3;
								break;
							}
							num3 = num4;
						}
						return num3;
					}).ToList(),
					Pattern = "horizontal_stripes",
					Silhouette = "t_shirt",
					Coverage = "short_sleeve",
					Confidence = 0.99
				}
			}
		};
		CompleteGeneration(spec, null, chargeResources: false);
	}

	private static string SafeSlash(string value)
	{
		return value.Replace('/', '-').Replace('\r', ' ').Replace('\n', ' ');
	}

	private static string CategoryName(string category)
	{
		return category switch
		{
			"shirt" => "上衣", 
			"pants" => "裤装", 
			"hat" => "帽子", 
			"boots" => "鞋子", 
			_ => category, 
		};
	}
}
