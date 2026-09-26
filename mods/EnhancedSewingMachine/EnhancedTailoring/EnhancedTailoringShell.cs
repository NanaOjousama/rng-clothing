using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;
using StardewValley.Objects;
using EnhancedSewingMachine.GarmentRuntime;
using EnhancedSewingMachine.TailoringSelection;

namespace EnhancedSewingMachine.EnhancedTailoring
{
    /// <summary>
    /// Adds an opt-in Enhanced mode to the vanilla TailoringMenu without
    /// replacing the menu or changing normal vanilla tailoring behavior.
    /// </summary>
    internal sealed class EnhancedTailoringShell
    {
        private const int ModeButtonId = 1200;
        private const int FragmentSlotId = 1201;
        private const int FitUpId = 1210;
        private const int FitDownId = 1211;
        private const int FitLeftId = 1212;
        private const int FitRightId = 1213;
        private const int FitResetPosId = 1214;
        private const int FitScaleDownId = 1215;
        private const int FitScaleUpId = 1216;
        private const int FitResetScaleId = 1217;
        private const int FitResetAllId = 1218;
        private const int FitViewPrevId = 1219;
        private const int FitViewNextId = 1220;
        private const int QcToggleId = 1221;
        private const int QcPrevId = 1222;
        private const int QcNextId = 1223;
        private const int FitRange = 8;
        private const float FitScaleMin = 0.85f;
        private const float FitScaleMax = 1.25f;
        private const float FitScaleStep = 0.05f;
        public const int FragmentCost = 5;

        private readonly IModHelper helper;
        private readonly IMonitor monitor;
        private readonly GarmentRuntimeHost runtime;
        private readonly TailoringSelectionService tailoring;

        private State state;

        private sealed class State
        {
            public TailoringMenu Menu;
            public ClickableComponent ModeButton;
            public ClickableTextureComponent FragmentSpot;
            public ClickableComponent FitUp, FitDown, FitLeft, FitRight;
            public ClickableComponent FitScaleDown, FitScaleUp;
            public ClickableComponent FitResetPos, FitResetScale, FitResetAll;
            public ClickableComponent FitViewPrev, FitViewNext;
            public ClickableComponent QcToggle, QcPrev, QcNext;
            public List<string> QcGarmentIds = new();
            public int QcIndex;
            public bool QcMode;
            public Hat QcHat;
            public int FitFacingDirection = 2;
            public bool Enhanced;
            public string StatusKey;
        }

        public EnhancedTailoringShell(
            IModHelper helper,
            IMonitor monitor,
            GarmentRuntimeHost runtime,
            TailoringSelectionService tailoring)
        {
            this.helper = helper;
            this.monitor = monitor;
            this.runtime = runtime;
            this.tailoring = tailoring;
        }

        public string DescribeState()
        {
            State s = this.state;
            if (s == null || Game1.activeClickableMenu != s.Menu)
                return "Enhanced tailoring shell: no active TailoringMenu.";

            static string ItemText(Item item)
                => item == null
                    ? "empty"
                    : $"{item.QualifiedItemId} x{item.Stack}";

            string held = ItemText(s.Menu.heldItem);
            if (s.Menu.heldItem is Hat heldHat
                && this.runtime.TryReadInstance(heldHat, out GarmentInstanceData instance))
            {
                held += $" [garment={instance.GarmentId} itemSeed={instance.Seed} generatorSeed={instance.GeneratorSeed}]";
            }

            return
                $"Enhanced tailoring shell: enhanced={s.Enhanced}; " +
                $"textile={ItemText(s.Menu.leftIngredientSpot.item)}; " +
                $"inspiration={ItemText(s.Menu.rightIngredientSpot.item)}; " +
                $"fragments={ItemText(s.FragmentSpot.item)}; " +
                $"held={held}; status={s.StatusKey}; " +
                $"mouseUI=({Game1.getMouseX(ui_scale: true)},{Game1.getMouseY(ui_scale: true)}).";
        }

        public void OnMenuChanged(object sender, MenuChangedEventArgs e)
        {
            if (this.state != null && e.OldMenu == this.state.Menu)
            {
                if (this.state.QcMode && this.state.QcHat != null)
                    FarmerRendererPatch.SetWorldPreview(this.state.QcHat);

                this.ReturnFragmentStack();
                this.state = null;
            }

            if (e.NewMenu is TailoringMenu menu)
                this.Attach(menu);
        }

