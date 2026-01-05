import pygame
import random
import copy
import os
import json
import time

# --- DEFAULT CONFIG ---
DEFAULT_CONFIG = {
    "game_settings": {
        "screen_width": 800,
        "screen_height": 400,
        "ground_y": 310,
        "fps": 60,
        "base_speed": 10,
        "max_speed": 30,
        "speed_increase_interval": 100
    },
    "entity_dimensions": {
        "dino": {
            "stand_width": 40,
            "stand_height": 40,
            "duck_width": 55,
            "duck_height": 25
        },
        "cactus": {
            "min_width": 30,
            "max_width": 50,
            "min_height": 40,
            "max_height": 60
        }
    },
    "physics": {
        "gravity": 0.8,
        "jump_power": -15,
        "fast_drop_gravity": 4.0,
        "variable_jump": {
            "enabled": True,
            "hold_gravity": 0.25,
            "max_hold_frames": 15
        }
    },
    "ai_settings": {
        "population_size": 50,
        "mutation_rate": 0.2,
        "mutation_power": 0.6,
        "elitism_count": 5
    },
    "assets": {
        "dino": "dino.png",
        "dino_duck": "dino_duck.png",
        "cactus": "cactus.png"
    }
}

# --- Config Manager ---
def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    if not os.path.exists(config_path):
        with open(config_path, "w") as f: json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(config_path, "r") as f: return json.load(f)
    except: return DEFAULT_CONFIG

def save_app_config(new_config):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    try:
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=4)
        print("[CONFIG] Settings saved to disk.")
    except Exception as e:
        print(f"[CONFIG ERROR] Could not save settings: {e}")

CFG = load_config()
GAME = CFG["game_settings"]
DIMS = CFG.get("entity_dimensions", DEFAULT_CONFIG["entity_dimensions"])
PHYS = CFG["physics"]
AI = CFG["ai_settings"]
ASSETS = CFG["assets"]
VAR_JUMP = PHYS.get("variable_jump", {"enabled": False, "hold_gravity": 0.8, "max_hold_frames": 0})

# --- GENE MANAGER ---
GENE_FOLDER = "best_genes"

def ensure_gene_folder():
    if not os.path.exists(GENE_FOLDER): os.makedirs(GENE_FOLDER)

def save_best_gene(dino, score, current_gen_num):
    ensure_gene_folder()
    filename = f"gen_{current_gen_num}_gene_{dino.origin_gen}.json"
    filepath = os.path.join(GENE_FOLDER, filename)
    
    gene_data = {
        "score": score,
        "weights": dino.weights,
        "bias": dino.bias,
        "origin_gen": dino.origin_gen,
        "saved_at_gen": current_gen_num
    }
    
    with open(filepath, "w") as f: json.dump(gene_data, f, indent=4)
    print(f"[GENE SAVED] {filename}")
    return gene_data

def get_all_saves():
    ensure_gene_folder()
    files = [f for f in os.listdir(GENE_FOLDER) if f.endswith(".json")]
    saves = []
    for f in files:
        try:
            with open(os.path.join(GENE_FOLDER, f), "r") as file:
                data = json.load(file)
                data['filename'] = f
                saves.append(data)
        except: continue
    saves.sort(key=lambda x: x['score'], reverse=True)
    return saves

# --- UI CLASSES ---
class Button:
    def __init__(self, x, y, w, h, text, color=(200, 200, 200), hover_color=(170, 170, 170)):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (50, 50, 50), self.rect, 2, border_radius=8)
        
        text_surf = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False

# --- PYGAME INIT ---
pygame.init()
SCREEN_WIDTH = GAME["screen_width"]
SCREEN_HEIGHT = GAME["screen_height"]
GROUND_Y = GAME.get("ground_y", 310)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Genetic AI Dino")
clock = pygame.time.Clock()

font_ui = pygame.font.Font(None, 30)
font_title = pygame.font.Font(None, 50)
font_small = pygame.font.Font(None, 24)

