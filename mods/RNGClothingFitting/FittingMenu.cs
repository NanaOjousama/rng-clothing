using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Menus;
using FashionSense.Framework.Models.Appearances.Hat;

namespace RNGClothingFitting
{
    /// <summary>The fitting screen, opened from a sewing machine.
    ///
    /// A real <see cref="IClickableMenu"/> drawn with the game's own dialogue
    /// box and fonts. That is the whole visual brief: this should read as part
    /// of Stardew, not as a tool bolted onto it, so there is no custom chrome,
    /// no flat panels and no editor styling.
    ///
    /// CONTROLLER FIRST. Every action is a real focusable component with
    /// neighbour links, so the game's own snappy-menu navigation drives the
    /// whole screen with the d-pad and A. The left stick additionally nudges
    /// the active target directly, and the shoulder buttons switch target — but
    /// nothing is reachable ONLY that way, and nothing is reachable only by
    /// mouse either.
    ///
    /// All geometry comes from <see cref="FittingGeometry"/>, so drawing and
    /// hit-testing read the same rectangles and cannot disagree.
    /// </summary>
    internal sealed class FittingMenu : IClickableMenu
    {
        // Component ids for snapped navigation.
        private const int IdHatTab = 100;
        private const int IdMotifTab = 101;
        private const int IdUp = 110;
        private const int IdLeft = 111;
        private const int IdRight = 112;
        private const int IdDown = 113;
        private const int IdRead1 = 120;
        private const int IdRead2 = 121;
        private const int IdRead4 = 122;
        private const int IdTurn = 130;
        private const int IdUndo = 131;
        private const int IdRedo = 132;
        private const int IdReset = 133;
        private const int IdCancel = 134;
        private const int IdSave = 135;

        private static readonly int[] ReadabilityScales = { 1, 2, 4 };

        private readonly IModHelper helper;
        private readonly FashionSenseBridge fs;
        private readonly FitStore store;
        private readonly FittingSession session;
        private readonly CapSidecar cap;
        private readonly HatContentPack pack;
        private readonly FittingGeometry geo;
        private readonly FitHistory history = new();

        private readonly Fit fit;              // the working copy the player edits
        private readonly Fit original;         // what was saved when we opened
        private readonly int motifPositions;
        private readonly string capName;
        private readonly int enteredFacing;
        private readonly TailoringMenu tailoring;
        private bool committed;
        private bool cleanedUp;

        private int previewFacing = 2;
        private bool clampedScale;
        private string toast = "";
        private int toastTimer;

        private ClickableTextureComponent nudgeUp, nudgeDown, nudgeLeft, nudgeRight;
        private ClickableTextureComponent saveButton, cancelButton;
        private ClickableComponent hatTab, motifTab, turnButton, resetButton, undoButton, redoButton;
        private readonly List<ClickableComponent> readButtons = new();

        public FittingMenu(IModHelper helper, FashionSenseBridge fs, FitStore store,
                           FittingSession session, CapSidecar cap, HatContentPack pack,
                           TailoringMenu tailoring)
            : base(Game1.uiViewport.Width / 2 - FittingGeometry.Width / 2,
                   Game1.uiViewport.Height / 2 - FittingGeometry.Height / 2,
                   FittingGeometry.Width, FittingGeometry.Height)
        {
            this.helper = helper;
            this.fs = fs;
            this.store = store;
            this.session = session ?? new FittingSession();
            this.cap = cap;
            this.pack = pack;
            this.tailoring = tailoring;
            this.geo = new FittingGeometry(this.xPositionOnScreen, this.yPositionOnScreen,
                                           cap.FrameSize);

            this.fit = store.Get(cap.ItemId);
            this.original = this.fit.Clone();
            this.motifPositions = FitRules.LegalPositionCount(cap);
            this.capName = this.T("fit.cap.name");
            this.enteredFacing = Game1.player.FacingDirection;

            // Restore the session's view state, but never the garment: a
            // reopened cap is exactly as it was saved.
            if (this.session.Target == FitTarget.Motif && !cap.HasMotif)
                this.session.Target = FitTarget.Hat;
            this.geo.SetCellWindow(FittingGeometry.WindowAroundMask(cap));
            this.ApplyReadability();

            this.BuildComponents();
            this.ApplyPreview(motifChanged: true);

            this.snapToDefaultClickableComponent();
        }

