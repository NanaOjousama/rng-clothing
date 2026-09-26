using System;
using System.Collections;
using System.IO;
using System.Linq;
using System.Reflection;
using StardewModdingAPI;

namespace PhotoTailorPersonalBridge;

public sealed class ModEntry : Mod
{
    public override void Entry(IModHelper helper)
    {
        helper.ConsoleCommands.Add(
            "pt_make_cap",
            "Run Photo Tailor's real analyzer + renderer on one local image. Usage: pt_make_cap <imagePath>",
            OnMakeCap);
        helper.ConsoleCommands.Add(
            "pt_make_trucker",
            "Analyze a real trucker-hat image as category=hat and render it through Photo Tailor using the trucker_hat silhouette. Usage: pt_make_trucker <imagePath>",
            (command, args) => OnMakeHat(command, args, "trucker_hat"));
        helper.ConsoleCommands.Add(
            "pt_stock_photo",
            "Run Photo Tailor stock Quick Recognition + stock renderer, with no spec/template modifications. Usage: pt_stock_photo <imagePath>",
            OnStockPhoto);
        helper.ConsoleCommands.Add(
            "pt_ui_equivalent",
            "Run the exact Photo Tailor Quick Recognition -> Preview -> RenderPrepared confirmation path. Usage: pt_ui_equivalent <imagePath>",
            OnUiEquivalent);
    }



