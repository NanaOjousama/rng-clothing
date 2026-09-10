using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using StardewModdingAPI;

namespace StardewVisualQCBridge
{
    /// <summary>Reads Fashion Sense hat content packs straight off disk.
    ///
    /// Deliberately not reflected out of Fashion Sense internals: the on-disk
    /// content pack is the same thing our generator writes, so reading it keeps
    /// the QC bridge honest about what was actually exported, and it keeps this
    /// mod from breaking every time Fashion Sense refactors.
    /// </summary>
    internal static class HatPacks
    {
        public sealed class HatEntry
        {
            public string PackId;
            public string PackName;
            public string AppearanceName;
            public string FolderName;
            public string JsonPath;
            public string TexturePath;
            public string AppearanceId => $"{this.PackId}/Hat/{this.AppearanceName}";
        }

        public sealed class HatDirModel
        {
            public string PackId, AppearanceName, TexturePath, DirectionKey;
            public int StartX, StartY, Width = 20, Height = 20, HeadX, HeadY;
            public float Scale = 4f;
            public bool HideHair, Flipped, DisableGrayscale;
        }

        private static readonly string[] DirectionKeys = { "BackHat", "RightHat", "FrontHat", "LeftHat" };

        private static string modsRoot;

        public static void Init(IModHelper helper)
        {
            // <game>/Mods — the mod folder is <game>/Mods/<this mod>
            modsRoot = Directory.GetParent(helper.DirectoryPath)?.FullName;
        }

        public static List<HatEntry> List()
        {
            var found = new List<HatEntry>();
            if (modsRoot == null || !Directory.Exists(modsRoot))
                return found;

            foreach (string packDir in SafeDirs(modsRoot))
            {
                string manifest = Path.Combine(packDir, "manifest.json");
                if (!File.Exists(manifest))
                    continue;
                string packId;
                string packName;
                try
                {
                    var m = JObject.Parse(File.ReadAllText(manifest));
                    string target = m["ContentPackFor"]?["UniqueID"]?.ToString();
                    if (!string.Equals(target, "PeacefulEnd.FashionSense", StringComparison.OrdinalIgnoreCase))
                        continue;
                    packId = m.Value<string>("UniqueID");
                    packName = m.Value<string>("Name") ?? packId;
                }
                catch { continue; }
                if (string.IsNullOrWhiteSpace(packId))
                    continue;

                foreach (string json in SafeFiles(packDir, "hat.json"))
                {
                    try
                    {
                        var o = JObject.Parse(File.ReadAllText(json));
                        string name = o.Value<string>("Name");
                        if (string.IsNullOrWhiteSpace(name))
                            continue;
                        string dir = Path.GetDirectoryName(json);
                        found.Add(new HatEntry
                        {
                            PackId = packId,
                            PackName = packName,
                            AppearanceName = name,
                            FolderName = Path.GetFileName(dir),
                            JsonPath = json,
                            TexturePath = Path.Combine(dir, "hat.png")
                        });
                    }
                    catch { /* a malformed pack is not our problem to report */ }
                }
            }
            found.Sort((a, b) => string.CompareOrdinal(a.AppearanceId, b.AppearanceId));
            return found;
        }

        /// <summary>Resolve the directional model Fashion Sense will use for this facing.</summary>
        public static HatDirModel ResolveModel(string appearanceId, int facingDirection)
        {
            var parts = (appearanceId ?? "").Split('/');
            if (parts.Length < 3)
                return null;
            string packId = parts[0];
            string name = string.Join("/", parts.Skip(2));

            var entry = List().FirstOrDefault(h =>
                h.PackId == packId && h.AppearanceName == name);
            if (entry == null)
                return null;

            string key = facingDirection >= 0 && facingDirection < 4
                ? DirectionKeys[facingDirection]
                : "FrontHat";
            try
            {
                var o = JObject.Parse(File.ReadAllText(entry.JsonPath));
                if (o[key] is not JObject d)
                    return null;
                var m = new HatDirModel
                {
                    PackId = packId,
                    AppearanceName = name,
                    TexturePath = entry.TexturePath,
                    DirectionKey = key,
                    StartX = d["StartingPosition"]?.Value<int>("X") ?? 0,
                    StartY = d["StartingPosition"]?.Value<int>("Y") ?? 0,
                    Width = d["HatSize"]?.Value<int>("Width") ?? 20,
                    Height = d["HatSize"]?.Value<int>("Length") ?? 20,
                    HeadX = d["HeadPosition"]?.Value<int>("X") ?? 0,
                    HeadY = d["HeadPosition"]?.Value<int>("Y") ?? 0,
                    Scale = d["Scale"]?.Value<float>() ?? 4f,
                    HideHair = d.Value<bool?>("HideHair") ?? false,
                    Flipped = d.Value<bool?>("Flipped") ?? false,
                    DisableGrayscale = d.Value<bool?>("DisableGrayscale") ?? false
                };
                return m;
            }
            catch { return null; }
        }

        private static IEnumerable<string> SafeDirs(string root)
        {
            var stack = new Stack<string>();
            stack.Push(root);
            while (stack.Count > 0)
            {
                string dir = stack.Pop();
                yield return dir;
                string[] children;
                try { children = Directory.GetDirectories(dir); }
                catch { continue; }
                foreach (string c in children)
                    stack.Push(c);
            }
        }

        private static IEnumerable<string> SafeFiles(string root, string pattern)
        {
            try { return Directory.GetFiles(root, pattern, SearchOption.AllDirectories); }
            catch { return Array.Empty<string>(); }
        }
    }
}
