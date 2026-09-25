using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace PhotoTailor;

internal sealed class SpriteRenderer
{
	private readonly record struct PantsDetailProfile(int WaistY, int HemY, int SeamX, int PocketY, int PleatStep, int Signature, bool SkirtLike, bool CargoPockets, bool Cuffed);

	private enum TextureProjectionMode
	{
		Uniform,
		FourFacingVertical,
		PantsAnimation
	}

	private enum GarmentFacing
	{
		Uniform,
		Front,
		Right,
		Left,
		Back
	}

	private sealed record TextureProjectionContext(IReadOnlyList<int> Map, int Width, int Height, IReadOnlyList<Color> Palette, IReadOnlyList<int> Histogram, int Occupied, int BaseIndex, bool HasSalientDetail, string Pattern)
	{
		public Color BaseColor
		{
			get
			{
				//IL_000c: Unknown result type (might be due to invalid IL or missing references)
				return Palette[BaseIndex];
			}
		}
	}

	internal const int CurrentRendererVersion = 11;

	private const string AssetPrefix = "Mods/Robin.PhotoTailor/Generated";

	private static readonly Dictionary<string, int> ShirtTemplates = new Dictionary<string, int>(StringComparer.Ordinal)
	{
		["t_shirt"] = 128,
		["polo"] = 140,
		["shirt"] = 140,
		["blouse"] = 2,
		["sweater"] = 176,
		["sweatshirt"] = 176,
		["hoodie"] = 160,
		["cardigan"] = 218,
		["jacket"] = 137,
		["coat"] = 221,
		["trench_coat"] = 221,
		["overcoat"] = 221,
		["blazer"] = 137,
		["bomber_jacket"] = 176,
		["denim_jacket"] = 137,
		["leather_jacket"] = 137,
		["windbreaker"] = 160,
		["parka"] = 160,
		["raincoat"] = 221,
		["long_raincoat"] = 221,
		["vest"] = 167,
		["tank_top"] = 129,
		["camisole"] = 128,
		["halter_top"] = 128,
		["off_shoulder_top"] = 128,
		["crop_top"] = 132,
		["tunic"] = 221,
		["long_tunic"] = 221,
		["bodysuit"] = 128,
		["overalls"] = 216,
		["dress"] = 221,
		["mini_dress"] = 221,
		["midi_dress"] = 221,
		["maxi_dress"] = 221,
		["jumpsuit"] = 216,
		["romper"] = 216
	};

	private static readonly Dictionary<string, int> PantsTemplates = new Dictionary<string, int>(StringComparer.Ordinal)
	{
		["pants"] = 0,
		["leggings"] = 9,
		["jeans"] = 0,
		["cargo_pants"] = 0,
		["wide_leg_pants"] = 0,
		["chinos"] = 0,
		["joggers"] = 9,
		["sweatpants"] = 9,
		["culottes"] = 1,
		["shorts"] = 1,
		["skirt"] = 3,
		["mini_skirt"] = 3,
		["midi_skirt"] = 3,
		["maxi_skirt"] = 2,
		["pencil_skirt"] = 3,
		["pleated_skirt"] = 3,
		["dress"] = 2,
		["mini_dress"] = 3,
		["midi_dress"] = 3,
		["maxi_dress"] = 2,
		["jumpsuit"] = 0,
		["romper"] = 1,
		["coat"] = 2,
		["trench_coat"] = 2,
		["overcoat"] = 2,
		["raincoat"] = 2,
		["long_raincoat"] = 2,
		["parka"] = 2,
		["tunic"] = 2,
		["long_tunic"] = 2,
		["overalls"] = 0,
		["bodysuit"] = 1
	};

