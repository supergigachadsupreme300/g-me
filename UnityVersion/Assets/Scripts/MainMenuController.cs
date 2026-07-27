using UnityEngine;
using UnityEngine.UI;

public class MainMenuController : MonoBehaviour
{
    public GameObject MainMenuRoot;
    public Button NewGameButton;
    public Button LoadGameButton;
    public Button QuitButton;
    public GameManager GameManager;

    private void Awake()
    {
        if (NewGameButton != null)
            NewGameButton.onClick.AddListener(OnNewGameClicked);
        if (LoadGameButton != null)
            LoadGameButton.onClick.AddListener(OnLoadGameClicked);
        if (QuitButton != null)
            QuitButton.onClick.AddListener(OnQuitClicked);
    }

    public void OnNewGameClicked()
    {
        if (GameManager != null)
        {
            GameManager.StartNewGame();
        }
        HideMenu();
    }

    public void OnLoadGameClicked()
    {
        if (GameManager != null)
        {
            GameManager.LoadGame();
        }
        HideMenu();
    }

    public void OnQuitClicked()
    {
        Application.Quit();
    }

    private void HideMenu()
    {
        if (MainMenuRoot != null)
            MainMenuRoot.SetActive(false);
    }
}