        public void OnButtonPressed(object sender, ButtonPressedEventArgs e)
        {
            State s = this.state;
            if (s == null || Game1.activeClickableMenu != s.Menu)
                return;

            bool isMouse = e.Button == SButton.MouseLeft;
            bool isControllerAction = e.Button == SButton.ControllerA;
            bool isKeyboardAction = e.Button == SButton.Enter || e.Button == SButton.Space;

            if (e.Button == SButton.Tab)
            {
                this.helper.Input.Suppress(e.Button);
                this.CycleKeyboardFocus();
                return;
            }

            if (!isMouse && !isControllerAction && !isKeyboardAction)
                return;

            // SMAPI's ButtonPressed event fires outside Stardew's temporary
            // PushUIMode scope, so the parameterless getters can use world
            // zoom instead of UI scale. Menu bounds are always UI-space.
            int x = Game1.getMouseX(ui_scale: true);
            int y = Game1.getMouseY(ui_scale: true);
            int snappedId = s.Menu.currentlySnappedComponent?.myID ?? -1;

            if (this.TryGetActiveFitHat(out Hat fitHat, out GarmentInstanceData fitInstance))
            {
                int fitId = -1;
                if (isMouse)
                {
                    if (s.FitUp.containsPoint(x, y)) fitId = FitUpId;
                    else if (s.FitDown.containsPoint(x, y)) fitId = FitDownId;
                    else if (s.FitLeft.containsPoint(x, y)) fitId = FitLeftId;
                    else if (s.FitRight.containsPoint(x, y)) fitId = FitRightId;
                    else if (s.FitScaleDown.containsPoint(x, y)) fitId = FitScaleDownId;
                    else if (s.FitScaleUp.containsPoint(x, y)) fitId = FitScaleUpId;
                    else if (s.FitResetPos.containsPoint(x, y)) fitId = FitResetPosId;
                    else if (s.FitResetScale.containsPoint(x, y)) fitId = FitResetScaleId;
                    else if (s.FitResetAll.containsPoint(x, y)) fitId = FitResetAllId;
                    else if (s.FitViewPrev.containsPoint(x, y)) fitId = FitViewPrevId;
                    else if (s.FitViewNext.containsPoint(x, y)) fitId = FitViewNextId;
                }
                else
                    fitId = snappedId;

                int dx = 0, dy = 0;
                bool changed = false;
                bool viewChanged = false;
                if (fitId == FitUpId) dy = -1;
                else if (fitId == FitDownId) dy = 1;
                else if (fitId == FitLeftId) dx = -1;
                else if (fitId == FitRightId) dx = 1;
                else if (fitId == FitScaleDownId)
                {
                    float currentScale = fitInstance.GetFitScale(s.FitFacingDirection);
                    fitInstance.SetFitScale(
                        s.FitFacingDirection,
                        Math.Clamp(
                            MathF.Round((currentScale - FitScaleStep) * 100f) / 100f,
                            FitScaleMin,
                            FitScaleMax));
                    changed = true;
                }
                else if (fitId == FitScaleUpId)
                {
                    float currentScale = fitInstance.GetFitScale(s.FitFacingDirection);
                    fitInstance.SetFitScale(
                        s.FitFacingDirection,
                        Math.Clamp(
                            MathF.Round((currentScale + FitScaleStep) * 100f) / 100f,
                            FitScaleMin,
                            FitScaleMax));
                    changed = true;
                }
                else if (fitId == FitResetPosId)
                {
                    fitInstance.SetFitOffset(s.FitFacingDirection, 0, 0);
                    changed = true;
                }
                else if (fitId == FitResetScaleId)
                {
                    fitInstance.SetFitScale(s.FitFacingDirection, 1f);
                    changed = true;
                }
                else if (fitId == FitResetAllId)
                {
                    fitInstance.ResetAllFitOffsets();
                    fitInstance.ResetAllFitScales();
                    changed = true;
                }
                else if (fitId == FitViewPrevId)
                {
                    s.FitFacingDirection = PreviousFitDirection(s.FitFacingDirection);
                    viewChanged = true;
                }
                else if (fitId == FitViewNextId)
                {
                    s.FitFacingDirection = NextFitDirection(s.FitFacingDirection);
                    viewChanged = true;
                }

                if (dx != 0 || dy != 0)
                {
                    int currentX = fitInstance.GetFitOffsetX(s.FitFacingDirection);
                    int currentY = fitInstance.GetFitOffsetY(s.FitFacingDirection);
                    fitInstance.SetFitOffset(
                        s.FitFacingDirection,
                        Math.Clamp(currentX + dx, -FitRange, FitRange),
                        Math.Clamp(currentY + dy, -FitRange, FitRange));
                    changed = true;
                }

                if (viewChanged)
                {
                    this.helper.Input.Suppress(e.Button);
                    Game1.playSound("shiny4");
                    return;
                }

                if (changed)
                {
                    this.runtime.WriteInstance(fitHat, fitInstance);
                    this.helper.Input.Suppress(e.Button);
                    Game1.playSound(dx != 0 || dy != 0 ? "stoneStep" : "smallSelect");
                    return;
                }
            }

            bool modePressed = isMouse
                ? s.ModeButton.containsPoint(x, y)
                : snappedId == ModeButtonId;

            if (modePressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.SetEnhanced(!s.Enhanced);
                Game1.playSound("smallSelect");
                return;
            }

            bool qcTogglePressed = isMouse
                ? s.QcToggle.containsPoint(x, y)
                : snappedId == QcToggleId;
            if (qcTogglePressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.SetQcMode(!s.QcMode);
                Game1.playSound("smallSelect");
                return;
            }

            if (s.QcMode)
            {
                bool qcPrevPressed = isMouse
                    ? s.QcPrev.containsPoint(x, y)
                    : snappedId == QcPrevId;
                bool qcNextPressed = isMouse
                    ? s.QcNext.containsPoint(x, y)
                    : snappedId == QcNextId;
                if (qcPrevPressed || qcNextPressed)
                {
                    this.helper.Input.Suppress(e.Button);
                    this.CycleQcCandidate(qcPrevPressed ? -1 : 1);
                    Game1.playSound("shiny4");
                    return;
                }
            }

            if (!s.Enhanced)
                return;

            bool leftPressed = isMouse
                ? s.Menu.leftIngredientSpot.containsPoint(x, y)
                : snappedId == TailoringMenu.region_leftIngredient;
            if (leftPressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.ClickEnhancedIngredientSlot(
                    s.Menu.leftIngredientSpot,
                    isTextile: true);
                return;
            }

            bool rightPressed = isMouse
                ? s.Menu.rightIngredientSpot.containsPoint(x, y)
                : snappedId == TailoringMenu.region_rightIngredient;
            if (rightPressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.ClickEnhancedIngredientSlot(
                    s.Menu.rightIngredientSpot,
                    isTextile: false);
                return;
            }

            bool fragmentPressed = isMouse
                ? s.FragmentSpot.containsPoint(x, y)
                : snappedId == FragmentSlotId;

            if (fragmentPressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.ClickFragmentSlot();
                return;
            }

            bool startPressed = isMouse
                ? s.Menu.startTailoringButton.containsPoint(x, y)
                : snappedId == TailoringMenu.region_startButton;

            if (startPressed)
            {
                this.helper.Input.Suppress(e.Button);
                this.TryCraftEnhanced();
            }
        }