	private static readonly Dictionary<string, PantsDetailProfile> PantsDetailProfiles = new Dictionary<string, PantsDetailProfile>(StringComparer.Ordinal)
	{
		["pants"] = new PantsDetailProfile(18, 29, 7, 20, 0, 1, SkirtLike: false, CargoPockets: false, Cuffed: false),
		["leggings"] = new PantsDetailProfile(19, 29, 6, 21, 0, 2, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["jeans"] = new PantsDetailProfile(18, 29, 7, 20, 0, 3, SkirtLike: false, CargoPockets: false, Cuffed: false),
		["cargo_pants"] = new PantsDetailProfile(18, 28, 6, 21, 0, 4, SkirtLike: false, CargoPockets: true, Cuffed: false),
		["wide_leg_pants"] = new PantsDetailProfile(18, 30, 5, 21, 0, 5, SkirtLike: false, CargoPockets: false, Cuffed: false),
		["chinos"] = new PantsDetailProfile(19, 29, 7, 20, 0, 6, SkirtLike: false, CargoPockets: false, Cuffed: false),
		["joggers"] = new PantsDetailProfile(18, 28, 6, 21, 0, 7, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["sweatpants"] = new PantsDetailProfile(19, 28, 5, 22, 0, 8, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["culottes"] = new PantsDetailProfile(18, 26, 5, 20, 0, 9, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["shorts"] = new PantsDetailProfile(18, 25, 7, 20, 0, 10, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["skirt"] = new PantsDetailProfile(18, 28, 7, 20, 3, 11, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["mini_skirt"] = new PantsDetailProfile(19, 24, 7, 20, 4, 12, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["midi_skirt"] = new PantsDetailProfile(18, 27, 7, 21, 3, 13, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["maxi_skirt"] = new PantsDetailProfile(18, 30, 7, 21, 2, 14, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["pencil_skirt"] = new PantsDetailProfile(19, 29, 7, 22, 5, 15, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["pleated_skirt"] = new PantsDetailProfile(18, 29, 7, 20, 2, 16, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["dress"] = new PantsDetailProfile(18, 29, 7, 21, 4, 17, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["mini_dress"] = new PantsDetailProfile(18, 24, 7, 20, 4, 18, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["midi_dress"] = new PantsDetailProfile(18, 27, 7, 21, 3, 19, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["maxi_dress"] = new PantsDetailProfile(18, 30, 7, 22, 3, 20, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["jumpsuit"] = new PantsDetailProfile(18, 29, 7, 20, 0, 21, SkirtLike: false, CargoPockets: false, Cuffed: false),
		["romper"] = new PantsDetailProfile(18, 25, 6, 20, 0, 22, SkirtLike: false, CargoPockets: false, Cuffed: true),
		["coat"] = new PantsDetailProfile(18, 29, 7, 20, 4, 23, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["trench_coat"] = new PantsDetailProfile(18, 30, 7, 21, 4, 24, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["overcoat"] = new PantsDetailProfile(19, 30, 7, 22, 5, 25, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["raincoat"] = new PantsDetailProfile(19, 29, 7, 20, 3, 26, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["long_raincoat"] = new PantsDetailProfile(18, 30, 7, 20, 3, 27, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["parka"] = new PantsDetailProfile(19, 29, 7, 21, 4, 28, SkirtLike: true, CargoPockets: true, Cuffed: false),
		["tunic"] = new PantsDetailProfile(19, 27, 7, 21, 4, 29, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["long_tunic"] = new PantsDetailProfile(18, 28, 7, 20, 3, 30, SkirtLike: true, CargoPockets: false, Cuffed: false),
		["overalls"] = new PantsDetailProfile(18, 29, 6, 20, 0, 31, SkirtLike: false, CargoPockets: true, Cuffed: false),
		["bodysuit"] = new PantsDetailProfile(19, 25, 7, 21, 0, 32, SkirtLike: false, CargoPockets: false, Cuffed: true)
	};

	private static readonly Dictionary<string, int> HatTemplates = new Dictionary<string, int>(StringComparer.Ordinal)
	{
		["cap"] = 5,
		["hat"] = 4,
		["helmet"] = 50,
		["bow"] = 12,
		["crown"] = 97
	};

	private static readonly Dictionary<string, int> BootsTemplates = new Dictionary<string, int>(StringComparer.Ordinal)
	{
		["boots"] = 511,
		["shoes"] = 504,
		["sandals"] = 513
	};

	private readonly string generatedDirectory;

	private readonly SemanticRetriever retriever;

	private readonly List<Color> vanillaPalette;

	public SpriteRenderer(string modDirectory, SemanticRetriever retriever)
	{
		this.retriever = retriever;
		generatedDirectory = Path.Combine(modDirectory, "generated");
		vanillaPalette = LoadVanillaPalette(Path.Combine(modDirectory, "models", "style_profile.json"));
	}

	public OutfitRenderPreview Preview(OutfitSpec outfit)
	{
		ArgumentNullException.ThrowIfNull(outfit, "outfit");
		Dictionary<string, CompiledGarmentArt> dictionary = new Dictionary<string, CompiledGarmentArt>(StringComparer.Ordinal);
		List<GarmentRenderPreview> list = new List<GarmentRenderPreview>(outfit.Items.Count);
		for (int i = 0; i < outfit.Items.Count; i++)
		{
			GarmentSpec garmentSpec = outfit.Items[i];
			CompiledGarmentArt value = null;
			if (garmentSpec.SchemaVersion >= 2)
			{
				string key = ((garmentSpec.SchemaVersion >= 3 && !string.IsNullOrWhiteSpace(garmentSpec.LogicalGarmentId)) ? garmentSpec.LogicalGarmentId : $"item:{i}");
				if (!dictionary.TryGetValue(key, out value))
				{
					value = (dictionary[key] = GarmentArtCompiler.Compile(garmentSpec));
				}
				else if (garmentSpec.SchemaVersion >= 3)
				{
					value = value.WithArtworkRange(garmentSpec.ArtworkTop, garmentSpec.ArtworkBottom);
				}
			}
			list.Add(Preview(garmentSpec, i, value));
		}
		return new OutfitRenderPreview(outfit.OutfitName, list);
	}

	public GarmentRenderPreview Preview(GarmentSpec spec, int itemIndex = 0)
	{
		CompiledGarmentArt compiledArt = ((spec.SchemaVersion >= 2) ? GarmentArtCompiler.Compile(spec) : null);
		return Preview(spec, itemIndex, compiledArt);
	}

	private GarmentRenderPreview Preview(GarmentSpec spec, int itemIndex, CompiledGarmentArt? compiledArt)
	{
		ArgumentNullException.ThrowIfNull(spec, "spec");
		int templateIndex = ResolveTemplateIndex(spec);
		return spec.Category switch
		{
			"shirt" => PreviewShirt(spec, templateIndex, itemIndex, compiledArt), 
			"pants" => PreviewPants(spec, templateIndex, itemIndex, compiledArt), 
			"hat" => PreviewHat(spec, templateIndex, itemIndex, compiledArt), 
			"boots" => PreviewBoots(spec, templateIndex, itemIndex, compiledArt), 
			_ => throw new InvalidOperationException("Unsupported garment category: " + spec.Category), 
		};
	}

	public GeneratedGarment Render(GarmentSpec spec, string uniqueSuffix)
	{
		string text = spec.Category.ToLowerInvariant();
		string id = "Robin.PhotoTailor_" + uniqueSuffix + "_" + text;
		return Save(spec, id, Preview(spec));
	}

	public GeneratedGarment RenderPrepared(GarmentSpec spec, string uniqueSuffix, GarmentRenderPreview preview)
	{
		ArgumentNullException.ThrowIfNull(spec, "spec");
		ArgumentNullException.ThrowIfNull(preview, "preview");
		string text = spec.Category.ToLowerInvariant();
		string id = "Robin.PhotoTailor_" + uniqueSuffix + "_" + text;
		return Save(spec, id, preview);
	}

	public void RerenderExisting(GarmentSpec spec, GeneratedGarment garment)
	{
		GeneratedGarment generatedGarment = Save(spec, garment.Id, Preview(spec));
		garment.RendererVersion = generatedGarment.RendererVersion;
		garment.HasSleeves = generatedGarment.HasSleeves;
	}

	private int ResolveTemplateIndex(GarmentSpec spec)
	{
		if (spec.Category == "shirt")
		{
			if (spec.Silhouette == "crop_top" && spec.Coverage != "sleeveless")
			{
				return 141;
			}
			if (spec.Silhouette == "overalls" && spec.Coverage == "sleeveless")
			{
				return 217;
			}
			int? num = ResolveBlueprintShirtTemplate(spec);
			if (num.HasValue)
			{
				return num.GetValueOrDefault();
			}
		}
		if ((spec.Category switch
		{
			"shirt" => ShirtTemplates, 
			"pants" => PantsTemplates, 
			"hat" => HatTemplates, 
			"boots" => BootsTemplates, 
			_ => throw new InvalidOperationException("Unsupported garment category: " + spec.Category), 
		}).TryGetValue(spec.Silhouette, out var value))
		{
			return value;
		}
		return retriever.Retrieve(spec.Category, spec.SemanticDescription).SpriteIndex;
	}

	internal static int? ResolveBlueprintShirtTemplate(GarmentSpec spec)
	{
		ArgumentNullException.ThrowIfNull(spec, "spec");
		GarmentProportions garmentProportions = spec.Blueprint?.Proportions;
		if (garmentProportions == null)
		{
			return null;
		}
		string text = NormalizeToken(spec.Silhouette);
		bool flag;
		switch (text)
		{
		case "shirt":
		case "t_shirt":
		case "blouse":
		case "sweater":
		case "sweatshirt":
			flag = true;
			break;
		default:
			flag = false;
			break;
		}
		if (!flag)
		{
			return null;
		}
		string text2 = NormalizeToken(spec.Coverage);
		string text3 = NormalizeToken(spec.Neckline);
		bool num = text2 == "sleeveless" || garmentProportions.SleeveLength <= 0.08;
		bool flag2 = garmentProportions.GarmentLength > 0.0 && garmentProportions.GarmentLength <= 0.58;
		bool flag3 = garmentProportions.GarmentLength >= 0.84;
		bool flag4 = garmentProportions.OpenFront || spec.Blueprint.Features.Any(delegate(GarmentFeature feature)
		{
			string type = feature.Type;
			return (type == "buttons" || type == "zipper") ? true : false;
		});
		bool flag5 = text3 == "collared" || spec.Blueprint.Features.Any((GarmentFeature feature) => feature.Type == "collar");
		if (num)
		{
			return flag2 ? 132 : 129;
		}
		if (text3 == "hooded")
		{
			return 160;
		}
		if (flag2)
		{
			return 141;
		}
		if (flag4 & flag3)
		{
			return 221;
		}
		if (flag4)
		{
			return (garmentProportions.Fit == "oversized") ? 137 : 140;
		}
		if (flag5)
		{
			return 140;
		}
		if (garmentProportions.Fit == "oversized")
		{
			return flag3 ? 221 : 176;
		}
		int value;
		switch (text)
		{
		case "blouse":
			value = 2;
			break;
		case "sweater":
		case "sweatshirt":
			flag = true;
			goto IL_0268;
		default:
			{
				flag = false;
				goto IL_0268;
			}
			IL_0268:
			value = (flag ? 176 : 128);
			break;
		}
		return value;
	}

	private GarmentRenderPreview PreviewShirt(GarmentSpec spec, int templateIndex, int itemIndex, CompiledGarmentArt? compiledArt)
	{
		Texture2D val = Game1.content.Load<Texture2D>("Characters/Farmer/shirts");
		int num = templateIndex % 16 * 8;
		int y = templateIndex / 16 * 32;
		Color[] baseLayer = Crop(val, num, y, 8, 32);
		Color[] dyeLayer = Crop(val, num + val.Width / 2, y, 8, 32);
		Color[] array = MergeShirtLayers(baseLayer, dyeLayer);
		ValidateVanillaShirtCoverage(array, spec.Silhouette);
		Color[] array2 = (Color[])(object)new Color[8192];
		int num2;
		if (spec.Coverage != "sleeveless")
		{
			string silhouette = spec.Silhouette;
			switch (silhouette)
			{
			default:
				num2 = ((!(silhouette == "halter_top")) ? 1 : 0);
				break;
			case "vest":
			case "tank_top":
			case "camisole":
				num2 = 0;
				break;
			}
		}
		else
		{
			num2 = 0;
		}
		bool flag = (byte)num2 != 0;
		Color[] array3 = Recolor(array, 8, 32, spec, 8, 8, softenTileBoundary: true, TextureProjectionMode.FourFacingVertical, compiledArt);
		if (spec.SchemaVersion < 2)
		{
			ApplyShirtDetails(array3, spec);
		}
		if (compiledArt != null)
		{
			ApplyCompiledShirtMotifs(array3, compiledArt);
		}
		ApplyBlueprintShirtFeatures(array3, spec);
		if (flag)
		{
			ApplySleevePalette(array3, spec, spec.Silhouette);
		}
		EnsureSameAlphaTopology(array, array3, spec.Silhouette);
		Blit(array3, 8, 32, array2, 256, 0, 0);
		return new GarmentRenderPreview(itemIndex, templateIndex, spec, 256, 32, array2, flag, 0, 0, null, compiledArt?.CanonicalCanvas.Width ?? 0, compiledArt?.CanonicalCanvas.Height ?? 0, ToArtworkColors(compiledArt));
	}

	private static Color[] MergeShirtLayers(Color[] baseLayer, Color[] dyeLayer)
	{
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0021: Unknown result type (might be due to invalid IL or missing references)
		//IL_002f: Unknown result type (might be due to invalid IL or missing references)
		Color[] array = (Color[])(object)new Color[baseLayer.Length];
		for (int i = 0; i < array.Length; i++)
		{
			array[i] = ((((Color)(ref dyeLayer[i])).A >= 16) ? dyeLayer[i] : baseLayer[i]);
		}
		return array;
	}

	private static void ValidateVanillaShirtCoverage(Color[] pixels, string silhouette)
	{
		int num = silhouette switch
		{
			"crop_top" => 165, 
			"tank_top" => 190, 
			"overalls" => 205, 
			_ => 215, 
		};
		int num2 = ((silhouette == "crop_top") ? 40 : ((!(silhouette == "tank_top")) ? 50 : 45));
		int num3 = num2;
		int num4 = 0;
		for (int i = 0; i < 4; i++)
		{
			int num5 = pixels.Skip(i * 64).Take(64).Count((Color pixel) => ((Color)(ref pixel)).A >= 16);
			if (num5 < num3)
			{
				throw new InvalidDataException($"Vanilla shirt topology '{silhouette}' has only {num5} covered pixels in facing {i}.");
			}
			num4 += num5;
		}
		if (num4 < num)
		{
			throw new InvalidDataException($"Vanilla shirt topology '{silhouette}' has only {num4} covered pixels.");
		}
	}

	private static void EnsureSameAlphaTopology(Color[] reference, Color[] rendered, string silhouette)
	{
		if (reference.Length != rendered.Length)
		{
			throw new InvalidDataException("Rendered garment topology '" + silhouette + "' changed dimensions.");
		}
		for (int i = 0; i < reference.Length; i++)
		{
			if (((Color)(ref reference[i])).A >= 16 != ((Color)(ref rendered[i])).A >= 16)
			{
				throw new InvalidDataException($"Rendered garment topology '{silhouette}' changed coverage at pixel {i}.");
			}
		}
	}

	private void ApplySleevePalette(Color[] pixels, GarmentSpec spec, string silhouette)
	{
		//IL_0014: Unknown result type (might be due to invalid IL or missing references)
		//IL_0028: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		List<Color> fallbackPalette = BuildAdaptivePalette(spec);
		Color[] array = BuildSleeveSwatches(spec, fallbackPalette);
		SetSleeveSwatch(pixels, 4, array[0], silhouette, "dark");
		SetSleeveSwatch(pixels, 3, array[1], silhouette, "mid");
		SetSleeveSwatch(pixels, 2, array[2], silhouette, "light");
	}

	internal static Color[] BuildSleeveSwatches(GarmentSpec spec, IReadOnlyList<Color> fallbackPalette)
	{
		//IL_00f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f5: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0282: Unknown result type (might be due to invalid IL or missing references)
		//IL_0287: Unknown result type (might be due to invalid IL or missing references)
		//IL_028e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0213: Unknown result type (might be due to invalid IL or missing references)
		//IL_0218: Unknown result type (might be due to invalid IL or missing references)
		//IL_0222: Unknown result type (might be due to invalid IL or missing references)
		//IL_0229: Unknown result type (might be due to invalid IL or missing references)
		//IL_022e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0235: Unknown result type (might be due to invalid IL or missing references)
		//IL_0237: Unknown result type (might be due to invalid IL or missing references)
		//IL_023e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0245: Unknown result type (might be due to invalid IL or missing references)
		//IL_024a: Unknown result type (might be due to invalid IL or missing references)
		//IL_011b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0120: Unknown result type (might be due to invalid IL or missing references)
		//IL_0127: Unknown result type (might be due to invalid IL or missing references)
		//IL_0436: Unknown result type (might be due to invalid IL or missing references)
		//IL_0440: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_045e: Unknown result type (might be due to invalid IL or missing references)
		//IL_044f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0459: Unknown result type (might be due to invalid IL or missing references)
		//IL_0143: Unknown result type (might be due to invalid IL or missing references)
		//IL_0148: Unknown result type (might be due to invalid IL or missing references)
		//IL_014f: Unknown result type (might be due to invalid IL or missing references)
		//IL_047d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0487: Unknown result type (might be due to invalid IL or missing references)
		//IL_04a5: Unknown result type (might be due to invalid IL or missing references)
		//IL_04af: Unknown result type (might be due to invalid IL or missing references)
		//IL_04b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_04b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_04be: Unknown result type (might be due to invalid IL or missing references)
		//IL_04c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_04c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_0496: Unknown result type (might be due to invalid IL or missing references)
		//IL_04a0: Unknown result type (might be due to invalid IL or missing references)
		//IL_016b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0170: Unknown result type (might be due to invalid IL or missing references)
		ArgumentNullException.ThrowIfNull(spec, "spec");
		ArgumentNullException.ThrowIfNull(fallbackPalette, "fallbackPalette");
		List<Color> photoPalette = spec.SleevePalette.Select(ParseColor).ToList();
		if (photoPalette.Count <= 0 || spec.SleevePatternWidth <= 0 || spec.SleevePatternHeight <= 0 || spec.SleevePatternMap.Count < spec.SleevePatternWidth * spec.SleevePatternHeight)
		{
			Color color = (Color)((photoPalette.Count > 0) ? photoPalette[0] : ((fallbackPalette.Count > 0) ? fallbackPalette[0] : new Color(58, 57, 70)));
			return (Color[])(object)new Color[3]
			{
				Shade(color, (photoPalette.Count > 0) ? 0.7f : 0.58f),
				Shade(color, (photoPalette.Count > 0) ? 1f : 0.82f),
				Shade(color, (photoPalette.Count > 0) ? 1.14f : 1.08f)
			};
		}
		int[] counts = new int[photoPalette.Count];
		int occupied = 0;
		int num = spec.SleevePatternWidth * spec.SleevePatternHeight;
		for (int i = 0; i < num; i++)
		{
			int num2 = spec.SleevePatternMap[i];
			if (num2 >= 0 && num2 < counts.Length)
			{
				counts[num2]++;
				occupied++;
			}
		}
		if (occupied == 0)
		{
			Color val = photoPalette[0];
			return (Color[])(object)new Color[3]
			{
				Shade(val, 0.7f),
				val,
				Shade(val, 1.14f)
			};
		}
		int dominantIndex = Enumerable.Range(0, counts.Length).MaxBy((int index) => counts[index]);
		Color dominant = photoPalette[dominantIndex];
		float dominantLuma = RelativeLuma(dominant);
		int minimumUsefulCells = Math.Max(2, (int)Math.Ceiling((double)occupied * 0.035));
		List<int> source = (from index in Enumerable.Range(0, counts.Length)
			where index != dominantIndex && counts[index] >= minimumUsefulCells
			select index).Where(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_000d: Unknown result type (might be due to invalid IL or missing references)
			return ColorDistance(photoPalette[index], dominant) >= 28f;
		}).Where(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_000d: Unknown result type (might be due to invalid IL or missing references)
			return IsTrustedPhotographedDark(photoPalette[index], dominant, counts[index], occupied, spec.Pattern);
		}).ToList();
		int? darkest = source.Where(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			return RelativeLuma(photoPalette[index]) < dominantLuma - 0.025f;
		}).OrderByDescending(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_001b: Unknown result type (might be due to invalid IL or missing references)
			return SleeveCandidateScore(photoPalette[index], counts[index], occupied, dominant, preferLight: false);
		}).Cast<int?>()
			.FirstOrDefault();
		int? lightest = source.Where(delegate(int index)
		{
			//IL_0022: Unknown result type (might be due to invalid IL or missing references)
			return index != darkest && RelativeLuma(photoPalette[index]) > dominantLuma + 0.025f;
		}).OrderByDescending(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_001b: Unknown result type (might be due to invalid IL or missing references)
			return SleeveCandidateScore(photoPalette[index], counts[index], occupied, dominant, preferLight: true);
		}).Cast<int?>()
			.FirstOrDefault();
		int? num3 = source.Where((int index) => index != darkest && index != lightest).OrderByDescending(delegate(int index)
		{
			//IL_0007: Unknown result type (might be due to invalid IL or missing references)
			//IL_000d: Unknown result type (might be due to invalid IL or missing references)
			return ColorDistance(photoPalette[index], dominant) * MathF.Sqrt((float)counts[index] / (float)occupied);
		}).Cast<int?>()
			.FirstOrDefault();
		if (num3.HasValue)
		{
			int valueOrDefault = num3.GetValueOrDefault();
			if (!darkest.HasValue && RelativeLuma(photoPalette[valueOrDefault]) <= dominantLuma)
			{
				darkest = valueOrDefault;
			}
			else if (!lightest.HasValue)
			{
				lightest = valueOrDefault;
			}
			else if (!darkest.HasValue)
			{
				darkest = valueOrDefault;
			}
		}
		Color val2;
		if (darkest.HasValue)
		{
			int valueOrDefault2 = darkest.GetValueOrDefault();
			val2 = Shade(photoPalette[valueOrDefault2], 0.88f);
		}
		else
		{
			val2 = Shade(dominant, 0.7f);
		}
		Color val3 = val2;
		Color val4;
		if (lightest.HasValue)
		{
			int valueOrDefault3 = lightest.GetValueOrDefault();
			val4 = Shade(photoPalette[valueOrDefault3], 1.04f);
		}
		else
		{
			val4 = Shade(dominant, 1.14f);
		}
		Color val5 = val4;
		return (Color[])(object)new Color[3] { val3, dominant, val5 };
	}

	private static float SleeveCandidateScore(Color candidate, int count, int total, Color dominant, bool preferLight)
	{
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_0011: Unknown result type (might be due to invalid IL or missing references)
		//IL_0030: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		float num = MathF.Sqrt((float)count / (float)Math.Max(1, total));
		float num2 = ColorDistance(candidate, dominant) / 255f;
		float num3 = (preferLight ? RelativeLuma(candidate) : (1f - RelativeLuma(candidate)));
		return num * 0.58f + num2 * 0.3f + num3 * 0.12f;
	}

	private static void SetSleeveSwatch(Color[] pixels, int y, Color color, string silhouette, string shade)
	{
		//IL_00a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a6: Unknown result type (might be due to invalid IL or missing references)
		int num = y * 8;
		if (num < 0 || num >= pixels.Length || ((Color)(ref pixels[num])).A < 16)
		{
			throw new InvalidDataException($"Vanilla shirt topology '{silhouette}' has no opaque {shade} sleeve swatch at (0,{y}).");
		}
		pixels[num] = new Color(((Color)(ref color)).R, ((Color)(ref color)).G, ((Color)(ref color)).B, ((Color)(ref pixels[num])).A);
	}

	private void ApplyShirtDetails(Color[] pixels, GarmentSpec spec)
	{
		//IL_000a: Unknown result type (might be due to invalid IL or missing references)
		//IL_000f: Unknown result type (might be due to invalid IL or missing references)
		//IL_001f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_0025: Unknown result type (might be due to invalid IL or missing references)
		//IL_0026: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_002c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0044: Unknown result type (might be due to invalid IL or missing references)
		//IL_1440: Unknown result type (might be due to invalid IL or missing references)
		//IL_144a: Unknown result type (might be due to invalid IL or missing references)
		//IL_1468: Unknown result type (might be due to invalid IL or missing references)
		//IL_146e: Unknown result type (might be due to invalid IL or missing references)
		//IL_147c: Unknown result type (might be due to invalid IL or missing references)
		//IL_1482: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b4e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b58: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b63: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b6d: Unknown result type (might be due to invalid IL or missing references)
		//IL_14d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_14df: Unknown result type (might be due to invalid IL or missing references)
		//IL_14e9: Unknown result type (might be due to invalid IL or missing references)
		//IL_07db: Unknown result type (might be due to invalid IL or missing references)
		//IL_07e5: Unknown result type (might be due to invalid IL or missing references)
		//IL_07f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_07fa: Unknown result type (might be due to invalid IL or missing references)
		//IL_128f: Unknown result type (might be due to invalid IL or missing references)
		//IL_1290: Unknown result type (might be due to invalid IL or missing references)
		//IL_1291: Unknown result type (might be due to invalid IL or missing references)
		//IL_082e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0838: Unknown result type (might be due to invalid IL or missing references)
		//IL_0843: Unknown result type (might be due to invalid IL or missing references)
		//IL_084d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0599: Unknown result type (might be due to invalid IL or missing references)
		//IL_05a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_05ad: Unknown result type (might be due to invalid IL or missing references)
		//IL_05b8: Unknown result type (might be due to invalid IL or missing references)
		//IL_05c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c56: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c60: Unknown result type (might be due to invalid IL or missing references)
		//IL_05d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_05dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_105a: Unknown result type (might be due to invalid IL or missing references)
		//IL_1065: Unknown result type (might be due to invalid IL or missing references)
		//IL_1395: Unknown result type (might be due to invalid IL or missing references)
		//IL_13a0: Unknown result type (might be due to invalid IL or missing references)
		//IL_06ea: Unknown result type (might be due to invalid IL or missing references)
		//IL_06f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_06fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0709: Unknown result type (might be due to invalid IL or missing references)
		//IL_0714: Unknown result type (might be due to invalid IL or missing references)
		//IL_071e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0559: Unknown result type (might be due to invalid IL or missing references)
		//IL_0564: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cf7: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d01: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ea2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0eac: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e73: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e7d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e87: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e92: Unknown result type (might be due to invalid IL or missing references)
		//IL_1223: Unknown result type (might be due to invalid IL or missing references)
		//IL_122e: Unknown result type (might be due to invalid IL or missing references)
		//IL_1239: Unknown result type (might be due to invalid IL or missing references)
		//IL_123f: Unknown result type (might be due to invalid IL or missing references)
		//IL_124d: Unknown result type (might be due to invalid IL or missing references)
		//IL_1253: Unknown result type (might be due to invalid IL or missing references)
		//IL_1261: Unknown result type (might be due to invalid IL or missing references)
		//IL_1267: Unknown result type (might be due to invalid IL or missing references)
		//IL_1275: Unknown result type (might be due to invalid IL or missing references)
		//IL_127b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f1d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f27: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f32: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f3d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f47: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f52: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f5d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f67: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f71: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f7b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f85: Unknown result type (might be due to invalid IL or missing references)
		//IL_12b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_12ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_12bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b89: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b9e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ba8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0fff: Unknown result type (might be due to invalid IL or missing references)
		//IL_100a: Unknown result type (might be due to invalid IL or missing references)
		//IL_1015: Unknown result type (might be due to invalid IL or missing references)
		//IL_1020: Unknown result type (might be due to invalid IL or missing references)
		//IL_1512: Unknown result type (might be due to invalid IL or missing references)
		//IL_1518: Unknown result type (might be due to invalid IL or missing references)
		//IL_1526: Unknown result type (might be due to invalid IL or missing references)
		//IL_152c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e21: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e2b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e35: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e3f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0610: Unknown result type (might be due to invalid IL or missing references)
		//IL_061b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0626: Unknown result type (might be due to invalid IL or missing references)
		//IL_0631: Unknown result type (might be due to invalid IL or missing references)
		//IL_0792: Unknown result type (might be due to invalid IL or missing references)
		//IL_079c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0647: Unknown result type (might be due to invalid IL or missing references)
		//IL_064d: Unknown result type (might be due to invalid IL or missing references)
		//IL_12e2: Unknown result type (might be due to invalid IL or missing references)
		//IL_12ec: Unknown result type (might be due to invalid IL or missing references)
		//IL_0752: Unknown result type (might be due to invalid IL or missing references)
		//IL_075d: Unknown result type (might be due to invalid IL or missing references)
		//IL_08f5: Unknown result type (might be due to invalid IL or missing references)
		//IL_08ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_090a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0914: Unknown result type (might be due to invalid IL or missing references)
		//IL_091f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0929: Unknown result type (might be due to invalid IL or missing references)
		//IL_0933: Unknown result type (might be due to invalid IL or missing references)
		//IL_10eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_10f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_069d: Unknown result type (might be due to invalid IL or missing references)
		//IL_06a8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a2e: Unknown result type (might be due to invalid IL or missing references)
		//IL_1574: Unknown result type (might be due to invalid IL or missing references)
		//IL_157a: Unknown result type (might be due to invalid IL or missing references)
		//IL_1589: Unknown result type (might be due to invalid IL or missing references)
		//IL_158f: Unknown result type (might be due to invalid IL or missing references)
		//IL_14fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_0814: Unknown result type (might be due to invalid IL or missing references)
		//IL_0810: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c70: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c86: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c90: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c9a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ca4: Unknown result type (might be due to invalid IL or missing references)
		//IL_1076: Unknown result type (might be due to invalid IL or missing references)
		//IL_107c: Unknown result type (might be due to invalid IL or missing references)
		//IL_099f: Unknown result type (might be due to invalid IL or missing references)
		//IL_09a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_09b4: Unknown result type (might be due to invalid IL or missing references)
		//IL_09be: Unknown result type (might be due to invalid IL or missing references)
		//IL_09c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_09d3: Unknown result type (might be due to invalid IL or missing references)
		//IL_09dd: Unknown result type (might be due to invalid IL or missing references)
		//IL_09e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_072e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0734: Unknown result type (might be due to invalid IL or missing references)
		//IL_0575: Unknown result type (might be due to invalid IL or missing references)
		//IL_057b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d11: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d1d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ebc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ed2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0edc: Unknown result type (might be due to invalid IL or missing references)
		//IL_1036: Unknown result type (might be due to invalid IL or missing references)
		//IL_103c: Unknown result type (might be due to invalid IL or missing references)
		//IL_11bb: Unknown result type (might be due to invalid IL or missing references)
		//IL_11c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_11cf: Unknown result type (might be due to invalid IL or missing references)
		//IL_11d9: Unknown result type (might be due to invalid IL or missing references)
		//IL_12a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_12a5: Unknown result type (might be due to invalid IL or missing references)
		//IL_12a6: Unknown result type (might be due to invalid IL or missing references)
		//IL_12ce: Unknown result type (might be due to invalid IL or missing references)
		//IL_12cf: Unknown result type (might be due to invalid IL or missing references)
		//IL_12d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_0867: Unknown result type (might be due to invalid IL or missing references)
		//IL_0864: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bec: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b1f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b29: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b33: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b3e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bb8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bbe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0bd7: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e4f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e55: Unknown result type (might be due to invalid IL or missing references)
		//IL_05f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_05f2: Unknown result type (might be due to invalid IL or missing references)
		//IL_07ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_07c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_07cc: Unknown result type (might be due to invalid IL or missing references)
		//IL_066c: Unknown result type (might be due to invalid IL or missing references)
		//IL_1107: Unknown result type (might be due to invalid IL or missing references)
		//IL_110d: Unknown result type (might be due to invalid IL or missing references)
		//IL_111c: Unknown result type (might be due to invalid IL or missing references)
		//IL_1122: Unknown result type (might be due to invalid IL or missing references)
		//IL_06b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_08da: Unknown result type (might be due to invalid IL or missing references)
		//IL_08e5: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ad9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ad5: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b0a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0b07: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a44: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a85: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a8f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a99: Unknown result type (might be due to invalid IL or missing references)
		//IL_0aa4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d96: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d93: Unknown result type (might be due to invalid IL or missing references)
		//IL_0fbd: Unknown result type (might be due to invalid IL or missing references)
		//IL_0fb9: Unknown result type (might be due to invalid IL or missing references)
		//IL_1542: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cb4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cca: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cd4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0cde: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ce8: Unknown result type (might be due to invalid IL or missing references)
		//IL_10d0: Unknown result type (might be due to invalid IL or missing references)
		//IL_10db: Unknown result type (might be due to invalid IL or missing references)
		//IL_13ee: Unknown result type (might be due to invalid IL or missing references)
		//IL_1404: Unknown result type (might be due to invalid IL or missing references)
		//IL_140e: Unknown result type (might be due to invalid IL or missing references)
		//IL_1418: Unknown result type (might be due to invalid IL or missing references)
		//IL_1423: Unknown result type (might be due to invalid IL or missing references)
		//IL_09f9: Unknown result type (might be due to invalid IL or missing references)
		//IL_09ff: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a18: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d58: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d62: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d6c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d77: Unknown result type (might be due to invalid IL or missing references)
		//IL_0eec: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f02: Unknown result type (might be due to invalid IL or missing references)
		//IL_0f0d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0778: Unknown result type (might be due to invalid IL or missing references)
		//IL_0774: Unknown result type (might be due to invalid IL or missing references)
		//IL_094c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0948: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c07: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c12: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c27: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c32: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c3d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0c47: Unknown result type (might be due to invalid IL or missing references)
		//IL_0ae5: Unknown result type (might be due to invalid IL or missing references)
		//IL_0db2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0dbd: Unknown result type (might be due to invalid IL or missing references)
		//IL_0dc8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0dde: Unknown result type (might be due to invalid IL or missing references)
		//IL_0de8: Unknown result type (might be due to invalid IL or missing references)
		//IL_0df2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0dfc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e07: Unknown result type (might be due to invalid IL or missing references)
		//IL_0e11: Unknown result type (might be due to invalid IL or missing references)
		//IL_10a5: Unknown result type (might be due to invalid IL or missing references)
		//IL_10a1: Unknown result type (might be due to invalid IL or missing references)
		//IL_13d3: Unknown result type (might be due to invalid IL or missing references)
		//IL_13cf: Unknown result type (might be due to invalid IL or missing references)
		//IL_067f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d43: Unknown result type (might be due to invalid IL or missing references)
		//IL_0d3f: Unknown result type (might be due to invalid IL or missing references)
		//IL_1337: Unknown result type (might be due to invalid IL or missing references)
		//IL_134c: Unknown result type (might be due to invalid IL or missing references)
		//IL_1356: Unknown result type (might be due to invalid IL or missing references)
		//IL_0967: Unknown result type (might be due to invalid IL or missing references)
		//IL_096d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0986: Unknown result type (might be due to invalid IL or missing references)
		//IL_0990: Unknown result type (might be due to invalid IL or missing references)
		//IL_11a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_11ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_06cc: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a57: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a5c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a63: Unknown result type (might be due to invalid IL or missing references)
		//IL_0a6f: Unknown result type (might be due to invalid IL or missing references)
		//IL_1555: Unknown result type (might be due to invalid IL or missing references)
		//IL_131b: Unknown result type (might be due to invalid IL or missing references)
		//IL_1317: Unknown result type (might be due to invalid IL or missing references)
		//IL_08a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_08a0: Unknown result type (might be due to invalid IL or missing references)
		//IL_10ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_10b6: Unknown result type (might be due to invalid IL or missing references)
		//IL_1366: Unknown result type (might be due to invalid IL or missing references)
		//IL_137c: Unknown result type (might be due to invalid IL or missing references)
		//IL_1386: Unknown result type (might be due to invalid IL or missing references)
		//IL_1208: Unknown result type (might be due to invalid IL or missing references)
		//IL_1204: Unknown result type (might be due to invalid IL or missing references)
		//IL_08af: Unknown result type (might be due to invalid IL or missing references)
		//IL_08b5: Unknown result type (might be due to invalid IL or missing references)
		//IL_08c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0fea: Unknown result type (might be due to invalid IL or missing references)
		//IL_0fe6: Unknown result type (might be due to invalid IL or missing references)
		//IL_1163: Unknown result type (might be due to invalid IL or missing references)
		//IL_115f: Unknown result type (might be due to invalid IL or missing references)
		//IL_118d: Unknown result type (might be due to invalid IL or missing references)
		//IL_1189: Unknown result type (might be due to invalid IL or missing references)
		List<Color> list = BuildAdaptivePalette(spec);
		Color val = list[0];
		Color val2 = list[Math.Min(2, list.Count - 1)];
		Color val3 = MakeOutline(val);
		Color val4 = Shade(val, 0.72f);
		Color val5 = Shade(val2, 1.08f);
		switch (spec.Silhouette)
		{
		case "t_shirt":
		{
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			for (int num35 = 1; num35 <= 6; num35++)
			{
				SetDetailPixel(pixels, 0, num35, 7, Shade(val, 0.86f));
			}
			break;
		}
		case "polo":
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 3, 2, val5);
			SetDetailPixel(pixels, 0, 4, 2, val4);
			SetDetailPixel(pixels, 0, 4, 3, val2);
			break;
		case "shirt":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			for (int num25 = 2; num25 <= 6; num25++)
			{
				SetDetailPixel(pixels, 0, 4, num25, (num25 % 2 == 0) ? val2 : val4);
			}
			break;
		}
		case "blouse":
			SetDetailPixel(pixels, 0, 3, 1, val5);
			SetDetailPixel(pixels, 0, 4, 1, val5);
			SetDetailPixel(pixels, 0, 1, 5, val4);
			SetDetailPixel(pixels, 0, 6, 5, val4);
			break;
		case "sweater":
		{
			for (int num23 = 2; num23 <= 5; num23++)
			{
				SetDetailPixel(pixels, 0, num23, 1, Shade(val, 0.82f));
			}
			for (int num24 = 1; num24 <= 6; num24++)
			{
				SetDetailPixel(pixels, 0, num24, 6, Shade(val, (num24 % 2 == 0) ? 0.78f : 0.94f));
			}
			break;
		}
		case "sweatshirt":
		{
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			for (int n = 1; n <= 6; n++)
			{
				SetDetailPixel(pixels, 0, n, 6, Shade(val, (n % 2 == 0) ? 0.8f : 0.96f));
			}
			break;
		}
		case "hoodie":
		{
			SetDetailPixel(pixels, 3, 2, 1, val3);
			SetDetailPixel(pixels, 3, 5, 1, val3);
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			SetDetailPixel(pixels, 0, 3, 2, val2);
			SetDetailPixel(pixels, 0, 4, 2, val2);
			for (int m = 2; m <= 5; m++)
			{
				SetDetailPixel(pixels, 0, m, 5, Shade(val, 0.78f));
			}
			break;
		}
		case "cardigan":
		{
			SetDetailPixel(pixels, 0, 2, 1, val4);
			SetDetailPixel(pixels, 0, 5, 1, val4);
			for (int num28 = 2; num28 <= 6; num28++)
			{
				SetDetailPixel(pixels, 0, 4, num28, (num28 % 2 == 0) ? val2 : val4);
			}
			break;
		}
		case "jacket":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			for (int num18 = 2; num18 <= 6; num18++)
			{
				SetDetailPixel(pixels, 0, 4, num18, val4);
			}
			SetDetailPixel(pixels, 0, 2, 5, val3);
			SetDetailPixel(pixels, 0, 5, 5, val3);
			break;
		}
		case "coat":
		{
			SetDetailPixel(pixels, 0, 2, 2, val3);
			SetDetailPixel(pixels, 0, 3, 3, val4);
			SetDetailPixel(pixels, 0, 5, 2, val3);
			SetDetailPixel(pixels, 0, 4, 3, val4);
			for (int num10 = 1; num10 <= 6; num10++)
			{
				SetDetailPixel(pixels, 0, num10, 5, (num10 == 4) ? val2 : val4);
			}
			break;
		}
		case "trench_coat":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 3, 2, val4);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 4, 2, val4);
			for (int num30 = 2; num30 <= 6; num30++)
			{
				SetDetailPixel(pixels, 0, 4, num30, (num30 % 2 == 0) ? val2 : val3);
			}
			for (int num31 = 1; num31 <= 6; num31++)
			{
				Color[] pixels2 = pixels;
				int x = num31;
				bool flag = ((num31 == 2 || num31 == 5) ? true : false);
				SetDetailPixel(pixels2, 0, x, 5, flag ? val3 : val4);
				SetDetailPixel(pixels, 3, num31, 2, Shade(val, 0.78f));
				SetDetailPixel(pixels, 3, num31, 5, val4);
			}
			SetDetailPixel(pixels, 1, 5, 5, val4);
			SetDetailPixel(pixels, 2, 2, 5, val4);
			break;
		}
		case "overcoat":
		{
			SetDetailPixel(pixels, 0, 1, 1, val3);
			SetDetailPixel(pixels, 0, 2, 2, val5);
			SetDetailPixel(pixels, 0, 6, 1, val3);
			SetDetailPixel(pixels, 0, 5, 2, val5);
			SetDetailPixel(pixels, 0, 4, 3, val2);
			SetDetailPixel(pixels, 0, 4, 4, val2);
			SetDetailPixel(pixels, 0, 4, 5, val2);
			for (int num14 = 2; num14 <= 6; num14++)
			{
				SetDetailPixel(pixels, 3, 4, num14, (num14 >= 5) ? val3 : val4);
			}
			for (int num15 = 1; num15 <= 6; num15++)
			{
				SetDetailPixel(pixels, 0, num15, 6, Shade(val, 0.78f));
			}
			SetDetailPixel(pixels, 1, 5, 6, val3);
			SetDetailPixel(pixels, 2, 2, 6, val3);
			break;
		}
		case "blazer":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 3, 2, val5);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 4, 2, val5);
			SetDetailPixel(pixels, 0, 4, 4, val2);
			SetDetailPixel(pixels, 0, 4, 5, val2);
			SetDetailPixel(pixels, 0, 2, 5, val4);
			SetDetailPixel(pixels, 0, 5, 5, val4);
			for (int num5 = 2; num5 <= 6; num5++)
			{
				SetDetailPixel(pixels, 3, 4, num5, Shade(val, 0.8f));
			}
			SetDetailPixel(pixels, 1, 5, 5, val4);
			break;
		}
		case "bomber_jacket":
		{
			for (int num33 = 2; num33 <= 6; num33++)
			{
				SetDetailPixel(pixels, 0, 4, num33, val3);
			}
			for (int num34 = 1; num34 <= 6; num34++)
			{
				Color color = Shade(val, (num34 % 2 == 0) ? 0.72f : 0.92f);
				SetDetailPixel(pixels, 0, num34, 6, color);
				SetDetailPixel(pixels, 3, num34, 6, color);
			}
			SetDetailPixel(pixels, 0, 2, 2, val2);
			SetDetailPixel(pixels, 0, 5, 2, val2);
			SetDetailPixel(pixels, 1, 5, 6, val4);
			SetDetailPixel(pixels, 2, 2, 6, val4);
			break;
		}
		case "denim_jacket":
		{
			for (int num19 = 1; num19 <= 6; num19++)
			{
				Color[] pixels2 = pixels;
				int x = num19;
				bool flag = (uint)(num19 - 3) <= 1u;
				SetDetailPixel(pixels2, 0, x, 2, flag ? val5 : val4);
				SetDetailPixel(pixels, 3, num19, 2, val4);
			}
			for (int num20 = 2; num20 <= 6; num20++)
			{
				SetDetailPixel(pixels, 0, 4, num20, (num20 % 2 == 0) ? val2 : val3);
			}
			SetDetailPixel(pixels, 0, 2, 4, val3);
			SetDetailPixel(pixels, 0, 5, 4, val3);
			SetDetailPixel(pixels, 1, 5, 3, val4);
			SetDetailPixel(pixels, 2, 2, 3, val4);
			break;
		}
		case "leather_jacket":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 3, 2, val5);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 5, 2, val5);
			for (int num8 = 0; num8 <= 4; num8++)
			{
				SetDetailPixel(pixels, 0, Math.Min(6, 2 + num8), 2 + num8, val3);
			}
			SetDetailPixel(pixels, 0, 2, 5, val2);
			SetDetailPixel(pixels, 0, 5, 5, val2);
			for (int num9 = 1; num9 <= 6; num9++)
			{
				SetDetailPixel(pixels, 3, num9, 2, Shade(val, 0.68f));
			}
			SetDetailPixel(pixels, 1, 5, 4, val3);
			break;
		}
		case "windbreaker":
		{
			for (int k = 2; k <= 6; k++)
			{
				SetDetailPixel(pixels, 0, 4, k, val3);
			}
			for (int l = 1; l <= 6; l++)
			{
				SetDetailPixel(pixels, 0, l, 3, val2);
				SetDetailPixel(pixels, 3, l, 3, val2);
			}
			SetDetailPixel(pixels, 0, 2, 6, val4);
			SetDetailPixel(pixels, 0, 5, 6, val4);
			SetDetailPixel(pixels, 1, 5, 6, val2);
			SetDetailPixel(pixels, 2, 2, 6, val2);
			break;
		}
		case "parka":
		{
			SetDetailPixel(pixels, 0, 3, 1, val3);
			SetDetailPixel(pixels, 0, 4, 1, val3);
			for (int num26 = 2; num26 <= 6; num26++)
			{
				SetDetailPixel(pixels, 0, 4, num26, val4);
			}
			SetDetailPixel(pixels, 0, 2, 3, val2);
			SetDetailPixel(pixels, 0, 5, 3, val2);
			SetDetailPixel(pixels, 0, 2, 6, val3);
			SetDetailPixel(pixels, 0, 5, 6, val3);
			for (int num27 = 1; num27 <= 6; num27++)
			{
				SetDetailPixel(pixels, 3, num27, 5, val4);
			}
			SetDetailPixel(pixels, 3, 2, 1, val3);
			SetDetailPixel(pixels, 3, 5, 1, val3);
			SetDetailPixel(pixels, 1, 5, 5, val2);
			SetDetailPixel(pixels, 2, 2, 5, val2);
			break;
		}
		case "raincoat":
		{
			SetDetailPixel(pixels, 0, 3, 1, val3);
			SetDetailPixel(pixels, 0, 4, 1, val3);
			for (int num16 = 1; num16 <= 6; num16++)
			{
				SetDetailPixel(pixels, 0, num16, 2, val5);
				SetDetailPixel(pixels, 3, num16, 2, val5);
			}
			for (int num17 = 2; num17 <= 6; num17++)
			{
				SetDetailPixel(pixels, 0, 4, num17, (num17 % 2 == 0) ? val2 : val4);
			}
			SetDetailPixel(pixels, 0, 2, 5, val3);
			SetDetailPixel(pixels, 0, 5, 5, val3);
			SetDetailPixel(pixels, 1, 5, 2, val5);
			SetDetailPixel(pixels, 2, 2, 2, val5);
			break;
		}
		case "long_raincoat":
		{
			for (int num6 = 1; num6 <= 6; num6++)
			{
				SetDetailPixel(pixels, 0, 4, num6, (num6 % 2 == 0) ? val5 : val3);
			}
			for (int num7 = 1; num7 <= 6; num7++)
			{
				SetDetailPixel(pixels, 0, num7, 2, val2);
				SetDetailPixel(pixels, 3, num7, 2, val2);
				SetDetailPixel(pixels, 3, num7, 6, val4);
			}
			SetDetailPixel(pixels, 0, 2, 5, val3);
			SetDetailPixel(pixels, 0, 5, 5, val3);
			SetDetailPixel(pixels, 1, 5, 2, val2);
			SetDetailPixel(pixels, 1, 5, 6, val4);
			SetDetailPixel(pixels, 2, 2, 2, val2);
			SetDetailPixel(pixels, 2, 2, 6, val4);
			break;
		}
		case "vest":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 3, 2, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 4, 2, val3);
			for (int num4 = 2; num4 <= 6; num4++)
			{
				SetDetailPixel(pixels, 0, 4, num4, Shade(val, 0.82f));
			}
			break;
		}
		case "tank_top":
			SetDetailPixel(pixels, 0, 2, 0, val3);
			SetDetailPixel(pixels, 0, 5, 0, val3);
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			break;
		case "camisole":
		{
			SetDetailPixel(pixels, 0, 2, 0, val3);
			SetDetailPixel(pixels, 0, 5, 0, val3);
			for (int num36 = 2; num36 <= 5; num36++)
			{
				SetDetailPixel(pixels, 0, num36, 2, val5);
			}
			SetDetailPixel(pixels, 3, 2, 0, val3);
			SetDetailPixel(pixels, 3, 5, 0, val3);
			for (int num37 = 2; num37 <= 5; num37++)
			{
				SetDetailPixel(pixels, 3, num37, 2, val4);
			}
			SetDetailPixel(pixels, 1, 6, 4, val4);
			SetDetailPixel(pixels, 2, 1, 4, val4);
			break;
		}
		case "halter_top":
			SetDetailPixel(pixels, 0, 2, 2, val3);
			SetDetailPixel(pixels, 0, 3, 1, val5);
			SetDetailPixel(pixels, 0, 4, 1, val5);
			SetDetailPixel(pixels, 0, 5, 2, val3);
			SetDetailPixel(pixels, 0, 3, 3, val4);
			SetDetailPixel(pixels, 0, 4, 3, val4);
			SetDetailPixel(pixels, 3, 3, 1, val2);
			SetDetailPixel(pixels, 3, 4, 1, val2);
			SetDetailPixel(pixels, 3, 2, 2, val3);
			SetDetailPixel(pixels, 3, 5, 2, val3);
			SetDetailPixel(pixels, 1, 5, 2, val4);
			break;
		case "off_shoulder_top":
		{
			for (int num32 = 1; num32 <= 6; num32++)
			{
				Color[] pixels2 = pixels;
				int x = num32;
				bool flag = ((num32 == 1 || num32 == 6) ? true : false);
				SetDetailPixel(pixels2, 0, x, 1, flag ? val3 : val5);
				pixels2 = pixels;
				x = num32;
				flag = ((num32 == 1 || num32 == 6) ? true : false);
				SetDetailPixel(pixels2, 3, x, 1, flag ? val3 : val4);
			}
			SetDetailPixel(pixels, 1, 5, 1, val5);
			SetDetailPixel(pixels, 2, 2, 1, val5);
			SetDetailPixel(pixels, 0, 2, 2, val4);
			SetDetailPixel(pixels, 0, 5, 2, val4);
			break;
		}
		case "crop_top":
		{
			for (int num29 = 1; num29 <= 6; num29++)
			{
				SetDetailPixel(pixels, 0, num29, 6, Shade(val, 0.76f));
			}
			break;
		}
		case "tunic":
		{
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			for (int num21 = 2; num21 <= 6; num21++)
			{
				SetDetailPixel(pixels, 0, 4, num21, Shade(val, 0.82f));
			}
			for (int num22 = 1; num22 <= 6; num22++)
			{
				SetDetailPixel(pixels, 0, num22, 6, (num22 % 2 == 0) ? val2 : val4);
				SetDetailPixel(pixels, 3, num22, 6, (num22 % 2 == 0) ? val4 : val5);
			}
			SetDetailPixel(pixels, 1, 5, 6, val4);
			SetDetailPixel(pixels, 2, 2, 6, val4);
			break;
		}
		case "long_tunic":
		{
			SetDetailPixel(pixels, 0, 3, 1, val5);
			SetDetailPixel(pixels, 0, 4, 1, val5);
			for (int num12 = 2; num12 <= 6; num12++)
			{
				SetDetailPixel(pixels, 0, 3, num12, Shade(val, 0.86f));
				SetDetailPixel(pixels, 3, 4, num12, Shade(val, 0.74f));
			}
			for (int num13 = 1; num13 <= 6; num13++)
			{
				Color[] pixels2 = pixels;
				int x = num13;
				bool flag = ((num13 == 2 || num13 == 5) ? true : false);
				SetDetailPixel(pixels2, 0, x, 6, flag ? val2 : val4);
				pixels2 = pixels;
				x = num13;
				flag = (uint)(num13 - 3) <= 1u;
				SetDetailPixel(pixels2, 3, x, 6, flag ? val2 : val4);
			}
			SetDetailPixel(pixels, 1, 5, 5, val2);
			SetDetailPixel(pixels, 2, 2, 5, val2);
			break;
		}
		case "overalls":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			SetDetailPixel(pixels, 0, 2, 2, val2);
			SetDetailPixel(pixels, 0, 5, 2, val2);
			for (int num11 = 2; num11 <= 5; num11++)
			{
				Color[] pixels2 = pixels;
				int x = num11;
				bool flag = (uint)(num11 - 3) <= 1u;
				SetDetailPixel(pixels2, 0, x, 4, flag ? val5 : val4);
			}
			break;
		}
		case "bodysuit":
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			SetDetailPixel(pixels, 0, 2, 6, Shade(val, 0.82f));
			SetDetailPixel(pixels, 0, 5, 6, Shade(val, 0.82f));
			SetDetailPixel(pixels, 0, 3, 7, Shade(val, 0.9f));
			SetDetailPixel(pixels, 0, 4, 7, Shade(val, 0.9f));
			break;
		case "dress":
			DrawBodiceSeams(pixels, 0, 1, 2, 3, val, val2, val4, 5, 0);
			break;
		case "mini_dress":
			DrawBodiceSeams(pixels, 0, 1, 2, 3, val, val2, val4, 4, 1);
			break;
		case "midi_dress":
			DrawBodiceSeams(pixels, 0, 1, 2, 3, val, val2, val4, 5, 2);
			break;
		case "maxi_dress":
			DrawBodiceSeams(pixels, 0, 1, 2, 3, val, val2, val4, 6, 3);
			break;
		case "jumpsuit":
		{
			SetDetailPixel(pixels, 0, 2, 1, val3);
			SetDetailPixel(pixels, 0, 5, 1, val3);
			for (int num = 2; num <= 5; num++)
			{
				Color[] pixels2 = pixels;
				int x = num;
				bool flag = (uint)(num - 3) <= 1u;
				SetDetailPixel(pixels2, 0, x, 3, flag ? val5 : val4);
			}
			for (int num2 = 1; num2 <= 6; num2++)
			{
				SetDetailPixel(pixels, 0, num2, 5, val2);
			}
			SetDetailPixel(pixels, 3, 2, 1, val3);
			SetDetailPixel(pixels, 3, 5, 1, val3);
			for (int num3 = 1; num3 <= 6; num3++)
			{
				SetDetailPixel(pixels, 3, num3, 5, val4);
			}
			SetDetailPixel(pixels, 1, 5, 5, val2);
			SetDetailPixel(pixels, 2, 2, 5, val2);
			break;
		}
		case "romper":
		{
			SetDetailPixel(pixels, 0, 3, 1, val4);
			SetDetailPixel(pixels, 0, 4, 1, val4);
			for (int i = 1; i <= 6; i++)
			{
				Color[] pixels2 = pixels;
				int x = i;
				bool flag = ((i == 2 || i == 5) ? true : false);
				SetDetailPixel(pixels2, 0, x, 4, flag ? val3 : val5);
			}
			for (int j = 2; j <= 5; j++)
			{
				SetDetailPixel(pixels, 3, j, 3, val4);
			}
			SetDetailPixel(pixels, 3, 3, 4, val2);
			SetDetailPixel(pixels, 3, 4, 4, val2);
			SetDetailPixel(pixels, 1, 5, 4, val5);
			SetDetailPixel(pixels, 2, 2, 4, val5);
			break;
		}
		}
		if (spec.Neckline == "v_neck")
		{
			SetDetailPixel(pixels, 0, 3, 1, val3);
			SetDetailPixel(pixels, 0, 4, 2, val3);
		}
		else if (spec.Neckline == "turtleneck")
		{
			SetDetailPixel(pixels, 0, 3, 0, Shade(val, 0.82f));
			SetDetailPixel(pixels, 0, 4, 0, Shade(val, 0.92f));
		}
		switch (spec.Detail)
		{
		case "buttons":
			SetDetailPixel(pixels, 0, 4, 2, val2);
			SetDetailPixel(pixels, 0, 4, 4, val2);
			SetDetailPixel(pixels, 0, 4, 6, val2);
			break;
		case "zipper":
		{
			for (int num39 = 2; num39 <= 6; num39++)
			{
				SetDetailPixel(pixels, 0, 4, num39, val3);
			}
			break;
		}
		case "pockets":
			SetDetailPixel(pixels, 0, 2, 5, Shade(val2, 0.9f));
			SetDetailPixel(pixels, 0, 5, 5, Shade(val2, 0.9f));
			break;
		case "ribbed_trim":
		{
			for (int num38 = 2; num38 <= 5; num38++)
			{
				SetDetailPixel(pixels, 0, num38, 6, Shade(val, (num38 % 2 == 0) ? 0.78f : 0.92f));
			}
			break;
		}
		}
		for (int num40 = 3; num40 <= 6; num40++)
		{
			SetDetailPixel(pixels, 1, 6, num40, Shade(val, 0.84f));
			SetDetailPixel(pixels, 2, 1, num40, Shade(val, 0.84f));
		}
	}

	private void ApplyBlueprintShirtFeatures(Color[] pixels, GarmentSpec spec)
	{
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		//IL_00bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00db: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00cd: Unknown result type (might be due to invalid IL or missing references)
		//IL_03a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_03ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_03b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_03c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_03cf: Unknown result type (might be due to invalid IL or missing references)
		//IL_03d5: Unknown result type (might be due to invalid IL or missing references)
		//IL_03e3: Unknown result type (might be due to invalid IL or missing references)
		//IL_03e9: Unknown result type (might be due to invalid IL or missing references)
		//IL_02d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_0467: Unknown result type (might be due to invalid IL or missing references)
		//IL_0473: Unknown result type (might be due to invalid IL or missing references)
		//IL_02f0: Unknown result type (might be due to invalid IL or missing references)
		//IL_0438: Unknown result type (might be due to invalid IL or missing references)
		//IL_0434: Unknown result type (might be due to invalid IL or missing references)
		//IL_035b: Unknown result type (might be due to invalid IL or missing references)
		//IL_037d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0393: Unknown result type (might be due to invalid IL or missing references)
		//IL_043a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0442: Unknown result type (might be due to invalid IL or missing references)
		//IL_044f: Unknown result type (might be due to invalid IL or missing references)
		//IL_032a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0326: Unknown result type (might be due to invalid IL or missing references)
		if (spec.SchemaVersion < 2 || spec.Blueprint == null || spec.Blueprint.Features.Count == 0)
		{
			return;
		}
		List<Color> list = BuildAdaptivePalette(spec);
		Color color = list[0];
		foreach (GarmentFeature item in from item in spec.Blueprint.Features
			where item.Confidence >= 0.55
			orderby item.Layer
			select item)
		{
			Color val = ((item.PaletteIndex >= 0 && item.PaletteIndex < list.Count) ? list[item.PaletteIndex] : list[Math.Min(2, list.Count - 1)]);
			Color val2 = Shade(val, 0.72f);
			int num = Math.Clamp((int)Math.Round((item.X + item.Width / 2.0) * 7.0), 1, 6);
			int num2 = Math.Clamp((int)Math.Floor(item.Y * 8.0), 0, 7);
			int num3 = Math.Clamp((int)Math.Ceiling((item.Y + item.Height) * 8.0) - 1, num2, 7);
			int num4 = Math.Clamp((int)Math.Floor(item.X * 8.0), 1, 6);
			int num5 = Math.Clamp((int)Math.Ceiling((item.X + item.Width) * 8.0) - 1, num4, 6);
			switch (NormalizeToken(item.Type))
			{
			case "logo":
			case "graphic":
				PaintBlueprintMotif(pixels, 0, num4, num5, num2, num3, val);
				break;
			case "buttons":
			{
				for (int num7 = Math.Max(1, num2); num7 <= Math.Min(6, num3); num7 += 2)
				{
					SetDetailPixel(pixels, 0, num, num7, val);
				}
				break;
			}
			case "zipper":
			{
				for (int num8 = Math.Max(1, num2); num8 <= Math.Min(6, num3); num8++)
				{
					SetDetailPixel(pixels, 0, num, num8, (num8 % 2 == 0) ? val : val2);
				}
				break;
			}
			case "pocket":
			{
				for (int num9 = num4; num9 <= num5; num9++)
				{
					SetDetailPixel(pixels, 0, num9, Math.Clamp(num3, 2, 6), val2);
				}
				SetDetailPixel(pixels, 0, num4, Math.Clamp(num3 - 1, 2, 6), val);
				SetDetailPixel(pixels, 0, num5, Math.Clamp(num3 - 1, 2, 6), val);
				break;
			}
			case "collar":
				SetDetailPixel(pixels, 0, 2, 1, val2);
				SetDetailPixel(pixels, 0, 3, 2, val);
				SetDetailPixel(pixels, 0, 5, 1, val2);
				SetDetailPixel(pixels, 0, 4, 2, val);
				SetDetailPixel(pixels, 3, 3, 1, Shade(color, 0.76f));
				SetDetailPixel(pixels, 3, 4, 1, Shade(color, 0.76f));
				break;
			case "belt":
			{
				int y = Math.Clamp((int)Math.Round((item.Y + item.Height / 2.0) * 7.0), 3, 6);
				for (int num6 = num4; num6 <= num5; num6++)
				{
					Color color2 = ((num6 == num) ? val : val2);
					SetDetailPixel(pixels, 0, num6, y, color2);
					SetDetailPixel(pixels, 3, num6, y, val2);
				}
				SetDetailPixel(pixels, 1, 5, y, val);
				SetDetailPixel(pixels, 2, 2, y, val);
				break;
			}
			}
		}
	}

	private static void PaintBlueprintMotif(Color[] pixels, int facing, int leftX, int rightX, int topY, int bottomY, Color fallback)
	{
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_0050: Unknown result type (might be due to invalid IL or missing references)
		//IL_0057: Unknown result type (might be due to invalid IL or missing references)
		//IL_007b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0082: Unknown result type (might be due to invalid IL or missing references)
		int num = Math.Clamp((leftX + rightX) / 2, 1, 6);
		int num2 = Math.Clamp((topY + bottomY) / 2, 2, 5);
		SetDetailPixel(pixels, facing, num, num2, fallback);
		if (rightX > leftX)
		{
			SetDetailPixel(pixels, facing, Math.Min(rightX, num + 1), num2, fallback);
		}
		if (bottomY > topY)
		{
			SetDetailPixel(pixels, facing, num, Math.Min(6, num2 + 1), Shade(fallback, 0.86f));
		}
		if (rightX - leftX >= 3 && bottomY - topY >= 2)
		{
			SetDetailPixel(pixels, facing, Math.Max(leftX, num - 1), num2, Shade(fallback, 1.08f));
		}
	}

	private static void DrawBodiceSeams(Color[] pixels, int frontFacing, int rightFacing, int leftFacing, int backFacing, Color primary, Color accent, Color seam, int waistY, int signature)
	{
		//IL_0004: Unknown result type (might be due to invalid IL or missing references)
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0019: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_007b: Unknown result type (might be due to invalid IL or missing references)
		//IL_008c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0098: Unknown result type (might be due to invalid IL or missing references)
		//IL_00a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_003d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0043: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0060: Unknown result type (might be due to invalid IL or missing references)
		SetDetailPixel(pixels, frontFacing, 3, 1, Shade(primary, 0.72f));
		SetDetailPixel(pixels, frontFacing, 4, 1, Shade(primary, 0.72f));
		for (int i = 1; i <= 6; i++)
		{
			Color color = ((i == 1 + signature % 5) ? accent : seam);
			SetDetailPixel(pixels, frontFacing, i, waistY, color);
			SetDetailPixel(pixels, backFacing, i, waistY, Shade(seam, 0.92f + (float)signature * 0.03f));
		}
		SetDetailPixel(pixels, frontFacing, 2 + signature % 3, 3, accent);
		SetDetailPixel(pixels, backFacing, 5 - signature % 3, 3, accent);
		SetDetailPixel(pixels, rightFacing, 5, waistY, accent);
		SetDetailPixel(pixels, leftFacing, 2, waistY, accent);
	}

	private static void SetDetailPixel(Color[] pixels, int frame, int x, int y, Color color)
	{
		//IL_0048: Unknown result type (might be due to invalid IL or missing references)
		//IL_004d: Unknown result type (might be due to invalid IL or missing references)
		int num = frame * 64 + y * 8 + x;
		if (num >= 0 && num < pixels.Length && ((Color)(ref pixels[num])).A >= 16)
		{
			pixels[num] = new Color(((Color)(ref color)).R, ((Color)(ref color)).G, ((Color)(ref color)).B, ((Color)(ref pixels[num])).A);
		}
	}

	private static void ApplyCompiledShirtMotifs(Color[] pixels, CompiledGarmentArt art)
	{
		(GarmentArtFacing, int)[] array = new(GarmentArtFacing, int)[4]
		{
			(GarmentArtFacing.Front, 0),
			(GarmentArtFacing.Right, 1),
			(GarmentArtFacing.Left, 2),
			(GarmentArtFacing.Back, 3)
		};
		for (int i = 0; i < array.Length; i++)
		{
			var (facing, num) = array[i];
			PaintCompiledMotifsInTile(pixels, 8, 0, num * 8, 8, 8, art.MotifsFor(facing));
		}
	}

	private static void ApplyCompiledPantsMotifs(Color[] pixels, CompiledGarmentArt art)
	{
		if (art.MotifStamps.Count == 0)
		{
			return;
		}
		for (int i = 0; i + 32 <= 672; i += 32)
		{
			for (int j = 0; j + 16 <= 192; j += 16)
			{
				GarmentFacing facing = ResolveFacing(TextureProjectionMode.PantsAnimation, j, i, 192, 16, 32);
				PaintCompiledMotifsInTile(pixels, 192, j, i, 16, 32, art.MotifsFor(ToArtFacing(facing)));
			}
		}
		PaintCompiledMotifsInTile(pixels, 192, 0, 672, 16, 16, art.MotifsFor(GarmentArtFacing.Front));
	}

	private static void PaintCompiledMotifsInTile(Color[] pixels, int canvasWidth, int tileX, int tileY, int tileWidth, int tileHeight, IReadOnlyList<GarmentMotifStamp> motifs)
	{
		//IL_0213: Unknown result type (might be due to invalid IL or missing references)
		//IL_0218: Unknown result type (might be due to invalid IL or missing references)
		//IL_0221: Unknown result type (might be due to invalid IL or missing references)
		//IL_0226: Unknown result type (might be due to invalid IL or missing references)
		//IL_02dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_02e1: Unknown result type (might be due to invalid IL or missing references)
		if (motifs.Count == 0 || canvasWidth <= 0 || tileWidth <= 0 || tileHeight <= 0)
		{
			return;
		}
		int num = pixels.Length / canvasWidth;
		if (tileX < 0 || tileY < 0 || tileX + tileWidth > canvasWidth || tileY + tileHeight > num)
		{
			return;
		}
		int num2 = tileWidth;
		int num3 = -1;
		int num4 = tileHeight;
		int num5 = -1;
		for (int i = 0; i < tileHeight; i++)
		{
			for (int j = 0; j < tileWidth; j++)
			{
				if (((Color)(ref pixels[(tileY + i) * canvasWidth + tileX + j])).A >= 16)
				{
					num2 = Math.Min(num2, j);
					num3 = Math.Max(num3, j);
					num4 = Math.Min(num4, i);
					num5 = Math.Max(num5, i);
				}
			}
		}
		if (num3 < num2 || num5 < num4)
		{
			return;
		}
		foreach (GarmentMotifStamp motif in motifs)
		{
			if (motif.Pixels.Count < 2)
			{
				continue;
			}
			int num6 = num2 + (int)Math.Round(motif.X * (double)Math.Max(0, num3 - num2));
			int num7 = num4 + (int)Math.Round(motif.Y * (double)Math.Max(0, num5 - num4));
			int num8 = int.MaxValue;
			int num9 = num6;
			int num10 = num7;
			List<int> list = new List<int>();
			for (int k = -2; k <= 2; k++)
			{
				for (int l = -2; l <= 2; l++)
				{
					int num11 = num6 + l;
					int num12 = num7 + k;
					List<int> list2 = LargestOpaqueMotifComponent(pixels, canvasWidth, tileX, tileY, tileWidth, tileHeight, num11, num12, motif.Pixels);
					int num13 = Math.Abs(l) + Math.Abs(k);
					if (list2.Count > list.Count || (list2.Count == list.Count && num13 < num8))
					{
						list = list2;
						num8 = num13;
						num9 = num11;
						num10 = num12;
					}
				}
			}
			if (list.Count < 2)
			{
				continue;
			}
			foreach (int item in list)
			{
				GarmentMotifPixel garmentMotifPixel = motif.Pixels[item];
				int num14 = tileX + num9 + garmentMotifPixel.X;
				int num15 = (tileY + num10 + garmentMotifPixel.Y) * canvasWidth + num14;
				Color val = pixels[num15];
				Color val2 = ToColor(garmentMotifPixel.Color);
				double num16 = Math.Clamp(motif.Opacity, 0.0, 1.0);
				pixels[num15] = new Color((byte)Math.Clamp((int)Math.Round((double)(int)((Color)(ref val)).R + (double)(((Color)(ref val2)).R - ((Color)(ref val)).R) * num16), 0, 255), (byte)Math.Clamp((int)Math.Round((double)(int)((Color)(ref val)).G + (double)(((Color)(ref val2)).G - ((Color)(ref val)).G) * num16), 0, 255), (byte)Math.Clamp((int)Math.Round((double)(int)((Color)(ref val)).B + (double)(((Color)(ref val2)).B - ((Color)(ref val)).B) * num16), 0, 255), ((Color)(ref val)).A);
			}
		}
	}

	private static List<int> LargestOpaqueMotifComponent(Color[] pixels, int canvasWidth, int tileX, int tileY, int tileWidth, int tileHeight, int anchorX, int anchorY, IReadOnlyList<GarmentMotifPixel> motif)
	{
		HashSet<int> hashSet = new HashSet<int>();
		for (int i = 0; i < motif.Count; i++)
		{
			int num = anchorX + motif[i].X;
			int num2 = anchorY + motif[i].Y;
			if (num >= 0 && num < tileWidth && num2 >= 0 && num2 < tileHeight && ((Color)(ref pixels[(tileY + num2) * canvasWidth + tileX + num])).A >= 16)
			{
				hashSet.Add(i);
			}
		}
		List<int> list = new List<int>();
		HashSet<int> hashSet2 = new HashSet<int>();
		foreach (int item in hashSet)
		{
			if (!hashSet2.Add(item))
			{
				continue;
			}
			Queue<int> queue = new Queue<int>();
			List<int> list2 = new List<int>();
			queue.Enqueue(item);
			while (queue.Count > 0)
			{
				int num3 = queue.Dequeue();
				list2.Add(num3);
				GarmentMotifPixel garmentMotifPixel = motif[num3];
				foreach (int item2 in hashSet)
				{
					if (!hashSet2.Contains(item2))
					{
						GarmentMotifPixel garmentMotifPixel2 = motif[item2];
						if (Math.Abs(garmentMotifPixel.X - garmentMotifPixel2.X) + Math.Abs(garmentMotifPixel.Y - garmentMotifPixel2.Y) == 1)
						{
							hashSet2.Add(item2);
							queue.Enqueue(item2);
						}
					}
				}
			}
			if (list2.Count > list.Count)
			{
				list = list2;
			}
		}
		return list;
	}

	private GarmentRenderPreview PreviewPants(GarmentSpec spec, int templateIndex, int itemIndex, CompiledGarmentArt? compiledArt)
	{
		Texture2D obj = Game1.content.Load<Texture2D>("Characters/Farmer/pants");
		int num = obj.Width / 192;
		Color[] array = Crop(obj, templateIndex % num * 192, templateIndex / num * 688, 192, 688);
		Color[] array2 = Recolor(array, 192, 688, spec, 16, 32, softenTileBoundary: false, TextureProjectionMode.PantsAnimation, compiledArt);
		if (spec.SchemaVersion < 2)
		{
			ApplyPantsDetails(array2, spec);
		}
		if (compiledArt != null)
		{
			ApplyCompiledPantsMotifs(array2, compiledArt);
		}
		ApplyBlueprintPantsFeatures(array2, spec);
		EnsureSameAlphaTopology(array, array2, spec.Silhouette);
		return new GarmentRenderPreview(itemIndex, templateIndex, spec, 192, 688, array2, hasSleeves: true, 0, 0, null, compiledArt?.CanonicalCanvas.Width ?? 0, compiledArt?.CanonicalCanvas.Height ?? 0, ToArtworkColors(compiledArt));
	}

	private void ApplyPantsDetails(Color[] pixels, GarmentSpec spec)
	{
		//IL_001f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		//IL_0034: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Unknown result type (might be due to invalid IL or missing references)
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_004d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0052: Unknown result type (might be due to invalid IL or missing references)
		//IL_021c: Unknown result type (might be due to invalid IL or missing references)
		//IL_020f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0215: Unknown result type (might be due to invalid IL or missing references)
		//IL_0248: Unknown result type (might be due to invalid IL or missing references)
		//IL_0238: Unknown result type (might be due to invalid IL or missing references)
		//IL_0234: Unknown result type (might be due to invalid IL or missing references)
		//IL_0252: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Unknown result type (might be due to invalid IL or missing references)
		//IL_028e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0293: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ba: Unknown result type (might be due to invalid IL or missing references)
		//IL_02bf: Unknown result type (might be due to invalid IL or missing references)
		//IL_027c: Unknown result type (might be due to invalid IL or missing references)
		//IL_026f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0275: Unknown result type (might be due to invalid IL or missing references)
		if (!PantsDetailProfiles.TryGetValue(spec.Silhouette, out var value))
		{
			return;
		}
		List<Color> list = BuildAdaptivePalette(spec);
		Color color = list[0];
		Color val = list[Math.Min(2, list.Count - 1)];
		Color val2 = Shade(color, 0.67f);
		Color val3 = Shade(val, 1.08f);
		for (int i = 0; i < 688; i++)
		{
			int num = i % 32;
			for (int j = 0; j < 192; j++)
			{
				int num2 = i * 192 + j;
				if (((Color)(ref pixels[num2])).A >= 16)
				{
					int num3 = j % 16;
					bool flag = num == value.WaistY && num3 >= 3 && num3 <= 12;
					bool num4 = num == value.HemY && num3 >= 2 && num3 <= 13;
					bool flag2 = num == value.PocketY && (num3 == 3 + value.Signature % 3 || num3 == 12 - value.Signature % 3);
					bool flag3 = value.CargoPockets && num >= 21 && num <= 23 && ((num3 >= 2 && num3 <= 4) || (num3 >= 11 && num3 <= 13));
					bool flag4;
					if (value.SkirtLike)
					{
						int num5 = Math.Max(2, value.PleatStep);
						flag4 = spec.Silhouette == "pleated_skirt" && num > value.WaistY && num < value.HemY && (num3 + value.Signature) % num5 == 0;
					}
					else
					{
						flag4 = num > value.PocketY && num < value.HemY && (num3 == value.SeamX || num3 == 15 - value.SeamX);
					}
					bool num6 = value.Cuffed && num == value.HemY - 1 && num3 >= 3 && num3 <= 12;
					Color? val4 = null;
					if (flag)
					{
						val4 = ((value.Signature % 2 == 0) ? val2 : Shade(color, 0.78f));
					}
					if (flag4)
					{
						val4 = ((value.Signature % 3 == 0) ? val3 : val2);
					}
					if (flag2 | flag3)
					{
						val4 = val;
					}
					if (num6)
					{
						val4 = Shade(color, 0.58f);
					}
					if (num4)
					{
						val4 = (value.SkirtLike ? val3 : Shade(color, 0.72f));
					}
					if (val4.HasValue)
					{
						Color valueOrDefault = val4.GetValueOrDefault();
						pixels[num2] = new Color(((Color)(ref valueOrDefault)).R, ((Color)(ref valueOrDefault)).G, ((Color)(ref valueOrDefault)).B, ((Color)(ref pixels[num2])).A);
					}
				}
			}
		}
	}

	private void ApplyBlueprintPantsFeatures(Color[] pixels, GarmentSpec spec)
	{
		//IL_016a: Unknown result type (might be due to invalid IL or missing references)
		//IL_017f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0181: Unknown result type (might be due to invalid IL or missing references)
		//IL_0188: Unknown result type (might be due to invalid IL or missing references)
		//IL_018d: Unknown result type (might be due to invalid IL or missing references)
		//IL_017a: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0232: Unknown result type (might be due to invalid IL or missing references)
		//IL_024b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0261: Unknown result type (might be due to invalid IL or missing references)
		//IL_0296: Unknown result type (might be due to invalid IL or missing references)
		//IL_0292: Unknown result type (might be due to invalid IL or missing references)
		if (spec.SchemaVersion < 2 || spec.Blueprint == null || spec.Blueprint.Features.Count == 0)
		{
			return;
		}
		PantsDetailProfiles.TryGetValue(spec.Silhouette, out var value);
		int num = ((value.WaistY > 0) ? value.WaistY : 18);
		int num2 = ((value.PocketY > 0) ? value.PocketY : 21);
		int num3 = ((value.HemY > 0) ? value.HemY : 29);
		List<Color> list = BuildAdaptivePalette(spec);
		foreach (GarmentFeature item in from item in spec.Blueprint.Features
			where item.Confidence >= 0.55
			orderby item.Layer
			select item)
		{
			string text = NormalizeToken(item.Type);
			bool flag;
			switch (text)
			{
			case "belt":
			case "pocket":
			case "buttons":
			case "zipper":
				flag = true;
				break;
			default:
				flag = false;
				break;
			}
			if (!flag)
			{
				continue;
			}
			Color val = ((item.PaletteIndex >= 0 && item.PaletteIndex < list.Count) ? list[item.PaletteIndex] : list[Math.Min(2, list.Count - 1)]);
			Color val2 = Shade(val, 0.7f);
			for (int num4 = 0; num4 < 688; num4 += 32)
			{
				for (int num5 = 0; num5 < 192; num5 += 16)
				{
					switch (text)
					{
					case "belt":
					{
						for (int num8 = 3; num8 <= 12; num8++)
						{
							SetPantsDetailPixel(pixels, num5, num4, num8, num, (num8 == 8) ? val : val2);
						}
						break;
					}
					case "pocket":
					{
						int localX = ((item.Side == "left") ? 4 : 11);
						SetPantsDetailPixel(pixels, num5, num4, localX, num2, val);
						SetPantsDetailPixel(pixels, num5, num4, localX, Math.Min(num3 - 1, num2 + 1), val2);
						break;
					}
					case "buttons":
					{
						for (int num7 = num; num7 <= Math.Min(num3 - 2, num + 5); num7 += 2)
						{
							SetPantsDetailPixel(pixels, num5, num4, 8, num7, val);
						}
						break;
					}
					case "zipper":
					{
						for (int num6 = num; num6 <= Math.Min(num3 - 2, num + 5); num6++)
						{
							SetPantsDetailPixel(pixels, num5, num4, 8, num6, (num6 % 2 == 0) ? val : val2);
						}
						break;
					}
					}
				}
			}
		}
	}

	private static void SetPantsDetailPixel(Color[] pixels, int tileX, int tileY, int localX, int localY, Color color)
	{
		//IL_005f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0064: Unknown result type (might be due to invalid IL or missing references)
		int num = tileX + localX;
		int num2 = tileY + localY;
		if (num >= 0 && num < 192 && num2 >= 0 && num2 < 688)
		{
			int num3 = num2 * 192 + num;
			if (((Color)(ref pixels[num3])).A >= 16)
			{
				pixels[num3] = new Color(((Color)(ref color)).R, ((Color)(ref color)).G, ((Color)(ref color)).B, ((Color)(ref pixels[num3])).A);
			}
		}
	}

	private GarmentRenderPreview PreviewHat(GarmentSpec spec, int templateIndex, int itemIndex, CompiledGarmentArt? compiledArt)
	{
		Texture2D obj = Game1.content.Load<Texture2D>("Characters/Farmer/hats");
		int num = obj.Width / 20;
		Color[] source = Crop(obj, templateIndex % num * 20, templateIndex / num * 80, 20, 80);
		Color[] pixels = Recolor(source, 20, 80, spec, 20, 20, softenTileBoundary: false, TextureProjectionMode.FourFacingVertical, compiledArt);
		return new GarmentRenderPreview(itemIndex, templateIndex, spec, 20, 80, pixels, hasSleeves: true, 0, 0, null, compiledArt?.CanonicalCanvas.Width ?? 0, compiledArt?.CanonicalCanvas.Height ?? 0, ToArtworkColors(compiledArt));
	}

	private GarmentRenderPreview PreviewBoots(GarmentSpec spec, int templateIndex, int itemIndex, CompiledGarmentArt? compiledArt)
	{
		//IL_004a: Unknown result type (might be due to invalid IL or missing references)
		//IL_004f: Unknown result type (might be due to invalid IL or missing references)
		//IL_005b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0061: Unknown result type (might be due to invalid IL or missing references)
		//IL_0066: Unknown result type (might be due to invalid IL or missing references)
		//IL_006e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0074: Unknown result type (might be due to invalid IL or missing references)
		//IL_0079: Unknown result type (might be due to invalid IL or missing references)
		//IL_0081: Unknown result type (might be due to invalid IL or missing references)
		//IL_0087: Unknown result type (might be due to invalid IL or missing references)
		//IL_008c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0094: Unknown result type (might be due to invalid IL or missing references)
		//IL_009a: Unknown result type (might be due to invalid IL or missing references)
		//IL_009f: Unknown result type (might be due to invalid IL or missing references)
		Texture2D obj = Game1.content.Load<Texture2D>("Maps/springobjects");
		int num = obj.Width / 16;
		Color[] source = Crop(obj, templateIndex % num * 16, templateIndex / num * 16, 16, 16);
		Color[] pixels = Recolor(source, 16, 16, spec, 16, 16, softenTileBoundary: false, TextureProjectionMode.Uniform, compiledArt);
		Color color = ParseColor(spec.PrimaryColor);
		return new GarmentRenderPreview(itemIndex, templateIndex, spec, 16, 16, pixels, hasSleeves: true, 4, 1, (Color[]?)(object)new Color[4]
		{
			Shade(color, 0.42f),
			Shade(color, 0.68f),
			Shade(color, 0.92f),
			Shade(color, 1.18f)
		}, compiledArt?.CanonicalCanvas.Width ?? 0, compiledArt?.CanonicalCanvas.Height ?? 0, ToArtworkColors(compiledArt));
	}

	private GeneratedGarment Save(GarmentSpec spec, string id, GarmentRenderPreview preview)
	{
		Directory.CreateDirectory(generatedDirectory);
		string text = id + ".png";
		SavePng(Path.Combine(generatedDirectory, text), preview.Pixels, preview.Width, preview.Height);
		File.WriteAllText(Path.Combine(generatedDirectory, id + ".spec.json"), JsonSerializer.Serialize(spec, new JsonSerializerOptions
		{
			WriteIndented = true
		}));
		GeneratedGarment generatedGarment = new GeneratedGarment
		{
			RendererVersion = 11,
			Id = id,
			Category = spec.Category,
			Name = Sanitize(spec.Name, 60),
			Description = "由照片裁缝根据外部图片生成，并经过原版服装风格模型约束。",
			TexturePath = "generated/" + text,
			TextureAsset = "Mods/Robin.PhotoTailor/Generated/" + id + "/texture",
			LogicalGarmentId = (string.IsNullOrWhiteSpace(spec.LogicalGarmentId) ? null : spec.LogicalGarmentId),
			HasSleeves = preview.HasSleeves
		};
		if (preview.HasArtwork)
		{
			string text2 = Path.Combine(generatedDirectory, "art");
			Directory.CreateDirectory(text2);
			string text3 = ((spec.SchemaVersion >= 3 && !string.IsNullOrWhiteSpace(spec.LogicalGarmentId)) ? SafeFileKey(spec.LogicalGarmentId) : SafeFileKey(id)) + ".png";
			SavePng(Path.Combine(text2, text3), preview.ArtworkPixels, preview.ArtworkWidth, preview.ArtworkHeight);
			generatedGarment.ArtworkPath = "generated/art/" + text3;
			generatedGarment.ArtworkWidth = preview.ArtworkWidth;
			generatedGarment.ArtworkHeight = preview.ArtworkHeight;
		}
		if (preview.HasPalette)
		{
			string text4 = id + ".palette.png";
			SavePng(Path.Combine(generatedDirectory, text4), preview.PalettePixels, preview.PaletteWidth, preview.PaletteHeight);
			generatedGarment.PalettePath = "generated/" + text4;
			generatedGarment.PaletteAsset = "Mods/Robin.PhotoTailor/Generated/" + id + "/palette";
		}
		return generatedGarment;
	}

	private static Color[]? ToArtworkColors(CompiledGarmentArt? compiledArt)
	{
		return ((IEnumerable<GarmentArtRgba>)compiledArt?.CanonicalCanvas.Pixels).Select((Func<GarmentArtRgba, Color>)delegate(GarmentArtRgba pixel)
		{
			//IL_001c: Unknown result type (might be due to invalid IL or missing references)
			return new Color(pixel.R, pixel.G, pixel.B, pixel.A);
		}).ToArray();
	}

	private Color[] Recolor(Color[] source, int width, int height, GarmentSpec spec, int repeatWidth, int repeatHeight, bool softenTileBoundary = false, TextureProjectionMode projectionMode = TextureProjectionMode.Uniform, CompiledGarmentArt? compiledArt = null)
	{
		//IL_000b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_0025: Unknown result type (might be due to invalid IL or missing references)
		//IL_0035: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_003b: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0042: Unknown result type (might be due to invalid IL or missing references)
		//IL_0047: Unknown result type (might be due to invalid IL or missing references)
		//IL_009a: Unknown result type (might be due to invalid IL or missing references)
		//IL_009f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_00b5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01af: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0194: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Unknown result type (might be due to invalid IL or missing references)
		//IL_0292: Unknown result type (might be due to invalid IL or missing references)
		//IL_0296: Unknown result type (might be due to invalid IL or missing references)
		//IL_0287: Unknown result type (might be due to invalid IL or missing references)
		//IL_028b: Unknown result type (might be due to invalid IL or missing references)
		//IL_01db: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0302: Unknown result type (might be due to invalid IL or missing references)
		//IL_0306: Unknown result type (might be due to invalid IL or missing references)
		//IL_030b: Unknown result type (might be due to invalid IL or missing references)
		//IL_032d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0332: Unknown result type (might be due to invalid IL or missing references)
		//IL_029b: Unknown result type (might be due to invalid IL or missing references)
		//IL_02bd: Unknown result type (might be due to invalid IL or missing references)
		//IL_02c2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e0: Unknown result type (might be due to invalid IL or missing references)
		//IL_023e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0235: Unknown result type (might be due to invalid IL or missing references)
		//IL_0237: Unknown result type (might be due to invalid IL or missing references)
		//IL_0240: Unknown result type (might be due to invalid IL or missing references)
		//IL_0251: Unknown result type (might be due to invalid IL or missing references)
		//IL_0253: Unknown result type (might be due to invalid IL or missing references)
		//IL_0254: Unknown result type (might be due to invalid IL or missing references)
		//IL_0255: Unknown result type (might be due to invalid IL or missing references)
		//IL_0265: Unknown result type (might be due to invalid IL or missing references)
		//IL_025f: Unknown result type (might be due to invalid IL or missing references)
		//IL_026a: Unknown result type (might be due to invalid IL or missing references)
		//IL_026f: Unknown result type (might be due to invalid IL or missing references)
		List<Color> list = BuildAdaptivePalette(spec);
		Color val = list[0];
		Color secondary = list[Math.Min(1, list.Count - 1)];
		Color val2 = list[Math.Min(2, list.Count - 1)];
		Color val3 = Mix(val, val2, 0.52f);
		if (compiledArt == null)
		{
			compiledArt = ((spec.SchemaVersion >= 2) ? GarmentArtCompiler.Compile(spec) : null);
		}
		TextureProjectionContext textureProjectionContext = ((compiledArt == null) ? BuildTextureProjection(spec, list) : null);
		Color[] array = (Color[])(object)new Color[source.Length];
		for (int i = 0; i < height; i++)
		{
			for (int j = 0; j < width; j++)
			{
				int num = i * width + j;
				Color val4 = source[num];
				if (((Color)(ref val4)).A < 16)
				{
					array[num] = Color.Transparent;
					continue;
				}
				float num2 = (0.2126f * (float)(int)((Color)(ref val4)).R + 0.7152f * (float)(int)((Color)(ref val4)).G + 0.0722f * (float)(int)((Color)(ref val4)).B) / 255f;
				int num3 = j % repeatWidth;
				int num4 = i % repeatHeight;
				GarmentFacing garmentFacing = ResolveFacing(projectionMode, j, i, width, repeatWidth, repeatHeight);
				Color val5;
				if (compiledArt != null)
				{
					double u = ((double)num3 + 0.5) / Math.Max(1.0, repeatWidth);
					double v = ((double)num4 + 0.5) / Math.Max(1.0, repeatHeight);
					val5 = ToColor(compiledArt.SampleProjection(ToArtFacing(garmentFacing), u, v, 1.0 / (double)Math.Max(1, repeatWidth), 1.0 / (double)Math.Max(1, repeatHeight)));
				}
				else
				{
					Color val6 = PickPatternColor(spec.Pattern, num3, num4, repeatWidth, repeatHeight, val, secondary, val2, val3);
					if (IsPlacedFrontPattern(spec.Pattern) && garmentFacing != GarmentFacing.Front && garmentFacing != GarmentFacing.Uniform)
					{
						val6 = textureProjectionContext?.BaseColor ?? val;
					}
					bool flag = (object)textureProjectionContext != null && IsPlacedFrontPattern(spec.Pattern);
					if (flag)
					{
						bool flag2 = (uint)garmentFacing <= 1u;
						flag = flag2;
					}
					bool flag3 = flag && !textureProjectionContext.HasSalientDetail;
					val5 = ((((object)textureProjectionContext == null) | flag3) ? val6 : PickTextureColor(textureProjectionContext, num3, num4, repeatWidth, repeatHeight, garmentFacing, val6));
					val5 = EnforcePatternStructure(spec.Pattern, num3, num4, repeatWidth, repeatHeight, val5, val, secondary, val2, (list.Count > 3) ? list[3] : val3);
				}
				if (IsTopologyBoundary(source, width, height, j, i, repeatWidth, repeatHeight))
				{
					Color val7 = (softenTileBoundary ? SoftenShirtBoundary(val5, num2) : SoftenGarmentBoundary(val5, num2));
					array[num] = new Color(((Color)(ref val7)).R, ((Color)(ref val7)).G, ((Color)(ref val7)).B, ((Color)(ref val4)).A);
					continue;
				}
				float num5 = ((compiledArt == null) ? (0.72f + 0.48f * num2) : (0.88f + 0.24f * num2));
				num5 = MathF.Round(num5 * 8f) / 8f;
				Color val8 = Shade(val5, num5);
				array[num] = new Color(((Color)(ref val8)).R, ((Color)(ref val8)).G, ((Color)(ref val8)).B, ((Color)(ref val4)).A);
			}
		}
		return array;
	}

	private static Color SoftenShirtBoundary(Color target, float sourceLuma)
	{
		//IL_001d: Unknown result type (might be due to invalid IL or missing references)
		//IL_001f: Unknown result type (might be due to invalid IL or missing references)
		float factor = Math.Clamp(0.55f + 0.48f * sourceLuma, 0.6f, 0.94f);
		return Shade(target, factor);
	}

	private static Color SoftenGarmentBoundary(Color target, float sourceLuma)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0031: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		float factor = ((RelativeLuma(target) < 0.25f) ? 0.96f : Math.Clamp(0.78f + 0.18f * sourceLuma, 0.8f, 0.96f));
		return Shade(target, factor);
	}

