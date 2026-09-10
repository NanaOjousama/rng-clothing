using System.Collections.Generic;
using Microsoft.Xna.Framework;

namespace RNGClothingFitting
{
    /// <summary>One complete, restorable customization state.
    ///
    /// Snapshots rather than deltas: the whole editable state is small — four
    /// offsets, a scale index, and (later) at most a few dozen painted cells —
    /// so copying it wholesale is cheaper than describing a change, and it
    /// cannot drift out of sync with what it claims to undo.
    ///
    /// PaintedCells is present but unused: no pixel editing exists yet. It is
    /// here so adding the masked editor does not require reworking history,
    /// and so a snapshot taken today still round-trips when it does.
    /// </summary>
    internal sealed class FitSnapshot
    {
        public int HatRight, HatDown;
        public int MotifRight, MotifDown;
        public int ScaleIndex;                 // inert: scale is not exposed
        public uint[] PaintedCells;            // future masked pixel edits

        public static FitSnapshot From(Fit fit, int scaleIndex = 0, uint[] painted = null)
        {
            return new FitSnapshot
            {
                HatRight = fit.HatRight,
                HatDown = fit.HatDown,
                MotifRight = fit.MotifRight,
                MotifDown = fit.MotifDown,
                ScaleIndex = scaleIndex,
                PaintedCells = painted == null ? null : (uint[])painted.Clone()
            };
        }

        public void ApplyTo(Fit fit)
        {
            fit.HatRight = this.HatRight;
            fit.HatDown = this.HatDown;
            fit.MotifRight = this.MotifRight;
            fit.MotifDown = this.MotifDown;
        }

        public bool SameAs(FitSnapshot o)
        {
            if (o == null)
                return false;
            if (this.HatRight != o.HatRight || this.HatDown != o.HatDown
                || this.MotifRight != o.MotifRight || this.MotifDown != o.MotifDown
                || this.ScaleIndex != o.ScaleIndex)
                return false;
            if (this.PaintedCells == null && o.PaintedCells == null)
                return true;
            if (this.PaintedCells == null || o.PaintedCells == null
                || this.PaintedCells.Length != o.PaintedCells.Length)
                return false;
            for (int i = 0; i < this.PaintedCells.Length; i++)
                if (this.PaintedCells[i] != o.PaintedCells[i])
                    return false;
            return true;
        }

        public FitSnapshot Clone() => new()
        {
            HatRight = this.HatRight, HatDown = this.HatDown,
            MotifRight = this.MotifRight, MotifDown = this.MotifDown,
            ScaleIndex = this.ScaleIndex,
            PaintedCells = this.PaintedCells == null ? null : (uint[])this.PaintedCells.Clone()
        };
    }

    /// <summary>Bounded undo / redo over <see cref="FitSnapshot"/>.
    ///
    /// Capture happens BEFORE a change, which is what makes one Undo land on
    /// the state the player last saw rather than one step short of it. Depth is
    /// deliberately modest — fitting is a handful of nudges, not a drawing
    /// session — and the oldest entry is dropped once it is reached.
    ///
    /// A capture that would record no change is discarded, so a blocked nudge
    /// never costs the player an undo step.
    /// </summary>
    internal sealed class FitHistory
    {
        public const int MaxDepth = 24;

        private readonly List<FitSnapshot> undo = new();
        private readonly List<FitSnapshot> redo = new();

        public bool CanUndo => this.undo.Count > 0;
        public bool CanRedo => this.redo.Count > 0;
        public int Depth => this.undo.Count;

        public void Clear()
        {
            this.undo.Clear();
            this.redo.Clear();
        }

        /// <summary>Record the state as it is now, before changing it.</summary>
        public void Capture(FitSnapshot current)
        {
            if (current == null)
                return;
            if (this.undo.Count > 0 && this.undo[^1].SameAs(current))
                return;                        // nothing actually changed
            this.undo.Add(current.Clone());
            if (this.undo.Count > MaxDepth)
                this.undo.RemoveAt(0);
            this.redo.Clear();                 // a new edit invalidates the redo branch
        }

        /// <summary>Step back. `current` is the live state, which becomes the
        /// redo entry. Returns the state to restore, or null if there is none.</summary>
        public FitSnapshot Undo(FitSnapshot current)
        {
            if (this.undo.Count == 0)
                return null;
            FitSnapshot prev = this.undo[^1];
            this.undo.RemoveAt(this.undo.Count - 1);
            if (current != null)
                this.redo.Add(current.Clone());
            return prev;
        }

        /// <summary>Step forward again.</summary>
        public FitSnapshot Redo(FitSnapshot current)
        {
            if (this.redo.Count == 0)
                return null;
            FitSnapshot next = this.redo[^1];
            this.redo.RemoveAt(this.redo.Count - 1);
            if (current != null)
            {
                this.undo.Add(current.Clone());
                if (this.undo.Count > MaxDepth)
                    this.undo.RemoveAt(0);
            }
            return next;
        }
    }
}