        public void OnUpdateTicked(object sender, UpdateTickedEventArgs e)
        {
            State s = this.state;
            if (s == null || Game1.activeClickableMenu != s.Menu)
                return;

            this.EnsureClickablesPresent();

            if (!s.Enhanced)
                return;

            // Vanilla still owns all ordinary inventory/slot interactions.
            // We only replace its validation presentation while Enhanced mode
            // is active.
            s.Menu.inventory.highlightMethod = TailoringIngredientMapper.IsEnhancedIngredient;
            bool ready = this.TryReadInputs(out _, out _, out string statusKey);
            s.StatusKey = statusKey;
            s.Menu.descriptionText = this.GetStatusText(statusKey);
            s.Menu.startTailoringButton.sourceRect.Y = ready ? 104 : 80;

            // The final garment is intentionally hidden until the stitch
            // succeeds; don't leak vanilla's invalid-recipe result preview.
            s.Menu.craftResultDisplay.visible = false;
        }

        public void OnRenderedActiveMenu(object sender, RenderedActiveMenuEventArgs e)
        {
            State s = this.state;
            if (s == null || Game1.activeClickableMenu != s.Menu)
                return;

            SpriteBatch b = e.SpriteBatch;
            Rectangle button = s.ModeButton.bounds;
            b.Draw(Game1.fadeToBlackRect, button, Color.Black * 0.78f);

            string modeText = s.Enhanced
                ? this.helper.Translation.Get("tailoring.mode.on")
                : this.helper.Translation.Get("tailoring.mode.off");
            Vector2 modeSize = Game1.smallFont.MeasureString(modeText);
            Utility.drawTextWithShadow(
                b,
                modeText,
                Game1.smallFont,
                new Vector2(
                    button.Center.X - modeSize.X / 2f,
                    button.Center.Y - modeSize.Y / 2f),
                Game1.textColor);

            DrawFitButton(b, s.QcToggle);
            if (s.QcMode)
            {
                DrawFitButton(b, s.QcPrev);
                DrawFitButton(b, s.QcNext);
                Utility.drawTextWithShadow(
                    b,
                    this.CurrentQcLabel(),
                    Game1.smallFont,
                    new Vector2(s.QcToggle.bounds.X, s.QcToggle.bounds.Y - 24),
                    Game1.textColor);
            }

            if (this.TryGetActiveFitHat(out Hat fitHat, out GarmentInstanceData fitInstance))
            {
                float displayScale = fitInstance.GetFitScale(s.FitFacingDirection);
                int fitX = fitInstance.GetFitOffsetX(s.FitFacingDirection);
                int fitY = fitInstance.GetFitOffsetY(s.FitFacingDirection);
                string fitLabel = this.helper.Translation.Get(
                    "tailoring.fit.label",
                    new
                    {
                        view = FitDirectionName(s.FitFacingDirection),
                        x = fitX,
                        y = fitY,
                        scale = MathF.Round(displayScale * 100f)
                    });
                Utility.drawTextWithShadow(b, fitLabel, Game1.smallFont,
                    new Vector2(s.FitLeft.bounds.X, s.FitUp.bounds.Y - 28), Game1.textColor);
                DrawFitButton(b, s.FitUp);
                DrawFitButton(b, s.FitDown);
                DrawFitButton(b, s.FitLeft);
                DrawFitButton(b, s.FitRight);
                DrawFitButton(b, s.FitScaleDown);
                DrawFitButton(b, s.FitScaleUp);
                DrawFitButton(b, s.FitViewPrev);
                DrawFitButton(b, s.FitViewNext);
                DrawFitButton(b, s.FitResetPos);
                DrawFitButton(b, s.FitResetScale);
                DrawFitButton(b, s.FitResetAll);
                DrawFarmerFitPreview(b, s.Menu, s.FitFacingDirection);
            }

            if (!s.Enhanced)
                return;

            // Third ingredient slot exists only in Enhanced mode.
            s.FragmentSpot.draw(b, Color.White, 0.87f);
            s.FragmentSpot.drawItem(b, 16, 16);

            string fragmentLabel = this.helper.Translation.Get(
                "tailoring.fragment.slot",
                new { cost = FragmentCost });
            Vector2 labelSize = Game1.smallFont.MeasureString(fragmentLabel);
            Utility.drawTextWithShadow(
                b,
                fragmentLabel,
                Game1.smallFont,
                new Vector2(
                    s.FragmentSpot.bounds.Center.X - labelSize.X / 2f,
                    s.FragmentSpot.bounds.Top - labelSize.Y - 2),
                Game1.textColor);

            string leftLabel = this.helper.Translation.Get("tailoring.slot.textile");
            string rightLabel = this.helper.Translation.Get("tailoring.slot.inspiration");
            DrawCenteredAbove(b, leftLabel, s.Menu.leftIngredientSpot.bounds);
            DrawCenteredAbove(b, rightLabel, s.Menu.rightIngredientSpot.bounds);
        }

