import json
import os
from ursina import Vec3, destroy

import game
import world
import inventory
import fields
import building_system
import stats
import pet
import tasks

# Khai báo file lưu trữ
SAVE_FILE = "savegame.json"

def vec3_to_dict(v):
    if v is None: return None
    return {"x": v.x, "y": v.y, "z": v.z}

def dict_to_vec3(d):
    if d is None: return Vec3(0,0,0)
    return Vec3(d["x"], d["y"], d["z"])

def save_game():
    data = {}
    
    # 1. Thời gian
    data["game"] = {
        "current_day": getattr(game, 'current_day', 1),
        "time_of_day": getattr(game, 'time_of_day', 8.0)
    }
    
    # 2. Người chơi (Vị trí, máu, thể lực, tiền, vợ)
    if world.player:
        data["player"] = {
            "position": vec3_to_dict(world.player.position),
            "rotation_y": world.player.rotation_y,
            "hp": world.player.hp,
            "max_hp": world.player.max_hp,
            "stamina": world.player.stamina,
            "max_stamina": world.player.max_stamina,
            "money": world.player.money,
            "wife_married": world.wife_married
        }

    # 3. Túi đồ
    data["inventory"] = inventory.inventory

    # 4. Cánh đồng & Cây trồng (Hỗ trợ lúa, ngô, khoai...)
    data["fields"] = []
    for f in fields.fields:
        data["fields"].append({
            "pos": vec3_to_dict(f["pos"]),
            "crop_type": f.get("crop_type", None),
            "wheat_planted": f.get("wheat_planted", False),
            "wheat_stage": f.get("wheat_stage", 0),
            "wheat_hp": f.get("wheat_hp", 0),
            "peashooter_planted": f.get("peashooter_planted", False),
            "peashooter_hp": f.get("peashooter_hp", 0)
        })

    # 5. Công trình
    data["buildings"] = []
    for b in building_system.buildings:
        data["buildings"].append({
            "type": b["type"],
            "position": vec3_to_dict(b["position"]),
            "rotation": b["rotation"],
            "current_health": b["current_health"],
            "max_health": b["max_health"]
        })

    # 6. Thống kê (Stats)
    try:
        data["stats"] = stats.get_summary()
    except Exception:
        pass

    # 7. Nhiệm vụ (Quests)
    try:
        active_q = tasks.get_active_quest()
        if active_q:
            data["tasks"] = {
                "active_name": active_q.name,
                "progress": active_q.progress,
                "completed": active_q.completed
            }
    except Exception:
        pass

    # 8. Thú cưng (Dog, Toad, Daden...)
    data["pets"] = []
    for p in pet.pets:
        pet_data = {
            "type": p.__class__.__name__,
            "position": vec3_to_dict(p.entity.position),
            "hp": getattr(p, "hp", 100)
        }
        # Lưu số lượng hạt giống nếu là đệ tử Daden
        if hasattr(p, "seed_count"):
            pet_data["seed_count"] = p.seed_count
        data["pets"].append(pet_data)

    # Ghi ra file JSON
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
    print("Game Saved!")
    inventory.show_message("Đã lưu game thành công!", 2)


