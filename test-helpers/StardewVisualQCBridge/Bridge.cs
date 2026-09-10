using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using StardewModdingAPI;

namespace StardewVisualQCBridge
{
    /// <summary>Filesystem request/response transport.
    ///
    /// Deliberately not an MCP server and not a socket: a directory of JSON files
    /// is inspectable, survives a game crash, needs no new dependency, and works
    /// the same whether the caller is Claude Code, a shell script or a human.
    /// </summary>
    internal sealed class Bridge
    {
        public string Root { get; }
        public string Requests => Path.Combine(this.Root, "requests");
        public string Responses => Path.Combine(this.Root, "responses");
        public string Captures => Path.Combine(this.Root, "captures");
        public string Sessions => Path.Combine(this.Root, "sessions");
        public string LatestState => Path.Combine(this.Root, "latest_state.json");
        public string SessionId { get; }

        private readonly IMonitor monitor;
        private readonly HashSet<string> seen = new();

        public Bridge(string root, IMonitor monitor)
        {
            this.Root = root;
            this.monitor = monitor;
            this.SessionId = DateTime.Now.ToString("yyyyMMdd-HHmmss");
            foreach (string dir in new[] { this.Root, this.Requests, this.Responses, this.Captures, this.Sessions })
                Directory.CreateDirectory(dir);
        }

        /// <summary>Oldest unclaimed request, or null. Claiming is by rename, so a
        /// request can never be executed twice even if a tick overlaps.</summary>
        public Request Claim()
        {
            string[] files;
            try
            {
                files = Directory.GetFiles(this.Requests, "*.json");
            }
            catch (Exception ex)
            {
                this.monitor.Log($"could not read requests: {ex.Message}", LogLevel.Trace);
                return null;
            }
            Array.Sort(files, StringComparer.Ordinal);
            foreach (string file in files)
            {
                if (this.seen.Contains(file))
                    continue;
                this.seen.Add(file);
                try
                {
                    string body = File.ReadAllText(file);
                    var req = Json.ParseRequest(body, Path.GetFileNameWithoutExtension(file));
                    File.Delete(file);
                    return req;
                }
                catch (Exception ex)
                {
                    this.monitor.Log($"bad request {Path.GetFileName(file)}: {ex.Message}", LogLevel.Warn);
                    try { File.Delete(file); } catch { /* fail open */ }
                }
            }
            return null;
        }

        public void Respond(string id, bool ok, string message, IDictionary<string, object> data = null)
        {
            var payload = new Dictionary<string, object>
            {
                ["id"] = id,
                ["ok"] = ok,
                ["message"] = message ?? "",
                ["session"] = this.SessionId,
                ["timestamp"] = DateTime.Now.ToString("o")
            };
            if (data != null)
                foreach (var kv in data)
                    payload[kv.Key] = kv.Value;

            string path = Path.Combine(this.Responses, id + ".json");
            try
            {
                // write-then-move so a reader never sees a half-written file
                string tmp = path + ".tmp";
                File.WriteAllText(tmp, Json.Write(payload));
                if (File.Exists(path))
                    File.Delete(path);
                File.Move(tmp, path);
            }
            catch (Exception ex)
            {
                this.monitor.Log($"could not write response {id}: {ex.Message}", LogLevel.Warn);
            }
        }

        public void WriteLatest(IDictionary<string, object> state)
        {
            try
            {
                string tmp = this.LatestState + ".tmp";
                File.WriteAllText(tmp, Json.Write(state));
                if (File.Exists(this.LatestState))
                    File.Delete(this.LatestState);
                File.Move(tmp, this.LatestState);
            }
            catch { /* fail open: QC must never break the game */ }
        }
    }

    internal sealed class Request
    {
        public string Id;
        public string Command;
        public Dictionary<string, string> Args = new();

        public string Arg(string name, string fallback = null)
            => this.Args.TryGetValue(name, out string v) ? v : fallback;

        public int ArgInt(string name, int fallback)
            => int.TryParse(this.Arg(name), out int v) ? v : fallback;
    }
}