        private void CycleKeyboardFocus()
        {
            State s = this.state;
            if (s == null)
                return;

            int current = s.Menu.currentlySnappedComponent?.myID ?? -1;
            bool hasGeneratedHat = this.TryGetActiveFitHat(out _, out _);
            int next = current switch
            {
                ModeButtonId => QcToggleId,
                QcToggleId => s.QcMode
                    ? QcPrevId
                    : (hasGeneratedHat ? FitUpId : TailoringMenu.region_leftIngredient),
                QcPrevId => QcNextId,
                QcNextId => hasGeneratedHat ? FitUpId : TailoringMenu.region_leftIngredient,
                FitUpId => FitRightId,
                FitRightId => FitDownId,
                FitDownId => FitScaleDownId,
                FitScaleDownId => FitScaleUpId,
                FitScaleUpId => FitViewPrevId,
                FitViewPrevId => FitViewNextId,
                FitViewNextId => FitResetPosId,
                FitResetPosId => FitResetScaleId,
                FitResetScaleId => FitResetAllId,
                FitResetAllId => TailoringMenu.region_leftIngredient,
                FitLeftId => FitUpId,
                TailoringMenu.region_leftIngredient => TailoringMenu.region_rightIngredient,
                TailoringMenu.region_rightIngredient => s.Enhanced
                    ? FragmentSlotId
                    : TailoringMenu.region_startButton,
                FragmentSlotId => TailoringMenu.region_startButton,
                TailoringMenu.region_startButton => ModeButtonId,
                _ => ModeButtonId
            };

            s.Menu.setCurrentlySnappedComponentTo(next);
            Game1.playSound("shiny4");
        }

