using System;
using System.Collections.Generic;
using System.IO;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Objects;

namespace RNGClothingFitting
{
    /// <summary>Every generated cap installed on this machine, by item id.
    ///
    /// Found by scanning the Mods folder for our own `fitting.json` sidecars.
    /// A cap without a sidecar is not a supported item and the mod leaves it
    /// entirely alone — that is what keeps the sewing machine vanilla for
    /// everything else.
    /// </summary>
    internal sealed class CapCatalog
    {
        private readonly Dictionary<string, CapSidecar> byItemId =
            new(StringComparer.OrdinalIgnoreCase);
        private readonly IMonitor monitor;

        public CapCatalog(IMonitor monitor) => this.monitor = monitor;

        public int Count => this.byItemId.Count;
        public IEnumerable<CapSidecar> All => this.byItemId.Values;

        public void Scan(IModHelper helper)
        {
            this.byItemId.Clear();
            string mods = Directory.GetParent(helper.DirectoryPath)?.FullName;
            if (mods == null || !Directory.Exists(mods))
                return;

            string[] files;
            try { files = Directory.GetFiles(mods, "fitting.json", SearchOption.AllDirectories); }
            catch (Exception ex)
            {
                this.monitor.Log($"Could not scan for generated caps: {ex.Message}", LogLevel.Warn);
                return;
            }

            foreach (string file in files)
            {
                CapSidecar cap;
                try { cap = CapSidecar.Load(file); }
                catch (Exception ex)
                {
                    this.monitor.Log($"Skipped {file}: {ex.Message}", LogLevel.Trace);
                    continue;
                }
                if (cap != null)
                    this.byItemId[cap.ItemId] = cap;
            }
            this.monitor.Log($"Found {this.byItemId.Count} adjustable cap(s).", LogLevel.Debug);
        }

        /// <summary>The sidecar for a bare item id, or null.</summary>
        public CapSidecar GetById(string itemId)
        {
            if (string.IsNullOrEmpty(itemId))
                return null;
            if (itemId.StartsWith("(H)", StringComparison.Ordinal))
                itemId = itemId.Substring(3);
            return this.byItemId.TryGetValue(itemId, out var cap) ? cap : null;
        }

        /// <summary>The sidecar for an item, or null if we do not support it.</summary>
        public CapSidecar Get(Item item)
        {
            if (item is not Hat)
                return null;
            // Item ids arrive both bare and qualified ("(H)<id>") depending on
            // where they came from, so both are accepted.
            string id = item.ItemId;
            if (!string.IsNullOrEmpty(id) && this.byItemId.TryGetValue(id, out var cap))
                return cap;
            string q = item.QualifiedItemId;
            if (!string.IsNullOrEmpty(q) && q.StartsWith("(H)", StringComparison.Ordinal)
                && this.byItemId.TryGetValue(q.Substring(3), out cap))
                return cap;
            return null;
        }
    }
}