# Assets
def load_asset(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [os.path.join(script_dir, "assets", name), os.path.join(script_dir, name), name]
    for p in paths:
        if os.path.exists(p): return pygame.image.load(p)
    return None

RAW_DINO_IMG = load_asset(ASSETS["dino"])
RAW_DUCK_IMG = load_asset(ASSETS["dino_duck"]) 
RAW_CACTUS_IMG = load_asset(ASSETS["cactus"])

# --- GAME ENTITIES ---
class Dino:
    def __init__(self, origin_gen=1):
        self.stand_width = DIMS["dino"]["stand_width"]
        self.stand_height = DIMS["dino"]["stand_height"]
        self.duck_width = DIMS["dino"]["duck_width"]
        self.duck_height = DIMS["dino"]["duck_height"]
        self.x = 50
        self.y = GROUND_Y - self.stand_height
        self.velocity_y = 0
        self.is_jumping = False
        self.is_ducking = False
        self.alive = True
        self.score = 0
        self.color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        self.origin_gen = origin_gen 
        self.wants_to_jump = False
        self.jump_timer = 0      
        self.rect = pygame.Rect(self.x, self.y, self.stand_width, self.stand_height)
        self.weights = [random.uniform(-1, 1) for _ in range(3)]
        self.bias = random.uniform(-1, 1)

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = PHYS["jump_power"]
            self.is_jumping = True
            self.is_ducking = False
            self.jump_timer = 0

    def duck(self, active):
        self.is_ducking = active

    def think(self, distance, speed):
        decision = (distance * self.weights[0]) + (speed * self.weights[1]) + (self.y * self.weights[2]) + self.bias
        if decision > 0.5:
            self.wants_to_jump = True
            self.jump()
        else:
            self.wants_to_jump = False
        if decision < -0.5: self.duck(True)
        else: self.duck(False)

    def update(self):
        if not self.alive: return
        if (VAR_JUMP["enabled"] and self.is_jumping and self.wants_to_jump and self.jump_timer < VAR_JUMP["max_hold_frames"]):
            self.velocity_y += VAR_JUMP["hold_gravity"]
            self.jump_timer += 1
        elif self.is_ducking and self.is_jumping:
            self.velocity_y += PHYS["fast_drop_gravity"]
        else:
            self.velocity_y += PHYS["gravity"]
        self.y += self.velocity_y

        current_w = self.duck_width if (self.is_ducking and not self.is_jumping) else self.stand_width
        current_h = self.duck_height if (self.is_ducking and not self.is_jumping) else self.stand_height
        
        ground_level = GROUND_Y - current_h
        if self.y >= ground_level:
            self.y = ground_level
            self.is_jumping = False
            self.jump_timer = 0
        self.rect = pygame.Rect(self.x, int(self.y), current_w, current_h)
        self.score += 1 

    def draw(self, screen, is_best=False):
        if not self.alive: return
        img = None
        if self.is_ducking and not self.is_jumping:
            img = pygame.transform.scale(RAW_DUCK_IMG or RAW_DINO_IMG, (self.duck_width, self.duck_height)) if (RAW_DUCK_IMG or RAW_DINO_IMG) else None
        else:
            img = pygame.transform.scale(RAW_DINO_IMG, (self.stand_width, self.stand_height)) if RAW_DINO_IMG else None

        if img:
            screen.blit(img, (self.x, self.y))
            if is_best: pygame.draw.rect(screen, (0, 200, 0), self.rect, 2)
        else:
            color = (0, 200, 0) if is_best else self.color
            pygame.draw.rect(screen, color, self.rect)
            if is_best: pygame.draw.rect(screen, (0,0,0), self.rect, 2)

class Cactus:
    def __init__(self, speed):
        self.width = random.randint(DIMS["cactus"]["min_width"], DIMS["cactus"]["max_width"])
        self.height = random.randint(DIMS["cactus"]["min_height"], DIMS["cactus"]["max_height"])
        self.x = SCREEN_WIDTH + random.randint(10, 300)
        self.y = GROUND_Y - self.height
        self.speed = speed 
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, current_speed):
        self.x -= current_speed 
        self.rect.x = int(self.x)

    def draw(self, screen):
        if RAW_CACTUS_IMG:
            scaled = pygame.transform.scale(RAW_CACTUS_IMG, (self.width, self.height))
            screen.blit(scaled, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (0,0,0), self.rect)

