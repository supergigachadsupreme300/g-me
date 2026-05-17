from ursina import Entity, color, Vec3, raycast, destroy, load_model, load_texture, time
from math import atan2, degrees
import time as pytime
import random
import world
import fields
import building_system
import items

rat_texture = []
rat_model = None


def load_rat_assets():
    global rat_texture, rat_model
    if rat_model is not None and rat_texture:
        return

    for path in ['texture/rat_grey.png', 'texture/rat_khaki.png', 'texture/rat_bege_psd.png']:
        try:
            tex = load_texture(path)
            if tex:
                rat_texture.append(tex)
                print(f"Loaded texture: {path}")
        except Exception as e:
            print(f"Failed loading rat texture {path}: {e}")

    if not rat_texture:
        rat_texture = [color.rgb(120/255, 80/255, 40/255)]  # fallback màu nâu

    try:
        rat_model = load_model('model/rat.fbx')
    except Exception as e:
        print(f"Failed to load rat model: {e}. Using fallback cube.")
        rat_model = 'cube'


enemies = []

SEARCH_WHEAT = 'SEARCH_WHEAT'
MOVE_TO_TARGET = 'MOVE_TO_TARGET'
ATTACK_OBSTACLE = 'ATTACK_OBSTACLE'
ATTACK_WHEAT = 'ATTACK_WHEAT'
FLEE_PLAYER = 'FLEE_PLAYER'
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
        load_rat_assets()
        position = Vec3(position.x, 0.0, position.z)
        texture_choice = random.choice(rat_texture)
        entity_kwargs = {
            'model': rat_model if rat_model is not None else 'cube',
            'scale': (0.8, 0.8, 0.8),
            'position': position,
            'collider': 'box'
        }
        if hasattr(texture_choice, 'width'):
            entity_kwargs['texture'] = texture_choice
            entity_kwargs['color'] = color.white
        else:
            entity_kwargs['color'] = texture_choice
        self.entity = Entity(**entity_kwargs)
        self.entity.y = self.entity.scale_y / 2
        self.entity.double_sided = True  # Fix texture appearing inside
        self.velocity_y = 0
        self.health_bar = Entity(model='cube', color=color.red, scale=(0.5, 0.05, 0.05), parent=self.entity, position=(0, 0.8, 0), origin=(0, 0))
        self.state = SEARCH_WHEAT
        self.target_field = None
        self.target_building = None
        self.wander_target = None
        self.wander_timer = pytime.time()
        self.flee_target = None
        self.flee_timer = 0
        self.hp = 15
        self.max_hp = 15
        self.speed = 2.2
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

    def face_direction(self, direction):
        if direction.length() == 0:
            return
        angle = degrees(atan2(direction.x, direction.z))
        self.entity.rotation_y = angle

    def wander(self):
        if self.wander_target is None or (self.wander_target - self.entity.position).length() < 0.5 or pytime.time() - self.wander_timer > 8:
            self.pick_wander_target()
        direction = (self.wander_target - self.entity.position)
        if direction.length() > 0:
            self.face_direction(direction)
            self.entity.position += direction.normalized() * self.speed * time.dt

    def update(self):
        # Apply gravity
        self.velocity_y -= 9.81 * time.dt
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
        
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

        if self.state == FLEE_PLAYER:
            if self.flee_target is None or pytime.time() - self.flee_timer > 3:
                self.state = SEARCH_WHEAT
                return
            direction = (self.flee_target - self.entity.position)
            if direction.length() > 0.5:
                self.face_direction(direction)
                self.entity.position += direction.normalized() * self.speed * time.dt * 1.2
            else:
                self.state = SEARCH_WHEAT
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
            if ray.hit and ray.entity in [b["entity"] for b in building_system.buildings]:
                self.target_building = next((b for b in building_system.buildings if b["entity"] == ray.entity), None)
                if self.target_building:
                    self.state = ATTACK_OBSTACLE
                    return
            self.face_direction(direction)
            self.entity.position += direction * self.speed * time.dt
            return

        if self.state == ATTACK_OBSTACLE:
            if not self.target_building or self.target_building not in building_system.buildings:
                self.state = MOVE_TO_TARGET
                return
            if pytime.time() - self.last_attack_time >= self.attack_cooldown:
                building_system.damage_building(self.target_building, self.attack_damage)
                self.last_attack_time = pytime.time()
            if self.target_building not in building_system.buildings:
                self.state = MOVE_TO_TARGET
            return

        if self.state == ATTACK_WHEAT:
            if not self.target_field or not self.target_field["rice_planted"] or self.target_field["rice_hp"] <= 0:
                self.state = SEARCH_WHEAT
                return
            target_position = Vec3(self.target_field["pos"].x, self.entity.y, self.target_field["pos"].z)
            distance = (target_position - self.entity.position).length()
            if distance > 1.2:
                self.state = MOVE_TO_TARGET
                return
            direction = (target_position - self.entity.position)
            if direction.length() > 0:
                self.face_direction(direction)
            if pytime.time() - self.last_attack_time >= self.attack_cooldown:
                self.target_field["rice_hp"] -= self.attack_damage
                fields.update_rice_health_bar(self.target_field)
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
            return
        self.state = FLEE_PLAYER
        player_pos = world.player.position
        away = (self.entity.position - player_pos)
        if away.length() == 0:
            away = Vec3(random.uniform(-1, 1), 0, random.uniform(-1, 1))
        self.flee_target = self.entity.position + away.normalized() * 6
        self.flee_timer = pytime.time()

    def die(self):
        self.state = DEAD
        items.spawn_ground_item("fertilizer", self.entity.position + Vec3(0, 0.2, 0))
        destroy(self.entity)
        destroy(self.health_bar)
        if self in enemies:
            enemies.remove(self)
        print(f"Rat died and dropped fertilizer")


