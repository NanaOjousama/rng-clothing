// Metadata index of an INSTALLED assembly -- classes, members, signatures.
//
// Why this exists: the Stardew wiki documents modding APIs, not the game's own
// class surface.  Questions like "what does IClickableMenu expose for controller
// snapping?" or "how does the tailoring menu name its members?" are answerable
// only from the binary the game is actually running, which is why the technical
// authority hierarchy puts this above the wiki.
//
// MetadataLoadContext reads metadata WITHOUT executing or JITing the assembly
// and without resolving every dependency -- the same technique used for the
// Cheerful Pixels study.  No IL bodies are decompiled, so this indexes the
// SHAPE of the API only: names, signatures, inheritance, enum members.  It
// never reproduces game code or content, and its output is gitignored.
//
//   dotnet run --project tools/AssemblyIndex -- <assembly> <out.json> [filter...]
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;

static class Program
{
    static int Main(string[] args)
    {
        if (args.Length < 2)
        {
            Console.Error.WriteLine("usage: AssemblyIndex <assembly.dll> <out.json> [namespace-or-name filter ...]");
            return 2;
        }
        string target = args[0], outPath = args[1];
        var filters = args.Skip(2).ToArray();
        if (!File.Exists(target)) { Console.Error.WriteLine($"no assembly at {target}"); return 1; }

        // Resolve ONLY against the assembly's own folder.  A Stardew install is
        // self-contained -- it ships System.Private.CoreLib beside the game -- so
        // this reads the exact framework the game runs on.  Adding the SDK's
        // shared runtime as well gives PathAssemblyResolver two assemblies with
        // the same simple name and core-assembly resolution then fails outright.
        var dir = Path.GetDirectoryName(Path.GetFullPath(target));
        var paths = new List<string>(Directory.GetFiles(dir, "*.dll"));

        using var mlc = new MetadataLoadContext(new PathAssemblyResolver(paths));
        var asm = mlc.LoadFromAssemblyPath(Path.GetFullPath(target));

        Type[] types;
        try { types = asm.GetTypes(); }
        catch (ReflectionTypeLoadException ex) { types = ex.Types.Where(t => t != null).ToArray(); }

        var rows = new List<object>();
        foreach (var t in types.OrderBy(t => t.FullName, StringComparer.Ordinal))
        {
            if (!t.IsPublic && !t.IsNestedPublic) continue;
            if (filters.Length > 0 && !filters.Any(f =>
                    (t.FullName ?? "").Contains(f, StringComparison.OrdinalIgnoreCase)))
                continue;

            const BindingFlags F = BindingFlags.Public | BindingFlags.NonPublic
                                 | BindingFlags.Instance | BindingFlags.Static
                                 | BindingFlags.DeclaredOnly;
            rows.Add(new
            {
                name = t.FullName,
                kind = t.IsEnum ? "enum" : t.IsInterface ? "interface"
                     : t.IsValueType ? "struct" : "class",
                @base = t.BaseType?.FullName,
                interfaces = Safe(() => t.GetInterfaces().Select(i => i.Name).ToArray()),
                isAbstract = t.IsAbstract,
                enumMembers = t.IsEnum ? Safe(() => t.GetFields(F)
                        .Where(f => f.IsStatic).Select(f => f.Name).ToArray()) : null,
                fields = Safe(() => t.GetFields(F).Where(f => !f.IsSpecialName)
                        .Select(f => $"{Short(f.FieldType)} {f.Name}").ToArray()),
                properties = Safe(() => t.GetProperties(F)
                        .Select(p => $"{Short(p.PropertyType)} {p.Name}").ToArray()),
                methods = Safe(() => t.GetMethods(F).Where(m => !m.IsSpecialName)
                        .Select(m => $"{Short(m.ReturnType)} {m.Name}(" +
                            string.Join(", ", m.GetParameters()
                                .Select(p => $"{Short(p.ParameterType)} {p.Name}")) + ")")
                        .ToArray()),
            });
        }

        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(outPath)));
        File.WriteAllText(outPath, JsonSerializer.Serialize(new
        {
            assembly = asm.GetName().Name,
            version = asm.GetName().Version?.ToString(),
            source = Path.GetFullPath(target),
            gathered = DateTime.UtcNow.ToString("yyyy-MM-dd"),
            note = "Metadata shapes only -- no IL bodies, no game content. Regenerate; do not commit.",
            filters,
            typeCount = rows.Count,
            types = rows,
        }, new JsonSerializerOptions { WriteIndented = false }));

        Console.WriteLine($"{rows.Count} public types -> {outPath}");
        return 0;
    }

    // A member whose signature touches an unresolvable type must not kill the run.
    static T[] Safe<T>(Func<T[]> f) { try { return f(); } catch { return Array.Empty<T>(); } }
    static string Short(Type t) { try { return t.Name; } catch { return "?"; } }
}
