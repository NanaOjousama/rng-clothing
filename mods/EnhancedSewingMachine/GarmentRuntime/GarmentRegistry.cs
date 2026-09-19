using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal sealed class GarmentRegistry
    {
        private const string IndexPath = "assets/garments/index.json";
        private readonly IModHelper helper;
        private readonly IMonitor monitor;
        private readonly Dictionary<string, RegisteredGarment> garments = new(StringComparer.OrdinalIgnoreCase);

        public GarmentRegistry(IModHelper helper, IMonitor monitor)
        {
            this.helper = helper;
            this.monitor = monitor;
        }

        public int Count => this.garments.Count;

        public IEnumerable<RegisteredGarment> All
            => this.garments.Values.OrderBy(p => p.Definition.Id, StringComparer.OrdinalIgnoreCase);

        public void Load()
        {
            this.garments.Clear();
            GarmentRegistryIndex index;
            try
            {
                index = this.helper.Data.ReadJsonFile<GarmentRegistryIndex>(IndexPath);
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Garment registry index failed to load; generated garments are disabled. {ex}", LogLevel.Error);
                return;
            }

            if (index?.Garments == null || index.Garments.Count == 0)
            {
                this.monitor.Log("Garment registry index is empty; generated garments are disabled.", LogLevel.Warn);
                return;
            }

            foreach (string file in index.Garments)
                this.LoadOne(file);

            this.monitor.Log($"Garment registry loaded {this.garments.Count}/{index.Garments.Count} definition(s).", LogLevel.Debug);
        }

        public bool TryGet(string garmentId, out RegisteredGarment garment)
        {
            garment = null;
            return !string.IsNullOrWhiteSpace(garmentId)
                && this.garments.TryGetValue(garmentId, out garment);
        }

        private void LoadOne(string file)
        {
            if (string.IsNullOrWhiteSpace(file)
                || file.Contains("..", StringComparison.Ordinal)
                || Path.IsPathRooted(file))
            {
                this.monitor.Log($"Skipped unsafe garment registry entry '{file}'.", LogLevel.Error);
                return;
            }

            string relativePath = $"assets/garments/{file.Replace('\\', '/')}";
            GarmentDefinition definition;
            try
            {
                definition = this.helper.Data.ReadJsonFile<GarmentDefinition>(relativePath);
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Skipped garment '{file}': JSON load failed: {ex.Message}", LogLevel.Error);
                return;
            }

            if (definition == null)
            {
                this.monitor.Log($"Skipped garment '{file}': definition is empty.", LogLevel.Error);
                return;
            }

            if (this.garments.ContainsKey(definition.Id ?? ""))
            {
                this.monitor.Log($"Skipped garment '{file}': duplicate Id '{definition.Id}'.", LogLevel.Error);
                return;
            }

            Texture2D texture;
            try
            {
                texture = this.helper.ModContent.Load<Texture2D>(definition.WornTexture);
            }
            catch (Exception ex)
            {
                this.monitor.Log($"Skipped garment '{definition.Id ?? file}': texture load failed: {ex.Message}", LogLevel.Error);
                return;
            }

            if (!definition.TryValidate(texture.Width, texture.Height, out string error))
            {
                this.monitor.Log($"Skipped garment '{definition.Id ?? file}': {error}", LogLevel.Error);
                return;
            }

            string digest = ComputeDigest(this.helper.DirectoryPath, relativePath, definition.WornTexture);
            this.garments[definition.Id] = new RegisteredGarment(definition, texture, digest);
        }

        private static string ComputeDigest(string modDirectory, string definitionPath, string texturePath)
        {
            try
            {
                byte[] a = File.ReadAllBytes(Path.Combine(modDirectory, definitionPath));
                byte[] b = File.ReadAllBytes(Path.Combine(modDirectory, texturePath));
                byte[] combined = new byte[a.Length + b.Length];
                Buffer.BlockCopy(a, 0, combined, 0, a.Length);
                Buffer.BlockCopy(b, 0, combined, a.Length, b.Length);
                return Convert.ToHexString(SHA256.HashData(combined)).ToLowerInvariant();
            }
            catch
            {
                return "";
            }
        }
    }

    internal sealed class RegisteredGarment
    {
        public RegisteredGarment(GarmentDefinition definition, Texture2D texture, string appearanceDigest)
        {
            this.Definition = definition;
            this.Texture = texture;
            this.AppearanceDigest = appearanceDigest ?? "";
        }

        public GarmentDefinition Definition { get; }
        public Texture2D Texture { get; }
        public string AppearanceDigest { get; }
    }

    internal sealed class GarmentRegistryIndex
    {
        public List<string> Garments { get; set; } = new();
    }
}