        private string T(string key) => this.helper.Translation.Get(key);
        private string T(string key, object tokens) => this.helper.Translation.Get(key, tokens);

        private int ReadabilityScale => ReadabilityScales[
            Math.Clamp(this.session.ReadabilityIndex, 0, ReadabilityScales.Length - 1)];

        /// <summary>Set the grid's cell size from the readability scale,
        /// clamped so it cannot overflow its panel.
        ///
        /// The clamp is why 2x and 4x no longer draw over the action buttons.
        /// `actualScale` records what was really applied, so the label can say
        /// so instead of claiming a zoom the panel could not hold.</summary>
        private void ApplyReadability()
        {
            Rectangle room = this.geo.ReadabilityPreview;
            int want = this.ReadabilityScale * 4;
            int max = this.geo.MaxCellSize(room.Width, room.Height);
            this.geo.SetCellSize(Math.Min(want, max));
            this.clampedScale = this.geo.CellSize < want;
        }

        private static string CapDisplayName(CapSidecar cap)
        {
            string n = cap.AppearanceId ?? "";
            int slash = n.LastIndexOf('/');
            if (slash >= 0)
                n = n.Substring(slash + 1);
            int hash = n.IndexOf('#');
            if (hash > 0)
                n = n.Substring(0, hash);
            return n.Trim();
        }

        // --- components -----------------------------------------------------

