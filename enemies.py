import importlib.util
from ursina import Entity, Text, color, Vec3, raycast, destroy, load_model, load_texture, time, camera
from math import atan2, degrees
from direct.actor.Actor import Actor
import time as pytime
from panda3d.core import TextureStage
import random
import world
import fields
import building_system
import items
import sound_manager
import stats

class BossHUD(Entity):
    def __init__(self):
        # Gắn vào camera.ui để nó không di chuyển theo camera
        super().__init__(parent=camera.ui, enabled=False)
        
        # Nền đen cho thanh máu
        self.bg = Entity(parent=self, model='quad', color=color.black66, 
                         scale=(0.8, 0.04), position=(0, 0.45))
        
        # Thanh máu chính (Màu tím/hồng giống Minecraft)
        self.bar = Entity(parent=self, model='quad', color=color.magenta, 
                          scale=(0.78, 0.03), position=(0, 0.45), z=-0.01)
        
        # Tên Boss hiện phía trên thanh máu
        self.name_text = Text(parent=self, text="BOSS", origin=(0,0), 
                              y=0.48, scale=1.5, color=color.white)

    def update_bar(self, name, hp, max_hp):
        self.name_text.text = name
        # Cập nhật độ dài thanh máu (scale_x nhân với độ dài gốc 0.78)
        self.bar.scale_x = max(0, (hp / max_hp) * 0.78)
        self.enabled = True

# Khởi tạo một cái dùng chung cho cả game
global_boss_hud = None

def update(self):
        # ... (các logic trọng lực cũ) ...

        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()

        # HIỂN THỊ BOSS BAR KHI Ở GẦN (Ví dụ trong vòng 15 mét)
        if dist < 15 and self.hp > 0:
            global_boss_hud.update_bar(self.__class__.__name__, self.hp, self.max_hp)
            # Bạn có thể đổi màu tùy quái vật
            if isinstance(self, Wolf):
                global_boss_hud.bar.color = color.red
            else:
                global_boss_hud.bar.color = color.magenta
        elif dist >= 15:
            # Nếu người chơi chạy xa, tắt thanh boss đi
            global_boss_hud.enabled = False

        # ... (logic rượt đuổi/tấn công cũ) ...

def die(self):
        global_boss_hud.enabled = False # Tắt thanh máu khi boss chết
        super().die()

rat_texture = []
rat_model = None


