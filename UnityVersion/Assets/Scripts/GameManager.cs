using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    public bool InGame { get; private set; }
    public bool GamePaused { get; private set; }

    public int CurrentDay = 1;
    public float TimeOfDay = 8f;
    public float TimeSpeed = 1f;

    public PlayerController Player;
    public WorldBuilder WorldBuilder;
    public UIManager UIManager;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
    }

    private void Start()
    {
        if (WorldBuilder != null)
        {
            WorldBuilder.CreateWorld();
        }

        if (UIManager != null)
        {
            UIManager.UpdateTimeText(CurrentDay, TimeOfDay);
            UIManager.UpdatePlayerStats(100, 100, 0);
        }

        if (Player != null)
        {
            Player.EnableInput(false);
        }
    }

    private void Update()
    {
        if (!InGame || GamePaused)
            return;

        TimeOfDay += TimeSpeed * Time.deltaTime;
        if (TimeOfDay >= 24f)
        {
            TimeOfDay -= 24f;
            CurrentDay++;
        }

        UpdateTimeUI();

        if (Input.GetKeyDown(KeyCode.Escape))
        {
            TogglePause(true);
        }
    }

    public void StartNewGame()
    {
        InGame = true;
        if (WorldBuilder != null)
        {
            WorldBuilder.ResetWorld();
        }

        if (Player != null)
        {
            Player.EnableInput(true);
            Player.ResetPlayer();
        }

        UpdateTimeUI();
        TogglePause(false);
    }

    public void LoadGame()
    {
        InGame = true;
        if (Player != null)
        {
            Player.EnableInput(true);
        }

        UpdateTimeUI();
        TogglePause(false);
    }

    public void TogglePause(bool paused)
    {
        GamePaused = paused;
        if (UIManager != null)
        {
            UIManager.ShowPauseMenu(paused);
        }

        if (Player != null)
        {
            Player.EnableInput(!paused);
        }
    }

    public void SetTimeOfDay(float hour)
    {
        TimeOfDay = Mathf.Repeat(hour, 24f);
        UpdateTimeUI();
    }

    public void UpdateTimeUI()
    {
        if (UIManager != null)
        {
            UIManager.UpdateTimeText(CurrentDay, TimeOfDay);
        }
    }
}