        private void BuildComponents()
        {
            Rectangle up = new(421, 459, 11, 12), down = new(421, 472, 11, 12);
            Rectangle left = new(352, 495, 12, 11), right = new(365, 495, 12, 11);

            this.hatTab = new ClickableComponent(this.geo.HatTab, this.T("fit.target.hat")) { myID = IdHatTab };
            this.motifTab = new ClickableComponent(this.geo.MotifTab, this.T("fit.target.motif")) { myID = IdMotifTab };

            this.nudgeUp = new ClickableTextureComponent(this.geo.NudgeUp, Game1.mouseCursors, up, 4f) { myID = IdUp };
            this.nudgeDown = new ClickableTextureComponent(this.geo.NudgeDown, Game1.mouseCursors, down, 4f) { myID = IdDown };
            this.nudgeLeft = new ClickableTextureComponent(this.geo.NudgeLeft, Game1.mouseCursors, left, 4f) { myID = IdLeft };
            this.nudgeRight = new ClickableTextureComponent(this.geo.NudgeRight, Game1.mouseCursors, right, 4f) { myID = IdRight };

            this.readButtons.Clear();
            for (int i = 0; i < ReadabilityScales.Length; i++)
                this.readButtons.Add(new ClickableComponent(
                    this.geo.ReadabilityButton(i), this.T("fit.zoom", new { scale = ReadabilityScales[i] }))
                    { myID = IdRead1 + i });

            this.turnButton = new ClickableComponent(this.geo.TurnButton, this.T("fit.hint.rotate")) { myID = IdTurn };
            this.undoButton = new ClickableComponent(this.geo.UndoButton, this.T("fit.undo")) { myID = IdUndo };
            this.redoButton = new ClickableComponent(this.geo.RedoButton, this.T("fit.redo")) { myID = IdRedo };
            this.resetButton = new ClickableComponent(this.geo.ResetButton, this.T("fit.reset")) { myID = IdReset };

            this.cancelButton = new ClickableTextureComponent(this.geo.CancelButton, Game1.mouseCursors,
                Game1.getSourceRectForStandardTileSheet(Game1.mouseCursors, 47), 1f)
                { myID = IdCancel, name = this.T("fit.cancel") };
            this.saveButton = new ClickableTextureComponent(this.geo.SaveButton, Game1.mouseCursors,
                Game1.getSourceRectForStandardTileSheet(Game1.mouseCursors, 46), 1f)
                { myID = IdSave, name = this.T("fit.save") };

            // Neighbour links, so the d-pad walks the screen in the order the
            // eye reads it. Without these, snappy menus jump unpredictably.
            Link(this.hatTab, right: IdMotifTab, down: IdUp);
            Link(this.motifTab, left: IdHatTab, down: IdRead1);
            Link(this.nudgeUp, up: IdHatTab, down: IdDown, left: IdLeft, right: IdRight);
            Link(this.nudgeLeft, up: IdHatTab, right: IdUp, down: IdUndo);
            Link(this.nudgeRight, up: IdMotifTab, left: IdUp, down: IdReset);
            Link(this.nudgeDown, up: IdUp, down: IdUndo, left: IdLeft, right: IdRight);
            Link(this.readButtons[0], up: IdMotifTab, right: IdRead2, down: IdReset);
            Link(this.readButtons[1], left: IdRead1, right: IdRead4, up: IdMotifTab, down: IdReset);
            Link(this.readButtons[2], left: IdRead2, up: IdMotifTab, down: IdSave);
            Link(this.turnButton, right: IdUndo, up: IdLeft);
            Link(this.undoButton, left: IdTurn, right: IdRedo, up: IdDown);
            Link(this.redoButton, left: IdUndo, right: IdReset, up: IdDown);
            Link(this.resetButton, left: IdRedo, right: IdCancel, up: IdRight);
            Link(this.cancelButton, left: IdReset, right: IdSave, up: IdRead4);
            Link(this.saveButton, left: IdCancel, up: IdRead4);

            this.allClickableComponents = new List<ClickableComponent>
            {
                this.hatTab, this.motifTab,
                this.nudgeUp, this.nudgeDown, this.nudgeLeft, this.nudgeRight,
                this.readButtons[0], this.readButtons[1], this.readButtons[2],
                this.turnButton, this.undoButton, this.redoButton, this.resetButton,
                this.cancelButton, this.saveButton
            };
        }

        private static void Link(ClickableComponent c, int up = -1, int down = -1,
                                 int left = -1, int right = -1)
        {
            c.upNeighborID = up;
            c.downNeighborID = down;
            c.leftNeighborID = left;
            c.rightNeighborID = right;
        }

        public override void snapToDefaultClickableComponent()
        {
            int want = this.session.SnappedComponentId;
            bool known = want >= 0 && this.allClickableComponents != null
                         && this.allClickableComponents.Exists(c => c.myID == want);
            this.setCurrentlySnappedComponentTo(known ? want : IdUp);
            this.snapCursorToCurrentSnappedComponent();
        }

        // --- preview --------------------------------------------------------

        /// <summary>Push the working fit onto the live Fashion Sense models.
        ///
        /// The hat's HeadPosition is a property Fashion Sense reads while
        /// drawing, so assigning it shows up next frame at no cost. The design
        /// offset needs new pixels, so it is only MARKED dirty here and rebuilt
        /// once per frame in <see cref="update"/>.
        /// </summary>
        private void ApplyPreview(bool motifChanged)
        {
            this.fs.ApplyHat(this.pack, this.cap, this.fit);
            if (motifChanged && this.cap.HasMotif)
                this.fs.MarkMotifDirty(this.cap, this.fit);
        }

        private FitSnapshot Snapshot() => FitSnapshot.From(this.fit);

        private void Toast(string message, bool bad = true)
        {
            this.toast = message;
            this.toastTimer = 2200;
            Game1.playSound(bad ? "cancel" : "crystal");
        }