	private static Color EnforcePatternStructure(string pattern, int x, int y, int width, int height, Color sampled, Color primary, Color secondary, Color accent, Color fourth)
	{
		//IL_0063: Unknown result type (might be due to invalid IL or missing references)
		//IL_0052: Unknown result type (might be due to invalid IL or missing references)
		//IL_0059: Unknown result type (might be due to invalid IL or missing references)
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0060: Unknown result type (might be due to invalid IL or missing references)
		//IL_0031: Unknown result type (might be due to invalid IL or missing references)
		if (pattern == "vertical_stripes")
		{
			int num = x * 8 / Math.Max(1, width);
			if ((num == 1 || num == 6) ? true : false)
			{
				return fourth;
			}
			if (num == 4)
			{
				return accent;
			}
		}
		else if (pattern == "horizontal_stripes")
		{
			switch (y * 8 / Math.Max(1, height))
			{
			case 3:
				return fourth;
			case 4:
				return secondary;
			case 6:
				return primary;
			}
		}
		return sampled;
	}

	private static bool IsTopologyBoundary(Color[] source, int width, int height, int x, int y, int tileWidth, int tileHeight)
	{
		int num = x % tileWidth;
		int num2 = y % tileHeight;
		if (num == 0 || num2 == 0 || num == tileWidth - 1 || num2 == tileHeight - 1)
		{
			return true;
		}
		(int, int)[] array = new(int, int)[4]
		{
			(-1, 0),
			(1, 0),
			(0, -1),
			(0, 1)
		};
		for (int i = 0; i < array.Length; i++)
		{
			(int, int) tuple = array[i];
			int item = tuple.Item1;
			int item2 = tuple.Item2;
			int num3 = x + item;
			int num4 = y + item2;
			if (num3 < 0 || num3 >= width || num4 < 0 || num4 >= height || ((Color)(ref source[num4 * width + num3])).A < 16)
			{
				return true;
			}
		}
		return false;
	}

