from ursina import Entity, color, destroy, load_model, load_texture, Vec3, Text, mouse
from ursina import time as ursina_time 
import time as pytime
import world
import inventory
import items
import fields
import tools
import enemies

pets = []

def update_pets():
    for pet in list(pets):
        if hasattr(pet, 'update'):
            try:
                pet.update()
            except Exception as e:
                print(f"Lỗi khi cập nhật hành động Pet: {e}")

#pet
class BasePet:
    def __init__(self, position, name="Pet", hp=0, speed=3.0, scale=(0.8, 0.8, 0.8)):
        self.entity = Entity(model='cube', color=color.clear, scale=scale, position=position, collider='box')
        self.mesh = Entity(parent=self.entity)
        
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        
        if self.hp > 0:
            self.health_bar = Entity(parent=self.entity, y=1.2, model='cube', color=color.green, scale=(1, 0.1, 0.1))
        else:
            self.health_bar = None

    def take_damage(self, amount):
        if self.hp <= 0: return
        self.hp -= amount
        if self.health_bar:
            self.health_bar.scale_x = max(0, self.hp / self.max_hp)
        if self.hp <= 0:
            self.die()

    def die(self):
        inventory.show_message(f"{self.name} đã bị hạ gục / bắt trộm!", 3)
        if self in pets:
            pets.remove(self)
        destroy(self.entity)

    def apply_gravity(self):
        self.entity.y -= 9.81 * ursina_time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2

    def follow_player(self, follow_distance=5):
        if world.player:
            player_pos = world.player.position
            dist = (self.entity.position - player_pos).length()
            if dist > follow_distance:
                direction = (player_pos - self.entity.position).normalized()
                self.entity.position += direction * (self.speed * 0.8) * ursina_time.dt
                target_look = Vec3(player_pos.x, self.entity.y, player_pos.z)
                self.entity.look_at(target_look)

#coc
try:
    toad_texture = load_texture('model/toad/MAT_Animal_Amphibian_Toad2_0_basecolor.jpg') 
    toad_texture = load_texture('model/toad/MAT_Animal_Amphibian_Toad2_0_basecolor.jpeg') 
except Exception:
    toad_texture = color.green

class Toad(BasePet):
    def __init__(self, position):   
        super().__init__(position, name="Cóc", hp=0, speed=2.0, scale=(0.3, 0.2, 0.3))
        
        try:
            self.mesh.model = load_model('model/toad/mesh.fbx')
        except Exception:
            self.mesh.model = 'cube'
            
        if hasattr(toad_texture, 'width'):
            self.mesh.texture = toad_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = toad_texture

        self.mesh.setTransparency(0)   
        self.mesh.alpha = 1           
        self.mesh.double_sided = True
        self.mesh.scale = (30, 30, 30) 
        self.mesh.y = -0.1
        
        self.attack_range = 2.0
        self.last_attack_time = 0
        
    def update(self):
        self.apply_gravity()
        
        target = None
        min_dist = float('inf')
        
        if hasattr(enemies, 'enemies') and enemies.enemies:
            for e in enemies.enemies:
                if e.__class__.__name__ == 'Grasshopper':
                    dist = (self.entity.position - e.entity.position).length()
                    if dist < min_dist:
                        min_dist = dist
                        target = e
        
        if target and min_dist < 15:
            if min_dist > self.attack_range:
                direction = (target.entity.position - self.entity.position).normalized()
                self.entity.position += direction * self.speed * ursina_time.dt
                self.entity.look_at(target.entity.position)
            else:
                if pytime.time() - self.last_attack_time > 1.0:
                    target.take_damage(999) 
                    self.last_attack_time = pytime.time()
                    inventory.show_message("Cóc đã xơi tái một con Châu Chấu!", 2)
        else:
            self.follow_player(follow_distance=5)

def spawn_toad(position):
    t = Toad(position)
    pets.append(t)
    return t

#cho
try:
    dog_texture = load_texture('model/dog/AM83_037_color_01.jpg') 
except Exception:
    dog_texture = color.orange

class Dog(BasePet):
    def __init__(self, position):
        super().__init__(position, name="Chó cưng", hp=100, speed=5.0, scale=(0.8, 0.8, 0.8))
        
        try:
            self.mesh.model = load_model('model/dog/пес.fbx') 
        except Exception:
            self.mesh.model = 'cube'
            
        if hasattr(dog_texture, 'width'):
            self.mesh.texture = dog_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = dog_texture
            
        self.mesh.scale = (0.05, 0.05, 0.05)
        self.mesh.y = -0.4 
        
        self.attack_range = 2.5
        self.attack_damage = 3
        self.last_attack_time = 0

    def update(self):
        if self.hp <= 0: return
        self.apply_gravity()
        
        target = None
        min_dist = float('inf')

        if hasattr(enemies, 'enemies') and enemies.enemies:
            for e in enemies.enemies:
                if e and hasattr(e, 'entity') and getattr(e, 'hp', 0) > 0:
                    dist = (self.entity.position - e.entity.position).length()
                    if dist < min_dist:
                        min_dist = dist
                        target = e
        
        if target and min_dist < 15: 
            if min_dist > self.attack_range:
                direction = (target.entity.position - self.entity.position).normalized()
                self.entity.position += direction * self.speed * ursina_time.dt
                self.entity.look_at(target.entity.position)
            else:
                if pytime.time() - self.last_attack_time > 1.0:
                    target.take_damage(self.attack_damage)
                    self.last_attack_time = pytime.time()
        else:
            self.follow_player(follow_distance=4)

