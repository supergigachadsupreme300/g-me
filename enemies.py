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


def find_nearest_wheat_field(position, max_dist=None):
    best = None
    best_dist = None
    for field_data in fields.fields:
        if field_data["wheat_planted"] and field_data["wheat_hp"] > 0:
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
            self.target_field = find_nearest_wheat_field(self.entity.position, DETECTION_RADIUS)
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
            if not self.target_field or not self.target_field["wheat_planted"] or self.target_field["wheat_hp"] <= 0:
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
            if not self.target_field or not self.target_field["wheat_planted"] or self.target_field["wheat_hp"] <= 0:
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
                self.target_field["wheat_hp"] -= self.attack_damage
                fields.update_wheat_health_bar(self.target_field)
                self.last_attack_time = pytime.time()
                if self.target_field["wheat_hp"] <= 0:
                    fields.destroy_wheat(self.target_field)
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
        if self in enemies:
            enemies.remove(self)


def spawn_rat(position):
    load_rat_assets()
    rat = Rat(position)
    enemies.append(rat)
    return rat


def update_enemies():
    for enemy in list(enemies):
        enemy.update()

#Chihai
try:
    grasshopper_texture = load_texture('model/grasshopper/grasshopper_tex.jpg')
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
        self.entity.scale = (0.4, 0.4, 0.4) 
        
        self.mesh = Entity(parent=self.entity)
        
        try:
            self.mesh.model = load_model('model/grasshopper/grasshopper.obj')
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

# Chihai quai vat tung tung sahur
tex_sahur_path = 'model/tungtungsahur/tungtungsahur_tex.png'
sahur_texture = load_texture(tex_sahur_path)

if sahur_texture is None:
    print(f"Không tìm thấy ảnh Sahur tại '{tex_sahur_path}'")
    sahur_texture = color.orange 

class Sahur(Rat):
    def __init__(self, position):
        super().__init__(position)
        
        self.entity = Entity(model='cube', color=color.clear, scale=(1.2, 1.2, 1.2), position=position, collider='box')
        
        self.mesh_run = Entity(parent=self.entity)
        self.mesh_attack = Entity(parent=self.entity)
        
        try:
            self.mesh_run.model = load_model('model/tungtungsahur/tung_tung_sahur_running.glb') 
            self.mesh_attack.model = load_model('model/tungtungsahur/tung_tung_sahur_baseball_hit.glb') 
        except Exception as e:
            print(f"Không load được model GLB Sahur: {e}")
            self.mesh_run.model = 'cube'
            self.mesh_attack.model = 'cube'
            
        for mesh in (self.mesh_run, self.mesh_attack):
            if hasattr(sahur_texture, 'width'):
                mesh.texture = sahur_texture
                mesh.color = color.white 
            else:
                mesh.texture = None 
                mesh.color = sahur_texture 
                
            mesh.setTransparency(0)
            mesh.double_sided = True
            
            mesh.scale = (0.003, 0.003, 0.003) 
            mesh.y = -0.6 
            
        self.mesh_run.enabled = True
        self.mesh_attack.enabled = False
        
        self.hp = 35
        self.max_hp = 35
        self.speed = 1.5
        self.attack_damage = 8
        self.attack_cooldown = 2.0
        self.last_attack_time = 0
        
        self.health_bar.y = 1.2
        self.velocity_y = 0

    def update(self):
        import time as pytime
        from ursina import time
        import world
        import inventory
        
        if self.hp <= 0:
            return
            
        self.velocity_y -= 18.0 * time.dt 
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
            
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.0:
            self.mesh_run.enabled = True
            self.mesh_attack.enabled = False
            
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            self.mesh_run.enabled = False
            self.mesh_attack.enabled = True
            
            if pytime.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime.time()
                
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị Tung Tung Sahur nện! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_sahur(position):
    s = Sahur(position)
    enemies.append(s)
    return s

#Chihai quai vat soi
tex_wolf_path = 'model/werewolf/lambert1_albedo.jpg' 
wolf_texture = load_texture(tex_wolf_path)

if wolf_texture is None:
    print(f"Không tìm thấy ảnh Sói tại '{tex_wolf_path}'")
    wolf_texture = color.gray 

class Wolf(Rat):
    def __init__(self, position):
        super().__init__(position)
        
        self.entity.model = 'cube'
        self.entity.color = color.clear
        self.entity.texture = None
        self.entity.scale = (0.8, 0.8, 0.8) 

        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/werewolf/Animation_Werewolf_Idle_Beta_02.fbx')
        except Exception as e:
            print(f"Không tìm thấy model Sói: {e}. Dùng khối vuông thay thế.")
            self.mesh.model = 'cube'
            
        if hasattr(wolf_texture, 'width'):
            self.mesh.texture = wolf_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = wolf_texture
            
        self.mesh.scale = (0.02, 0.02, 0.02) 
        self.mesh.y = -0.5
        
        self.hp = 20
        self.max_hp = 20
        self.speed = 3.5
        self.attack_damage = 5
        
        self.health_bar.y = 1.2
        self.health_bar.color = color.blue

