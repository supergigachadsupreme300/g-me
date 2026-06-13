#Chihai
from ursina import Entity, color, destroy, load_model, load_texture, Vec3
from ursina import time as ursina_time 
import time as pytime
import world

pets = []

def update_pets():
    for pet in list(pets):
        if hasattr(pet, 'update'):
            try:
                pet.update()
            except Exception as e:
                print(f"Lỗi khi cập nhật hành động Pet: {e}")

#coc
try:
    toad_texture = load_texture('model/toad/MAT_Animal_Amphibian_Toad2_0_basecolor.jpg') 
    toad_texture = load_texture('model/toad/MAT_Animal_Amphibian_Toad2_0_basecolor.jpeg') 
except Exception as e:
    toad_texture = color.rgb(34/255, 139/255, 34/255)

class Toad:
    def __init__(self, position):
        self.entity = Entity(model='cube', color=color.clear, scale=(0.3, 0.2, 0.3), position=position, collider='box')
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/toad/mesh.fbx')
        except Exception as e:
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
        
        self.speed = 2.0
        self.attack_range = 2.0
        self.last_attack_time = 0
        
    def update(self):
        import enemies 
        target = None
        min_dist = float('inf')
        
        if hasattr(enemies, 'enemies') and enemies.enemies:
            for e in enemies.enemies:
                if e.__class__.__name__ == 'Grasshopper':
                    dist = (self.entity.position - e.entity.position).length()
                    if dist < min_dist:
                        min_dist = dist
                        target = e
        
        if target:
            if min_dist > self.attack_range:
                direction = (target.entity.position - self.entity.position).normalized()
                self.entity.position += direction * self.speed * ursina_time.dt
                self.entity.look_at(target.entity.position)
            else:
                if pytime.time() - self.last_attack_time > 1.0:
                    target.take_damage(999) 
                    self.last_attack_time = pytime.time()
                    import inventory
                    inventory.show_message("Cóc đã xơi tái một con Châu Chấu!", 2)
        else:
            if world.player:
                player_pos = world.player.position
                dist_to_player = (self.entity.position - player_pos).length()
                if dist_to_player > 5:
                    direction = (player_pos - self.entity.position).normalized()
                    self.entity.position += direction * (self.speed * 0.8) * ursina_time.dt
                    self.entity.look_at(player_pos)

def spawn_toad(position):
    t = Toad(position)
    pets.append(t)
    return t


#cho
try:
    dog_texture = load_texture('model/dog/AM83_037_color_01.jpg') 
except Exception as e:
    dog_texture = color.orange

class Dog:
    def __init__(self, position):
        self.entity = Entity(model='cube', color=color.clear, scale=(0.8, 0.8, 0.8), position=position, collider='box')
        
        self.mesh = Entity(parent=self.entity)
        try:
            self.mesh.model = load_model('model/dog/пес.fbx') 
        except Exception as e:
            self.mesh.model = 'cube'
            
        if hasattr(dog_texture, 'width'):
            self.mesh.texture = dog_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = dog_texture
            
        self.mesh.scale = (0.05, 0.05, 0.05)
        self.mesh.y = -0.4 
        
        self.speed = 5.0
        self.attack_range = 2.5
        self.attack_damage = 3
        self.last_attack_time = 0
        self.hp = 100
        self.max_hp = 100
        self.health_bar = Entity(parent=self.entity, y=1.2, model='cube', color=color.green, scale=(1, 0.1, 0.1))

    def take_damage(self, amount):
        self.hp -= amount
        self.health_bar.scale_x = max(0, self.hp / self.max_hp)
        if self.hp <= 0:
            self.die()

    def die(self):
        import inventory
        inventory.show_message("Chó cưng đã bị hạ gục / bắt trộm!", 3)
        if self in pets:
            pets.remove(self)
        destroy(self.entity)

    def update(self):
        import enemies 
        target = None
        min_dist = float('inf')

        if hasattr(enemies, 'enemies') and enemies.enemies:
            for e in enemies.enemies:
                if e and hasattr(e, 'entity') and e.entity:
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
            if world.player:
                player_pos = world.player.position
                dist_to_player = (self.entity.position - player_pos).length()
                if dist_to_player > 4:
                    direction = (player_pos - self.entity.position).normalized()
                    self.entity.position += direction * self.speed * ursina_time.dt
                    self.entity.look_at(player_pos)

def spawn_dog(position):
    d = Dog(position)
    pets.append(d)
    return d

#daden
try:
    daden_texture = load_texture('model/daden/texdaden.png')
except Exception as e:
    daden_texture = color.rgb(30, 30, 30)

class DaDen:
    def __init__(self, position):
        self.entity = Entity(model='cube', color=color.clear, scale=(0.8, 1.8, 0.8), position=position, collider='box')
        
        self.mesh = Entity(parent=self.entity)
        
        try:
            self.mesh.model = load_model('model/daden/noledaden.glb')
        except Exception as e:
            self.mesh.model = 'cube'

        if hasattr(daden_texture, 'width'):
            self.mesh.texture = daden_texture
            self.mesh.color = color.white
        else:
            self.mesh.texture = None
            self.mesh.color = daden_texture
        
        self.mesh.y = -0.8
        
        self.speed = 3.5
        self.action_range = 2.0
        self.last_action_time = 0
        self.action_cooldown = 1.5 
        
    def update(self):
        import world
        import fields
        import items
        import inventory
        import time as pytime
        from ursina import time as ursina_time, Vec3
        
        self.entity.y -= 9.81 * ursina_time.dt
        if self.entity.y < self.entity.scale_y / 2:
            self.entity.y = self.entity.scale_y / 2

        target_field = None
        action_type = None 
        min_dist = float('inf')

        for field_data in fields.fields:
            dist = (self.entity.position - field_data["pos"]).length()
            
            if field_data["wheat_planted"] and field_data.get("wheat_stage", 0) >= 4 and field_data.get("wheat_hp", 0) > 0:
                if action_type != 'harvest' or dist < min_dist:
                    min_dist = dist
                    target_field = field_data
                    action_type = 'harvest'
            
            elif not field_data["wheat_planted"] and not field_data.get("peashooter_planted", False):
                if action_type != 'harvest' and dist < min_dist:
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
                        fields.plant_wheat_on_field(target_field)
                        inventory.show_message("Đệ tử đã TRỒNG hạt giống!", 1.5)
        else:
            if world.player:
                player_pos = world.player.position
                dist_to_player = (self.entity.position - player_pos).length()
                if dist_to_player > 5: 
                    direction = (player_pos - self.entity.position).normalized()
                    self.entity.position += direction * (self.speed * 0.8) * ursina_time.dt
                    target_look = Vec3(player_pos.x, self.entity.y, player_pos.z)
                    self.entity.look_at(target_look)

def spawn_daden(position):
    dd = DaDen(position)
    pets.append(dd)
    return dd