        private void Attach(TailoringMenu menu)
        {
            var mode = new ClickableComponent(
                new Rectangle(
                    menu.xPositionOnScreen + menu.width - 246,
                    menu.yPositionOnScreen + 18,
                    182,
                    44),
                "Enhanced Mode")
            {
                myID = ModeButtonId,
                leftNeighborID = TailoringMenu.region_startButton,
                rightNeighborID = -99998,
                upNeighborID = -99998,
                downNeighborID = TailoringMenu.region_resultItem
            };

            int fitX = menu.xPositionOnScreen + menu.width - 246;
            int fitY = menu.yPositionOnScreen + 72;
            var fitUp = new ClickableComponent(new Rectangle(fitX + 92, fitY, 44, 36), "↑")
            {
                myID = FitUpId,
                upNeighborID = ModeButtonId,
                downNeighborID = FitDownId,
                leftNeighborID = FitLeftId,
                rightNeighborID = FitRightId
            };
            var fitLeft = new ClickableComponent(new Rectangle(fitX + 44, fitY + 40, 44, 36), "←")
            {
                myID = FitLeftId,
                upNeighborID = FitUpId,
                downNeighborID = FitScaleDownId,
                leftNeighborID = TailoringMenu.region_startButton,
                rightNeighborID = FitUpId
            };
            var fitRight = new ClickableComponent(new Rectangle(fitX + 140, fitY + 40, 44, 36), "→")
            {
                myID = FitRightId,
                upNeighborID = FitUpId,
                downNeighborID = FitScaleUpId,
                leftNeighborID = FitUpId,
                rightNeighborID = -99998
            };
            var fitDown = new ClickableComponent(new Rectangle(fitX + 92, fitY + 80, 44, 36), "↓")
            {
                myID = FitDownId,
                upNeighborID = FitUpId,
                downNeighborID = FitScaleDownId,
                leftNeighborID = FitLeftId,
                rightNeighborID = FitRightId
            };
            var fitScaleDown = new ClickableComponent(
                new Rectangle(fitX + 4, fitY + 120, 108, 36),
                this.helper.Translation.Get("tailoring.fit.scale-down"))
            {
                myID = FitScaleDownId,
                upNeighborID = FitDownId,
                downNeighborID = FitViewPrevId,
                leftNeighborID = TailoringMenu.region_startButton,
                rightNeighborID = FitScaleUpId
            };
            var fitScaleUp = new ClickableComponent(
                new Rectangle(fitX + 116, fitY + 120, 108, 36),
                this.helper.Translation.Get("tailoring.fit.scale-up"))
            {
                myID = FitScaleUpId,
                upNeighborID = FitDownId,
                downNeighborID = FitViewNextId,
                leftNeighborID = FitScaleDownId,
                rightNeighborID = -99998
            };
            var fitViewPrev = new ClickableComponent(
                new Rectangle(fitX + 4, fitY + 160, 108, 36),
                this.helper.Translation.Get("tailoring.fit.view-prev"))
            {
                myID = FitViewPrevId,
                upNeighborID = FitScaleDownId,
                downNeighborID = FitResetPosId,
                leftNeighborID = TailoringMenu.region_startButton,
                rightNeighborID = FitViewNextId
            };
            var fitViewNext = new ClickableComponent(
                new Rectangle(fitX + 116, fitY + 160, 108, 36),
                this.helper.Translation.Get("tailoring.fit.view-next"))
            {
                myID = FitViewNextId,
                upNeighborID = FitScaleUpId,
                downNeighborID = FitResetScaleId,
                leftNeighborID = FitViewPrevId,
                rightNeighborID = -99998
            };
            var fitResetPos = new ClickableComponent(
                new Rectangle(fitX + 4, fitY + 200, 72, 36),
                this.helper.Translation.Get("tailoring.fit.reset-pos"))
            {
                myID = FitResetPosId,
                upNeighborID = FitViewPrevId,
                downNeighborID = TailoringMenu.region_resultItem,
                leftNeighborID = TailoringMenu.region_startButton,
                rightNeighborID = FitResetScaleId
            };
            var fitResetScale = new ClickableComponent(
                new Rectangle(fitX + 80, fitY + 200, 72, 36),
                this.helper.Translation.Get("tailoring.fit.reset-scale"))
            {
                myID = FitResetScaleId,
                upNeighborID = FitViewNextId,
                downNeighborID = TailoringMenu.region_resultItem,
                leftNeighborID = FitResetPosId,
                rightNeighborID = FitResetAllId
            };
            var fitResetAll = new ClickableComponent(
                new Rectangle(fitX + 156, fitY + 200, 68, 36),
                this.helper.Translation.Get("tailoring.fit.reset-all"))
            {
                myID = FitResetAllId,
                upNeighborID = FitViewNextId,
                downNeighborID = TailoringMenu.region_resultItem,
                leftNeighborID = FitResetScaleId,
                rightNeighborID = -99998
            };

            var qcToggle = new ClickableComponent(
                new Rectangle(menu.xPositionOnScreen + 40, menu.yPositionOnScreen + 300, 180, 36),
                this.helper.Translation.Get("tailoring.qc.toggle"))
            {
                myID = QcToggleId,
                upNeighborID = -99998,
                downNeighborID = QcPrevId,
                leftNeighborID = -99998,
                rightNeighborID = -99998
            };
            var qcPrev = new ClickableComponent(
                new Rectangle(menu.xPositionOnScreen + 40, menu.yPositionOnScreen + 340, 86, 36),
                this.helper.Translation.Get("tailoring.qc.prev"))
            {
                myID = QcPrevId,
                upNeighborID = QcToggleId,
                downNeighborID = -99998,
                leftNeighborID = -99998,
                rightNeighborID = QcNextId
            };
            var qcNext = new ClickableComponent(
                new Rectangle(menu.xPositionOnScreen + 134, menu.yPositionOnScreen + 340, 86, 36),
                this.helper.Translation.Get("tailoring.qc.next"))
            {
                myID = QcNextId,
                upNeighborID = QcToggleId,
                downNeighborID = -99998,
                leftNeighborID = QcPrevId,
                rightNeighborID = -99998
            };

            var fragment = new ClickableTextureComponent(
                new Rectangle(
                    menu.rightIngredientSpot.bounds.X,
                    menu.leftIngredientSpot.bounds.Y,
                    96,
                    96),
                menu.tailoringTextures,
                new Rectangle(0, 128, 24, 24),
                4f)
            {
                myID = FragmentSlotId,
                leftNeighborID = TailoringMenu.region_leftIngredient,
                rightNeighborID = TailoringMenu.region_startButton,
                upNeighborID = TailoringMenu.region_rightIngredient,
                downNeighborID = -99998,
                visible = false
            };

            this.state = new State
            {
                Menu = menu,
                ModeButton = mode,
                FragmentSpot = fragment,
                FitUp = fitUp,
                FitDown = fitDown,
                FitLeft = fitLeft,
                FitRight = fitRight,
                FitScaleDown = fitScaleDown,
                FitScaleUp = fitScaleUp,
                FitViewPrev = fitViewPrev,
                FitViewNext = fitViewNext,
                FitResetPos = fitResetPos,
                FitResetScale = fitResetScale,
                FitResetAll = fitResetAll,
                QcToggle = qcToggle,
                QcPrev = qcPrev,
                QcNext = qcNext,
                Enhanced = false,
                StatusKey = "tailoring.status.off"
            };

            this.EnsureClickablesPresent();
        }

        private bool TryGetActiveFitHat(out Hat hat, out GarmentInstanceData instance)
        {
            hat = null;
            instance = null;
            State s = this.state;
            if (s?.QcMode == true)
            {
                if (s.QcHat != null
                    && this.runtime.TryReadInstance(s.QcHat, out instance))
                {
                    hat = s.QcHat;
                    return true;
                }
                return false;
            }

            if (FarmerRendererPatch.WorldPreviewHat is Hat worldPreview
                && this.runtime.TryReadInstance(worldPreview, out instance))
            {
                hat = worldPreview;
                return true;
            }

            if (Game1.player.hat.Value is Hat equipped
                && this.runtime.TryReadInstance(equipped, out instance))
            {
                hat = equipped;
                return true;
            }

            return false;
        }