def spawn_wolf(position):
    w = Wolf(position)
    enemies.append(w)
    return w

#Chihai quai vat kẻ trộm và cẩu tặc
try:
    thief_texture = load_texture('model/thief/tenant texture.png')
except Exception as e:
    thief_texture = color.black

try:
    dogthief_texture = load_texture('model/thief/tenant texture.png')
except Exception as e:
    dogthief_texture = color.rgb(50, 50, 50)

class Thief:
    def __init__(self, position):
        self.entity = Entity(model='cube', color=color.clear, scale=(0.8, 1.8, 0.8), position=position, collider='box')
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/thief/Ready Tower Tenant walk.fbx')
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(thief_texture, 'width'):
            self.mesh.texture = thief_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = thief_texture
            
        self.mesh.scale = (0.02, 0.02, 0.01)
        self.mesh.y = -0.6
        
        self.hp = 30
        self.max_hp = 30
        self.speed = 3.5
        self.attack_damage = 5 
        self.last_attack_time = 0
        self.health_bar = Entity(parent=self.entity, y=1.2, model='cube', color=color.red, scale=(1, 0.1, 0.1))

    def take_damage(self, amount):
        self.hp -= amount
        self.health_bar.scale_x = max(0, self.hp / self.max_hp)
        if self.hp <= 0:
            self.die()

    def die(self):
        if self in enemies:
            enemies.remove(self)
        destroy(self.entity)

    def update(self):
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.5:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.entity.look_at(player_pos)
        else:
            if pytime.time() - self.last_attack_time > 1.5:
                self.last_attack_time = pytime.time()
                import game, inventory
                if game.player_money >= self.attack_damage:
                    game.player_money -= self.attack_damage
                    inventory.show_message(f"Bị ĂN TRỘM mất {self.attack_damage} Gold! Còn {game.player_money} Gold", 2)
                else:
                    game.player_money = 0
                    inventory.show_message("Ăn trộm: Ngươi cạn tiền rồi!", 2)

def spawn_thief(position):
    t = Thief(position)
    enemies.append(t)
    return t


class DogThief(Thief):
    def __init__(self, position):
        super().__init__(position) 
        self.speed = 4.0 
        
        if hasattr(dogthief_texture, 'width'):
            self.mesh.texture = dogthief_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = dogthief_texture
            
        
    def update(self):
        import pet 
        target_dog = None
        min_dist = float('inf')
        
        for p in pet.pets:
            if p.__class__.__name__ == 'Dog':
                dist = (self.entity.position - p.entity.position).length()
                if dist < min_dist:
                    min_dist = dist
                    target_dog = p
                    
        if target_dog:
            if min_dist > 2.5:
                direction = (target_dog.entity.position - self.entity.position).normalized()
                self.entity.position += direction * self.speed * time.dt
                self.entity.look_at(target_dog.entity.position)
            else:
                if pytime.time() - self.last_attack_time > 1.5:
                    self.last_attack_time = pytime.time()
                    target_dog.take_damage(25) 
                    import inventory
                    inventory.show_message("CẨU TẶC đang ăn trộm chó của bạn!", 1.5)
        else:
            super().update()

def spawn_dog_thief(position):
    dt = DogThief(position)
    enemies.append(dt)
    return dt

#Chihai quai vat lua
try:
    arrogant_wheat_texture = load_texture('model/wheat/WheatTEX.png')
except Exception as e:
    arrogant_wheat_texture = color.rgb(255, 200, 0) 

class ArrogantWheat(Rat):
    def __init__(self, position):
        super().__init__(position) 
        
        self.entity.model = 'cube'
        self.entity.color = color.clear
        self.entity.scale = (0.6, 2.0, 0.6) 
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/wheat/WHEAT_spin.fbx')
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(arrogant_wheat_texture, 'width'):
            self.mesh.texture = arrogant_wheat_texture
            self.mesh.color = color.white 
        else:
            self.mesh.texture = None
            self.mesh.color = arrogant_wheat_texture
            
        self.mesh.setTransparency(0)   
        self.mesh.alpha = 1            
        self.mesh.double_sided = True  
        
        self.mesh.scale = (0.03, 0.03, 0.03) 
        self.mesh.y = -0.7
        
        self.hp = 40
        self.max_hp = 40
        self.speed = 4.0 
        self.attack_damage = 8
        self.attack_cooldown = 1.5 
        self.last_attack_time = 0
        
        self.health_bar.y = 1.3
        self.health_bar.color = color.magenta 
        self.velocity_y = 0 

    def die(self):
        import items
        items.spawn_ground_item("seed", self.entity.position + Vec3(0, 0.5, 0))
        items.spawn_ground_item("wheat", self.entity.position + Vec3(0, 0.5, 0.5))
        super().die()

    def update(self):
        import time as pytime
        from ursina import time
        import world
        import inventory
        
        if self.hp <= 0:
            return
            
        self.velocity_y -= 18.0 * time.dt 
        self.entity.y += self.velocity_y * time.dt
        
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
            
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.5:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            if pytime.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime.time()
                self.velocity_y = 7.0 
                
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị LÚA KIÊU NGẠO đập trúng! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_arrogant_wheat(position):
    aw = ArrogantWheat(position)
    enemies.append(aw)
    return aw

