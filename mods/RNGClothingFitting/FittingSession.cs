using System.Collections.Generic;
using Microsoft.Xna.Framework;

namespace RNGClothingFitting
{
    internal enum FitTarget { Hat, Motif }

    /// <summary>What the player had open last time, per generated item.
    ///
    /// This is VIEW state, not garment state. It restores the screen the player
    /// left — which tab they were on, how zoomed in they were, where the cell
    /// cursor sat — and it deliberately does NOT touch the saved fit. Reopening
    /// a cap changes nothing about the cap unless Save was used.
    ///
    /// Held in memory for the play session only. Persisting it would mean
    /// writing to the save file every time someone glanced at a menu, which is
    /// not worth a save-data write, and none of it matters across a restart.
    /// </summary>
    internal sealed class FittingSession
    {
        public FitTarget Target = FitTarget.Hat;

        /// <summary>Index into the readability scales (1x / 2x / 4x).</summary>
        public int ReadabilityIndex = 2;        // 4x = gameplay scale, the authority

        /// <summary>Selected validated swatch, for the future masked editor.
        ///
        /// Nothing writes this yet -- there is no editor to pick a colour in.
        /// It is carried in session state now so that adding one does not
        /// change this type's shape.</summary>
#pragma warning disable CS0649 // assigned once the masked editor exists
        public int SwatchIndex;
#pragma warning restore CS0649

        /// <summary>Cell cursor for the future masked editor.</summary>
        public Point? Cursor;

        /// <summary>Off by default; no editor consumes it yet.</summary>
        public SymmetryMode Symmetry = SymmetryMode.Off;

        /// <summary>Which control had focus, so controller users come back to
        /// where they were instead of the default button.</summary>
        public int SnappedComponentId = -1;
    }

    /// <summary>Sessions by item id.</summary>
    internal sealed class SessionStore
    {
        private readonly Dictionary<string, FittingSession> byItem = new();

        public FittingSession For(string itemId)
        {
            if (string.IsNullOrEmpty(itemId))
                return new FittingSession();
            if (!this.byItem.TryGetValue(itemId, out var s))
                this.byItem[itemId] = s = new FittingSession();
            return s;
        }

        public void Clear() => this.byItem.Clear();
    }
}
