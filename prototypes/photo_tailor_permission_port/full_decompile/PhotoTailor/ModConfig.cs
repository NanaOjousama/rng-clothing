namespace PhotoTailor;

internal sealed class ModConfig
{
	public int ConfigVersion { get; set; } = 2;

	public int MachinePrice { get; set; } = 25000;

	public int ClothCost { get; set; } = 1;

	public int GoldCost { get; set; } = 2000;
}