def spawn_dog(position):
    d = Dog(position)
    pets.append(d)
    return d

#daden
try:
    daden_texture = load_texture('model/daden/texdaden.png')
except Exception:
    daden_texture = color.rgb(30, 30, 30)

class DaDen(BasePet):
    def __init__(self, position):
        super().__init__(position, name="Đệ tử", hp=0, speed=3.5, scale=(0.8, 1.8, 0.8))
        
        self.seed_count = 0
        self.seed_text = Text(parent=self.entity, text="Hạt giống: 0", y=1.2, scale=8, color=color.green, billboard=True, origin=(0, 0))
        
        def pet_input(key):
            if key == 'left mouse down' or key == 'right mouse down':
                if getattr(mouse, 'hovered_entity', None) == self.entity:
                    if world.player and (world.player.position - self.entity.position).length() < 4.0:
                        current_slot = inventory.inventory[inventory.selected_slot]
                        current_item = inventory.get_item(current_slot)
                        
                        if current_item == 'seed':
                            amount = inventory.get_count(current_slot)
                            inventory.remove_item(inventory.selected_slot, amount)
                            inventory.update_inventory_ui()
                            tools.set_active_item(inventory.get_item(inventory.inventory[inventory.selected_slot]))
                            
                            self.seed_count += amount
                            self.seed_text.text = f"Hạt giống: {self.seed_count}"
                            inventory.show_message(f"Đã đưa {amount} hạt giống LÚA cho đệ tử!", 1.5)
                            
                        elif current_item in ['corn seed', 'potato']:
                            inventory.show_message("Đệ tử: Trồng cái này mệt lắm, tôi chỉ trồng Lúa thôi!", 2)
                        else:
                            inventory.show_message("Hãy cầm hạt giống LÚA trên tay và bấm vào tôi!", 2)
        
        self.entity.input = pet_input

        try:
            self.mesh.model = load_model('model/daden/noledaden.glb')
        except Exception:
            self.mesh.model = 'cube'

        if hasattr(daden_texture, 'width'):
            self.mesh.texture = daden_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = daden_texture
        
        self.mesh.y = -0.8
        
        self.action_range = 2.0
        self.last_action_time = 0
        self.action_cooldown = 1.5 
        
    def update(self):
        self.apply_gravity()

        target_field = None
        action_type = None 
        min_dist = float('inf')

        for field_data in fields.fields:
            dist = (self.entity.position - field_data["pos"]).length()
            
            if field_data.get("crop_type") == 'wheat' and field_data.get("wheat_stage", 0) >= 4 and field_data.get("wheat_hp", 0) > 0:
                if action_type != 'harvest' or dist < min_dist:
                    min_dist = dist
                    target_field = field_data
                    action_type = 'harvest'
            
            elif not field_data.get("wheat_planted", False) and not field_data.get("peashooter_planted", False):
                if action_type != 'harvest' and dist < min_dist and self.seed_count > 0:
                    min_dist = dist
                    target_field = field_data
                    action_type = 'plant'

        if target_field:
            if min_dist > self.action_range:
                direction = (target_field["pos"] - self.entity.position).normalized()
                self.entity.position += direction * self.speed * ursina_time.dt
                target_look = Vec3(target_field["pos"].x, self.entity.y, target_field["pos"].z)
                self.entity.look_at(target_look)
            else:
                if pytime.time() - self.last_action_time > self.action_cooldown:
                    self.last_action_time = pytime.time()
                    
                    if action_type == 'harvest':
                        fields.destroy_wheat(target_field)
                        items.spawn_ground_item("wheat", self.entity.position + Vec3(0, 0.5, 0.5))
                        inventory.show_message("Đệ tử đã GẶT LÚA giúp bạn!", 1.5)
                        
                    elif action_type == 'plant':
                        if self.seed_count > 0:
                            fields.plant_wheat_on_field(target_field)
                            self.seed_count -= 1
                            self.seed_text.text = f"Hạt giống: {self.seed_count}"
                            inventory.show_message(f"Đệ tử đã TRỒNG lúa! (Còn {self.seed_count} hạt)", 1.5)
        else:
            self.follow_player(follow_distance=5)

def spawn_daden(position):
    dd = DaDen(position)
    pets.append(dd)
    return dd