	private static Color PickTextureColor(TextureProjectionContext projection, int localX, int localY, int repeatWidth, int repeatHeight, GarmentFacing facing, Color fallback)
	{
		//IL_0029: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b0: Unknown result type (might be due to invalid IL or missing references)
		bool flag = IsPlacedFrontPattern(projection.Pattern);
		if (flag)
		{
			bool flag2 = (uint)(facing - 2) <= 2u;
			flag = flag2;
		}
		if (flag)
		{
			return projection.BaseColor;
		}
		int num = 0;
		int num2 = projection.Width;
		if (facing == GarmentFacing.Right && projection.Width >= 3)
		{
			num = projection.Width * 2 / 3;
		}
		else if (facing == GarmentFacing.Left && projection.Width >= 3)
		{
			num2 = Math.Max(1, (projection.Width + 2) / 3);
		}
		int num3 = Math.Max(1, num2 - num);
		int value = num + localX * num3 / Math.Max(1, repeatWidth);
		int value2 = num + (int)Math.Ceiling((double)((localX + 1) * num3) / (double)Math.Max(1, repeatWidth));
		int value3 = localY * projection.Height / Math.Max(1, repeatHeight);
		int value4 = (int)Math.Ceiling((double)((localY + 1) * projection.Height) / (double)Math.Max(1, repeatHeight));
		value = Math.Clamp(value, num, num2 - 1);
		value2 = Math.Clamp(value2, value + 1, num2);
		value3 = Math.Clamp(value3, 0, projection.Height - 1);
		int num4 = Math.Clamp(value4, value3 + 1, projection.Height);
		IReadOnlyList<int> map = projection.Map;
		int width = projection.Width;
		int height = projection.Height;
		int startX = value;
		int endX = value2;
		int startY = value3;
		int endY = num4;
		IReadOnlyList<int> histogram = projection.Histogram;
		int occupied = projection.Occupied;
		IReadOnlyList<Color> palette = projection.Palette;
		int baseIndex = projection.BaseIndex;
		flag = (uint)facing <= 1u;
		int num5 = SelectSalientPatternIndex(map, width, height, startX, endX, startY, endY, histogram, occupied, palette, baseIndex, flag && IsSaliencePattern(projection.Pattern), projection.Pattern);
		if (num5 < 0 || num5 >= projection.Palette.Count)
		{
			return fallback;
		}
		return projection.Palette[num5];
	}

