using StardewValley;

namespace EnhancedSewingMachine.EnhancedTailoring
{
    internal static class TailoringIngredientMapper
    {
        public static bool TryGetTextile(Item item, out string textileId)
        {
            textileId = item?.QualifiedItemId switch
            {
                "(O)428" => "cotton", // Cloth
                "(O)440" => "wool",   // Wool
                _ => null
            };
            return textileId != null;
        }

        public static bool TryGetInspiration(Item item, out string inspirationId)
        {
            inspirationId = item?.QualifiedItemId switch
            {
                "(O)421" => "sunflower",
                "(O)84" => "frozen-tear",
                "(O)103" => "ancient-doll",
                _ => null
            };
            return inspirationId != null;
        }

        public static bool IsFashionFragment(Item item)
            => item?.QualifiedItemId == FashionFragmentItem.QualifiedItemId;

        public static bool IsEnhancedIngredient(Item item)
            => TryGetTextile(item, out _)
                || TryGetInspiration(item, out _)
                || IsFashionFragment(item);
    }
}