        // --- editing --------------------------------------------------------

        private void Nudge(int dx, int dy)
        {
            FitSnapshot before = this.Snapshot();
            MoveResult r = this.session.Target == FitTarget.Hat
                ? FitRules.TryMoveHat(this.fit, this.cap, dx, dy)
                : FitRules.TryMoveMotif(this.fit, this.cap, dx, dy);

            switch (r)
            {
                case MoveResult.Ok:
                    this.history.Capture(before);
                    Game1.playSound("stoneStep");
                    this.ApplyPreview(this.session.Target == FitTarget.Motif);
                    break;
                case MoveResult.OutOfRange:
                    this.Toast(this.T("fit.blocked.range"));
                    break;
                case MoveResult.OutsideMask:
                    // Blocked WHOLE rather than clipped: half a mark is a
                    // different mark. A blocked move costs no undo step.
                    this.Toast(this.T("fit.blocked.mask"));
                    break;
                case MoveResult.NoMotif:
                    this.Toast(this.T("fit.blocked.nomotif"));
                    break;
            }
        }

        private void SetTarget(FitTarget t)
        {
            if (t == FitTarget.Motif && !this.cap.HasMotif)
            {
                this.Toast(this.T("fit.blocked.nomotif"));
                return;
            }
            if (this.session.Target == t)
                return;
            this.session.Target = t;
            Game1.playSound("shwip");
        }

        private void SwitchTarget() =>
            this.SetTarget(this.session.Target == FitTarget.Hat ? FitTarget.Motif : FitTarget.Hat);

        private void SetReadability(int index)
        {
            this.session.ReadabilityIndex = Math.Clamp(index, 0, ReadabilityScales.Length - 1);
            this.ApplyReadability();
            Game1.playSound("smallSelect");
        }

        private void Rotate()
        {
            this.previewFacing = (this.previewFacing + 1) % 4;
            Game1.playSound("shwip");
        }

        private void DoUndo()
        {
            FitSnapshot prev = this.history.Undo(this.Snapshot());
            if (prev == null)
            {
                this.Toast(this.T("fit.nothing.undo"));
                return;
            }
            prev.ApplyTo(this.fit);
            this.fs.InvalidateMotif(this.cap);
            this.ApplyPreview(true);
            Game1.playSound("dwop");
        }

        private void DoRedo()
        {
            FitSnapshot next = this.history.Redo(this.Snapshot());
            if (next == null)
            {
                this.Toast(this.T("fit.nothing.redo"));
                return;
            }
            next.ApplyTo(this.fit);
            this.fs.InvalidateMotif(this.cap);
            this.ApplyPreview(true);
            Game1.playSound("dwop");
        }

        private void ResetFit()
        {
            this.history.Capture(this.Snapshot());
            this.fit.ResetAll();
            this.fs.InvalidateMotif(this.cap);
            this.fs.ApplyHat(this.pack, this.cap, this.fit);
            if (this.cap.HasMotif)
                this.fs.ResetMotif(this.cap);
            this.Toast(this.T("fit.reset.done"), bad: false);
        }

        private void SaveAndClose()
        {
            this.ApplyPreview(true);
            this.fs.FlushMotif();
            this.store.Save(this.fit);
            this.committed = true;
            Game1.playSound("coin");
            this.CloseMenu();
        }

        private void CancelAndClose()
        {
            this.CloseMenu();
        }

        protected override void cleanupBeforeExit()
        {
            if (this.cleanedUp)
                return;
            this.cleanedUp = true;
            this.session.SnappedComponentId = this.currentlySnappedComponent?.myID ?? -1;
            Game1.player.faceDirection(this.enteredFacing);
            if (this.committed)
                return;
            // Put the live models back to what was saved before we opened, so
            // an abandoned fitting leaves nothing behind.
            this.fs.ApplyHat(this.pack, this.cap, this.original);
            this.fs.InvalidateMotif(this.cap);
            if (this.cap.HasMotif)
            {
                if (this.original.IsDefault)
                    this.fs.ResetMotif(this.cap);
                else
                {
                    this.fs.MarkMotifDirty(this.cap, this.original);
                    this.fs.FlushMotif();
                }
            }
        }