# --- GAME LOGIC ---
def next_generation(last_best_gene_data, current_generation_number):
    new_population = []
    pop_size = AI["population_size"]
    
    if last_best_gene_data:
        champ = Dino(origin_gen=last_best_gene_data.get("origin_gen", 1)) 
        champ.weights = copy.deepcopy(last_best_gene_data["weights"])
        champ.bias = last_best_gene_data["bias"]
        champ.color = (0, 200, 0) 
        new_population.append(champ)
    else:
        new_population.append(Dino(origin_gen=current_generation_number))

    while len(new_population) < pop_size:
        baby = Dino(origin_gen=current_generation_number) 
        if last_best_gene_data:
            baby.weights = copy.deepcopy(last_best_gene_data["weights"])
            baby.bias = last_best_gene_data["bias"]
            rate = AI["mutation_rate"]
            power = AI["mutation_power"]
            for i in range(3):
                if random.random() < rate: baby.weights[i] += random.uniform(-power, power)
            if random.random() < rate: baby.bias += random.uniform(-power, power)
        new_population.append(baby)
    return new_population

def run_game(loaded_gene_data=None):
    generation = 1
    best_gene_memory = loaded_gene_data
    if loaded_gene_data:
        generation = loaded_gene_data.get("saved_at_gen", 0) + 1

    dinos = next_generation(best_gene_memory, generation)
    cacti = []
    spawn_timer = 0 
    all_time_high_score = best_gene_memory["score"] if best_gene_memory else 0
    current_score = 0
    
    running = True
    while running:
        screen.fill((255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return 
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return 

        alive_dinos = [d for d in dinos if d.alive]
        current_best_dino = max(alive_dinos, key=lambda d: d.score, default=dinos[0]) if alive_dinos else dinos[0]
        current_score = current_best_dino.score
        
        if current_score > all_time_high_score:
            all_time_high_score = current_score

        current_speed = min(GAME["max_speed"], GAME["base_speed"] + (current_score // GAME["speed_increase_interval"]))
        
        spawn_timer += 1
        spawn_threshold = max(30, 100 - current_speed * 2) 
        if len(cacti) == 0 or (cacti[-1].x < SCREEN_WIDTH - 250 and spawn_timer > spawn_threshold and random.randint(0, 50) == 0):
            cacti.append(Cactus(current_speed))
            spawn_timer = 0
        if len(cacti) > 0 and cacti[0].x < -50: cacti.pop(0)

        target = None
        for c in cacti:
            if c.x + c.width > 50: target = c; break
        dist = target.x - 50 if target else 1000

        alive_count = 0
        for dino in dinos:
            if dino.alive:
                alive_count += 1
                dino.think(dist, current_speed)
                dino.update()
                for c in cacti:
                    if dino.rect.colliderect(c.rect): 
                        dino.alive = False
                        if dino.score >= all_time_high_score and dino.score > 0:
                            best_gene_memory = save_best_gene(dino, dino.score, generation)

        for c in cacti: c.update(current_speed); c.draw(screen)
        
        if alive_count > 0:
            for d in dinos: d.draw(screen, is_best=(d == current_best_dino))
        else:
            generation += 1
            dinos = next_generation(best_gene_memory, generation)
            cacti = []
            spawn_timer = 0
            
        ui_texts = [f"Gen: {generation}", f"Alive: {alive_count}", f"Speed: {int(current_speed)}"]
        for i, t in enumerate(ui_texts):
            screen.blit(font_ui.render(t, True, (100, 100, 100)), (10, 10 + i * 25))
            
        score_surf = font_title.render(f"{int(current_score):05d}", True, (0,0,0))
        hs_surf = font_title.render(f"HI {int(all_time_high_score):05d}", True, (200,200,200))
        screen.blit(hs_surf, (SCREEN_WIDTH - 300, 10))
        screen.blit(score_surf, (SCREEN_WIDTH - 130, 10))

        pygame.draw.line(screen, (100,100,100), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)
        pygame.display.flip()
        clock.tick(GAME["fps"])

# --- CONFIG MENU SCREEN ---
def config_menu_screen():
    # Helper to create setting row logic
    settings_map = [
        # Label, Dict Key 1, Dict Key 2, Step, Min, Max
        {"label": "FPS Limit", "keys": ["game_settings", "fps"], "step": 10, "min": 30, "max": 240},
        {"label": "Base Speed", "keys": ["game_settings", "base_speed"], "step": 1, "min": 5, "max": 50},
        {"label": "Pop Size", "keys": ["ai_settings", "population_size"], "step": 10, "min": 10, "max": 500},
        {"label": "Mutation Rate", "keys": ["ai_settings", "mutation_rate"], "step": 0.05, "min": 0.0, "max": 1.0},
    ]

    buttons = []
    # Create +/- buttons for each setting
    start_y = 120
    for i, item in enumerate(settings_map):
        y_pos = start_y + i * 50
        # Decrease Button
        btn_dec = Button(400, y_pos, 40, 30, "-")
        btn_dec.action = "DEC"
        btn_dec.index = i
        buttons.append(btn_dec)
        
        # Increase Button
        btn_inc = Button(550, y_pos, 40, 30, "+")
        btn_inc.action = "INC"
        btn_inc.index = i
        buttons.append(btn_inc)

    btn_save = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 70, 200, 50, "Save & Back")

    while True:
        screen.fill((240, 240, 240))
        title = font_title.render("Game Configuration", True, (50, 50, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT"
            if btn_save.is_clicked(event):
                save_app_config(CFG)
                return "BACK"
            
            for btn in buttons:
                if btn.is_clicked(event):
                    # Handle Value Change
                    setting = settings_map[btn.index]
                    k1, k2 = setting["keys"]
                    current_val = CFG[k1][k2]
                    
                    if btn.action == "DEC":
                        new_val = current_val - setting["step"]
                    else:
                        new_val = current_val + setting["step"]
                        
                    # Clamp and set
                    if setting["min"] <= new_val <= setting["max"]:
                        # Round floats to avoid 0.19999999 issues
                        if isinstance(setting["step"], float):
                            new_val = round(new_val, 2)
                        CFG[k1][k2] = new_val

        # Draw Settings Rows
        for i, item in enumerate(settings_map):
            y_pos = start_y + i * 50
            # Draw Label
            label_surf = font_ui.render(item["label"], True, (0,0,0))
            screen.blit(label_surf, (200, y_pos + 5))
            
            # Draw Value
            k1, k2 = item["keys"]
            val = CFG[k1][k2]
            val_text = f"{val}"
            val_surf = font_ui.render(val_text, True, (0, 0, 150))
            # Center value between buttons (approx x=495)
            screen.blit(val_surf, (495 - val_surf.get_width()//2, y_pos + 5))

        # Draw Buttons
        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen, font_ui)
            
        btn_save.check_hover(mouse_pos)
        btn_save.draw(screen, font_ui)

        pygame.display.flip()
        clock.tick(60)

# --- MENU SCREENS ---
def load_menu_screen():
    saves = get_all_saves()
    file_buttons = []
    for i, save in enumerate(saves[:5]): # Only top 5
        btn_text = f"Score: {save['score']} | Gen: {save.get('saved_at_gen','?')} | Origin: {save.get('origin_gen','?')}"
        btn = Button(SCREEN_WIDTH//2 - 200, 100 + i * 60, 400, 50, btn_text)
        btn.data = save 
        file_buttons.append(btn)
    back_btn = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 70, 200, 50, "Back")
    
    while True:
        screen.fill((240, 240, 240))
        title = font_title.render("Select Save File", True, (50, 50, 50))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT"
            if back_btn.is_clicked(event): return None
            for btn in file_buttons:
                if btn.is_clicked(event): return btn.data

        for btn in file_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(screen, font_small)
        back_btn.check_hover(mouse_pos)
        back_btn.draw(screen, font_ui)
        pygame.display.flip()
        clock.tick(60)

def main_menu():
    btn_new = Button(SCREEN_WIDTH//2 - 100, 120, 200, 50, "New Simulation")
    btn_load = Button(SCREEN_WIDTH//2 - 100, 190, 200, 50, "Load Best Genes")
    btn_cfg = Button(SCREEN_WIDTH//2 - 100, 260, 200, 50, "Settings") # NEW BUTTON
    btn_exit = Button(SCREEN_WIDTH//2 - 100, 330, 200, 50, "Exit")
    
    while True:
        screen.fill((255, 255, 255))
        title = font_title.render("Genetic Dino AI", True, (0, 0, 0))
        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "EXIT"
            if btn_new.is_clicked(event): run_game(None) 
            if btn_load.is_clicked(event):
                selected_data = load_menu_screen()
                if selected_data == "EXIT": return "EXIT"
                if selected_data: run_game(selected_data)
            if btn_cfg.is_clicked(event): # NEW LOGIC
                res = config_menu_screen()
                if res == "EXIT": return "EXIT"
            if btn_exit.is_clicked(event): return "EXIT"

        for btn in [btn_new, btn_load, btn_cfg, btn_exit]:
            btn.check_hover(mouse_pos)
            btn.draw(screen, font_ui)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main_menu()
    pygame.quit()