        private void SetQcMode(bool enabled)
        {
            State s = this.state;
            if (s == null)
                return;

            if (!enabled)
            {
                s.QcMode = false;
                s.QcHat = null;
                FarmerRendererPatch.ClearWorldPreview();
                return;
            }

            // Preview should reflect the ACTIVE ESM registry, not a historical
            // QC-tag convention. The registry itself is now the curated list of
            // garments exposed for fitting/preview, so filtering by QualityTier
            // == QC can incorrectly leave Preview with zero candidates.
            s.QcGarmentIds = this.runtime.Registry.All
                .Select(g => g.Definition.Id)
                .OrderBy(id => id, StringComparer.OrdinalIgnoreCase)
                .ToList();

            if (s.QcGarmentIds.Count == 0)
            {
                s.QcMode = false;
                s.QcHat = null;
                return;
            }

            s.QcIndex = Math.Clamp(s.QcIndex, 0, s.QcGarmentIds.Count - 1);
            s.QcMode = true;
            this.LoadQcCandidate();
        }

        private void CycleQcCandidate(int delta)
        {
            State s = this.state;
            if (s == null || !s.QcMode || s.QcGarmentIds.Count == 0)
                return;

            s.QcIndex = (s.QcIndex + delta) % s.QcGarmentIds.Count;
            if (s.QcIndex < 0)
                s.QcIndex += s.QcGarmentIds.Count;
            this.LoadQcCandidate();
        }

        private void LoadQcCandidate()
        {
            State s = this.state;
            if (s == null || s.QcGarmentIds.Count == 0)
                return;

            string id = s.QcGarmentIds[s.QcIndex];
            try
            {
                s.QcHat = this.runtime.CreateHat(id, 0);
                s.FitFacingDirection = 2;
            }
            catch (Exception ex)
            {
                s.QcHat = null;
                this.monitor.Log($"QC preview could not load '{id}': {ex.Message}", LogLevel.Warn);
            }
        }

        private string CurrentQcLabel()
        {
            State s = this.state;
            if (s == null || !s.QcMode || s.QcGarmentIds.Count == 0)
                return this.helper.Translation.Get("tailoring.qc.off");

            return this.helper.Translation.Get("tailoring.qc.label", new
            {
                index = s.QcIndex + 1,
                count = s.QcGarmentIds.Count,
                id = s.QcGarmentIds[s.QcIndex]
            });
        }

        private void EnsureClickablesPresent()
        {
            State s = this.state;
            if (s == null)
                return;

            if (s.Menu.allClickableComponents == null)
                s.Menu.populateClickableComponentList();

            if (!s.Menu.allClickableComponents.Contains(s.ModeButton))
                s.Menu.allClickableComponents.Add(s.ModeButton);
            if (!s.Menu.allClickableComponents.Contains(s.FragmentSpot))
                s.Menu.allClickableComponents.Add(s.FragmentSpot);
            if (!s.Menu.allClickableComponents.Contains(s.QcToggle))
                s.Menu.allClickableComponents.Add(s.QcToggle);
            if (s.QcMode && s.QcGarmentIds.Count > 0)
            {
                if (!s.Menu.allClickableComponents.Contains(s.QcPrev))
                    s.Menu.allClickableComponents.Add(s.QcPrev);
                if (!s.Menu.allClickableComponents.Contains(s.QcNext))
                    s.Menu.allClickableComponents.Add(s.QcNext);
            }
            else
            {
                s.Menu.allClickableComponents.Remove(s.QcPrev);
                s.Menu.allClickableComponents.Remove(s.QcNext);
            }

            bool hasGeneratedHat = this.TryGetActiveFitHat(out _, out _);
            foreach (ClickableComponent c in new[]
            {
                s.FitUp, s.FitDown, s.FitLeft, s.FitRight,
                s.FitScaleDown, s.FitScaleUp,
                s.FitViewPrev, s.FitViewNext,
                s.FitResetPos, s.FitResetScale, s.FitResetAll
            })
            {
                if (hasGeneratedHat)
                {
                    if (!s.Menu.allClickableComponents.Contains(c))
                        s.Menu.allClickableComponents.Add(c);
                }
                else
                    s.Menu.allClickableComponents.Remove(c);
            }

            s.ModeButton.downNeighborID = QcToggleId;
            s.QcToggle.downNeighborID = s.QcMode && s.QcGarmentIds.Count > 0
                ? QcPrevId
                : (hasGeneratedHat ? FitUpId : TailoringMenu.region_resultItem);
            s.QcPrev.rightNeighborID = QcNextId;
            s.QcNext.leftNeighborID = QcPrevId;
            s.Menu.startTailoringButton.rightNeighborID = ModeButtonId;
            s.Menu.rightIngredientSpot.downNeighborID = s.Enhanced
                ? FragmentSlotId
                : TailoringMenu.region_startButton;
            s.FragmentSpot.visible = s.Enhanced;
        }