        private void CloseMenu()
        {
            this.exitThisMenu();
            Game1.activeClickableMenu = this.tailoring;
        }

        public override void emergencyShutDown()
        {
            this.cleanupBeforeExit();
            this.tailoring.emergencyShutDown();
            base.emergencyShutDown();
        }

        // --- input ----------------------------------------------------------

        public override void receiveLeftClick(int x, int y, bool playSound = true)
        {
            if (this.saveButton.containsPoint(x, y)) { this.SaveAndClose(); return; }
            if (this.cancelButton.containsPoint(x, y)) { this.CancelAndClose(); return; }
            if (this.resetButton.containsPoint(x, y)) { this.ResetFit(); return; }
            if (this.undoButton.containsPoint(x, y)) { this.DoUndo(); return; }
            if (this.redoButton.containsPoint(x, y)) { this.DoRedo(); return; }
            if (this.turnButton.containsPoint(x, y)) { this.Rotate(); return; }
            if (this.hatTab.containsPoint(x, y)) { this.SetTarget(FitTarget.Hat); return; }
            if (this.motifTab.containsPoint(x, y)) { this.SetTarget(FitTarget.Motif); return; }
            if (this.nudgeUp.containsPoint(x, y)) { this.Nudge(0, -1); return; }
            if (this.nudgeDown.containsPoint(x, y)) { this.Nudge(0, 1); return; }
            if (this.nudgeLeft.containsPoint(x, y)) { this.Nudge(-1, 0); return; }
            if (this.nudgeRight.containsPoint(x, y)) { this.Nudge(1, 0); return; }
            for (int i = 0; i < this.readButtons.Count; i++)
                if (this.readButtons[i].containsPoint(x, y)) { this.SetReadability(i); return; }

            // The grid is read-only today. The mapping is exercised anyway, so
            // the future editor inherits a proven conversion rather than a
            // freshly written one.
            Point? cell = this.geo.ScreenToCell(x, y);
            if (cell.HasValue)
                this.session.Cursor = cell;
        }

        public override void receiveKeyPress(Keys key)
        {
            if (Game1.options.gamepadControls && !Game1.GetKeyboardState().IsKeyDown(key))
                return;
            switch (key)
            {
                case Keys.Left: case Keys.A: this.Nudge(-1, 0); return;
                case Keys.Right: case Keys.D: this.Nudge(1, 0); return;
                case Keys.Up: case Keys.W: this.Nudge(0, -1); return;
                case Keys.Down: case Keys.S: this.Nudge(0, 1); return;
                case Keys.Tab: this.SwitchTarget(); return;
                case Keys.R: this.ResetFit(); return;
                case Keys.Z: this.DoUndo(); return;
                case Keys.Y: this.DoRedo(); return;
                case Keys.D1: this.SetReadability(0); return;
                case Keys.D2: this.SetReadability(1); return;
                case Keys.D4: this.SetReadability(2); return;
                case Keys.Enter: this.SaveAndClose(); return;
            }
            if (Game1.options.doesInputListContain(Game1.options.menuButton, key))
            {
                this.CancelAndClose();
                return;
            }
            base.receiveKeyPress(key);
        }