	internal static int SelectSalientPatternIndex(IReadOnlyList<int> map, int mapWidth, int mapHeight, int startX, int endX, int startY, int endY, IReadOnlyList<int> histogram, int occupied, IReadOnlyList<Color> palette, int baseIndex, bool preserveSalient, string pattern = "")
	{
		//IL_0139: Unknown result type (might be due to invalid IL or missing references)
		//IL_0142: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ab: Unknown result type (might be due to invalid IL or missing references)
		//IL_01cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d4: Unknown result type (might be due to invalid IL or missing references)
		if (mapWidth <= 0 || mapHeight <= 0 || map.Count < mapWidth * mapHeight)
		{
			return -1;
		}
		startX = Math.Clamp(startX, 0, mapWidth - 1);
		endX = Math.Clamp(endX, startX + 1, mapWidth);
		startY = Math.Clamp(startY, 0, mapHeight - 1);
		endY = Math.Clamp(endY, startY + 1, mapHeight);
		Span<int> span = ((palette.Count > 64) ? ((Span<int>)new int[palette.Count]) : stackalloc int[palette.Count]);
		Span<int> span2 = span;
		int num = 0;
		for (int i = startY; i < endY; i++)
		{
			for (int j = startX; j < endX; j++)
			{
				int num2 = map[i * mapWidth + j];
				if (num2 >= 0 && num2 < palette.Count && num2 < histogram.Count)
				{
					span2[num2]++;
					num++;
				}
			}
		}
		if (num == 0)
		{
			return -1;
		}
		int num3 = 0;
		for (int k = 1; k < span2.Length; k++)
		{
			if (span2[k] > span2[num3])
			{
				num3 = k;
			}
		}
		if (!preserveSalient || baseIndex < 0 || baseIndex >= palette.Count || occupied <= 0)
		{
			return num3;
		}
		int result = (IsTrustedPhotographedDark(palette[num3], palette[baseIndex], histogram[num3], occupied, pattern) ? num3 : baseIndex);
		double num4 = double.NegativeInfinity;
		for (int l = 0; l < span2.Length; l++)
		{
			int num5 = span2[l];
			if (num5 == 0)
			{
				continue;
			}
			double num6 = (double)num5 / (double)num;
			double num7 = (double)histogram[l] / (double)occupied;
			if (IsTrustedPhotographedDark(palette[l], palette[baseIndex], histogram[l], occupied, pattern))
			{
				double num8 = Math.Clamp((double)ColorDistance(palette[l], palette[baseIndex]) / 150.0, 0.0, 1.0);
				double num9 = ((histogram[l] >= 2) ? ((1.0 - num7) * num8 * 0.86) : 0.0);
				double num10 = ((l == baseIndex) ? 0.08 : 0.0);
				double num11 = num6 + num9 + num10;
				if (num11 > num4)
				{
					num4 = num11;
					result = l;
				}
			}
		}
		return result;
	}

