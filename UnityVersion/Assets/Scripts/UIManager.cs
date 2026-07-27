using UnityEngine;
using UnityEngine.UI;

public class UIManager : MonoBehaviour
{
    public Text TimeText;
    public Text AmmoText;
    public Text PlayerHPText;
    public Text PlayerStaminaText;
    public Text PlayerMoneyText;
    public Text QuestText;

    public GameObject PauseMenu;
    public GameObject StatsPanel;
    public GameObject QuestPanel;
    public GameObject InstructionsPanel;

    public void UpdateTimeText(int day, float hour)
    {
        if (TimeText != null)
        {
            TimeText.text = $"Day {day} - {hour:00.00}";
        }
    }

    public void UpdatePlayerStats(int hp, int maxHp, float stamina)
    {
        if (PlayerHPText != null)
            PlayerHPText.text = $"HP: {hp}/{maxHp}";
        if (PlayerStaminaText != null)
            PlayerStaminaText.text = $"Stamina: {(int)stamina}/{(int)stamina}";
    }

    public void UpdateMoneyText(long money)
    {
        if (PlayerMoneyText != null)
            PlayerMoneyText.text = $"Money: {money}";
    }

    public void UpdateQuestText(string quest)
    {
        if (QuestText != null)
            QuestText.text = quest;
    }

    public void ShowPauseMenu(bool show)
    {
        if (PauseMenu != null)
            PauseMenu.SetActive(show);
    }

    public void ShowStatsPanel(bool show)
    {
        if (StatsPanel != null)
            StatsPanel.SetActive(show);
    }

    public void ShowQuestPanel(bool show)
    {
        if (QuestPanel != null)
            QuestPanel.SetActive(show);
    }

    public void ShowInstructions(bool show)
    {
        if (InstructionsPanel != null)
            InstructionsPanel.SetActive(show);
    }
}