        public override void receiveGamePadButton(Buttons b)
        {
            switch (b)
            {
                case Buttons.DPadUp: this.applyMovementKey(0); return;
                case Buttons.DPadRight: this.applyMovementKey(1); return;
                case Buttons.DPadDown: this.applyMovementKey(2); return;
                case Buttons.DPadLeft: this.applyMovementKey(3); return;
                case Buttons.A:
                    if (this.currentlySnappedComponent == null)
                        this.snapToDefaultClickableComponent();
                    Point center = this.currentlySnappedComponent.bounds.Center;
                    this.receiveLeftClick(center.X, center.Y);
                    return;
                // The left stick nudges directly, for speed. The d-pad is left
                // to the game's snappy-menu navigation so every control stays
                // reachable, which is what keeps this controller-complete.
                case Buttons.LeftThumbstickLeft: this.Nudge(-1, 0); return;
                case Buttons.LeftThumbstickRight: this.Nudge(1, 0); return;
                case Buttons.LeftThumbstickUp: this.Nudge(0, -1); return;
                case Buttons.LeftThumbstickDown: this.Nudge(0, 1); return;
                case Buttons.LeftShoulder: case Buttons.RightShoulder: this.SwitchTarget(); return;
                case Buttons.LeftTrigger: this.DoUndo(); return;
                case Buttons.RightTrigger: this.DoRedo(); return;
                case Buttons.X: this.ResetFit(); return;
                case Buttons.Y: this.Rotate(); return;
                case Buttons.B: case Buttons.Back: this.CancelAndClose(); return;
            }
            base.receiveGamePadButton(b);
        }

        public override bool areGamePadControlsImplemented() => true;

        public override void populateClickableComponentList()
        {
            this.BuildComponents();
        }

        public override void update(GameTime time)
        {
            base.update(time);
            if (this.toastTimer > 0)
            {
                this.toastTimer -= time.ElapsedGameTime.Milliseconds;
                if (this.toastTimer <= 0)
                    this.toast = "";
            }
            // One deferred texture rebuild per frame at most, and none at all
            // when the design has not moved.
            this.fs.FlushMotif();

            if (Game1.player.FacingDirection != this.previewFacing)
                Game1.player.faceDirection(this.previewFacing);
        }

        // --- drawing --------------------------------------------------------

        public override void draw(SpriteBatch b)
        {
            b.Draw(Game1.fadeToBlackRect,
                   new Rectangle(0, 0, Game1.uiViewport.Width, Game1.uiViewport.Height),
                   Color.Black * 0.5f);
            IClickableMenu.drawTextureBox(b, this.geo.X, this.geo.Y, FittingGeometry.Width,
                                          FittingGeometry.Height, Color.White);

            SpriteFont font = Game1.smallFont;

            Utility.drawTextWithShadow(b, this.T("fit.title"), Game1.dialogueFont,
                new Vector2(this.geo.Title.X, this.geo.Title.Y), Game1.textColor);
            if (!string.IsNullOrEmpty(this.capName))
                Utility.drawTextWithShadow(b, this.capName, font,
                    new Vector2(this.geo.Subtitle.X, this.geo.Subtitle.Y), Game1.textColor * 0.7f);

            this.DrawFarmerPreview(b, this.geo.FarmerPreview);

            this.DrawTab(b, this.hatTab, this.session.Target == FitTarget.Hat, true);
            this.DrawTab(b, this.motifTab, this.session.Target == FitTarget.Motif, this.cap.HasMotif);

            int right = this.session.Target == FitTarget.Hat ? this.fit.HatRight : this.fit.MotifRight;
            int down = this.session.Target == FitTarget.Hat ? this.fit.HatDown : this.fit.MotifDown;
            string offset = (right == 0 && down == 0)
                ? this.T("fit.offset.none")
                : this.T("fit.offset", new { right, down });
            Utility.drawTextWithShadow(b, offset, Game1.dialogueFont,
                new Vector2(this.geo.OffsetReadout.X, this.geo.OffsetReadout.Y), Game1.textColor);

            this.DrawWrapped(b, this.NoteText(), font, this.geo.Note, Game1.textColor * 0.75f);

            this.nudgeUp.draw(b);
            this.nudgeDown.draw(b);
            this.nudgeLeft.draw(b);
            this.nudgeRight.draw(b);

            for (int i = 0; i < this.readButtons.Count; i++)
                this.DrawLabelButton(b, this.readButtons[i],
                                     enabled: !(this.clampedScale
                                                && i == this.session.ReadabilityIndex),
                                     active: i == this.session.ReadabilityIndex);
            this.DrawMotifGrid(b);

            this.DrawLabelButton(b, this.turnButton);
            this.DrawLabelButton(b, this.undoButton, enabled: this.history.CanUndo);
            this.DrawLabelButton(b, this.redoButton, enabled: this.history.CanRedo);
            this.DrawLabelButton(b, this.resetButton);
            this.DrawLabelButton(b, this.cancelButton);
            this.DrawLabelButton(b, this.saveButton);

            if (!string.IsNullOrEmpty(this.toast))
            {
                Vector2 size = font.MeasureString(this.toast);
                Utility.drawTextWithShadow(b, this.toast, font,
                    new Vector2(this.geo.Toast.X + FittingGeometry.Width / 2 - size.X / 2,
                                this.geo.Toast.Y),
                    Color.DarkRed);
            }

            this.drawMouse(b);
        }

