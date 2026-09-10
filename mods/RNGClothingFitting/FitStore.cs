using System.Collections.Generic;
using StardewModdingAPI;

namespace RNGClothingFitting
{
    /// <summary>Saved fitting adjustments, per save file.
    ///
    /// THE GENERATED PACK IS NEVER REWRITTEN. A player's fitting is stored
    /// here and re-applied when the save loads, so the authored default stays
    /// intact on disk: Reset can always recover it, and re-rolling the same
    /// seed still reproduces the same cap. A cap sitting at its default stores
    /// nothing at all.
    /// </summary>
    internal sealed class FitStore
    {
        private const string Key = "fitting";

        internal sealed class Model
        {
            public Dictionary<string, Fit> Fits { get; set; } = new();
        }

        private readonly IModHelper helper;
        private Model data = new();

        public FitStore(IModHelper helper) => this.helper = helper;

        public void Load()
        {
            this.data = this.helper.Data.ReadSaveData<Model>(Key) ?? new Model();
        }

        public IEnumerable<KeyValuePair<string, Fit>> All => this.data.Fits;

        public Fit Get(string itemId)
        {
            if (this.data.Fits.TryGetValue(itemId, out var f) && f != null)
            {
                f.ItemId = itemId;
                return f.Clone();
            }
            return new Fit { ItemId = itemId };
        }

        public void Save(Fit fit)
        {
            if (fit?.ItemId == null)
                return;
            if (fit.IsDefault)
                this.data.Fits.Remove(fit.ItemId);
            else
                this.data.Fits[fit.ItemId] = fit.Clone();
            this.helper.Data.WriteSaveData(Key, this.data);
        }
    }
}
