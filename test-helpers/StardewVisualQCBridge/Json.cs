using System.Collections.Generic;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace StardewVisualQCBridge
{
    /// <summary>Thin wrapper over the Newtonsoft build SMAPI already loads.
    /// No new dependency is introduced.</summary>
    internal static class Json
    {
        public static string Write(object value)
            => JsonConvert.SerializeObject(value, Formatting.Indented);

        public static Request ParseRequest(string body, string fallbackId)
        {
            var obj = JObject.Parse(body);
            var req = new Request
            {
                Id = obj.Value<string>("id") ?? fallbackId,
                Command = (obj.Value<string>("command") ?? obj.Value<string>("cmd") ?? "").Trim()
            };
            if (obj["args"] is JObject args)
            {
                foreach (var prop in args.Properties())
                    req.Args[prop.Name] = prop.Value?.ToString() ?? "";
            }
            return req;
        }
    }
}
