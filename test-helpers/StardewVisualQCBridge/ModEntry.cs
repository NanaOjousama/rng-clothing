using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace StardewVisualQCBridge
{
    public sealed class ModConfig
    {
        /// <summary>Where the request/response tree lives. Empty = inside the mod folder.</summary>
        public string BridgePath { get; set; } = "";
        /// <summary>Ticks between request polls. 15 is a quarter second; QC does not need more.</summary>
        public int PollIntervalTicks { get; set; } = 15;
        /// <summary>Master switch. When false the mod does nothing at all.</summary>
        public bool Enabled { get; set; } = true;
    }

    /// <summary>Development-only QC bridge.
    ///
    /// Scope discipline, because this runs inside someone's save:
    ///   * it never patches Fashion Sense or the game renderer;
    ///   * it only reads state, moves the player's facing, and equips hats — all
    ///     things the player can already do;
    ///   * every path fails open: a QC error is logged and swallowed, never
    ///     allowed to break a frame;
    ///   * with Enabled=false it subscribes to nothing.
    /// </summary>
    public sealed class ModEntry : Mod
    {
        private ModConfig config;
        private Bridge bridge;
        private int tick;

        private PendingCapture pending;
        private List<HatPacks.HatEntry> hats = new();
        private int cursor = -1;

        private sealed class PendingCapture
        {
            public string RequestId;
            public string Label;
            public Queue<int> Directions = new();
            public List<string> Written = new();
            public Dictionary<string, object> PerDirection = new();
            public bool ClearHatPass;
            public string RestoreHatId;
            public int SettleTicks;
        }

        public override void Entry(IModHelper helper)
        {
            this.config = helper.ReadConfig<ModConfig>();
            if (!this.config.Enabled)
            {
                this.Monitor.Log("QC Bridge disabled by config; doing nothing.", LogLevel.Info);
                return;
            }

            string root = string.IsNullOrWhiteSpace(this.config.BridgePath)
                ? Path.Combine(helper.DirectoryPath, "qc_bridge")
                : this.config.BridgePath;
            this.bridge = new Bridge(root, this.Monitor);
            HatPacks.Init(helper);

            helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
            helper.Events.GameLoop.UpdateTicking += (_, _) => FittingProbe.ApplyInput(helper);
            helper.Events.Display.Rendered += this.OnRendered;
            helper.ConsoleCommands.Add("qc", "Stardew Visual QC Bridge.\n"
                + "Usage: qc <list|equip <id>|next|prev|clear|dir <front|right|back|left>|"
                + "scene|state|capture [label]|capture_all [label]|vanilla <id>|vlist|give <item id>>", this.OnConsole);

            this.Monitor.Log($"QC Bridge ready. Session {this.bridge.SessionId}", LogLevel.Info);
            this.Monitor.Log($"Bridge root: {root}", LogLevel.Info);
        }

        // ------------------------------------------------------------------
        // request loop
        // ------------------------------------------------------------------

        private void OnUpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            if (this.pending != null && this.pending.SettleTicks > 0)
                this.pending.SettleTicks--;

            if (++this.tick < this.config.PollIntervalTicks)
                return;
            this.tick = 0;

            if (this.pending != null)
                return;                     // one capture at a time

            Request req = this.bridge.Claim();
            if (req == null)
                return;

            try
            {
                this.Dispatch(req);
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"{req.Command} failed: {ex}", LogLevel.Error);
                this.bridge.Respond(req.Id, false, ex.Message);
            }
        }

        private void Dispatch(Request req)
        {
            switch (req.Command.ToLowerInvariant())
            {
                case "ping":
                    this.bridge.Respond(req.Id, true, "pong", new Dictionary<string, object>
                    {
                        ["world_ready"] = Context.IsWorldReady
                    });
                    return;

                case "list_hats":
                    this.RespondList(req.Id);
                    return;

                case "fs_reload":
                    this.FsReload(req);
                    return;

                case "give_item":
                    this.GiveItem(req);
                    return;

                case "equip_garment":
                    this.EquipGeneratedGarment(req);
                    return;

                case "fitting_probe":
                    this.bridge.Respond(req.Id, true, "fitting probe",
                        FittingProbe.Run(this.Helper, req, this.bridge.Root));
                    return;

                case "get_render_state":
                {
                    var state = RenderState.Capture(this.Helper, this.bridge);
                    this.bridge.WriteLatest(state);
                    this.bridge.Respond(req.Id, true, "state", new Dictionary<string, object> { ["state"] = state });
                    return;
                }

                case "equip_hat":
                    this.Equip(req.Id, req.Arg("id") ?? req.Arg("hat"));
                    return;

                case "next_hat":
                    this.Step(req.Id, +1);
                    return;

                case "previous_hat":
                    this.Step(req.Id, -1);
                    return;

                case "list_vanilla_hats":
                    this.RespondVanillaList(req.Id);
                    return;

                case "equip_vanilla_hat":
                    this.EquipVanilla(req.Id, req.Arg("id") ?? req.Arg("hat"));
                    return;

                case "clear_hat":
                    this.RequireWorld(req.Id, () =>
                    {
                        Game1.player.modData.Remove("FashionSense.CustomHat.Id");
                        Game1.player.Equip(null, Game1.player.hat);
                        this.SetDirty();
                        this.bridge.Respond(req.Id, true, "cleared");
                    });
                    return;

                case "set_direction":
                    this.RequireWorld(req.Id, () =>
                    {
                        int d = RenderState.FacingFromName(req.Arg("direction") ?? req.Arg("dir"));
                        if (d < 0)
                        {
                            this.bridge.Respond(req.Id, false, "direction must be front|right|back|left");
                            return;
                        }
                        this.FaceAndSettle(d);
                        this.bridge.Respond(req.Id, true, RenderState.Facing(d));
                    });
                    return;

                case "set_scene":
                    this.RequireWorld(req.Id, () => this.SetScene(req));
                    return;

                case "capture_hat":
                case "capture":
                    this.BeginCapture(req, new[] { Game1.player?.FacingDirection ?? 2 });
                    return;

                case "capture_all_directions":
                case "capture_all":
                    // front, right, back, left — reported in the order a reviewer reads them
                    this.BeginCapture(req, new[] { 2, 1, 0, 3 });
                    return;

                default:
                    this.bridge.Respond(req.Id, false, $"unknown command '{req.Command}'");
                    return;
            }
        }

        private void RequireWorld(string id, Action action)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(id, false, "no save loaded");
                return;
            }
            action();
        }

        // ------------------------------------------------------------------
        // hats
        // ------------------------------------------------------------------

        private void RespondList(string id)
        {
            this.hats = HatPacks.List();
            var rows = this.hats.Select((h, i) => (object)new Dictionary<string, object>
            {
                ["index"] = i,
                ["appearance_id"] = h.AppearanceId,
                ["pack_id"] = h.PackId,
                ["pack_name"] = h.PackName,
                ["name"] = h.AppearanceName,
                ["folder"] = h.FolderName
            }).ToList();
            this.bridge.Respond(id, true, $"{rows.Count} Fashion Sense hats",
                new Dictionary<string, object> { ["hats"] = rows });
        }

        private void Equip(string id, string wanted)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(id, false, "no save loaded");
                return;
            }
            if (string.IsNullOrWhiteSpace(wanted))
            {
                this.bridge.Respond(id, false, "equip_hat needs args.id");
                return;
            }

            this.hats = HatPacks.List();
            HatPacks.HatEntry hit =
                this.hats.FirstOrDefault(h => h.AppearanceId == wanted)
                ?? this.hats.FirstOrDefault(h => string.Equals(h.AppearanceName, wanted, StringComparison.OrdinalIgnoreCase))
                ?? this.hats.FirstOrDefault(h => string.Equals(h.FolderName, wanted, StringComparison.OrdinalIgnoreCase))
                ?? this.hats.FirstOrDefault(h => h.AppearanceName.IndexOf(wanted, StringComparison.OrdinalIgnoreCase) >= 0)
                ?? this.hats.FirstOrDefault(h => h.FolderName.IndexOf(wanted, StringComparison.OrdinalIgnoreCase) >= 0);

            if (hit == null)
            {
                this.bridge.Respond(id, false, $"no Fashion Sense hat matching '{wanted}'");
                return;
            }

            this.cursor = this.hats.IndexOf(hit);
            Game1.player.modData["FashionSense.CustomHat.Id"] = hit.AppearanceId;
            this.SetDirty();
            this.bridge.Respond(id, true, $"equipped {hit.AppearanceId}", new Dictionary<string, object>
            {
                ["appearance_id"] = hit.AppearanceId,
                ["index"] = this.cursor,
                ["folder"] = hit.FolderName
            });
        }

        /// <summary>Vanilla hats, for the calibration group. Read from the game's
        /// own hat data so the list is whatever this install actually has.</summary>
        private void RespondVanillaList(string id)
        {
            var rows = new List<object>();
            try
            {
                var data = Game1.content.Load<Dictionary<string, string>>("Data\\hats");
                foreach (var pair in data)
                {
                    var row = new Dictionary<string, object> { ["id"] = pair.Key };
                    try
                    {
                        var hat = new StardewValley.Objects.Hat(pair.Key);
                        row["name"] = hat.Name;
                        row["display_name"] = hat.DisplayName;
                        row["item_id"] = hat.ItemId;
                    }
                    catch { row["name"] = pair.Key; }
                    rows.Add(row);
                }
            }
            catch (Exception ex)
            {
                this.bridge.Respond(id, false, ex.Message);
                return;
            }
            this.bridge.Respond(id, true, $"{rows.Count} vanilla hats",
                new Dictionary<string, object> { ["hats"] = rows });
        }

        private void EquipVanilla(string id, string wanted)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(id, false, "no save loaded");
                return;
            }
            if (string.IsNullOrWhiteSpace(wanted))
            {
                this.bridge.Respond(id, false, "equip_vanilla_hat needs args.id");
                return;
            }
            try
            {
                // a vanilla hat and a Fashion Sense hat both draw; clear ours first
                Game1.player.modData.Remove("FashionSense.CustomHat.Id");
                var hat = new StardewValley.Objects.Hat(wanted);
                Game1.player.Equip(hat, Game1.player.hat);
                this.SetDirty();
                this.bridge.Respond(id, true, $"equipped vanilla {wanted}",
                    new Dictionary<string, object>
                    {
                        ["id"] = wanted,
                        ["name"] = hat.Name,
                        ["item_id"] = hat.ItemId
                    });
            }
            catch (Exception ex)
            {
                this.bridge.Respond(id, false, $"could not equip vanilla hat '{wanted}': {ex.Message}");
            }
        }

        private void Step(string id, int delta)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(id, false, "no save loaded");
                return;
            }
            this.hats = HatPacks.List();
            if (this.hats.Count == 0)
            {
                this.bridge.Respond(id, false, "no Fashion Sense hats installed");
                return;
            }
            this.cursor = ((this.cursor + delta) % this.hats.Count + this.hats.Count) % this.hats.Count;
            var hit = this.hats[this.cursor];
            Game1.player.modData["FashionSense.CustomHat.Id"] = hit.AppearanceId;
            this.SetDirty();
            this.bridge.Respond(id, true, $"equipped {hit.AppearanceId}", new Dictionary<string, object>
            {
                ["appearance_id"] = hit.AppearanceId,
                ["index"] = this.cursor
            });
        }

        /// <summary>Reload Fashion Sense content packs in place, the way the
        /// fs_reload console command does.
        ///
        /// Fashion Sense loads pack textures once at startup, so a rebuilt pack
        /// is invisible until it reloads. Three QC capture runs were lost to
        /// that: the watcher saw a world already loaded, captured against stale
        /// textures, and two newly installed hats silently drew nothing.
        ///
        /// The framework exposes fs_reload as a SMAPI console command, but
        /// SMAPI 4.0 removed ICommandHelper.Trigger, so a mod can no longer
        /// invoke another mod's command. The command handler itself is a
        /// private method on the Fashion Sense entry class, so this reaches it
        /// the same way the rest of this file already reaches the FS API: by
        /// reflection, failing loudly rather than pretending a reload happened.
        ///
        /// LoadContentPacks(bool silent, string packId) is preferred because it
        /// accepts a single pack id; ReloadFashionSense(command, args) is the
        /// public-facing entry point and is used as a fallback.</summary>
        private void FsReload(Request req)
        {
            string packId = req.Arg("pack");
            var info = this.Helper.ModRegistry.Get("PeacefulEnd.FashionSense");
            if (info == null)
            {
                this.bridge.Respond(req.Id, false, "Fashion Sense is not installed");
                return;
            }

            object mod = null;
            try
            {
                var prop = info.GetType().GetProperty("Mod",
                    System.Reflection.BindingFlags.Public
                    | System.Reflection.BindingFlags.NonPublic
                    | System.Reflection.BindingFlags.Instance);
                mod = prop?.GetValue(info);
            }
            catch (Exception ex)
            {
                this.bridge.Respond(req.Id, false, $"could not reach the Fashion Sense mod instance: {ex.Message}");
                return;
            }
            if (mod == null)
            {
                this.bridge.Respond(req.Id, false, "could not reach the Fashion Sense mod instance");
                return;
            }

            const System.Reflection.BindingFlags Flags =
                System.Reflection.BindingFlags.NonPublic
                | System.Reflection.BindingFlags.Public
                | System.Reflection.BindingFlags.Instance;
            string how;
            try
            {
                var load = mod.GetType().GetMethod("LoadContentPacks", Flags);
                if (load != null)
                {
                    load.Invoke(mod, new object[] { false, packId });
                    how = packId == null ? "LoadContentPacks" : $"LoadContentPacks({packId})";
                }
                else
                {
                    var reload = mod.GetType().GetMethod("ReloadFashionSense", Flags);
                    if (reload == null)
                    {
                        this.bridge.Respond(req.Id, false,
                            "Fashion Sense has neither LoadContentPacks nor ReloadFashionSense; "
                            + "the framework's internals changed. Fall back to restarting the game.");
                        return;
                    }
                    reload.Invoke(mod, new object[] { "fs_reload",
                        packId == null ? new string[0] : new[] { packId } });
                    how = "ReloadFashionSense";
                }
            }
            catch (Exception ex)
            {
                var inner = ex.InnerException ?? ex;
                this.bridge.Respond(req.Id, false, $"reload threw: {inner.Message}");
                return;
            }

            // The reload replaces the loaded models, so anything the player is
            // wearing now points at a stale object: rebuild the sprite and hand
            // back the fresh appearance list in the same response, so a caller
            // cannot capture against what it listed BEFORE the reload.
            this.SetDirty();
            List<HatPacks.HatEntry> hats;
            try { hats = HatPacks.List(); }
            catch (Exception ex)
            {
                this.bridge.Respond(req.Id, false, $"reloaded ({how}) but re-listing failed: {ex.Message}");
                return;
            }
            this.bridge.Respond(req.Id, true, $"reloaded via {how}", new Dictionary<string, object>
            {
                ["method"] = how,
                ["pack"] = packId,
                ["hat_count"] = hats.Count,
                ["hats"] = hats.Select(h => h.AppearanceId).ToList()
            });
        }

        /// <summary>Ask Fashion Sense to rebuild the player sprite. Uses the public
        /// API when present; a facing nudge is enough on its own in practice.</summary>
        private void SetDirty()
        {
            try
            {
                var api = this.Helper.ModRegistry.GetApi("PeacefulEnd.FashionSense");
                api?.GetType().GetMethod("SetSpriteDirty")?.Invoke(api, new object[] { Game1.player, true });
            }
            catch { /* fail open */ }
            try { Game1.player.FarmerRenderer.MarkSpriteDirty(); } catch { }
        }

        // ------------------------------------------------------------------
        // scene control
        // ------------------------------------------------------------------

        private void SetScene(Request req)
        {
            Farmer who = Game1.player;
            if (int.TryParse(req.Arg("hairstyle"), out int hair))
                who.changeHairStyle(hair);
            // Zoom is deliberately NOT set here. Options.zoomLevel is derived and
            // read-only in 1.6, and forcing the base zoom mid-session desyncs the
            // viewport. Zoom is RECORDED with every capture instead, so a QC run
            // is comparable as long as the player does not change it.
            if (bool.TryParse(req.Arg("freeze"), out bool freeze) && freeze)
                this.Freeze();
            int d = RenderState.FacingFromName(req.Arg("direction") ?? req.Arg("dir"));
            if (d >= 0)
                this.FaceAndSettle(d);
            this.SetDirty();
            this.bridge.Respond(req.Id, true, "scene set",
                new Dictionary<string, object> { ["state"] = RenderState.Capture(this.Helper, this.bridge) });
        }

        /// <summary>Face a direction and settle to the idle frame, so captures across
        /// directions differ only by direction — not by whatever the walk cycle
        /// happened to be doing. The animation frame changes the hat's own feature
        /// offset, so an unsettled capture measures the wrong thing.</summary>
        private void FaceAndSettle(int direction)
        {
            Farmer who = Game1.player;
            this.Freeze();
            who.faceDirection(direction);
            who.FarmerSprite.StopAnimation();
            who.completelyStopAnimatingOrDoingAction();
            this.SetDirty();
        }

        private void Freeze()
        {
            Farmer who = Game1.player;
            who.Halt();
            who.setRunning(false, true);
            who.forceTimePass = false;
            Game1.player.CanMove = true;
        }

        // ------------------------------------------------------------------
        // capture
        // ------------------------------------------------------------------

        private void BeginCapture(Request req, IEnumerable<int> directions)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(req.Id, false, "no save loaded");
                return;
            }
            string label = req.Arg("label");
            if (string.IsNullOrWhiteSpace(label))
            {
                Game1.player.modData.TryGetValue("FashionSense.CustomHat.Id", out string cur);
                label = Sanitize(cur ?? Game1.player.hat.Value?.Name ?? "nohat");
            }
            this.pending = new PendingCapture
            {
                RequestId = req.Id,
                Label = label,
                SettleTicks = 4
            };
            foreach (int d in directions)
                this.pending.Directions.Enqueue(d);
            this.FaceAndSettle(this.pending.Directions.Peek());
        }

        private void OnRendered(object sender, RenderedEventArgs e)
        {
            if (this.pending == null || this.pending.SettleTicks > 0)
                return;
            if (!Context.IsWorldReady || Game1.player == null)
            {
                this.bridge.Respond(this.pending.RequestId, false, "world went away mid-capture");
                this.pending = null;
                return;
            }

            try
            {
                this.CaptureOneDirection();
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"capture failed: {ex}", LogLevel.Error);
                this.bridge.Respond(this.pending.RequestId, false, ex.Message);
                this.pending = null;
            }
        }

        private void CaptureOneDirection()
        {
            PendingCapture p = this.pending;
            int direction = p.Directions.Dequeue();
            string dirName = RenderState.Facing(direction);
            string dir = Path.Combine(this.bridge.Captures, this.bridge.SessionId, p.Label);
            Directory.CreateDirectory(dir);

            var record = new Dictionary<string, object>
            {
                ["direction"] = dirName,
                ["facing_direction"] = direction
            };

            // 1. the authority: what is actually on screen
            string screen = Path.Combine(dir, $"{dirName}_screen.png");
            if (Capture.SaveScreen(screen, out string screenError))
            {
                record["screen"] = screen;
                p.Written.Add(screen);
            }
            else
                record["screen_error"] = screenError;

            string crop = Path.Combine(dir, $"{dirName}_head.png");
            if (Capture.SaveHeadCrop(crop, out string cropError, out var cropDebug))
            {
                record["head_crop"] = crop;
                p.Written.Add(crop);
            }
            else
                record["head_crop_error"] = cropError;
            record["screen_anchors"] = cropDebug;

            // 2. the measurable pass: same renderer, no world behind it
            string worn = Path.Combine(dir, $"{dirName}_worn.png");
            Color[] withHat = Capture.SaveIsolated(worn, out int w, out int h, out string wornError);
            if (withHat != null)
            {
                record["worn"] = worn;
                record["worn_bounds"] = Capture.AlphaBounds(withHat, w, h);
                p.Written.Add(worn);

                // 3. the same farmer with the hat removed, so the hat's real
                //    drawn footprint can be recovered by difference
                Game1.player.modData.TryGetValue("FashionSense.CustomHat.Id", out string keep);
                // Fashion Sense writes the literal string "None" for no hat.
                if (string.Equals(keep, "None", StringComparison.OrdinalIgnoreCase))
                    keep = null;
                StardewValley.Objects.Hat vanillaHat = Game1.player.hat.Value;
                bool hadHat = !string.IsNullOrEmpty(keep) || vanillaHat != null;
                if (hadHat)
                {
                    // the hairstyle the hat's hair policy actually draws
                    // (vanilla Farmer.getHair: e.g. DrawObscuredHair maps 38 -> 30)
                    int policyHair = Game1.player.getHair();
                    if (keep != null)
                        Game1.player.modData.Remove("FashionSense.CustomHat.Id");
                    if (vanillaHat != null)
                        Game1.player.Equip(null, Game1.player.hat);
                    this.SetDirty();
                    string bare = Path.Combine(dir, $"{dirName}_nohat.png");
                    Color[] without = Capture.SaveIsolated(bare, out _, out _, out _);

                    // 3b. hat removed but its hair policy kept: the "mannequin"
                    //     a replacement hat is designed against
                    int realHair = Game1.player.hair.Value;
                    record["hair_real"] = realHair;
                    record["hair_policy"] = policyHair;
                    if (policyHair >= 0 && policyHair != realHair)
                    {
                        Game1.player.hair.Value = policyHair;
                        this.SetDirty();
                        string policyPath = Path.Combine(dir, $"{dirName}_nohat_policy.png");
                        if (Capture.SaveIsolated(policyPath, out _, out _, out _) != null)
                        {
                            record["nohat_policy"] = policyPath;
                            p.Written.Add(policyPath);
                        }
                        Game1.player.hair.Value = realHair;
                        this.SetDirty();
                    }
                    else if (policyHair < 0)
                        record["nohat_policy_note"] = "hat hides hair entirely (HideHair); not captured";

                    if (keep != null)
                        Game1.player.modData["FashionSense.CustomHat.Id"] = keep;
                    if (vanillaHat != null)
                        Game1.player.Equip(vanillaHat, Game1.player.hat);
                    this.SetDirty();

                    if (without != null)
                    {
                        record["nohat"] = bare;
                        p.Written.Add(bare);
                        Color[] only = Capture.Difference(withHat, without, w, h, out int changed, out int removed);
                        string onlyPath = Path.Combine(dir, $"{dirName}_hatonly.png");
                        Capture.SaveBuffer(only, w, h, onlyPath);
                        record["hat_only"] = onlyPath;
                        record["hat_only_bounds"] = Capture.AlphaBounds(only, w, h);
                        record["hat_changed_pixels"] = changed;
                        // pixels the hat DELETED rather than drew (hidden hair,
                        // a bald head, or hair the hat now covers). Reported
                        // rather than drawn, so the isolated frame stays clean.
                        record["body_pixels_removed_by_hat"] = removed;
                        record["head_bounds_without_hat"] = Capture.AlphaBounds(without, w, h);
                        p.Written.Add(onlyPath);
                    }
                }
            }
            else
                record["worn_error"] = wornError;

            record["render_state"] = RenderState.Capture(this.Helper, this.bridge);
            p.PerDirection[dirName] = record;

            if (p.Directions.Count > 0)
            {
                this.FaceAndSettle(p.Directions.Peek());
                p.SettleTicks = 4;
                return;
            }

            string statePath = Path.Combine(dir, "render_state.json");
            File.WriteAllText(statePath, Json.Write(new Dictionary<string, object>
            {
                ["label"] = p.Label,
                ["session"] = this.bridge.SessionId,
                ["timestamp"] = DateTime.Now.ToString("o"),
                ["isolated_target_size"] = Capture.TargetSize,
                ["directions"] = p.PerDirection
            }));

            this.bridge.Respond(p.RequestId, true, $"captured {p.PerDirection.Count} direction(s)",
                new Dictionary<string, object>
                {
                    ["label"] = p.Label,
                    ["directory"] = dir,
                    ["render_state"] = statePath,
                    ["files"] = p.Written
                });
            this.pending = null;
        }

        private static string Sanitize(string name)
        {
            var chars = (name ?? "hat").Select(c => char.IsLetterOrDigit(c) ? c : '_').ToArray();
            string s = new string(chars).Trim('_');
            return string.IsNullOrEmpty(s) ? "hat" : s;
        }

        // ------------------------------------------------------------------
        // console
        // ------------------------------------------------------------------

        /// <summary>DEV TESTING ONLY. Put a generated wearable in the player's
        /// hands so the sewing-machine fitting flow can be exercised.
        ///
        /// Fashion Sense appearances that declare `Item` become real hats with
        /// an id of the form `&lt;PackId&gt;/Hat/&lt;Name&gt;/Item`; this accepts that
        /// bare form as well as the qualified `(H)` one.</summary>
        private void EquipGeneratedGarment(Request req)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(req.Id, false, "world not ready");
                return;
            }
            if (Game1.activeClickableMenu != null)
            {
                this.bridge.Respond(req.Id, false, "close the current menu first");
                return;
            }

            string wanted = req.Arg("id");
            if (string.IsNullOrWhiteSpace(wanted))
            {
                this.bridge.Respond(req.Id, false, "equip_garment needs args.id");
                return;
            }

            string modsPath = Directory.GetParent(this.Helper.DirectoryPath)?.FullName
                ?? throw new InvalidOperationException("could not resolve Mods folder");
            string garmentRoot = Path.Combine(
                modsPath,
                "EnhancedSewingMachine",
                "assets",
                "garments");
            if (!Directory.Exists(garmentRoot))
            {
                this.bridge.Respond(req.Id, false, "EnhancedSewingMachine garment registry folder not found");
                return;
            }

            string hitPath = null;
            JsonElement hit = default;
            foreach (string path in Directory.GetFiles(garmentRoot, "*.json", SearchOption.AllDirectories))
            {
                if (Path.GetFileName(path).Equals("index.json", StringComparison.OrdinalIgnoreCase))
                    continue;
                try
                {
                    using JsonDocument doc = JsonDocument.Parse(File.ReadAllText(path));
                    JsonElement root = doc.RootElement;
                    if (root.TryGetProperty("Id", out JsonElement id)
                        && string.Equals(id.GetString(), wanted, StringComparison.Ordinal))
                    {
                        hitPath = path;
                        hit = root.Clone();
                        break;
                    }
                }
                catch
                {
                    // Ignore malformed unrelated lab/dev files; ESM owns registry validation.
                }
            }

            if (hitPath == null)
            {
                this.bridge.Respond(req.Id, false, $"unknown garment '{wanted}'");
                return;
            }

            string Str(JsonElement obj, string name, string fallback = "")
                => obj.TryGetProperty(name, out JsonElement v) && v.ValueKind == JsonValueKind.String
                    ? v.GetString() ?? fallback
                    : fallback;
            int Int(JsonElement obj, string name, int fallback = 0)
                => obj.TryGetProperty(name, out JsonElement v) && v.TryGetInt32(out int n) ? n : fallback;

            JsonElement metadata = hit.TryGetProperty("Metadata", out JsonElement meta)
                ? meta
                : default;

            var render = new Dictionary<string, object>
            {
                ["DefinitionVersion"] = Int(hit, "DefinitionVersion", 1),
                ["WornTexture"] = Str(hit, "WornTexture"),
                ["FrameWidth"] = Int(hit, "FrameWidth"),
                ["FrameHeight"] = Int(hit, "FrameHeight"),
                ["RenderScale"] = hit.TryGetProperty("RenderScale", out JsonElement rs) ? rs.GetSingle() : 1f,
                ["VanillaReferenceAnchor"] = hit.GetProperty("VanillaReferenceAnchor").Clone(),
                ["Directions"] = hit.GetProperty("Directions").Clone(),
                ["AppearanceDigest"] = ""
            };

            var payload = new Dictionary<string, object>
            {
                ["SchemaVersion"] = 1,
                ["GarmentId"] = Str(hit, "Id"),
                ["GenerationVersion"] = Int(hit, "DefinitionVersion", 1),
                ["Seed"] = 0L,
                ["Category"] = Str(hit, "Category", "Hat"),
                ["Family"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Family") : "",
                ["Construction"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Construction") : "",
                ["Material"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Material") : "",
                ["Palette"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Palette") : "",
                ["Motif"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Motif") : "",
                ["GeneratorId"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "GeneratorId") : "",
                ["GeneratorVersion"] = metadata.ValueKind == JsonValueKind.Object ? Int(metadata, "GeneratorVersion", 1) : 1,
                ["GeneratorSeed"] = metadata.ValueKind == JsonValueKind.Object && metadata.TryGetProperty("GeneratorSeed", out JsonElement gs) && gs.TryGetInt64(out long gsv) ? gsv : 0L,
                ["Style"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Style") : "",
                ["QualityTier"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "QualityTier") : "",
                ["Decals"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Decals") : "",
                ["Classification"] = metadata.ValueKind == JsonValueKind.Object ? Str(metadata, "Classification") : "",
                ["FitOffsetX"] = 0,
                ["FitOffsetY"] = 0,
                ["FitScale"] = 1f,
                ["Render"] = render
            };

            var hat = ItemRegistry.Create<StardewValley.Objects.Hat>("(H)RNGClothing.ESM.GeneratedHat");
            hat.modData["RNGClothing.ESM/Instance"] = JsonSerializer.Serialize(payload);
            hat.modData["RNGClothing.ESM/GarmentId"] = wanted;
            hat.modData["RNGClothing.ESM/AppearanceDigest"] = "";
            hat.modData["RNGClothing.ESM/GenerationVersion"] = Int(hit, "DefinitionVersion", 1).ToString();

            StardewValley.Objects.Hat previous = Game1.player.hat.Value;
            if (previous != null && !Game1.player.addItemToInventoryBool(previous))
            {
                this.bridge.Respond(req.Id, false, "inventory is full; current hat left equipped");
                return;
            }

            Game1.player.hat.Value = hat;
            this.SetDirty();
            this.bridge.Respond(req.Id, true, $"equipped generated garment {wanted}",
                new Dictionary<string, object>
                {
                    ["garment_id"] = wanted,
                    ["definition"] = hitPath,
                    ["qualified_item_id"] = hat.QualifiedItemId
                });
        }

        private void GiveItem(Request req)
        {
            if (!Context.IsWorldReady)
            {
                this.bridge.Respond(req.Id, false, "world not ready");
                return;
            }
            string id = req.Args.TryGetValue("id", out string raw) ? raw : null;
            if (string.IsNullOrWhiteSpace(id))
            {
                this.bridge.Respond(req.Id, false, "give <item id>");
                return;
            }
            if (!id.StartsWith("(", StringComparison.Ordinal))
                id = "(H)" + id;

            Item item = ItemRegistry.Create(id, 1, 0, allowNull: true);
            if (item == null)
            {
                this.bridge.Respond(req.Id, false, $"no such item: {id}");
                return;
            }
            if (!Game1.player.addItemToInventoryBool(item))
            {
                this.bridge.Respond(req.Id, false, "inventory is full");
                return;
            }
            this.Monitor.Log($"gave {item.DisplayName} ({id})", LogLevel.Info);
            this.bridge.Respond(req.Id, true, item.DisplayName, new Dictionary<string, object>
            {
                ["item_id"] = item.ItemId,
                ["qualified_item_id"] = item.QualifiedItemId
            });
        }

        private void OnConsole(string command, string[] args)
        {
            string sub = args.Length > 0 ? args[0].ToLowerInvariant() : "help";
            var req = new Request { Id = $"console-{DateTime.Now:HHmmssfff}", Command = sub };
            switch (sub)
            {
                case "list": req.Command = "list_hats"; break;
                case "equip": req.Command = "equip_hat"; req.Args["id"] = string.Join(" ", args.Skip(1)); break;
                case "next": req.Command = "next_hat"; break;
                case "prev": req.Command = "previous_hat"; break;
                case "clear": req.Command = "clear_hat"; break;
                case "vlist": req.Command = "list_vanilla_hats"; break;
                case "vanilla": req.Command = "equip_vanilla_hat"; req.Args["id"] = string.Join(" ", args.Skip(1)); break;
                case "dir": req.Command = "set_direction"; req.Args["direction"] = args.ElementAtOrDefault(1) ?? ""; break;
                case "state": req.Command = "get_render_state"; break;
                case "scene": req.Command = "set_scene";
                    for (int i = 1; i + 1 < args.Length; i += 2) req.Args[args[i]] = args[i + 1];
                    break;
                case "capture": req.Command = "capture_hat"; req.Args["label"] = args.ElementAtOrDefault(1) ?? ""; break;
                case "capture_all": req.Command = "capture_all_directions"; req.Args["label"] = args.ElementAtOrDefault(1) ?? ""; break;
                case "give": req.Command = "give_item"; req.Args["id"] = string.Join(" ", args.Skip(1)); break;
                default:
                    this.Monitor.Log("qc <list|equip <id>|next|prev|clear|dir <front|right|back|left>|"
                        + "scene key value ...|state|capture [label]|capture_all [label]>", LogLevel.Info);
                    return;
            }
            try
            {
                this.Dispatch(req);
                this.Monitor.Log($"queued {req.Command}; response in {this.bridge.Responses}", LogLevel.Info);
            }
            catch (Exception ex)
            {
                this.Monitor.Log(ex.ToString(), LogLevel.Error);
            }
        }
    }
}
