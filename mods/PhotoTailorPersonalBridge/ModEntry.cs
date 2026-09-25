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
    }

    private void OnMakeCap(string command, string[] args)
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
                silhouetteProperty?.SetValue(item, "cap");
                Monitor.Log($"PT precise hat: forcing silhouette {originalSilhouette} -> cap", LogLevel.Info);

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
