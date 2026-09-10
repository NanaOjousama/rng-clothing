using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace RNGClothing.HoodieHairPolicy;

/// <summary>
/// Optional selector for the exact Harbor Haze Rare+ weather hood.
/// Fashion Sense still performs every draw; this mod only chooses between two
/// locked, pixel-identical Hat appearances with different HideHair policies.
/// </summary>
public sealed class ModEntry : Mod
{
    private const string FashionSenseId = "PeacefulEnd.FashionSense";
    private const string PackId = "RNGClothing.FashionSense.HoodieWeatherTest";
    private const string ShirtName = "Harbor Haze Weather Hoodie";
    private const string BaseHatName = "Harbor Haze Weather Hood";
    private const string AutoBackHatName = "Harbor Haze Weather Hood - Auto HideBackOnly";
    private const string AutoFrontHatName = "Harbor Haze Weather Hood - Auto PreserveFrontOnly";

    private const string CustomHairKey = "FashionSense.CustomHair.Id";
    private const string CustomBodyKey = "FashionSense.CustomBody.Id";

    private static readonly string ShirtId = $"{PackId}/Shirt/{ShirtName}";
    private static readonly string BaseHatId = $"{PackId}/Hat/{BaseHatName}";
    private static readonly string AutoBackHatId = $"{PackId}/Hat/{AutoBackHatName}";
    private static readonly string AutoFrontHatId = $"{PackId}/Hat/{AutoFrontHatName}";

    private IFashionSenseApi? fashionSense;
    private PolicyMap policyMap = new();

    public override void Entry(IModHelper helper)
    {
        this.policyMap = helper.Data.ReadJsonFile<PolicyMap>("vanilla-hair-policy-map.json")
            ?? throw new InvalidOperationException("Missing vanilla-hair-policy-map.json.");
        this.policyMap.Validate();

        helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
    }

    private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
    {
        this.fashionSense = this.Helper.ModRegistry.GetApi<IFashionSenseApi>(FashionSenseId);
        if (this.fashionSense is null)
            this.Monitor.Log("Fashion Sense API unavailable; automatic hoodie hair policy is disabled.", LogLevel.Error);
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!e.IsMultipleOf(15) || !Context.IsWorldReady || this.fashionSense is null)
            return;

        Farmer who = Game1.player;
        if (!who.IsLocalPlayer)
            return;

        string? currentHat = this.GetAppearanceId(IFashionSenseApi.Type.Hat, who);
        if (!IsManagedHat(currentHat))
            return;

        string? currentShirt = this.GetAppearanceId(IFashionSenseApi.Type.Shirt, who);
        string desiredHat = BaseHatId;

        // Never leave an internal policy Hat active after this exact hoodie is
        // removed. A player-selected unrelated Hat is never touched.
        if (currentShirt == ShirtId && IsHoodUp(who) && this.TryGetVanillaPolicy(who, out bool preserveFrontOnly))
            desiredHat = preserveFrontOnly ? AutoFrontHatId : AutoBackHatId;

        if (currentHat == desiredHat)
            return;

        string desiredName = desiredHat == AutoFrontHatId
            ? AutoFrontHatName
            : desiredHat == AutoBackHatId
                ? AutoBackHatName
                : BaseHatName;
        KeyValuePair<bool, string> result = this.fashionSense.SetAppearance(
            IFashionSenseApi.Type.Hat,
            PackId,
            desiredName,
            this.ModManifest
        );
        if (!result.Key)
            this.Monitor.Log($"Could not switch hoodie hair policy: {result.Value}", LogLevel.Warn);
    }

    private string? GetAppearanceId(IFashionSenseApi.Type type, Farmer who)
    {
        KeyValuePair<bool, string> result = this.fashionSense!.GetCurrentAppearanceId(type, who);
        return result.Key ? result.Value : null;
    }

    private bool TryGetVanillaPolicy(Farmer who, out bool preserveFrontOnly)
    {
        preserveFrontOnly = false;

        // Any Fashion Sense Hair is outside the audited vanilla contract.
        // Fail open by restoring the normal configured Hat instead of guessing.
        if (HasCustomAppearance(who, CustomHairKey) || HasCustomAppearance(who, CustomBodyKey))
            return false;

        int hairId = who.getHair();
        if (!this.policyMap.SupportedVanillaHairIds.Contains(hairId))
            return false;

        HashSet<int> severe = who.IsMale
            ? this.policyMap.PreserveFrontOnly.Masculine
            : this.policyMap.PreserveFrontOnly.Feminine;
        preserveFrontOnly = severe.Contains(hairId);
        return true;
    }

    private static bool IsHoodUp(Farmer who)
    {
        GameLocation? location = who.currentLocation;
        return location is not null
            && location.IsOutdoors
            && (Game1.IsRainingHere(location) || Game1.IsSnowingHere(location));
    }

    private static bool IsManagedHat(string? id)
    {
        return id == BaseHatId || id == AutoBackHatId || id == AutoFrontHatId;
    }

    private static bool HasCustomAppearance(Farmer who, string key)
    {
        return who.modData.TryGetValue(key, out string? value)
            && !string.IsNullOrWhiteSpace(value)
            && !string.Equals(value, "None", StringComparison.OrdinalIgnoreCase);
    }
}

public sealed class PolicyMap
{
    public string AuditSource { get; set; } = string.Empty;
    public HashSet<int> SupportedVanillaHairIds { get; set; } = new();
    public BranchPolicy PreserveFrontOnly { get; set; } = new();

    public void Validate()
    {
        if (this.SupportedVanillaHairIds.Count == 0)
            throw new InvalidOperationException("The vanilla hairstyle allowlist is empty.");
        if (!this.PreserveFrontOnly.Masculine.IsSubsetOf(this.SupportedVanillaHairIds)
            || !this.PreserveFrontOnly.Feminine.IsSubsetOf(this.SupportedVanillaHairIds))
        {
            throw new InvalidOperationException("The fallback map contains a non-vanilla hairstyle ID.");
        }
    }
}

public sealed class BranchPolicy
{
    public HashSet<int> Masculine { get; set; } = new();
    public HashSet<int> Feminine { get; set; } = new();
}

/// <summary>
/// Minimal proxy for Fashion Sense 7.5.0's public API. Keeping this local is
/// the standard SMAPI API-consumer pattern and avoids linking or vendoring the
/// Fashion Sense assembly.
/// </summary>
public interface IFashionSenseApi
{
    public enum Type
    {
        Unknown,
        Hair,
        Accessory,
        AccessorySecondary,
        AccessoryTertiary,
        Hat,
        Shirt,
        Pants,
        Sleeves,
        Shoes,
        Player
    }

    KeyValuePair<bool, string> SetAppearance(
        Type appearanceType,
        string targetPackId,
        string targetAppearanceName,
        IManifest callerManifest
    );

    KeyValuePair<bool, string> GetCurrentAppearanceId(Type appearanceType, Farmer? target = null);
}