def load_rat_assets():
    global rat_texture, rat_model
    if rat_model is not None and rat_texture:
        return

    for path in ['model/rat/texture/rat_grey.png', 'model/rat/texture/rat_khaki.png', 'model/rat/texture/rat_bege_psd.png']:
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
        rat_model = load_model('model/rat/source/rat.fbx')
        if not rat_model:
            raise ValueError('rat.fbx loaded but returned no model')
        print('Loaded rat model: model/rat/source/rat.fbx')
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
    # Thêm các tham số mặc định để khi các con khác kế thừa dễ dàng đổi tên và máu
    def __init__(self, position, name="Chuột", max_hp=15, ui_height=2.0, speed=2.2, attack_damage=4):
        load_rat_assets()
        position = Vec3(position.x, 0.0, position.z)
        
        # CHỈNH SỬA: Tách riêng phần Entity gốc để chứa mô hình
        # Đây là khối hộp tàng hình dùng để va chạm (hitbox)
        self.entity = Entity(model='cube', color=color.clear, position=position, scale=(0.8, 0.8, 0.8), collider='box')
        self.entity.y = self.entity.scale_y / 2 + 0.05
        
        # Phần hiển thị mô hình con chuột
        self.mesh = Entity(parent=self.entity, double_sided=True)
        texture_choice = random.choice(rat_texture)
        
        if rat_model not in (None, 'cube'):
            self.mesh.model = rat_model
            self.mesh.scale = (0.1, 0.1, 0.1) # Tỷ lệ mô hình chuột
            self.mesh.rotation_y = 180
            if hasattr(texture_choice, 'width'):
                self.mesh.texture = texture_choice
                self.mesh.color = color.white
            else:
                self.mesh.color = texture_choice
        else:
            self.mesh.model = 'cube'
            if hasattr(texture_choice, 'width'):
                self.mesh.texture = texture_choice
                self.mesh.color = color.white
            else:
                self.mesh.color = texture_choice

        self.velocity_y = 0
        
        # Các chỉ số sinh tồn và chiến đấu (lấy từ tham số truyền vào)
        self.hp = max_hp
        self.max_hp = max_hp
        self.speed = speed
        self.attack_damage = attack_damage
        self.attack_cooldown = 1.0
        self.last_attack_time = 0
        
        # ==========================================
        # GIAO DIỆN CHUNG CHO MỌI QUÁI VẬT (UI)
        # ==========================================
        
        # 1. Thanh máu xanh lá
        self.health_bar = Entity(parent=self.entity, model='cube', color=color.green, 
                                 y=ui_height, z=1.5, scale=(3, 0.2, 1))
        
        # 2. Số lượng máu
        self.hp_text = Text(parent=self.entity, text=f"{self.hp}/{self.max_hp}",
                            y=ui_height, z=1.4, scale=10, billboard=True, origin=(0, 0), color=color.red)
        
        # 3. Nền đen cho Tên
        self.name_bg = Entity(parent=self.entity, model='cube', color=color.black, 
                              y=ui_height + 0.5, z=1.5, scale=(4.0, 0.3, 1))
        
        # 4. Chữ hiển thị tên
        self.name_text = Text(parent=self.entity, text=name, 
                              y=ui_height + 0.5, z=1.4, scale=20, billboard=True, origin=(0, 0), color=color.yellow)
        
        # ==========================================
        # LOGIC AI (Giữ nguyên của bạn)
        # ==========================================
        self.state = SEARCH_WHEAT
        self.target_field = None
        self.target_building = None
        self.wander_target = None
        self.wander_timer = pytime.time()
        self.flee_target = None
        self.flee_timer = 0
        self.sub_entities = [self.entity, self.mesh]
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
        
        self.health_bar.scale_x = max(0, self.hp / self.max_hp) * 3
        
        if hasattr(self, 'hp_text'):
            self.hp_text.text = f"{int(self.hp)}/{self.max_hp}"

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
        
        if hasattr(self, 'hp_text'): destroy(self.hp_text)
        if hasattr(self, 'name_text'): destroy(self.name_text)
        if hasattr(self, 'name_bg'): destroy(self.name_bg)
        
        try:
            loot_choices = ["seed", "peashooter seed", "fertilizer", "ammo"]
            dropped = random.choice(loot_choices)
            items.spawn_ground_item(dropped, self.entity.position + Vec3(0, 0.2, 0))
        except Exception:
            try:
                items.spawn_ground_item("fertilizer", self.entity.position + Vec3(0, 0.2, 0))
            except Exception:
                pass
        try:
            sound_manager.play('pop')
        except Exception:
            pass
        try:
            stats.record_enemy_kill(self.__class__.__name__)
        except Exception:
            pass
            
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

#quai vat chau chau
try:
    grasshopper_texture = load_texture('model/grasshopper/texture/grasshopper_tex.jpg')
    print("Loaded grasshopper texture")
except Exception as e:
    print(f"Failed loading grasshopper texture: {e}")
    grasshopper_texture = color.green 

class Grasshopper(Rat):
    def __init__(self, position):
        super().__init__(position, name="Châu Chấu", max_hp=8, ui_height=6.5, speed=4.0, attack_damage=2)

        self.entity.scale = (0.4, 0.4, 0.4) 
        
        try:
            self.mesh.model = load_model('model/grasshopper/source/grasshopper.obj')
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
        self.mesh.y = 3
        self.mesh.rotation_y = 90

    def take_damage(self, amount):
        self.hp -= amount
        
        self.health_bar.scale_x = max(0, self.hp / self.max_hp) * 3
        
        if hasattr(self, 'hp_text'):
            self.hp_text.text = f"{int(self.hp)}/{self.max_hp}"

        if self.hp <= 0:
            self.die()

    def update(self):
        import time as pytime_mod
        from ursina import time
        import world
        import inventory

        if self.hp <= 0 or self.state == 'DEAD': # Biến 'DEAD' kế thừa từ Rat
            return

        self.velocity_y -= 9.81 * time.dt
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0

        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        direction = (player_pos - self.entity.position)

        if direction.length() > 0:
            self.face_direction(direction)

        if dist > 1.5:
            self.entity.position += direction.normalized() * self.speed * time.dt
        else:
            if pytime_mod.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime_mod.time()
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị Châu chấu cắn! HP: {world.player.hp}/100", 2)

def spawn_grasshopper(position):
    g = Grasshopper(position)
    enemies.append(g)
    return g

#quai vat tung tung sahur
tex_sahur_path = 'model/tungtungsahur/shaded.png'
sahur_texture = load_texture(tex_sahur_path)

