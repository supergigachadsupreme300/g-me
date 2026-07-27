using UnityEngine;

public class ToolManager : MonoBehaviour
{
    public enum ToolType
    {
        None,
        Axe,
        Pickaxe,
        Hoe,
        Hammer,
        Sword,
        Gun,
        Scythe,
        Fertilizer,
        Seed,
        PeashooterSeed,
        Wheat,
        Corn,
        Potato
    }

    public ToolType ActiveTool = ToolType.None;

    public void SetActiveTool(ToolType tool)
    {
        ActiveTool = tool;
        UpdateToolState();
    }

    private void UpdateToolState()
    {
        Debug.Log($"Active tool set to: {ActiveTool}");
    }
}