def load_game():
    if not os.path.exists(SAVE_FILE):
        print("No save file found!")
        inventory.show_message("Không tìm thấy file save!", 2)
        return False
        
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Khôi phục Thời gian
    if "game" in data:
        if hasattr(game, 'current_day'):
            game.current_day = data["game"].get("current_day", 1)
        if hasattr(game, 'set_time_of_day'):
            game.set_time_of_day(data["game"].get("time_of_day", 8.0))

    # Khôi phục Người chơi
    if "player" in data and world.player:
        p_data = data["player"]
        world.player.position = dict_to_vec3(p_data.get("position"))
        world.player.rotation_y = p_data.get("rotation_y", 0)
        world.player.hp = p_data.get("hp", 100)
        world.player.max_hp = p_data.get("max_hp", 100)
        world.player.stamina = p_data.get("stamina", 1000)
        world.player.max_stamina = p_data.get("max_stamina", 1000)
        world.player.money = p_data.get("money", 0)
        world.wife_married = p_data.get("wife_married", False)
        
        import rendering
        rendering.update_player_hud(world.player.hp, world.player.max_hp, world.player.stamina, world.player.max_stamina, world.player.money)

    # Khôi phục Túi đồ
    if "inventory" in data:
        inventory.inventory = data["inventory"]
        inventory.update_inventory_ui()

    # Khôi phục Đồng ruộng & Cây trồng
    if "fields" in data:
        # Dọn sạch ruộng cũ trên map trước
        for f in fields.fields:
            if hasattr(fields, 'destroy_wheat'):
                fields.destroy_wheat(f)
            destroy(f["entity"])
            if f.get("health_bar"): destroy(f["health_bar"])
            if f.get("peashooter_entity"): destroy(f["peashooter_entity"])
        fields.fields.clear()
        
        for f_data in data["fields"]:
            pos = dict_to_vec3(f_data["pos"])
            # Tái tạo ô đất
            f_root = fields.create_field(Vec3(pos.x, 0, pos.z))
            f_dict = fields.fields[-1] 
            
            # Trồng lại cây trồng (Hỗ trợ lúa/ngô/khoai dựa vào crop_type)
            crop_type = f_data.get("crop_type")
            is_wheat = f_data.get("wheat_planted")
            
            if crop_type or is_wheat:
                f_dict["crop_type"] = crop_type if crop_type else "wheat"
                f_dict["wheat_planted"] = True
                f_dict["wheat_stage"] = f_data.get("wheat_stage", 1)
                f_dict["wheat_hp"] = f_data.get("wheat_hp", 20)
                
                # Gọi hàm update hình ảnh cây trồng
                if hasattr(fields, '_update_wheat_patch'):
                    fields._update_wheat_patch(f_dict, f_dict["wheat_stage"])
                if hasattr(fields, 'update_wheat_health_bar'):
                    fields.update_wheat_health_bar(f_dict)

            if f_data.get("peashooter_planted"):
                if hasattr(fields, 'plant_peashooter_on_field'):
                    fields.plant_peashooter_on_field(f_dict)
                f_dict["peashooter_hp"] = f_data.get("peashooter_hp", 20)

    # Khôi phục Công trình
    if "buildings" in data:
        for b in building_system.buildings:
            destroy(b["entity"])
            if b.get("health_bar"): destroy(b["health_bar"])
            for d in b.get("details", []): destroy(d)
        building_system.buildings.clear()

        for b_data in data["buildings"]:
            old_rot = building_system.current_rotation
            old_idx = building_system.current_building_index
            
            for i, ab in enumerate(building_system.available_buildings):
                if ab["name"] == b_data["type"]:
                    building_system.current_building_index = i
                    break
            building_system.current_rotation = b_data.get("rotation", 0)
            
            new_b = building_system.place_building(dict_to_vec3(b_data["position"]))
            if new_b:
                new_b["current_health"] = b_data.get("current_health", 100)
                new_b["max_health"] = b_data.get("max_health", 100)
            
            building_system.current_rotation = old_rot
            building_system.current_building_index = old_idx

    # Khôi phục Thú cưng / Đệ tử
    if "pets" in data:
        for p in pet.pets:
            if hasattr(p, 'entity'):
                destroy(p.entity)
        pet.pets.clear()

        for p_data in data["pets"]:
            ptype = p_data["type"].lower()
            pos = dict_to_vec3(p_data["position"])
            new_p = None
            
            if ptype == "dog" and hasattr(pet, 'spawn_dog'):
                new_p = pet.spawn_dog(pos)
            elif ptype == "toad" and hasattr(pet, 'spawn_toad'):
                new_p = pet.spawn_toad(pos)
            elif ptype == "daden" and hasattr(pet, 'spawn_daden'):
                new_p = pet.spawn_daden(pos)

            if new_p:
                new_p.hp = p_data.get("hp", 100)
                if hasattr(new_p, "seed_count"):
                    new_p.seed_count = p_data.get("seed_count", 0)
                    if hasattr(new_p, "seed_text"):
                        new_p.seed_text.text = f"Hạt giống: {new_p.seed_count}"

    # Khôi phục Thống kê (Stats)
    if "stats" in data:
        s_data = data["stats"]
        stats.stats.harvested_wheat = s_data.get("harvested_wheat", 0)
        stats.stats.enemies_killed = s_data.get("enemies_killed", {})
        stats.stats.money_earned = s_data.get("money_earned", 0)
        stats.stats.money_stolen = s_data.get("money_stolen", 0)
        import rendering
        rendering.update_stats_display()

    # Khôi phục Nhiệm vụ (Tasks/Quests)
    if "tasks" in data:
        t_data = data["tasks"]
        if hasattr(tasks, 'initialize_quests'):
            tasks.initialize_quests()
        
        # Tìm nhiệm vụ tương ứng và khôi phục tiến độ
        if hasattr(tasks, 'quest_list'):
            for q in tasks.quest_list:
                if q.name == t_data["active_name"]:
                    tasks.set_active_quest(q)
                    q.progress = t_data.get("progress", 0)
                    q.completed = t_data.get("completed", False)
                    import rendering
                    rendering.update_quest_text(q.name, q.progress, q.goal)
                    break

    print("Game Loaded Successfully!")
    inventory.show_message("Đã tải game thành công!", 2)
    return True