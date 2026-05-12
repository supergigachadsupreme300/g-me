from ursina import Entity, color, Vec3, raycast, destroy, load_model, load_texture, time
import time as pytime
import random
import world
import fields
import buildings
import items

# load rat texture from available assets
rat_texture = None
for path in ['texture/rat_texture.png', 'texture/rat_grey.tga', 'texture/rat_khaki.tga', 'texture/rat_bege_psd.psd']:
    try:
        rat_texture = load_texture(path)
        if rat_texture:
            print(f"Loaded rat texture from: {path}")
            break
    except Exception:
        rat_texture = None

if rat_texture is None:
    rat_texture = color.rgb(120, 80, 40)

enemies = []

SEARCH_WHEAT = 'SEARCH_WHEAT'
MOVE_TO_TARGET = 'MOVE_TO_TARGET'
ATTACK_OBSTACLE = 'ATTACK_OBSTACLE'
ATTACK_WHEAT = 'ATTACK_WHEAT'
DEAD = 'DEAD'


DETECTION_RADIUS = 12


def find_nearest_rice_field(position, max_dist=None):
    best = None
    best_dist = None
    for field_data in fields.fields:
        if field_data["rice_planted"] and field_data["rice_hp"] > 0:
            dist = abs(field_data["pos"].x - position.x) + abs(field_data["pos"].z - position.z)
            if max_dist is not None and dist > max_dist:
                continue
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best = field_data
    return best


def find_enemy_by_entity(entity):
    current = entity
    while current is not None:
        for enemy in enemies:
            if enemy.entity == current:
                return enemy
        current = getattr(current, 'parent', None)
    return None


class Rat:
    def __init__(self, position):
        try:
            rat_model = load_model('model/rat.fbx')
        except Exception as e:
            print(f"Failed to load rat model: {e}. Using fallback cube.")
            rat_model = 'cube'
        self.entity = Entity(model=rat_model, color=color.rgb(120, 80, 40), scale=(0.8, 0.8, 0.8), position=position, collider='box')
        if hasattr(rat_texture, 'width'):
            self.entity.texture = rat_texture
        self.health_bar = Entity(model='cube', color=color.red, scale=(0.5, 0.05, 0.05), parent=self.entity, position=(0, 0.8, 0), origin=(0, 0))
        self.state = SEARCH_WHEAT
        self.target_field = None
        self.target_building = None
        self.wander_target = None
        self.wander_timer = pytime.time()
        self.hp = 15
        self.max_hp = 15
        self.speed = 2.0
        self.attack_damage = 4
        self.attack_cooldown = 1.0
        self.last_attack_time = 0
        self.sub_entities = [self.entity]

    def pick_wander_target(self):
        edge = world.GROUND_HALF - 2
        if random.random() < 0.5:
            x = random.choice([-edge, edge])
            z = random.uniform(-edge, edge)
        else:
            x = random.uniform(-edge, edge)
            z = random.choice([-edge, edge])
        self.wander_target = Vec3(x, self.entity.y, z)
        self.wander_timer = pytime.time()

    def wander(self):
        if self.wander_target is None or (self.wander_target - self.entity.position).length() < 0.5 or pytime.time() - self.wander_timer > 8:
            self.pick_wander_target()
        direction = (self.wander_target - self.entity.position)
        if direction.length() > 0:
            self.entity.position += direction.normalized() * self.speed * time.dt

    def update(self):
        if self.state == DEAD:
            return
        if self.hp <= 0:
            self.die()
            return
        if self.state == SEARCH_WHEAT:
            self.target_field = find_nearest_rice_field(self.entity.position, DETECTION_RADIUS)
            if self.target_field:
                self.state = MOVE_TO_TARGET
            else:
                self.wander()
            return

        if self.state == MOVE_TO_TARGET:
            if not self.target_field or not self.target_field["rice_planted"] or self.target_field["rice_hp"] <= 0:
                self.state = SEARCH_WHEAT
                return
            target_position = Vec3(self.target_field["pos"].x, self.entity.y, self.target_field["pos"].z)
            direction = (target_position - self.entity.position)
            distance = direction.length()
            if distance < 1.0:
                self.state = ATTACK_WHEAT
                return
            direction = direction.normalized()
            ray = raycast(self.entity.world_position + Vec3(0, 0.2, 0), direction, distance=distance, ignore=(self.entity,))
            if ray.hit and ray.entity in [b["entity"] for b in buildings.buildings]:
                self.target_building = next((b for b in buildings.buildings if b["entity"] == ray.entity), None)
                if self.target_building:
                    self.state = ATTACK_OBSTACLE
                    return
            self.entity.position += direction * self.speed * time.dt
            return

        if self.state == ATTACK_OBSTACLE:
            if not self.target_building or self.target_building not in buildings.buildings:
                self.state = MOVE_TO_TARGET
                return
            if pytime.time() - self.last_attack_time >= self.attack_cooldown:
                buildings.damage_building(self.target_building, self.attack_damage)
                self.last_attack_time = pytime.time()
            if self.target_building not in buildings.buildings:
                self.state = MOVE_TO_TARGET
            return

        if self.state == ATTACK_WHEAT:
            if not self.target_field or not self.target_field["rice_planted"] or self.target_field["rice_hp"] <= 0:
                self.state = SEARCH_WHEAT
                return
            distance = (Vec3(self.target_field["pos"].x, self.entity.y, self.target_field["pos"].z) - self.entity.position).length()
            if distance > 1.2:
                self.state = MOVE_TO_TARGET
                return
            if pytime.time() - self.last_attack_time >= self.attack_cooldown:
                self.target_field["rice_hp"] -= self.attack_damage
                self.last_attack_time = pytime.time()
                if self.target_field["rice_hp"] <= 0:
                    fields.destroy_rice(self.target_field)
                    self.state = SEARCH_WHEAT
            return

    def take_damage(self, amount):
        self.hp -= amount
        self.health_bar.scale_x = max(0, self.hp / self.max_hp) * 0.5
        if self.hp <= 0:
            self.die()

    def die(self):
        self.state = DEAD
        items.spawn_ground_item("seed", self.entity.position + Vec3(0, 0.2, 0))
        destroy(self.entity)
        destroy(self.health_bar)
        if self in enemies:
            enemies.remove(self)
        print(f"Rat died and dropped a seed")


def spawn_rat(position):
    rat = Rat(position)
    enemies.append(rat)
    return rat


def update_enemies():
    for enemy in list(enemies):
        enemy.update()