	private static TextureProjectionContext? BuildTextureProjection(GarmentSpec spec, IReadOnlyList<Color> palette)
	{
		if (spec.PatternWidth <= 0 || spec.PatternHeight <= 0 || spec.PatternMap.Count < spec.PatternWidth * spec.PatternHeight || palette.Count == 0)
		{
			return null;
		}
		int num = spec.PatternWidth * spec.PatternHeight;
		int[] histogram = new int[palette.Count];
		int occupied = 0;
		for (int i = 0; i < num; i++)
		{
			int num2 = spec.PatternMap[i];
			if (num2 >= 0 && num2 < histogram.Length)
			{
				histogram[num2]++;
				occupied++;
			}
		}
		if (occupied == 0)
		{
			return null;
		}
		int baseIndex = Enumerable.Range(0, histogram.Length).MaxBy((int index) => histogram[index]);
		bool hasSalientDetail = Enumerable.Range(0, histogram.Length).Any(delegate(int index)
		{
			//IL_001b: Unknown result type (might be due to invalid IL or missing references)
			//IL_002c: Unknown result type (might be due to invalid IL or missing references)
			//IL_0058: Unknown result type (might be due to invalid IL or missing references)
			//IL_0069: Unknown result type (might be due to invalid IL or missing references)
			return index != baseIndex && histogram[index] >= 2 && IsTrustedPhotographedDark(palette[index], palette[baseIndex], histogram[index], occupied, spec.Pattern) && ColorDistance(palette[index], palette[baseIndex]) >= 28f;
		});
		return new TextureProjectionContext(spec.PatternMap, spec.PatternWidth, spec.PatternHeight, palette, histogram, occupied, baseIndex, hasSalientDetail, spec.Pattern);
	}

