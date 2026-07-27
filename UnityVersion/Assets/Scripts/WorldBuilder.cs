using System.Collections.Generic;
using UnityEngine;

public class WorldBuilder : MonoBehaviour
{
    public int TreeCount = 200;
    public int RockCount = 100;
    public Vector3 GroundSize = new Vector3(150f, 0.2f, 150f);
    public Transform WorldRoot;
    public GameObject PlayerPrefab;

    private readonly List<GameObject> trees = new List<GameObject>();
    private readonly List<GameObject> rocks = new List<GameObject>();
    private GameObject groundObject;
    private GameObject playerObject;

    public void CreateWorld()
    {
        if (WorldRoot == null)
        {
            WorldRoot = new GameObject("WorldRoot").transform;
        }

        CreateGround();
        BuildRoad();
        SpawnTrees(TreeCount);
        SpawnRocks(RockCount);
        BuildHouse();
        CreatePlayer();
    }

    public void ResetWorld()
    {
        foreach (var tree in trees)
            Destroy(tree);
        trees.Clear();
        foreach (var rock in rocks)
            Destroy(rock);
        rocks.Clear();
        if (groundObject != null)
            Destroy(groundObject);
        if (playerObject != null)
            Destroy(playerObject);
        CreateWorld();
    }

    private void CreateGround()
    {
        groundObject = GameObject.CreatePrimitive(PrimitiveType.Plane);
        groundObject.name = "Ground";
        groundObject.transform.SetParent(WorldRoot);
        groundObject.transform.localScale = new Vector3(GroundSize.x / 10f, 1f, GroundSize.z / 10f);
        groundObject.transform.position = Vector3.zero;
        var renderer = groundObject.GetComponent<Renderer>();
        if (renderer != null)
        {
            renderer.material.color = new Color(0.35f, 0.65f, 0.3f);
        }
    }

    private void BuildRoad()
    {
        var road = GameObject.CreatePrimitive(PrimitiveType.Cube);
        road.name = "Road";
        road.transform.SetParent(WorldRoot);
        road.transform.localScale = new Vector3(10f, 0.1f, 80f);
        road.transform.position = new Vector3(14f, 0.05f, 30f);
        var renderer = road.GetComponent<Renderer>();
        if (renderer != null)
            renderer.material.color = Color.black;
    }

    private void SpawnTrees(int count)
    {
        for (int i = 0; i < count; i++)
        {
            Vector3 position = GetRandomWorldPosition();
            if (Mathf.Abs(position.x) <= 9 && Mathf.Abs(position.z) <= 9)
            {
                i--;
                continue;
            }

            var tree = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tree.name = "Tree" + i;
            tree.transform.SetParent(WorldRoot);
            tree.transform.position = position + Vector3.up * 2.5f;
            tree.transform.localScale = new Vector3(2f, 6f, 2f);
            var renderer = tree.GetComponent<Renderer>();
            if (renderer != null)
                renderer.material.color = new Color(0.15f, 0.45f, 0.1f);
            trees.Add(tree);
        }
    }

    private void SpawnRocks(int count)
    {
        for (int i = 0; i < count; i++)
        {
            Vector3 position = GetRandomWorldPosition();
            if (Mathf.Abs(position.x) <= 9 && Mathf.Abs(position.z) <= 9)
            {
                i--;
                continue;
            }

            var rock = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            rock.name = "Rock" + i;
            rock.transform.SetParent(WorldRoot);
            rock.transform.position = position + Vector3.up * 1f;
            rock.transform.localScale = new Vector3(2f, 2f, 2f);
            var renderer = rock.GetComponent<Renderer>();
            if (renderer != null)
                renderer.material.color = Color.gray;
            rocks.Add(rock);
        }
    }

    private void BuildHouse()
    {
        var houseRoot = new GameObject("House");
        houseRoot.transform.SetParent(WorldRoot);
        houseRoot.transform.position = new Vector3(0f, 0f, 0f);

        CreateWall(houseRoot.transform, new Vector3(10f, 5f, 0.5f), new Vector3(0f, 2.5f, -5f), new Color(0.6f, 0.3f, 0.15f));
        CreateWall(houseRoot.transform, new Vector3(10f, 5f, 0.5f), new Vector3(0f, 2.5f, 5f), new Color(0.6f, 0.3f, 0.15f));
        CreateWall(houseRoot.transform, new Vector3(0.5f, 5f, 10f), new Vector3(-5f, 2.5f, 0f), new Color(0.6f, 0.3f, 0.15f));
        CreateWall(houseRoot.transform, new Vector3(10f, 0.5f, 10f), new Vector3(0f, 0f, 0f), new Color(0.6f, 0.3f, 0.15f));

        var roof = GameObject.CreatePrimitive(PrimitiveType.Cube);
        roof.name = "Roof";
        roof.transform.SetParent(houseRoot.transform);
        roof.transform.position = new Vector3(0f, 6f, 0f);
        roof.transform.localScale = new Vector3(10f, 1f, 10f);
        var renderer = roof.GetComponent<Renderer>();
        if (renderer != null)
            renderer.material.color = new Color(0.55f, 0.15f, 0.1f);
    }

    private void CreateWall(Transform parent, Vector3 scale, Vector3 position, Color color)
    {
        var wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
        wall.transform.SetParent(parent);
        wall.transform.localScale = scale;
        wall.transform.localPosition = position;
        var renderer = wall.GetComponent<Renderer>();
        if (renderer != null)
            renderer.material.color = color;
    }

    private void CreatePlayer()
    {
        if (PlayerPrefab != null)
        {
            playerObject = Instantiate(PlayerPrefab, new Vector3(0f, 2f, -10f), Quaternion.identity, WorldRoot);
            playerObject.name = "Player";
        }
    }

    private Vector3 GetRandomWorldPosition()
    {
        float halfSize = GroundSize.x / 2f - 5f;
        float x = Random.Range(-halfSize, halfSize);
        float z = Random.Range(-halfSize, halfSize);
        return new Vector3(x, 0f, z);
    }
}