        private string NoteText()
        {
            if (this.session.Target == FitTarget.Motif)
            {
                if (!this.cap.HasMotif)
                    return this.T("fit.note.nomotif");
                if (this.motifPositions <= 1)
                    return this.T("fit.note.motiffixed");
                return this.T("fit.note.motifroom", new { count = this.motifPositions });
            }
            return this.T("fit.note.hatrange", new { range = this.cap.HatRange });
        }

        /// <summary>The front frame at the chosen readability scale, with the
        /// safe mask marked.
        ///
        /// Cells outside the mask are drawn but dimmed rather than hidden: the
        /// player should see the crown the design sits on, and why it cannot
        /// leave. That is also exactly the surface the future masked editor
        /// needs, so it is built through the same conversions now.
        /// </summary>
        private void DrawMotifGrid(SpriteBatch b)
        {
            Rectangle grid = this.geo.MotifGrid;
            Color[] front = this.fs.ComposeFrontFrame(this.cap, this.fit);
            if (front == null)
                return;

            int cell = this.geo.CellSize;
            int n = this.cap.FrameSize;
            IClickableMenu.drawTextureBox(b, grid.X - 12, grid.Y - 12,
                                          grid.Width + 24, grid.Height + 24, Color.White);
            Rectangle win = this.geo.CellWindow;

            // The sprite, cell by cell as flat filled squares. One source
            // pixel becomes one solid square, so the grid is nearest-neighbour
            // by construction at any zoom -- no filtering can creep in.
            for (int cy = win.Y; cy < win.Bottom; cy++)
            for (int cx = win.X; cx < win.Right; cx++)
            {
                if (cx < 0 || cy < 0 || cx >= n || cy >= n)
                    continue;
                Color c = front[cy * n + cx];
                if (c.A == 0)
                    continue;
                b.Draw(Game1.staminaRect, this.geo.CellToScreen(new Point(cx, cy)), c);
            }

            // Mask outline, drawn from the authored mask.
            foreach (var c in this.cap.SafeCells)
            {
                if (!this.geo.CellVisible(c))
                    continue;
                DrawOutline(b, this.geo.CellToScreen(c), Color.White * 0.55f,
                            Math.Max(1, cell / 8));
            }

            // Where the design currently sits.
            foreach (var c in FitRules.PlacedMotif(this.fit, this.cap))
                if (this.geo.CellVisible(c))
                    DrawOutline(b, this.geo.CellToScreen(c), Color.Gold * 0.9f,
                                Math.Max(1, cell / 6));
        }