	private static GarmentFacing ResolveFacing(TextureProjectionMode mode, int x, int y, int width, int repeatWidth, int repeatHeight)
	{
		if (repeatHeight <= 0)
		{
			return GarmentFacing.Uniform;
		}
		switch (mode)
		{
		case TextureProjectionMode.FourFacingVertical:
			return (y / repeatHeight % 4) switch
			{
				0 => GarmentFacing.Front, 
				1 => GarmentFacing.Right, 
				2 => GarmentFacing.Left, 
				_ => GarmentFacing.Back, 
			};
		case TextureProjectionMode.PantsAnimation:
			if (repeatWidth > 0 && y < 672)
			{
				int num = Math.Max(1, width / repeatWidth);
				int num2 = y / repeatHeight * num + x / repeatWidth;
				return ((num2 < 216) ? ((num2 < 192) ? (num2 % 32 / 8) : ((num2 >= 200) ? ((num2 - 200) / 4) : ((num2 - 192) / 2))) : ((num2 >= 232) ? ((num2 - 232) / 8) : 0)) switch
				{
					1 => GarmentFacing.Right, 
					2 => GarmentFacing.Back, 
					3 => GarmentFacing.Left, 
					_ => GarmentFacing.Front, 
				};
			}
			goto default;
		default:
			return GarmentFacing.Uniform;
		}
	}

	private static GarmentArtFacing ToArtFacing(GarmentFacing facing)
	{
		return facing switch
		{
			GarmentFacing.Right => GarmentArtFacing.Right, 
			GarmentFacing.Left => GarmentArtFacing.Left, 
			GarmentFacing.Back => GarmentArtFacing.Back, 
			_ => GarmentArtFacing.Front, 
		};
	}

	private static bool IsPlacedFrontPattern(string pattern)
	{
		if (pattern == "graphic" || pattern == "logo")
		{
			return true;
		}
		return false;
	}

	private static bool IsSaliencePattern(string pattern)
	{
		switch (pattern)
		{
		case "graphic":
		case "logo":
		case "floral":
		case "polka_dot":
		case "animal_print":
			return true;
		default:
			return false;
		}
	}

	private static Color PickPatternColor(string pattern, int x, int localY, int repeatWidth, int repeatHeight, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_02ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_02ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_02af: Unknown result type (might be due to invalid IL or missing references)
		//IL_0265: Unknown result type (might be due to invalid IL or missing references)
		//IL_0267: Unknown result type (might be due to invalid IL or missing references)
		//IL_0269: Unknown result type (might be due to invalid IL or missing references)
		//IL_026b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0270: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01eb: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ef: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_0252: Unknown result type (might be due to invalid IL or missing references)
		//IL_0254: Unknown result type (might be due to invalid IL or missing references)
		//IL_0256: Unknown result type (might be due to invalid IL or missing references)
		//IL_0258: Unknown result type (might be due to invalid IL or missing references)
		//IL_025d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0283: Unknown result type (might be due to invalid IL or missing references)
		//IL_0285: Unknown result type (might be due to invalid IL or missing references)
		//IL_02a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_02a9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0213: Unknown result type (might be due to invalid IL or missing references)
		//IL_0215: Unknown result type (might be due to invalid IL or missing references)
		//IL_0217: Unknown result type (might be due to invalid IL or missing references)
		//IL_0219: Unknown result type (might be due to invalid IL or missing references)
		//IL_021b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0220: Unknown result type (might be due to invalid IL or missing references)
		//IL_022b: Unknown result type (might be due to invalid IL or missing references)
		//IL_022d: Unknown result type (might be due to invalid IL or missing references)
		//IL_022f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0231: Unknown result type (might be due to invalid IL or missing references)
		//IL_0233: Unknown result type (might be due to invalid IL or missing references)
		//IL_0238: Unknown result type (might be due to invalid IL or missing references)
		//IL_01fe: Unknown result type (might be due to invalid IL or missing references)
		//IL_0200: Unknown result type (might be due to invalid IL or missing references)
		//IL_0202: Unknown result type (might be due to invalid IL or missing references)
		//IL_0204: Unknown result type (might be due to invalid IL or missing references)
		//IL_0206: Unknown result type (might be due to invalid IL or missing references)
		//IL_020b: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ac: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ae: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b0: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b2: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b9: Unknown result type (might be due to invalid IL or missing references)
		//IL_0197: Unknown result type (might be due to invalid IL or missing references)
		//IL_0199: Unknown result type (might be due to invalid IL or missing references)
		//IL_019b: Unknown result type (might be due to invalid IL or missing references)
		//IL_019d: Unknown result type (might be due to invalid IL or missing references)
		//IL_019f: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a4: Unknown result type (might be due to invalid IL or missing references)
		//IL_0275: Unknown result type (might be due to invalid IL or missing references)
		//IL_0277: Unknown result type (might be due to invalid IL or missing references)
		//IL_0279: Unknown result type (might be due to invalid IL or missing references)
		//IL_027b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0280: Unknown result type (might be due to invalid IL or missing references)
		//IL_023d: Unknown result type (might be due to invalid IL or missing references)
		//IL_023f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0241: Unknown result type (might be due to invalid IL or missing references)
		//IL_0243: Unknown result type (might be due to invalid IL or missing references)
		//IL_0245: Unknown result type (might be due to invalid IL or missing references)
		//IL_024a: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c1: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c5: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c7: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_01ce: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d6: Unknown result type (might be due to invalid IL or missing references)
		//IL_01d8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01da: Unknown result type (might be due to invalid IL or missing references)
		//IL_01dc: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e1: Unknown result type (might be due to invalid IL or missing references)
		return (Color)(pattern switch
		{
			"horizontal_stripes" => HorizontalStripe(x, localY, primary, secondary, accent, neutral), 
			"vertical_stripes" => VerticalStripe(x, localY, primary, secondary, accent, neutral), 
			"plaid" => Plaid(x, localY, primary, secondary, accent, neutral), 
			"polka_dot" => PolkaDot(x, localY, primary, secondary, accent), 
			"floral" => Floral(x, localY, primary, secondary, accent, neutral), 
			"animal_print" => AnimalPrint(x, localY, primary, secondary, accent, neutral), 
			"camouflage" => Camouflage(x, localY, primary, secondary, accent, neutral), 
			"color_block" => ColorBlock(x, localY, repeatWidth, repeatHeight, primary, secondary, accent, neutral), 
			"geometric" => Geometric(x, localY, primary, secondary, accent, neutral), 
			"graphic" => Graphic(x, localY, repeatWidth, repeatHeight, primary, secondary, accent), 
			"logo" => Graphic(x, localY, repeatWidth, repeatHeight, primary, secondary, accent), 
			"denim" => Denim(x, localY, primary, secondary, accent), 
			"gradient" => Mix(primary, secondary, Math.Clamp((float)localY / (float)Math.Max(1, repeatHeight - 1), 0f, 1f)), 
			_ => primary, 
		});
	}

	private List<Color> BuildAdaptivePalette(GarmentSpec spec)
	{
		//IL_0075: Unknown result type (might be due to invalid IL or missing references)
		//IL_007a: Unknown result type (might be due to invalid IL or missing references)
		//IL_007f: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d2: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_00c9: Unknown result type (might be due to invalid IL or missing references)
		//IL_009c: Unknown result type (might be due to invalid IL or missing references)
		//IL_00d7: Unknown result type (might be due to invalid IL or missing references)
		//IL_00f6: Unknown result type (might be due to invalid IL or missing references)
		//IL_00e8: Unknown result type (might be due to invalid IL or missing references)
		//IL_00ed: Unknown result type (might be due to invalid IL or missing references)
		//IL_00fb: Unknown result type (might be due to invalid IL or missing references)
		//IL_011a: Unknown result type (might be due to invalid IL or missing references)
		//IL_010c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0111: Unknown result type (might be due to invalid IL or missing references)
		//IL_011f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0128: Unknown result type (might be due to invalid IL or missing references)
		//IL_0129: Unknown result type (might be due to invalid IL or missing references)
		//IL_012f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0134: Unknown result type (might be due to invalid IL or missing references)
		//IL_013b: Unknown result type (might be due to invalid IL or missing references)
		//IL_013c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0142: Unknown result type (might be due to invalid IL or missing references)
		//IL_0147: Unknown result type (might be due to invalid IL or missing references)
		//IL_014e: Unknown result type (might be due to invalid IL or missing references)
		//IL_014f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0155: Unknown result type (might be due to invalid IL or missing references)
		//IL_015a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0161: Unknown result type (might be due to invalid IL or missing references)
		//IL_0162: Unknown result type (might be due to invalid IL or missing references)
		//IL_0168: Unknown result type (might be due to invalid IL or missing references)
		//IL_016d: Unknown result type (might be due to invalid IL or missing references)
		//IL_0174: Unknown result type (might be due to invalid IL or missing references)
		//IL_017a: Unknown result type (might be due to invalid IL or missing references)
		//IL_017f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0186: Unknown result type (might be due to invalid IL or missing references)
		//IL_018c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0191: Unknown result type (might be due to invalid IL or missing references)
		//IL_0198: Unknown result type (might be due to invalid IL or missing references)
		//IL_019e: Unknown result type (might be due to invalid IL or missing references)
		//IL_01a3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b3: Unknown result type (might be due to invalid IL or missing references)
		//IL_01b8: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c4: Unknown result type (might be due to invalid IL or missing references)
		//IL_01c6: Unknown result type (might be due to invalid IL or missing references)
		//IL_01cb: Unknown result type (might be due to invalid IL or missing references)
		//IL_01e8: Unknown result type (might be due to invalid IL or missing references)
		List<Color> list = new List<Color>();
		if (spec.Palette.Count > 0)
		{
			list.AddRange(spec.Palette.Take(48).Select(delegate(string value2)
			{
				//IL_0002: Unknown result type (might be due to invalid IL or missing references)
				//IL_0007: Unknown result type (might be due to invalid IL or missing references)
				return Harmonize(ParseColor(value2));
			}));
		}
		else
		{
			string[] array = new string[3] { spec.PrimaryColor, spec.SecondaryColor, spec.AccentColor };
			foreach (string value in array)
			{
				Color candidate = Harmonize(ParseColor(value));
				if (list.All(delegate(Color existing)
				{
					//IL_0000: Unknown result type (might be due to invalid IL or missing references)
					//IL_0002: Unknown result type (might be due to invalid IL or missing references)
					return ColorDistance(existing, candidate) >= 9f;
				}))
				{
					list.Add(candidate);
				}
			}
		}
		Color val = ((list.Count > 0) ? list[0] : Harmonize(ParseColor(spec.PrimaryColor)));
		Color val2 = ((list.Count > 1) ? list[1] : Harmonize(ParseColor(spec.SecondaryColor)));
		Color val3 = ((list.Count > 2) ? list[2] : Harmonize(ParseColor(spec.AccentColor)));
		Color[] array2 = (Color[])(object)new Color[7]
		{
			Mix(val, val2, 0.28f),
			Mix(val, val2, 0.68f),
			Mix(val, val3, 0.36f),
			Mix(val2, val3, 0.42f),
			Shade(val, 0.76f),
			Shade(val2, 1.12f),
			Shade(val3, 0.88f)
		};
		foreach (Color source in array2)
		{
			Color harmonized = Harmonize(source);
			if (list.All(delegate(Color existing)
			{
				//IL_0000: Unknown result type (might be due to invalid IL or missing references)
				//IL_0002: Unknown result type (might be due to invalid IL or missing references)
				return ColorDistance(existing, harmonized) >= 9f;
			}))
			{
				list.Add(harmonized);
			}
			if (list.Count >= 48)
			{
				break;
			}
		}
		return list;
	}

