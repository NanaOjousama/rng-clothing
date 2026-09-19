using System;
using System.Text.Json;

namespace EnhancedSewingMachine.GarmentRuntime
{
    internal static class GarmentInstanceCodec
    {
        private static readonly JsonSerializerOptions Options = new()
        {
            PropertyNameCaseInsensitive = true,
            WriteIndented = false
        };

        public static string Encode(GarmentInstanceData instance)
        {
            if (instance == null)
                throw new ArgumentNullException(nameof(instance));
            return JsonSerializer.Serialize(instance, Options);
        }

        public static bool TryDecode(string json, out GarmentInstanceData instance, out string error)
        {
            instance = null;
            if (string.IsNullOrWhiteSpace(json))
            {
                error = "instance payload is empty";
                return false;
            }

            try
            {
                instance = JsonSerializer.Deserialize<GarmentInstanceData>(json, Options);
                if (instance == null || !instance.IsUsable())
                {
                    instance = null;
                    error = "instance payload is incomplete";
                    return false;
                }

                error = null;
                return true;
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return false;
            }
        }
    }
}