        private static void DrawOutline(SpriteBatch b, Rectangle r, Color c, int t)
        {
            b.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, r.Width, t), c);
            b.Draw(Game1.staminaRect, new Rectangle(r.X, r.Bottom - t, r.Width, t), c);
            b.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, t, r.Height), c);
            b.Draw(Game1.staminaRect, new Rectangle(r.Right - t, r.Y, t, r.Height), c);
        }

        private void DrawWrapped(SpriteBatch b, string text, SpriteFont font,
                                 Rectangle area, Color color)
        {
            if (string.IsNullOrEmpty(text))
                return;
            var line = new System.Text.StringBuilder();
            int dy = 0;
            foreach (string word in text.Split(' '))
            {
                string trial = line.Length == 0 ? word : line + " " + word;
                if (font.MeasureString(trial).X > area.Width && line.Length > 0)
                {
                    Utility.drawTextWithShadow(b, line.ToString(), font,
                        new Vector2(area.X, area.Y + dy), color);
                    line.Clear().Append(word);
                    dy += 30;
                }
                else
                    line.Clear().Append(trial);
            }
            if (line.Length > 0)
                Utility.drawTextWithShadow(b, line.ToString(), font,
                    new Vector2(area.X, area.Y + dy), color);
        }

        /// <summary>The live farmer, wearing the cap as it is being adjusted.
        ///
        /// Gameplay scale is the authority, so this stays on screen at all
        /// times rather than living behind the readability toggle.
        ///
        /// The overload WITHOUT a scale argument is used deliberately: on the
        /// scale-taking overload that argument multiplies the farmer's normal
        /// 4x, so passing 4f drew the farmer at 16x -- it burst out of its box,
        /// and the head came out garbled because Fashion Sense places the hat
        /// using its own scale, which no longer matched the body.
        /// </summary>
        private void DrawFarmerPreview(SpriteBatch b, Rectangle box)
        {
            IClickableMenu.drawTextureBox(b, box.X, box.Y, box.Width, box.Height, Color.White);
            Farmer who = Game1.player;
            var pos = new Vector2(box.X + box.Width / 2 - 32, box.Y + box.Height / 2 - 96);
            try
            {
                who.FarmerRenderer.draw(b, who.FarmerSprite, who.FarmerSprite.SourceRect,
                                        pos, Vector2.Zero, 0.8f, Color.White, 0f, who);
            }
            catch
            {
                // A preview that cannot draw must not take the menu down with
                // it; the fitting itself is unaffected.
            }
        }

        private void DrawTab(SpriteBatch b, ClickableComponent c, bool active, bool enabled)
        {
            IClickableMenu.drawTextureBox(b, Game1.mouseCursors, new Rectangle(384, 396, 15, 15),
                c.bounds.X, c.bounds.Y, c.bounds.Width, c.bounds.Height,
                active ? Color.White : Color.White * 0.6f, 4f, false);
            Vector2 size = Game1.smallFont.MeasureString(c.name);
            Utility.drawTextWithShadow(b, c.name, Game1.smallFont,
                new Vector2(c.bounds.Center.X - size.X / 2, c.bounds.Center.Y - size.Y / 2),
                enabled ? Game1.textColor : Game1.textColor * 0.4f);
        }

        private void DrawLabelButton(SpriteBatch b, ClickableComponent c,
                                     bool enabled = true, bool active = false)
        {
            IClickableMenu.drawTextureBox(b, Game1.mouseCursors, new Rectangle(432, 439, 9, 9),
                c.bounds.X, c.bounds.Y, c.bounds.Width, c.bounds.Height,
                active ? Color.White : Color.White * 0.85f, 4f, false);
            Vector2 size = Game1.smallFont.MeasureString(c.name);
            Utility.drawTextWithShadow(b, c.name, Game1.smallFont,
                new Vector2(c.bounds.Center.X - size.X / 2, c.bounds.Center.Y - size.Y / 2),
                enabled ? Game1.textColor : Game1.textColor * 0.4f);
        }
    }
}