        private void SetEnhanced(bool enabled)
        {
            State s = this.state;
            if (s == null || s.Enhanced == enabled)
                return;

            if (!enabled)
            {
                this.ReturnFragmentStack();
                s.Menu.inventory.highlightMethod = s.Menu.HighlightItems;
                s.Menu.BuildHighlightCache();
                this.helper.Reflection.GetMethod(s.Menu, "_ValidateCraft").Invoke();
                s.Menu.craftResultDisplay.visible = true;
                s.StatusKey = "tailoring.status.off";
            }
            else
            {
                s.Menu.inventory.highlightMethod = TailoringIngredientMapper.IsEnhancedIngredient;
                s.StatusKey = "tailoring.status.missing";
            }

            s.Enhanced = enabled;
            s.FragmentSpot.visible = enabled;
            s.Menu.rightIngredientSpot.downNeighborID = enabled
                ? FragmentSlotId
                : TailoringMenu.region_startButton;
        }

        private void ClickEnhancedIngredientSlot(
            ClickableTextureComponent slot,
            bool isTextile)
        {
            State s = this.state;
            if (s == null || slot == null)
                return;

            Item held = s.Menu.heldItem;
            Item slotted = slot.item;

            bool validHeld = held == null
                || (isTextile
                    ? TailoringIngredientMapper.TryGetTextile(held, out _)
                    : TailoringIngredientMapper.TryGetInspiration(held, out _));

            if (!validHeld)
            {
                Game1.playSound("cancel");
                s.StatusKey = isTextile
                    ? "tailoring.status.textile"
                    : "tailoring.status.inspiration";
                return;
            }

            slot.item = held;
            s.Menu.heldItem = slotted;
            Game1.playSound("stoneStep");
        }

        private void ClickFragmentSlot()
        {
            State s = this.state;
            if (s == null)
                return;

            Item held = s.Menu.heldItem;
            Item slotted = s.FragmentSpot.item;

            if (held != null && !TailoringIngredientMapper.IsFashionFragment(held))
            {
                Game1.playSound("cancel");
                s.StatusKey = "tailoring.status.fragments-only";
                return;
            }

            s.FragmentSpot.item = held;
            s.Menu.heldItem = slotted;
            Game1.playSound("stoneStep");
        }

        private bool TryReadInputs(
            out string textileId,
            out string inspirationId,
            out string statusKey)
        {
            textileId = null;
            inspirationId = null;
            State s = this.state;

            if (s == null || !s.Enhanced)
            {
                statusKey = "tailoring.status.off";
                return false;
            }

            if (!TailoringIngredientMapper.TryGetTextile(
                s.Menu.leftIngredientSpot.item,
                out textileId))
            {
                statusKey = "tailoring.status.textile";
                return false;
            }

            if (!TailoringIngredientMapper.TryGetInspiration(
                s.Menu.rightIngredientSpot.item,
                out inspirationId))
            {
                statusKey = "tailoring.status.inspiration";
                return false;
            }

            if (!TailoringIngredientMapper.IsFashionFragment(s.FragmentSpot.item)
                || s.FragmentSpot.item.Stack < FragmentCost)
            {
                statusKey = "tailoring.status.fragments";
                return false;
            }

            if (s.Menu.heldItem != null)
            {
                statusKey = "tailoring.status.cursor";
                return false;
            }

            statusKey = "tailoring.status.ready";
            return true;
        }

        private void TryCraftEnhanced()
        {
            State s = this.state;
            if (s == null || !s.Enhanced)
                return;

            if (!this.TryReadInputs(
                out string textileId,
                out string inspirationId,
                out string statusKey))
            {
                s.StatusKey = statusKey;
                Game1.playSound("cancel");
                return;
            }

            // Selection and item construction happen before ANY ingredient is
            // consumed. Failure therefore leaves all three inputs untouched.
            long sewingSeed = Random.Shared.NextInt64(0, long.MaxValue);
            if (!this.tailoring.TrySelect(
                textileId,
                inspirationId,
                sewingSeed,
                out TailoringSelectionResult selection,
                out string error))
            {
                this.monitor.Log(
                    $"Enhanced tailoring selection failed: {error}",
                    LogLevel.Error);
                s.StatusKey = "tailoring.status.failed";
                Game1.playSound("cancel");
                return;
            }

            Hat output;
            try
            {
                output = this.runtime.CreateHat(selection.GarmentId, sewingSeed);
            }
            catch (Exception ex)
            {
                this.monitor.Log(
                    $"Enhanced tailoring could not construct '{selection.GarmentId}': {ex}",
                    LogLevel.Error);
                s.StatusKey = "tailoring.status.failed";
                Game1.playSound("cancel");
                return;
            }

            if (!this.runtime.TryReadInstance(output, out GarmentInstanceData createdInstance)
                || !string.Equals(
                    createdInstance.GarmentId,
                    selection.GarmentId,
                    StringComparison.Ordinal))
            {
                this.monitor.Log(
                    $"Enhanced tailoring constructed an invalid carrier for '{selection.GarmentId}'; ingredients were not consumed.",
                    LogLevel.Error);
                s.StatusKey = "tailoring.status.failed";
                Game1.playSound("cancel");
                return;
            }

            // Transaction commit. Selection, item construction, and instance
            // payload round-trip have all succeeded before any input is spent.
            s.Menu.leftIngredientSpot.item =
                s.Menu.leftIngredientSpot.item.ConsumeStack(1);
            s.Menu.rightIngredientSpot.item =
                s.Menu.rightIngredientSpot.item.ConsumeStack(1);
            s.FragmentSpot.item =
                s.FragmentSpot.item.ConsumeStack(FragmentCost);

            s.Menu.heldItem = output;
            s.StatusKey = "tailoring.status.complete";
            s.Menu.descriptionText =
                this.helper.Translation.Get("tailoring.status.complete");
            Game1.playSound("coin");

            this.monitor.Log(
                $"Enhanced sewing completed: textile={textileId} " +
                $"inspiration={inspirationId} seed={sewingSeed} " +
                $"=> {selection.GarmentId}. Ingredients committed after item construction.",
                LogLevel.Info);
        }