if sahur_texture is None:
    print(f"\033[91m[CẢNH BÁO] KHÔNG TÌM THẤY ẢNH TẠI: {tex_sahur_path}\033[0m")

def _sahur_apply_tex(actor):
    if sahur_texture is None or not hasattr(sahur_texture, '_texture'):
        return
    try:
        actor.setTexture(sahur_texture._texture, 1)
        for geom in actor.findAllMatches('**/+GeomNode'):
            geom.setTexture(sahur_texture._texture, 1)
    except Exception as e:
        print(f"[LỖI DÁN ẢNH] {e}")

class Sahur(Rat):
    def __init__(self, position):
        super().__init__(position, name="Tung Tung Sahur", max_hp=35, ui_height=3.2, speed=1.5, attack_damage=8)
        
        destroy(self.mesh)
        
        global global_boss_hud
        if global_boss_hud is None:
            global_boss_hud = BossHUD()

        self.health_bar.enabled = False 
        self.hp_text.enabled = False
        
        self.entity.scale = (1.2, 1.2, 1.2)
        self.visual = Entity(scale=(1, 1, 1))
        self.actor = None
        try:
            self.actor = Actor(
                'model/tungtungsahur/tungtungsahur_run.glb', 
                {
                    'run': 'model/tungtungsahur/tungtungsahur_run.glb',
                    'attack': 'model/tungtungsahur/tungtungsahur_hit.glb'
                }
            )
            self.actor.reparent_to(self.visual)
            self.actor.setHpr(180, 0, 0)
            self.actor.setScale(0.3, 0.3, 0.3)
            self.actor.loop('run')
            self._anim = 'run'
            
        except Exception as e:
            print(f"[LỖI LOAD GLB] {e}")
            self.visual.model = 'cube'
            self.visual.color = color.red
            self.visual.scale = (2, 2, 2) 
            self._anim = None

    def _switch(self, state):
        if self._anim == state or self.actor is None:
            return
        self._anim = state
        self.actor.loop(state) 
        if state == 'attack':
            try:
                sound_manager.play('bonk')
            except Exception:
                pass

    def take_damage(self, amount):
        self.hp -= amount
        
        global global_boss_hud
        if global_boss_hud is not None and global_boss_hud.enabled:
            global_boss_hud.update_bar("TUNG TUNG SAHUR", self.hp, self.max_hp)

        if self.hp <= 0:
            self.die()

    def die(self):
        global global_boss_hud
        if global_boss_hud is not None:
            global_boss_hud.enabled = False
            
        destroy(self.visual)
        if self.actor:
            try:
                self.actor.cleanup()
                self.actor.removeNode()
            except Exception:
                pass
                
        super().die()

    def update(self):
        import time as pytime_mod
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
        direction = (player_pos - self.entity.position).normalized()

        global global_boss_hud
        if dist < 20: 
            global_boss_hud.update_bar("TUNG TUNG SAHUR", self.hp, self.max_hp)
            global_boss_hud.bar.color = color.magenta 
            global_boss_hud.enabled = True
        else:
            if global_boss_hud.enabled and global_boss_hud.name_text.text == "TUNG TUNG SAHUR":
                global_boss_hud.enabled = False

        if dist > 2.0:
            self._switch('run')
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            self._switch('attack')
            self.face_direction(direction)
            if pytime_mod.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime_mod.time()
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị Tung Tung Sahur nện! HP: {world.player.hp}/100", 2)

        self.visual.position = self.entity.position + Vec3(0, -0.6, 0)
        self.visual.rotation = self.entity.rotation

def spawn_sahur(position):
    s = Sahur(position)
    enemies.append(s)
    return s

#quai vat soi
try:
    wolf_texture = load_texture('model/werewolf/lambert1_albedo.jpg')
except Exception as e:
    wolf_texture = color.gray

