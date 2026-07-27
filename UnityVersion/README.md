# Unity Version

This folder contains a C# Unity version of the current Python Ursina game logic.

## Structure
- `Assets/Scripts/GameManager.cs` - manages game state, time, and pause behavior.
- `Assets/Scripts/MainMenuController.cs` - handles the main menu buttons and game start/load flow.
- `Assets/Scripts/WorldBuilder.cs` - generates a simple ground, road, trees, rocks, and house geometry at runtime.
- `Assets/Scripts/PlayerController.cs` - implements basic movement, sprint, and a blocky player model.
- `Assets/Scripts/UIManager.cs` - updates HUD text and toggles UI menus.
- `Assets/Scripts/ToolManager.cs` - placeholder tool selection manager.

## Usage
1. Open Unity and create a new project.
2. Copy the `UnityVersion/Assets/Scripts` folder into the Unity project's `Assets` folder.
3. Create a new scene and add a `GameObject` with the `GameManager` component.
4. Add `PlayerController`, `WorldBuilder`, and `UIManager` components as needed.
5. Wire UI elements to `MainMenuController` and `UIManager` in the Inspector.

## Notes
- This is a code-level port, not a complete Unity scene package.
- The runtime world builder is a simplified translation of the Python world creation logic.
- Additional Unity assets and prefabs must be created in Unity to complete the experience.
