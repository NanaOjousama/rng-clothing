using System.Globalization;
using System.Text.Json;

namespace PhotoTailor;

internal static class GeneratedGarmentMigrationPolicy
{
	internal const int LegacySchemaVersion = 1;

	internal const int SafeRerenderSchemaVersion = 2;

	internal static int ReadSchemaVersion(string json)
	{
		using JsonDocument jsonDocument = JsonDocument.Parse(json);
		JsonElement rootElement = jsonDocument.RootElement;
		if (rootElement.ValueKind != JsonValueKind.Object)
		{
			return 1;
		}
		if (!rootElement.TryGetProperty("schema_version", out var value) && !rootElement.TryGetProperty("SchemaVersion", out value))
		{
			return 1;
		}
		if (value.ValueKind == JsonValueKind.Number && value.TryGetInt32(out var value2))
		{
			return value2;
		}
		if (value.ValueKind == JsonValueKind.String && int.TryParse(value.GetString(), NumberStyles.Integer, CultureInfo.InvariantCulture, out var result))
		{
			return result;
		}
		return 1;
	}

	internal static bool ShouldRerender(int storedRendererVersion, int currentRendererVersion, int schemaVersion)
	{
		if (schemaVersion >= 2)
		{
			return storedRendererVersion < currentRendererVersion;
		}
		return false;
	}
}