        private string GetStatusText(string key)
        {
            if (key == "tailoring.status.fragments")
            {
                return this.helper.Translation.Get(
                    key,
                    new { cost = FragmentCost });
            }

            return this.helper.Translation.Get(key);
        }

        private void ReturnFragmentStack()
        {
            State s = this.state;
            if (s?.FragmentSpot?.item == null)
                return;

            Utility.CollectOrDrop(s.FragmentSpot.item);
            s.FragmentSpot.item = null;
        }

        private static int PreviousFitDirection(int direction)
            => direction switch
            {
                2 => 3,
                3 => 0,
                0 => 1,
                _ => 2
            };

        private static int NextFitDirection(int direction)
            => direction switch
            {
                2 => 1,
                1 => 0,
                0 => 3,
                _ => 2
            };

        private string FitDirectionName(int direction)
        {
            string key = direction switch
            {
                0 => "tailoring.fit.view.back",
                1 => "tailoring.fit.view.right",
                3 => "tailoring.fit.view.left",
                _ => "tailoring.fit.view.front"
            };
            return this.helper.Translation.Get(key);
        }

        private static int FitPreviewFrame(int direction)
            => direction switch
            {
                0 => 12,
                1 => 6,
                3 => 6,
                _ => 0
            };

        private void DrawFarmerFitPreview(SpriteBatch b, TailoringMenu menu, int facingDirection)
        {
            var box = new Rectangle(
                menu.xPositionOnScreen + 40,
                menu.yPositionOnScreen + 72,
                180,
                220);

            IClickableMenu.drawTextureBox(
                b,
                box.X,
                box.Y,
                box.Width,
                box.Height,
                Color.White);

            Farmer who = Game1.player;
            Hat realHat = who.hat.Value;
            Hat previewHat = this.state?.QcMode == true && this.state.QcHat != null
                ? this.state.QcHat
                : realHat;
            int oldFacing = who.FacingDirection;
            int oldFrame = who.FarmerSprite?.CurrentFrame ?? 0;
            bool oldFlip = who.FarmerSprite?.CurrentAnimationFrame.flip ?? false;
            try
            {
                // Draw a stable farmer pose without the carrier hat first, then
                // draw the ESM garment explicitly for the selected fitting view.
                // Stardew uses the right-facing side frame for both side views
                // and distinguishes Left by setting animationFrame.flip = true.
                who.FacingDirection = facingDirection;
                who.FarmerSprite?.setCurrentSingleFrame(
                    FitPreviewFrame(facingDirection),
                    32000,
                    secondaryArm: false,
                    flip: facingDirection == 3);

                Vector2 pos = new(
                    box.Center.X - 32,
                    box.Center.Y - 92);

                who.hat.Value = null;
                who.FarmerRenderer.draw(
                    b,
                    who.FarmerSprite.CurrentAnimationFrame,
                    who.FarmerSprite.CurrentFrame,
                    who.FarmerSprite.SourceRect,
                    pos,
                    Vector2.Zero,
                    0.8f,
                    facingDirection,
                    Color.White,
                    0f,
                    1f,
                    who);

                who.hat.Value = previewHat;
                if (previewHat != null && this.runtime.TryReadInstance(previewHat, out _))
                {
                    this.runtime.Draw(
                        b,
                        facingDirection,
                        who,
                        pos,
                        Vector2.Zero,
                        1f,
                        who.FarmerSprite.CurrentFrame,
                        0f,
                        Color.White,
                        0.8f,
                        Vector2.Zero,
                        0);
                }
            }
            catch
            {
                // A preview draw failure must never break the tailoring menu.
            }
            finally
            {
                who.hat.Value = realHat;
                who.FacingDirection = oldFacing;
                who.FarmerSprite?.setCurrentSingleFrame(
                    oldFrame,
                    32000,
                    secondaryArm: false,
                    flip: oldFlip);
            }
        }

        private static void DrawFitButton(SpriteBatch b, ClickableComponent c)
        {
            IClickableMenu.drawTextureBox(b, c.bounds.X, c.bounds.Y, c.bounds.Width, c.bounds.Height, Color.White);
            Vector2 size = Game1.smallFont.MeasureString(c.name);
            Utility.drawTextWithShadow(b, c.name, Game1.smallFont,
                new Vector2(c.bounds.Center.X - size.X / 2f, c.bounds.Center.Y - size.Y / 2f), Game1.textColor);
        }

        private static void DrawCenteredAbove(
            SpriteBatch b,
            string text,
            Rectangle bounds)
        {
            Vector2 size = Game1.smallFont.MeasureString(text);
            Utility.drawTextWithShadow(
                b,
                text,
                Game1.smallFont,
                new Vector2(
                    bounds.Center.X - size.X / 2f,
                    bounds.Top - size.Y - 2),
                Game1.textColor);
        }
    }
}