class Wolf(Rat):
    def __init__(self, position):
        super().__init__(position, name="Werewolf", max_hp=20, ui_height=4.0, speed=3.5, attack_damage=5)
        
        destroy(self.mesh)
        
        global global_boss_hud
        if global_boss_hud is None:
            global_boss_hud = BossHUD()

        self.health_bar.enabled = False 
        self.hp_text.enabled = False
        
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
        
        self.attack_cooldown = 1.5 

    def take_damage(self, amount):
        self.hp -= amount
        
        global global_boss_hud
        if global_boss_hud is not None and global_boss_hud.enabled:
            global_boss_hud.update_bar("WEREWOLF", self.hp, self.max_hp)

        if self.hp <= 0:
            self.die()

    def die(self):
        global global_boss_hud
        if global_boss_hud is not None:
            global_boss_hud.enabled = False
            
        super().die()

    def update(self):
        import time as pytime_mod
        from ursina import time
        import world
        import inventory

        if self.hp <= 0:
            return

        self.velocity_y -= 9.81 * time.dt
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0

        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        direction = (player_pos - self.entity.position)

        global global_boss_hud
        if dist < 20: 
            global_boss_hud.update_bar("WEREWOLF", self.hp, self.max_hp)
            global_boss_hud.bar.color = color.red # Màu đỏ máu cho Sói
            global_boss_hud.enabled = True
        else:
            if global_boss_hud.enabled and global_boss_hud.name_text.text == "WEREWOLF":
                global_boss_hud.enabled = False

        if direction.length() > 0:
            self.face_direction(direction)

        if dist > 2.0:
            self.entity.position += direction.normalized() * self.speed * time.dt
        else:
            if pytime_mod.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime_mod.time()
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bạn đã bị người sói cắn! HP: {world.player.hp}/100", 2)

def spawn_wolf(position):
    w = Wolf(position)
    enemies.append(w)
    return w

#an trom
try:
    thief_texture = load_texture('model/thief/tenant texture.png')
except Exception as e:
    thief_texture = color.black

try:
    dogthief_texture = load_texture('model/thief/tenant texture.png')
except Exception as e:
    dogthief_texture = color.rgb(50, 50, 50)

class Thief(Rat):
    def __init__(self, position):
  
        super().__init__(position, name="Ăn Trộm", max_hp=30, ui_height=2.2, speed=3.5, attack_damage=5)
        
        self.entity.scale = (0.8, 1.3, 0.8)
        
        try:
            self.mesh.model = load_model('model/thief/Ready Tower Tenant walk.fbx')
        except Exception:
            self.mesh.model = 'cube'
            
        if hasattr(thief_texture, 'width'):
            self.mesh.texture = thief_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = thief_texture
            
        self.mesh.scale = (0.02, 0.02, 0.01)
        self.mesh.y = -0.6
        self.mesh.rotation_y = 0 
    
    def update(self):
        import time as pytime_mod
        from ursina import time, Vec3
        import world
        
        if self.hp <= 0 or self.state == DEAD:
            return
            
        self.velocity_y -= 9.81 * time.dt
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0

        player_pos = world.player.position
        dist = (self.entity.position - player_pos).length()
        
        if dist > 2.5:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt

            target_pos = Vec3(player_pos.x, self.entity.y, player_pos.z)
            self.entity.look_at(target_pos)
        else:
            if pytime_mod.time() - self.last_attack_time > 1.5:
                self.last_attack_time = pytime_mod.time()
                import inventory
                if world.player is not None and world.player.money >= self.attack_damage:
                    world.player.money -= self.attack_damage
                    inventory.show_message(f"Bị ĂN TRỘM mất {self.attack_damage} Gold! Còn {world.player.money} Gold", 2)
                elif world.player is not None:
                    world.player.money = 0
                    inventory.show_message("Ăn trộm: Ngươi cạn tiền rồi!", 2)
def spawn_thief(position):
    t = Thief(position)
    enemies.append(t)
    return t

#cau tac
class DogThief(Thief):
    def __init__(self, position):
        super().__init__(position) 
        
        self.speed = 4.0 
        
        if hasattr(self, 'name_text'):
            self.name_text.text = "Cẩu Tặc"
            self.name_text.color = color.red 
        
        if hasattr(dogthief_texture, 'width'):
            self.mesh.texture = dogthief_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = dogthief_texture
            
    def update(self):
        import time as pytime_mod
        from ursina import time, Vec3
        import world
        import pet 

        if self.hp <= 0 or getattr(self, 'state', '') == 'DEAD':
            return

        self.velocity_y -= 9.81 * time.dt
        self.entity.y += self.velocity_y * time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2
            self.velocity_y = 0

        target_dog = None
        min_dist = float('inf')
        
        for p in pet.pets:
            if p.__class__.__name__ == 'Dog' and getattr(p, 'hp', 1) > 0:
                dist = (self.entity.position - p.entity.position).length()
                if dist < min_dist:
                    min_dist = dist
                    target_dog = p
                    
        if target_dog:
            if min_dist > 2.5:
                direction = (target_dog.entity.position - self.entity.position).normalized()
                self.entity.position += direction * self.speed * time.dt
                
                target_pos = Vec3(target_dog.entity.position.x, self.entity.y, target_dog.entity.position.z)
                self.entity.look_at(target_pos)
            else:
                if pytime_mod.time() - self.last_attack_time > 1.5:
                    self.last_attack_time = pytime_mod.time()
                    target_dog.take_damage(25) 
                    import inventory
                    inventory.show_message("CẨU TẶC đang bắt chó của bạn!", 1.5)
        else:
            player_pos = world.player.position
            player_dist = (self.entity.position - player_pos).length()
            
            if player_dist > 2.5:
                direction = (player_pos - self.entity.position).normalized()
                self.entity.position += direction * self.speed * time.dt
                
                target_pos = Vec3(player_pos.x, self.entity.y, player_pos.z)
                self.entity.look_at(target_pos)
            else:
                if pytime_mod.time() - self.last_attack_time > 1.5:
                    self.last_attack_time = pytime_mod.time()
                    import inventory
                    if world.player is not None and world.player.money >= self.attack_damage:
                        world.player.money -= self.attack_damage
                        inventory.show_message(f"Bị CẨU TẶC giật mất {self.attack_damage} Gold!", 2)
                    elif world.player is not None:
                        world.player.money = 0
                        inventory.show_message("Cẩu tặc: Không có chó, lại còn nghèo!", 2)