def spawn_rat(position):
    load_rat_assets()
    rat = Rat(position)
    texture_choice = random.choice(rat_texture)
    if hasattr(texture_choice, 'width'):
        rat.entity.texture = texture_choice
        rat.entity.color = color.white
    else:
        rat.entity.color = texture_choice
    enemies.append(rat)
    return rat


def update_enemies():
    for enemy in list(enemies):
        enemy.update()

#Chihai
try:
    grasshopper_texture = load_texture('texture/grasshopper_tex.jpg')
    print("Loaded grasshopper texture")
except Exception as e:
    print(f"Failed loading grasshopper texture: {e}")
    grasshopper_texture = color.green 

#chihai quai vat chau chau
class Grasshopper(Rat):
    def __init__(self, position):
        super().__init__(position)

        self.entity.model = 'cube'
        self.entity.color = color.clear 
        self.entity.scale = (0.5, 0.5, 0.5) 
        
        self.mesh = Entity(parent=self.entity)
        
        try:
            self.mesh.model = load_model('model/grasshopper.obj')
        except Exception as e:
            print(f"Không tìm thấy model châu chấu: {e}. Dùng khối vuông thay thế.")
            self.mesh.model = 'cube'
            
        if hasattr(grasshopper_texture, 'width'):
            self.mesh.texture = grasshopper_texture
            self.mesh.color = color.white 
        else:
            self.mesh.texture = None 
            self.mesh.color = grasshopper_texture 
            
        self.mesh.scale = (0.1, 0.1, 0.1) 
     
        self.mesh.y = 3.5
        
        self.hp = 8
        self.max_hp = 8
        self.speed = 4.0 
        self.attack_damage = 2
        
        self.health_bar.color = color.lime

def spawn_grasshopper(position):
    g = Grasshopper(position)
    enemies.append(g)
    return g

#Chihai quai vat tung tung sahur
tex_sahur_path = 'texture/tungtungsahur_tex.png'
sahur_texture = load_texture(tex_sahur_path)

if sahur_texture is None:
    print(f"Không tìm thấy ảnh Sahur tại '{tex_sahur_path}'")
    sahur_texture = color.orange 


class Sahur(Rat):
    def __init__(self, position):
        super().__init__(position)
        
        try:
            self.entity.model = load_model('model/tungtungsahur.fbx') 
        except Exception as e:
            print(f"Không tìm thấy model Sahur: {e}")
            self.entity.model = 'cube'
            
        if hasattr(sahur_texture, 'width'):
            self.entity.texture = sahur_texture
            self.entity.color = color.white 
        else:
            self.entity.texture = None 
            self.entity.color = sahur_texture 
            
        self.entity.scale = (0.003, 0.003, 0.003) 
        self.entity.y = self.entity.scale_y / 2 
        
        self.hp = 35
        self.max_hp = 35
        self.speed = 1.5
        self.attack_damage = 8

def spawn_sahur(position):
    s = Sahur(position)
    enemies.append(s)
    return s