    private void OnUiEquivalent(string command, string[] args)
    {
        if (args.Length < 1) { Monitor.Log("Usage: pt_ui_equivalent <imagePath>", LogLevel.Warn); return; }
        string imagePath = string.Join(" ", args);
        try
        {
            if (!File.Exists(imagePath)) throw new FileNotFoundException("Reference image not found.", imagePath);
            Assembly pt = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => string.Equals(a.GetName().Name, "PhotoTailor", StringComparison.Ordinal))
                ?? throw new InvalidOperationException("PhotoTailor assembly is not loaded.");
            string modsRoot = Path.GetDirectoryName(Helper.DirectoryPath) ?? throw new InvalidOperationException("Cannot resolve Mods directory.");
            string ptDir = Path.Combine(modsRoot, "PhotoTailor");
            Type analyzerType = pt.GetType("PhotoTailor.LocalOutfitAnalyzer", true)!;
            Type retrieverType = pt.GetType("PhotoTailor.SemanticRetriever", true)!;
            Type rendererType = pt.GetType("PhotoTailor.SpriteRenderer", true)!;
            object analyzer = Activator.CreateInstance(analyzerType, ptDir)!;
            object retriever = Activator.CreateInstance(retrieverType, ptDir)!;
            object renderer = Activator.CreateInstance(rendererType, ptDir, retriever)!;
            MethodInfo analyze = analyzerType.GetMethods(BindingFlags.Instance | BindingFlags.Public).First(m => m.Name == "Analyze" && m.GetParameters().Length == 1);
            object outfit = Invoke(analyze, analyzer, imagePath)!;

            // This is the same call ModEntry.PopulateRecognitionPreview makes before the UI displays the preview.
            MethodInfo previewOutfit = rendererType.GetMethods(BindingFlags.Instance | BindingFlags.Public).First(m => m.Name == "Preview" && m.GetParameters().Length == 1 && m.GetParameters()[0].ParameterType.Name == "OutfitSpec");
            object preparedOutfit = Invoke(previewOutfit, renderer, outfit)!;

            // GarmentMenuPreviewRenderer.Populate only copies these pixels into GPU Texture2D objects for display;
            // it doesn't modify the prepared preview. Confirmation later passes these exact objects to RenderPrepared.
            IEnumerable items = (IEnumerable)(outfit.GetType().GetProperty("Items")!.GetValue(outfit) ?? throw new InvalidOperationException("No garment list."));
            IEnumerable previewItems = (IEnumerable)(preparedOutfit.GetType().GetProperty("Items")!.GetValue(preparedOutfit) ?? throw new InvalidOperationException("No preview list."));
            object[] specs = items.Cast<object>().ToArray();
            object[] previews = previewItems.Cast<object>().ToArray();
            if (specs.Length != previews.Length) throw new InvalidOperationException("Preview/spec item count mismatch.");

            MethodInfo renderPrepared = rendererType.GetMethods(BindingFlags.Instance | BindingFlags.Public).First(m => m.Name == "RenderPrepared" && m.GetParameters().Length == 3);
            for (int i = 0; i < specs.Length; i++)
            {
                object item = specs[i];
                Type st = item.GetType();
                string category = st.GetProperty("Category")?.GetValue(item)?.ToString() ?? "";
                string silhouette = st.GetProperty("Silhouette")?.GetValue(item)?.ToString() ?? "";
                string semantic = st.GetProperty("SemanticDescription")?.GetValue(item)?.ToString() ?? "";
                Monitor.Log($"PT UI-EQUIV DETECT item={i} category={category} silhouette={silhouette} semantic={semantic}", LogLevel.Info);
                string suffix = $"uiequiv_{DateTime.UtcNow:yyyyMMddHHmmss}_{i:D2}";
                object generated = Invoke(renderPrepared, renderer, item, suffix, previews[i])!;
                Type gt = generated.GetType();
                string texturePath = gt.GetProperty("TexturePath")?.GetValue(generated)?.ToString() ?? "";
                string artworkPath = gt.GetProperty("ArtworkPath")?.GetValue(generated)?.ToString() ?? "";
                Monitor.Log($"PT UI-EQUIV OUTPUT texture={Path.Combine(ptDir, texturePath)}", LogLevel.Info);
                if (!string.IsNullOrWhiteSpace(artworkPath)) Monitor.Log($"PT UI-EQUIV ARTWORK artwork={Path.Combine(ptDir, artworkPath)}", LogLevel.Info);
            }
            Monitor.Log($"PT UI-EQUIV complete items={specs.Length}", LogLevel.Info);
        }
        catch (Exception ex) { Monitor.Log(Unwrap(ex).ToString(), LogLevel.Error); }
    }

    private void OnStockPhoto(string command, string[] args)
    {
        if (args.Length < 1) { Monitor.Log("Usage: pt_stock_photo <imagePath>", LogLevel.Warn); return; }
        string imagePath = string.Join(" ", args);
        try
        {
            if (!File.Exists(imagePath)) throw new FileNotFoundException("Reference image not found.", imagePath);
            Assembly pt = AppDomain.CurrentDomain.GetAssemblies().FirstOrDefault(a => string.Equals(a.GetName().Name, "PhotoTailor", StringComparison.Ordinal))
                ?? throw new InvalidOperationException("PhotoTailor assembly is not loaded.");
            string modsRoot = Path.GetDirectoryName(Helper.DirectoryPath) ?? throw new InvalidOperationException("Cannot resolve Mods directory.");
            string ptDir = Path.Combine(modsRoot, "PhotoTailor");
            Type analyzerType = pt.GetType("PhotoTailor.LocalOutfitAnalyzer", true)!;
            Type retrieverType = pt.GetType("PhotoTailor.SemanticRetriever", true)!;
            Type rendererType = pt.GetType("PhotoTailor.SpriteRenderer", true)!;
            object analyzer = Activator.CreateInstance(analyzerType, ptDir)!;
            object retriever = Activator.CreateInstance(retrieverType, ptDir)!;
            object renderer = Activator.CreateInstance(rendererType, ptDir, retriever)!;
            MethodInfo analyze = analyzerType.GetMethods(BindingFlags.Instance | BindingFlags.Public).First(m => m.Name == "Analyze" && m.GetParameters().Length == 1);
            object outfit = Invoke(analyze, analyzer, imagePath)!;
            IEnumerable items = (IEnumerable)(outfit.GetType().GetProperty("Items")!.GetValue(outfit) ?? throw new InvalidOperationException("No garment list."));
            MethodInfo render = rendererType.GetMethods(BindingFlags.Instance | BindingFlags.Public).First(m => m.Name == "Render" && m.GetParameters().Length == 2 && m.GetParameters()[1].ParameterType == typeof(string));
            int i = 0;
            foreach (object item in items)
            {
                Type st = item.GetType();
                string category = st.GetProperty("Category")?.GetValue(item)?.ToString() ?? "";
                string silhouette = st.GetProperty("Silhouette")?.GetValue(item)?.ToString() ?? "";
                string semantic = st.GetProperty("SemanticDescription")?.GetValue(item)?.ToString() ?? "";
                Monitor.Log($"PT STOCK DETECT item={i} category={category} silhouette={silhouette} semantic={semantic}", LogLevel.Info);
                string suffix = $"stock_{DateTime.UtcNow:yyyyMMddHHmmss}_{i:D2}";
                object generated = Invoke(render, renderer, item, suffix)!;
                Type gt = generated.GetType();
                string texturePath = gt.GetProperty("TexturePath")?.GetValue(generated)?.ToString() ?? "";
                string artworkPath = gt.GetProperty("ArtworkPath")?.GetValue(generated)?.ToString() ?? "";
                Monitor.Log($"PT STOCK OUTPUT texture={Path.Combine(ptDir, texturePath)}", LogLevel.Info);
                if (!string.IsNullOrWhiteSpace(artworkPath)) Monitor.Log($"PT STOCK ARTWORK artwork={Path.Combine(ptDir, artworkPath)}", LogLevel.Info);
                i++;
            }
            Monitor.Log($"PT STOCK complete items={i}", LogLevel.Info);
        }
        catch (Exception ex) { Monitor.Log(Unwrap(ex).ToString(), LogLevel.Error); }
    }

    private void OnMakeCap(string command, string[] args)
        => OnMakeHat(command, args, null);

    private void OnMakeHat(string command, string[] args, string? forcedHatSilhouette)
    {
        if (args.Length < 1)
        {
            Monitor.Log("Usage: pt_make_cap <imagePath>", LogLevel.Warn);
            return;
        }

        string imagePath = string.Join(" ", args);
        try
        {
            if (!File.Exists(imagePath))
                throw new FileNotFoundException("Reference image not found.", imagePath);

            Assembly pt = AppDomain.CurrentDomain.GetAssemblies()
                .FirstOrDefault(a => string.Equals(a.GetName().Name, "PhotoTailor", StringComparison.Ordinal))
                ?? throw new InvalidOperationException("PhotoTailor assembly is not loaded.");

            string modsRoot = Path.GetDirectoryName(Helper.DirectoryPath)
                ?? throw new InvalidOperationException("Cannot resolve Mods directory.");
            string ptDir = Path.Combine(modsRoot, "PhotoTailor");

            Type analyzerType = pt.GetType("PhotoTailor.LocalOutfitAnalyzer", throwOnError: true)!;
            Type retrieverType = pt.GetType("PhotoTailor.SemanticRetriever", throwOnError: true)!;
            Type rendererType = pt.GetType("PhotoTailor.SpriteRenderer", throwOnError: true)!;
            InstallHatTemplate(rendererType, "trucker_hat", 16);
            InstallHatTemplate(rendererType, "trucker", 16);
            object analyzer = Activator.CreateInstance(analyzerType, ptDir)
                ?? throw new InvalidOperationException("Failed to create PhotoTailor analyzer.");

            Type selectionType = pt.GetType("PhotoTailor.GarmentCropSelection", throwOnError: true)!;
            object selection = Activator.CreateInstance(selectionType)
                ?? throw new InvalidOperationException("Failed to create PhotoTailor crop selection.");
            selectionType.GetProperty("Left")!.SetValue(selection, 0d);
            selectionType.GetProperty("Top")!.SetValue(selection, 0d);
            selectionType.GetProperty("Right")!.SetValue(selection, 1d);
            selectionType.GetProperty("Bottom")!.SetValue(selection, 1d);
            selectionType.GetProperty("CategoryHint")!.SetValue(selection, "hat");

            Type listType = typeof(System.Collections.Generic.List<>).MakeGenericType(selectionType);
            object selections = Activator.CreateInstance(listType)!;
            ((IList)selections).Add(selection);

            MethodInfo analyze = analyzerType.GetMethods(BindingFlags.Instance | BindingFlags.Public)
                .First(m => m.Name == "Analyze" && m.GetParameters().Length == 2);

            object outfit = Invoke(analyze, analyzer, imagePath, selections)
                ?? throw new InvalidOperationException("PhotoTailor returned no outfit.");

            PropertyInfo itemsProperty = outfit.GetType().GetProperty("Items")
                ?? throw new MissingMemberException("OutfitSpec.Items");
            IEnumerable items = (IEnumerable)(itemsProperty.GetValue(outfit)
                ?? throw new InvalidOperationException("PhotoTailor returned no garment list."));
            object retriever = Activator.CreateInstance(retrieverType, ptDir)
                ?? throw new InvalidOperationException("Failed to create PhotoTailor retriever.");
            object renderer = Activator.CreateInstance(rendererType, ptDir, retriever)
                ?? throw new InvalidOperationException("Failed to create PhotoTailor renderer.");

            MethodInfo render = rendererType.GetMethods(BindingFlags.Instance | BindingFlags.Public)
                .FirstOrDefault(m =>
                    m.Name == "Render" &&
                    m.GetParameters().Length == 2 &&
                    m.GetParameters()[1].ParameterType == typeof(string))
                ?? throw new MissingMethodException("PhotoTailor.SpriteRenderer.Render");

            int hatCount = 0;
            int itemIndex = 0;
            foreach (object item in items)
            {
                Type specType = item.GetType();
                string category = specType.GetProperty("Category")?.GetValue(item)?.ToString() ?? "";
                if (!string.Equals(category, "hat", StringComparison.OrdinalIgnoreCase))
                {
                    itemIndex++;
                    continue;
                }

                PropertyInfo? silhouetteProperty = specType.GetProperty("Silhouette");
                string originalSilhouette = silhouetteProperty?.GetValue(item)?.ToString() ?? "";
                if (!string.IsNullOrWhiteSpace(forcedHatSilhouette))
                {
                    silhouetteProperty?.SetValue(item, forcedHatSilhouette);
                    PropertyInfo? semanticProperty = specType.GetProperty("SemanticDescription");
                    string semantic = semanticProperty?.GetValue(item)?.ToString() ?? "";
                    if (!semantic.Contains("trucker", StringComparison.OrdinalIgnoreCase))
                        semanticProperty?.SetValue(item, $"trucker hat {semantic}".Trim());
                    Monitor.Log($"PT hat override: {originalSilhouette} -> {forcedHatSilhouette}; category remains hat; template selection stays inside Photo Tailor.", LogLevel.Info);
                }
                else
                {
                    Monitor.Log($"PT hat: preserving analyzer silhouette {originalSilhouette}", LogLevel.Info);
                }

                string suffix = $"personal_{DateTime.UtcNow:yyyyMMddHHmmss}_{itemIndex:D2}";
                object generated = Invoke(render, renderer, item, suffix)
                    ?? throw new InvalidOperationException("PhotoTailor returned no generated garment.");

                Type generatedType = generated.GetType();
                string id = generatedType.GetProperty("Id")?.GetValue(generated)?.ToString() ?? "(unknown)";
                string texturePath = generatedType.GetProperty("TexturePath")?.GetValue(generated)?.ToString() ?? "";
                string artworkPath = generatedType.GetProperty("ArtworkPath")?.GetValue(generated)?.ToString() ?? "";
                string silhouette = specType.GetProperty("Silhouette")?.GetValue(item)?.ToString() ?? "";

                Monitor.Log($"PT GENERATED HAT id={id} silhouette={silhouette}", LogLevel.Info);
                Monitor.Log($"texture={Path.Combine(ptDir, texturePath)}", LogLevel.Info);
                if (!string.IsNullOrWhiteSpace(artworkPath))
                    Monitor.Log($"artwork={Path.Combine(ptDir, artworkPath)}", LogLevel.Info);

                hatCount++;
                itemIndex++;
            }
            if (hatCount == 0)
                Monitor.Log("PhotoTailor generated no hat from this reference.", LogLevel.Warn);
            else
                Monitor.Log($"PhotoTailor generated {hatCount} hat candidate(s).", LogLevel.Info);
        }
        catch (Exception ex)
        {
            Monitor.Log(Unwrap(ex).ToString(), LogLevel.Error);
        }
    }


    private void InstallHatTemplate(Type rendererType, string silhouette, int vanillaHatIndex)
    {
        FieldInfo field = rendererType.GetField("HatTemplates", BindingFlags.Static | BindingFlags.NonPublic)
            ?? throw new MissingFieldException("PhotoTailor.SpriteRenderer.HatTemplates");
        object value = field.GetValue(null)
            ?? throw new InvalidOperationException("PhotoTailor HatTemplates dictionary is null.");
        PropertyInfo indexer = value.GetType().GetProperty("Item")
            ?? throw new MissingMemberException("HatTemplates indexer");
        indexer.SetValue(value, vanillaHatIndex, new object[] { silhouette });
        Monitor.Log($"Photo Tailor hat template extension: {silhouette} -> vanilla hat #{vanillaHatIndex}", LogLevel.Debug);
    }

    private static object? Invoke(MethodInfo method, object target, params object[] args)
    {
        try
        {
            return method.Invoke(target, args);
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            throw ex.InnerException;
        }
    }

    private static Exception Unwrap(Exception ex)
        => ex is TargetInvocationException tie && tie.InnerException is not null
            ? tie.InnerException
            : ex;
}