#Chihai quai vat zombie
try:
    zombie_texture = load_texture('model/zombie/Disco.png')
except Exception as e:
    zombie_texture = color.green

class Zombie(Rat):
    def __init__(self, position):
        super().__init__(position) 
        
        self.entity.model = 'cube'
        self.entity.color = color.clear
        self.entity.scale = (0.8, 1.8, 0.8) 
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/zombie/Disco.fbx')
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(zombie_texture, 'width'):
            self.mesh.texture = zombie_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = zombie_texture
            
        self.mesh.setTransparency(0)   
        self.mesh.alpha = 1            
        self.mesh.double_sided = True  
        
        self.mesh.scale = (0.8, 0.8, 0.8) 
        self.mesh.y = -0.33
        
        self.hp = 50
        self.max_hp = 50
        self.speed = 1.8 
        self.attack_damage = 12
        self.attack_cooldown = 2.0 
        self.last_attack_time = 0
        
        self.health_bar.y = 1.2
        self.health_bar.color = color.dark_gray 
        self.velocity_y = 0 

    def update(self):
        import time as pytime
        from ursina import time
        import world
        import inventory
        
        if self.hp <= 0:
            return
            
        self.velocity_y -= 18.0 * time.dt 
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
            
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.0:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            if pytime.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime.time()
                
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị ZOMBIE cắn! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_zombie(position):
    z = Zombie(position)
    enemies.append(z)
    return z

#Chihai quai vat khung long
try:
    dino_texture = load_texture('model/dinosaur/T Rex - Battling.png')
except Exception as e:
    dino_texture = color.rgb(50, 100, 40) 
class Dinosaur(Rat):
    def __init__(self, position):
        super().__init__(position) 
        
        self.entity.model = 'cube'
        self.entity.color = color.clear
        self.entity.scale = (2.5, 4.0, 5.0) 
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/dinosaur/TrexHigh.fbx')
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(dino_texture, 'width'):
            self.mesh.texture = dino_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = dino_texture
            
        self.mesh.setTransparency(0)   
        self.mesh.alpha = 1            
        self.mesh.double_sided = True  
        
        self.mesh.scale = (0.008, 0.008, 0.008) 
        self.mesh.y = -0.53
        
        self.hp = 200
        self.max_hp = 200
        self.speed = 2.5 
        self.attack_damage = 25 
        self.attack_cooldown = 2.5 
        self.last_attack_time = 0
        
        self.health_bar.y = 2.2
        self.health_bar.scale_x = 1.5 
        self.health_bar.color = color.red 
        self.velocity_y = 0 

    def update(self):
        import time as pytime
        from ursina import time
        import world
        import inventory
        
        if self.hp <= 0:
            return

        self.velocity_y -= 18.0 * time.dt 
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
            
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 4.0:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            if pytime.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime.time()
                
                world.player.hp -= self.attack_damage
                inventory.show_message(f"⚠️ Khủng long T-REX cắn! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_dinosaur(position):
    d = Dinosaur(position)
    enemies.append(d)
    return d

#Chihai quai vat nam
try:
    mushroom_texture = load_texture('model/monsterMushroom/GribUV_lambert3_BaseColor.png')
except Exception as e:
    mushroom_texture = color.purple

class MushroomMonster(Rat):
    def __init__(self, position):
        super().__init__(position) 
        
        self.entity.model = 'cube'
        self.entity.color = color.clear
        self.entity.scale = (0.5, 0.8, 0.5) 
        
        # 2. Lớp vỏ hiển thị 3D
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/monsterMushroom/GribRiggedReady.fbx')
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(mushroom_texture, 'width'):
            self.mesh.texture = mushroom_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = mushroom_texture
            
        self.mesh.setTransparency(0)   
        self.mesh.alpha = 1            
        self.mesh.double_sided = True  
        
        self.mesh.scale = (0.8, 0.8, 0.8) 
        self.mesh.y = -0.4 
        
        self.hp = 30
        self.max_hp = 30
        self.speed = 1.5 
        self.attack_damage = 10
        self.attack_cooldown = 1.5 
        self.last_attack_time = 0
        
        self.health_bar.y = 1.0
        self.health_bar.color = color.magenta 
        self.velocity_y = 0 

    def update(self):
        import time as pytime
        from ursina import time
        import world
        import inventory
        
        if self.hp <= 0:
            return
            
        self.velocity_y -= 18.0 * time.dt 
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0
            
        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.0:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            if pytime.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime.time()
                
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị trúng BÀO TỬ ĐỘC của Nấm! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_mushroom(position):
    m = MushroomMonster(position)
    enemies.append(m)
    return m