	private Color Harmonize(Color source)
	{
		//IL_0007: Unknown result type (might be due to invalid IL or missing references)
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		//IL_0038: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Unknown result type (might be due to invalid IL or missing references)
		//IL_001b: Unknown result type (might be due to invalid IL or missing references)
		if (vanillaPalette.Count == 0)
		{
			return source;
		}
		Color b = vanillaPalette.MinBy(delegate(Color candidate)
		{
			//IL_0001: Unknown result type (might be due to invalid IL or missing references)
			//IL_0006: Unknown result type (might be due to invalid IL or missing references)
			return ColorDistance(source, candidate);
		});
		return Mix(source, b, 0.05f);
	}

	private static Color HorizontalStripe(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_002f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0034: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		return (Color)((new int[8] { 0, 0, 1, 2, 2, 3, 0, 1 })[y & 7] switch
		{
			0 => primary, 
			1 => secondary, 
			2 => accent, 
			_ => neutral, 
		});
	}

	private static Color VerticalStripe(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_002f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0034: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		return (Color)((new int[8] { 0, 1, 1, 2, 3, 0, 0, 2 })[x & 7] switch
		{
			0 => primary, 
			1 => secondary, 
			2 => accent, 
			_ => neutral, 
		});
	}

	private static Color Plaid(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_0025: Unknown result type (might be due to invalid IL or missing references)
		//IL_002b: Unknown result type (might be due to invalid IL or missing references)
		//IL_0033: Unknown result type (might be due to invalid IL or missing references)
		//IL_0030: Unknown result type (might be due to invalid IL or missing references)
		int num = x % 5;
		bool flag = (uint)num <= 1u;
		bool flag2 = flag;
		num = y % 6;
		flag = (uint)num <= 1u;
		bool flag3 = flag;
		if (flag2 & flag3)
		{
			return accent;
		}
		if (flag2)
		{
			return secondary;
		}
		if (flag3)
		{
			return neutral;
		}
		return primary;
	}

	private static Color PolkaDot(int x, int y, Color primary, Color secondary, Color accent)
	{
		//IL_0022: Unknown result type (might be due to invalid IL or missing references)
		//IL_0020: Unknown result type (might be due to invalid IL or missing references)
		//IL_0024: Unknown result type (might be due to invalid IL or missing references)
		int num = ((y / 4) & 1) * 2;
		int num2 = (x + num) % 5;
		int num3 = y % 4;
		if (num2 > 1 || num3 > 1)
		{
			if ((x + y) % 9 != 0)
			{
				return primary;
			}
			return secondary;
		}
		return accent;
	}

	private static Color Floral(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		//IL_0010: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		int num = x % 6;
		int num2 = y % 6;
		if (num == 3 && num2 == 3)
		{
			return accent;
		}
		if (Math.Abs(num - 3) + Math.Abs(num2 - 3) == 1)
		{
			return secondary;
		}
		if ((num == 1 && num2 >= 3) || (num2 == 5 && num == 2))
		{
			return neutral;
		}
		return primary;
	}

	private static Color AnimalPrint(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_002e: Unknown result type (might be due to invalid IL or missing references)
		//IL_0045: Unknown result type (might be due to invalid IL or missing references)
		//IL_0055: Unknown result type (might be due to invalid IL or missing references)
		//IL_0053: Unknown result type (might be due to invalid IL or missing references)
		int num = (x + y / 3 * 2) % 7;
		int num2 = y % 6;
		bool flag = num == 2 || num == 3;
		if (flag)
		{
			bool flag2 = (uint)(num2 - 2) <= 1u;
			flag = flag2;
		}
		if (flag)
		{
			return accent;
		}
		if (Math.Abs(num - 3) + Math.Abs(num2 - 3) == 2)
		{
			return secondary;
		}
		if ((x * 3 + y * 5) % 17 != 0)
		{
			return primary;
		}
		return neutral;
	}

	private static Color Camouflage(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_0031: Unknown result type (might be due to invalid IL or missing references)
		//IL_0032: Unknown result type (might be due to invalid IL or missing references)
		//IL_0035: Unknown result type (might be due to invalid IL or missing references)
		//IL_0037: Unknown result type (might be due to invalid IL or missing references)
		//IL_003a: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0041: Unknown result type (might be due to invalid IL or missing references)
		//IL_003f: Unknown result type (might be due to invalid IL or missing references)
		//IL_0040: Unknown result type (might be due to invalid IL or missing references)
		int num = x / 2;
		int num2 = y / 2;
		switch ((num * 11 + num2 * 7 + (num ^ num2) * 3) & 7)
		{
		case 0:
		case 1:
			return secondary;
		case 2:
			return accent;
		case 3:
			return neutral;
		default:
			return primary;
		}
	}

	private static Color ColorBlock(int x, int y, int width, int height, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_0028: Unknown result type (might be due to invalid IL or missing references)
		//IL_003c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0039: Unknown result type (might be due to invalid IL or missing references)
		//IL_0031: Unknown result type (might be due to invalid IL or missing references)
		bool flag = x >= Math.Max(1, width) / 2;
		bool flag2 = y >= Math.Max(1, height) / 2;
		if (!flag2 & flag)
		{
			return secondary;
		}
		if (flag2 && !flag)
		{
			return accent;
		}
		if (flag2 & flag)
		{
			return neutral;
		}
		return primary;
	}

	private static Color Geometric(int x, int y, Color primary, Color secondary, Color accent, Color neutral)
	{
		//IL_000e: Unknown result type (might be due to invalid IL or missing references)
		//IL_001e: Unknown result type (might be due to invalid IL or missing references)
		//IL_002a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0027: Unknown result type (might be due to invalid IL or missing references)
		int num = (x + y) & 5;
		if ((x & 3) == (y & 3))
		{
			return accent;
		}
		if ((uint)num <= 1u)
		{
			return secondary;
		}
		if (((x - y) & 7) == 0)
		{
			return neutral;
		}
		return primary;
	}

	private static Color Graphic(int x, int y, int width, int height, Color primary, Color secondary, Color accent)
	{
		//IL_0044: Unknown result type (might be due to invalid IL or missing references)
		//IL_0059: Unknown result type (might be due to invalid IL or missing references)
		//IL_0056: Unknown result type (might be due to invalid IL or missing references)
		float num = ((float)x + 0.5f) / (float)Math.Max(1, width) - 0.5f;
		float num2 = ((float)y + 0.5f) / (float)Math.Max(1, height) - 0.52f;
		float num3 = num * num * 1.15f + num2 * num2;
		if (num3 < 0.075f)
		{
			return accent;
		}
		if (num3 < 0.16f && ((x + y) & 1) == 0)
		{
			return secondary;
		}
		return primary;
	}

	private static Color Denim(int x, int y, Color primary, Color secondary, Color accent)
	{
		//IL_000a: Unknown result type (might be due to invalid IL or missing references)
		//IL_0016: Unknown result type (might be due to invalid IL or missing references)
		//IL_0014: Unknown result type (might be due to invalid IL or missing references)
		if ((x - y + 32) % 7 == 0)
		{
			return accent;
		}
		if ((x + y) % 4 == 0)
		{
			return secondary;
		}
		return primary;
	}

	private static Color[] Crop(Texture2D texture, int x, int y, int width, int height)
	{
		Color[] array = (Color[])(object)new Color[texture.Width * texture.Height];
		texture.GetData<Color>(array);
		Color[] array2 = (Color[])(object)new Color[width * height];
		for (int i = 0; i < height; i++)
		{
			Array.Copy(array, (y + i) * texture.Width + x, array2, i * width, width);
		}
		return array2;
	}

	private static void Blit(Color[] source, int sourceWidth, int sourceHeight, Color[] target, int targetWidth, int x, int y)
	{
		for (int i = 0; i < sourceHeight; i++)
		{
			Array.Copy(source, i * sourceWidth, target, (y + i) * targetWidth + x, sourceWidth);
		}
	}

	private static void SavePng(string path, Color[] pixels, int width, int height)
	{
		//IL_000c: Unknown result type (might be due to invalid IL or missing references)
		//IL_0012: Expected O, but got Unknown
		Texture2D val = new Texture2D(Game1.graphics.GraphicsDevice, width, height);
		try
		{
			val.SetData<Color>(pixels);
			using FileStream fileStream = File.Create(path);
			val.SaveAsPng((Stream)fileStream, width, height);
		}
		finally
		{
			((IDisposable)val)?.Dispose();
		}
	}

	private static List<Color> LoadVanillaPalette(string path)
	{
		if (!File.Exists(path))
		{
			return new List<Color>();
		}
		try
		{
			using JsonDocument jsonDocument = JsonDocument.Parse(File.ReadAllText(path));
			return jsonDocument.RootElement.GetProperty("palette").GetProperty("colors").EnumerateArray()
				.Select(delegate(JsonElement item)
				{
					//IL_001d: Unknown result type (might be due to invalid IL or missing references)
					return ParseColor(item.GetProperty("hex").GetString() ?? "");
				})
				.Take(96)
				.ToList();
		}
		catch
		{
			return new List<Color>();
		}
	}

	private static Color ParseColor(string value)
	{
		//IL_0068: Unknown result type (might be due to invalid IL or missing references)
		//IL_005c: Unknown result type (might be due to invalid IL or missing references)
		if (value.Length == 7 && value[0] == '#' && byte.TryParse(value.AsSpan(1, 2), NumberStyles.HexNumber, null, out var result) && byte.TryParse(value.AsSpan(3, 2), NumberStyles.HexNumber, null, out var result2) && byte.TryParse(value.AsSpan(5, 2), NumberStyles.HexNumber, null, out var result3))
		{
			return new Color((int)result, (int)result2, (int)result3);
		}
		return new Color(58, 57, 70);
	}

	private static Color ToColor(GarmentArtRgb color)
	{
		//IL_0015: Unknown result type (might be due to invalid IL or missing references)
		return new Color((int)color.R, (int)color.G, (int)color.B);
	}

	private static float RelativeLuma(Color color)
	{
		return (0.2126f * (float)(int)((Color)(ref color)).R + 0.7152f * (float)(int)((Color)(ref color)).G + 0.0722f * (float)(int)((Color)(ref color)).B) / 255f;
	}

	private static Color Shade(Color color, float factor)
	{
		//IL_005e: Unknown result type (might be due to invalid IL or missing references)
		return new Color((byte)Math.Clamp((int)Math.Round((float)(int)((Color)(ref color)).R * factor), 0, 255), (byte)Math.Clamp((int)Math.Round((float)(int)((Color)(ref color)).G * factor), 0, 255), (byte)Math.Clamp((int)Math.Round((float)(int)((Color)(ref color)).B * factor), 0, 255), ((Color)(ref color)).A);
	}

	private static Color MakeOutline(Color primary)
	{
		//IL_0000: Unknown result type (might be due to invalid IL or missing references)
		//IL_0051: Unknown result type (might be due to invalid IL or missing references)
		//IL_0053: Unknown result type (might be due to invalid IL or missing references)
		float num = RelativeLuma(primary);
		float num2 = ((num >= 0.82f) ? 0.68f : ((num >= 0.58f) ? 0.64f : ((num >= 0.34f) ? 0.62f : ((!(num >= 0.18f)) ? 0.88f : 0.72f))));
		float factor = num2;
		return Shade(primary, factor);
	}

	private static bool IsTrustedPhotographedDark(Color candidate, Color baseColor, int count, int occupied, string pattern)
	{
		//IL_0008: Unknown result type (might be due to invalid IL or missing references)
		//IL_0009: Unknown result type (might be due to invalid IL or missing references)
		//IL_0013: Unknown result type (might be due to invalid IL or missing references)
		//IL_001a: Unknown result type (might be due to invalid IL or missing references)
		if (count <= 0 || occupied <= 0 || candidate == baseColor)
		{
			return true;
		}
		float num = RelativeLuma(candidate);
		float num2 = RelativeLuma(baseColor);
		if (!(num < 0.17f) || !(num2 - num >= 0.12f))
		{
			return true;
		}
		bool flag;
		switch (pattern)
		{
		case "logo":
		case "graphic":
		case "horizontal_stripes":
		case "vertical_stripes":
		case "plaid":
		case "polka_dot":
			flag = true;
			break;
		default:
			flag = false;
			break;
		}
		if (flag)
		{
			return count >= 2;
		}
		return (double)count / (double)occupied >= 0.16;
	}

	private static Color Mix(Color a, Color b, float amount)
	{
		//IL_0066: Unknown result type (might be due to invalid IL or missing references)
		return new Color((int)(byte)Math.Round((float)(int)((Color)(ref a)).R + (float)(((Color)(ref b)).R - ((Color)(ref a)).R) * amount), (int)(byte)Math.Round((float)(int)((Color)(ref a)).G + (float)(((Color)(ref b)).G - ((Color)(ref a)).G) * amount), (int)(byte)Math.Round((float)(int)((Color)(ref a)).B + (float)(((Color)(ref b)).B - ((Color)(ref a)).B) * amount));
	}

	private static float ColorDistance(Color a, Color b)
	{
		float num = ((Color)(ref a)).R - ((Color)(ref b)).R;
		float num2 = ((Color)(ref a)).G - ((Color)(ref b)).G;
		float num3 = ((Color)(ref a)).B - ((Color)(ref b)).B;
		return MathF.Sqrt(num * num + num2 * num2 + num3 * num3);
	}

	private static string Sanitize(string text, int maxLength)
	{
		string text2 = text.Replace('/', '-').Replace('\n', ' ').Replace('\r', ' ')
			.Trim();
		if (text2.Length > maxLength)
		{
			return text2.Substring(0, maxLength);
		}
		return text2;
	}

	private static string SafeFileKey(string text)
	{
		HashSet<char> invalid = Path.GetInvalidFileNameChars().ToHashSet();
		string text2 = string.Concat((text ?? "").Select((char character) => (!invalid.Contains(character)) ? character : '_'));
		text2 = text2.Trim().Trim('.');
		if (!string.IsNullOrWhiteSpace(text2))
		{
			return text2;
		}
		return Guid.NewGuid().ToString("N");
	}

	private static string NormalizeToken(string? value)
	{
		return (value ?? "").Trim().ToLowerInvariant().Replace('-', '_')
			.Replace(' ', '_');
	}
}