def spawn_dog_thief(position):
    dt = DogThief(position)
    enemies.append(dt)
    return dt

#boss nam doc
try:
    mushroom_texture = load_texture('model/monsterMushroom/GribUV_lambert3_BaseColor.png')
except Exception as e:
    mushroom_texture = color.purple

class MushroomMonster(Rat):
    def __init__(self, position):
        super().__init__(position, name="Quái Vật Nấm", max_hp=30, ui_height=4.5, speed=1.5, attack_damage=10) 
        
        destroy(self.mesh)

        global global_boss_hud
        if global_boss_hud is None:
            global_boss_hud = BossHUD()

        self.health_bar.enabled = False 
        self.hp_text.enabled = False
        if hasattr(self, 'name_text'):
            self.name_text.color = color.magenta 
        
        self.entity.scale = (0.5, 0.8, 0.5) 
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
        self.mesh.scale = (0.6, 0.6, 0.6) 
        self.mesh.y = -0.4 
        
        self.attack_cooldown = 1.5 

    def take_damage(self, amount):
        self.hp -= amount
        
        global global_boss_hud
        if global_boss_hud is not None and global_boss_hud.enabled:
            global_boss_hud.update_bar("QUÁI VẬT NẤM", self.hp, self.max_hp)

        if self.hp <= 0:
            self.die()

    def die(self):
        global global_boss_hud
        if global_boss_hud is not None:
            global_boss_hud.enabled = False
            
        super().die() 

    def update(self):
        import time as pytime_mod
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
        
        global global_boss_hud
        if dist < 20:
            global_boss_hud.update_bar("QUÁI VẬT NẤM", self.hp, self.max_hp)
            global_boss_hud.bar.color = color.magenta 
            global_boss_hud.enabled = True
        else:
            if global_boss_hud.enabled and global_boss_hud.name_text.text == "QUÁI VẬT NẤM":
                global_boss_hud.enabled = False

        if dist > 2.0:
            direction = (player_pos - self.entity.position).normalized()
            self.entity.position += direction * self.speed * time.dt
            self.face_direction(direction)
        else:
            direction = (player_pos - self.entity.position).normalized()
            self.face_direction(direction)
            if pytime_mod.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = pytime_mod.time()
                world.player.hp -= self.attack_damage
                inventory.show_message(f"Bị trúng BÀO TỬ ĐỘC của Nấm! HP: {world.player.hp}/100", 2)

def spawn_mushroom(position):
    m = MushroomMonster(position)
    enemies.append(m)
    return m

#boss khung long
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
        
        self.mesh.scale = (0.005, 0.005, 0.005) 
        self.mesh.y = -0.5 
        
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
                inventory.show_message(f"Khủng long T-REX cắn! HP: {world.player.hp}/100", 2)
                
                direction = (player_pos - self.entity.position).normalized()
                self.face_direction(direction)

def spawn_dinosaur(position):
    d = Dinosaur(position)
    enemies.append(d)
    return d

#quai vat lua
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
        
        self.mesh.scale = (0.023, 0.023, 0.023) 
        self.mesh.y = -0.5
        
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

#quai vat zombie
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
        
        self.mesh.scale = (0.5, 0.5, 0.5) 
        self.mesh.y = -0.2
        
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