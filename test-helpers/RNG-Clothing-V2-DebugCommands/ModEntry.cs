using System;
using System.Collections.Generic;
using StardewModdingAPI;
using StardewValley;

namespace RNGClothingV2.DebugCommands;

/// <summary>Test-only shorthand commands for the isolated RNG Clothing V2 pack.</summary>
public sealed class ModEntry : Mod
{
    private static readonly ShirtDefinition[] Shirts =
    {
        new("Stonefield Essential Tee", "(S)RNGClothing.V2.StonefieldEssentialTee"),
        new("Stonefield Rib-Knit Sweater", "(S)RNGClothing.V2.StonefieldRibKnitSweater"),
        new("Stonefield Tailored Shirt", "(S)RNGClothing.V2.StonefieldTailoredShirt"),
        new("Stonefield Layer Jacket", "(S)RNGClothing.V2.StonefieldLayerJacket"),
        new("Stonefield Sailor-Yoke Top", "(S)RNGClothing.V2.StonefieldSailorYokeTop"),
        new("Meadow Everyday Tee", "(S)RNGClothing.V2.MeadowEverydayTee"),
        new("Woodland Yoke Sweater", "(S)RNGClothing.V2.WoodlandYokeSweater"),
        new("Meadow Placket Shirt", "(S)RNGClothing.V2.MeadowPlacketShirt"),
        new("Mistral Lapel Layer Jacket", "(S)RNGClothing.V2.MistralLapelLayerJacket"),
        new("Garnet Yoke Top", "(S)RNGClothing.V2.GarnetYokeTop")
    };

    public override void Entry(IModHelper helper)
    {
        helper.ConsoleCommands.Add(
            "rngv2",
            "TEST ONLY. Give RNG Clothing V2 shirts.\n"
            + "Usage: rngv2 <all|control|rarity|1..10>",
            HandleCommand
        );
    }

    private void HandleCommand(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            Monitor.Log("Load a save before using rngv2.", LogLevel.Error);
            return;
        }

        if (!TrySelect(args, out int startIndex, out int count))
        {
            Monitor.Log("Usage: rngv2 <all|control|rarity|1..10>", LogLevel.Info);
            return;
        }

        var selected = new List<ShirtDefinition>(count);
        for (int index = startIndex; index < startIndex + count; index++)
        {
            ShirtDefinition shirt = Shirts[index];
            if (!ItemRegistry.Exists(shirt.QualifiedItemId))
            {
                Monitor.Log(
                    $"Can't find {shirt.Name} ({shirt.QualifiedItemId}). "
                    + "Make sure the RNG-Clothing-V2 Content Patcher pack is installed and loaded.",
                    LogLevel.Error
                );
                return;
            }

            selected.Add(shirt);
        }

        var dropped = new List<string>();
        foreach (ShirtDefinition shirt in selected)
        {
            Item item = ItemRegistry.Create(shirt.QualifiedItemId);
            if (!Utility.CollectOrDrop(item))
                dropped.Add(shirt.Name);
        }

        Monitor.Log(
            $"RNG Clothing V2 added: {string.Join(", ", GetNames(selected))}",
            LogLevel.Info
        );
        if (dropped.Count > 0)
        {
            Monitor.Log(
                $"Inventory was full; dropped at the player's feet: {string.Join(", ", dropped)}",
                LogLevel.Warn
            );
        }
    }

    private static bool TrySelect(string[] args, out int startIndex, out int count)
    {
        startIndex = 0;
        count = 0;
        if (args.Length != 1)
            return false;

        string selector = args[0].Trim().ToLowerInvariant();
        switch (selector)
        {
            case "all":
                count = Shirts.Length;
                return true;
            case "control":
                count = 5;
                return true;
            case "rarity":
                startIndex = 5;
                count = 5;
                return true;
            default:
                if (int.TryParse(selector, out int number) && number >= 1 && number <= Shirts.Length)
                {
                    startIndex = number - 1;
                    count = 1;
                    return true;
                }

                return false;
        }
    }

    private static IEnumerable<string> GetNames(IEnumerable<ShirtDefinition> shirts)
    {
        foreach (ShirtDefinition shirt in shirts)
            yield return shirt.Name;
    }

    private sealed class ShirtDefinition
    {
        public string Name { get; }
        public string QualifiedItemId { get; }

        public ShirtDefinition(string name, string qualifiedItemId)
        {
            Name = name;
            QualifiedItemId = qualifiedItemId;
        }
    }
}
