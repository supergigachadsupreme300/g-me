using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class PlayerController : MonoBehaviour
{
    public float MoveSpeed = 5f;
    public float SprintMultiplier = 2f;
    public float Gravity = -9.81f;
    public float JumpHeight = 1.5f;

    public int HP = 100;
    public int MaxHP = 100;
    public float Stamina = 1000f;
    public float MaxStamina = 1000f;
    public float StaminaRegenRate = 25f;
    public float SprintCost = 35f;
    public long Money = 10000000000;

    public bool IgnoreInput { get; private set; }

    private CharacterController controller;
    private Vector3 velocity;
    private Transform cameraTransform;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
        cameraTransform = Camera.main != null ? Camera.main.transform : null;
        CreateBlockyPlayerModel();
    }

    private void Update()
    {
        if (IgnoreInput)
            return;

        HandleMovement();
        HandleStamina();
    }

    public void ResetPlayer()
    {
        HP = MaxHP;
        Stamina = MaxStamina;
        transform.position = new Vector3(0f, 2f, -10f);
        transform.rotation = Quaternion.identity;
    }

    public void EnableInput(bool enabled)
    {
        IgnoreInput = !enabled;
    }

    private void HandleMovement()
    {
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");
        Vector3 direction = new Vector3(horizontal, 0f, vertical);
        if (direction.magnitude > 1f)
            direction.Normalize();

        bool sprint = Input.GetKey(KeyCode.LeftShift) && Stamina > 0f;
        float speed = MoveSpeed * (sprint ? SprintMultiplier : 1f);

        if (controller != null)
        {
            Vector3 move = transform.TransformDirection(direction) * speed;
            controller.Move(move * Time.deltaTime);

            if (controller.isGrounded && Input.GetButtonDown("Jump"))
            {
                velocity.y = Mathf.Sqrt(JumpHeight * -2f * Gravity);
            }

            velocity.y += Gravity * Time.deltaTime;
            controller.Move(velocity * Time.deltaTime);
        }

        if (sprint && direction.magnitude > 0f)
        {
            Stamina = Mathf.Max(0f, Stamina - SprintCost * Time.deltaTime);
        }
    }

    private void HandleStamina()
    {
        if (!Input.GetKey(KeyCode.LeftShift) || controller == null || !controller.isGrounded)
        {
            Stamina = Mathf.Min(MaxStamina, Stamina + StaminaRegenRate * Time.deltaTime);
        }
    }

    private void CreateBlockyPlayerModel()
    {
        var root = new GameObject("PlayerModel");
        root.transform.SetParent(transform);
        root.transform.localPosition = Vector3.zero;

        CreatePart(root.transform, "Torso", new Vector3(0.88f, 0.45f, 0.46f), new Vector3(0f, 1.25f, 0f), new Color(0.05f, 0.41f, 0.69f));
        CreatePart(root.transform, "Head", new Vector3(0.5f, 0.5f, 0.5f), new Vector3(0f, 1.8f, 0f), new Color(1f, 0.8f, 0.58f));
        CreatePart(root.transform, "LeftLeg", new Vector3(0.4f, 0.55f, 0.42f), new Vector3(-0.25f, 0.65f, 0f), new Color(0.16f, 0.5f, 0.28f));
        CreatePart(root.transform, "RightLeg", new Vector3(0.4f, 0.55f, 0.42f), new Vector3(0.25f, 0.65f, 0f), new Color(0.16f, 0.5f, 0.28f));
        CreatePart(root.transform, "LeftArm", new Vector3(0.36f, 0.45f, 0.38f), new Vector3(-0.62f, 1.25f, 0f), new Color(0.05f, 0.41f, 0.69f));
        CreatePart(root.transform, "RightArm", new Vector3(0.36f, 0.45f, 0.38f), new Vector3(0.62f, 1.25f, 0f), new Color(0.05f, 0.41f, 0.69f));
    }

    private void CreatePart(Transform parent, string name, Vector3 scale, Vector3 localPosition, Color color)
    {
        var part = GameObject.CreatePrimitive(PrimitiveType.Cube);
        part.name = name;
        part.transform.SetParent(parent);
        part.transform.localScale = scale;
        part.transform.localPosition = localPosition;
        var renderer = part.GetComponent<Renderer>();
        if (renderer != null)
            renderer.material.color = color;
    }
}
