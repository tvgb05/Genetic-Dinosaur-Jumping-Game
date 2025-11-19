import pygame
import random
import copy
import os
import json

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

# --- Config Loader ---
def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    if not os.path.exists(config_path):
        print("[CONFIG] Creating default config.json...")
        with open(config_path, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG ERROR] {e}. Using defaults.")
        return DEFAULT_CONFIG

CFG = load_config()
GAME = CFG["game_settings"]
DIMS = CFG.get("entity_dimensions", DEFAULT_CONFIG["entity_dimensions"])
PHYS = CFG["physics"]
AI = CFG["ai_settings"]
ASSETS = CFG["assets"]
VAR_JUMP = PHYS.get("variable_jump", {"enabled": False, "hold_gravity": 0.8, "max_hold_frames": 0})

# --- Constants ---
SCREEN_WIDTH = GAME["screen_width"]
SCREEN_HEIGHT = GAME["screen_height"]
GROUND_Y = GAME.get("ground_y", 310)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DINO_COLOR = (83, 83, 83)
BEST_DINO_COLOR = (0, 200, 0) 

# --- Asset Loader ---
def load_asset(name):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths_to_check = [
        os.path.join(script_dir, "assets", name),
        os.path.join(script_dir, name),
        name
    ]
    for path in paths_to_check:
        if os.path.exists(path):
            try:
                img = pygame.image.load(path)
                return img
            except: pass
    return None

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Genetic AI Dino - High Score Tracker")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24) # Slightly smaller font for cleaner UI
font_big = pygame.font.Font(None, 40) # Bigger font for main score

RAW_DINO_IMG = load_asset(ASSETS["dino"])
RAW_DUCK_IMG = load_asset(ASSETS["dino_duck"]) 
RAW_CACTUS_IMG = load_asset(ASSETS["cactus"])

class Dino:
    def __init__(self):
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
        decision = (distance * self.weights[0]) + \
                   (speed * self.weights[1]) + \
                   (self.y * self.weights[2]) + \
                   self.bias
        
        if decision > 0.5:
            self.wants_to_jump = True
            self.jump()
        else:
            self.wants_to_jump = False
            
        if decision < -0.5:
            self.duck(True)
        else:
            self.duck(False)

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

        if self.is_ducking and not self.is_jumping:
            current_w = self.duck_width
            current_h = self.duck_height
        else:
            current_w = self.stand_width
            current_h = self.stand_height
        
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
            if RAW_DUCK_IMG: img = pygame.transform.scale(RAW_DUCK_IMG, (self.duck_width, self.duck_height))
            elif RAW_DINO_IMG: img = pygame.transform.scale(RAW_DINO_IMG, (self.duck_width, self.duck_height))
        else:
            if RAW_DINO_IMG: img = pygame.transform.scale(RAW_DINO_IMG, (self.stand_width, self.stand_height))

        if img:
            screen.blit(img, (self.x, self.y))
            if is_best: pygame.draw.rect(screen, BEST_DINO_COLOR, self.rect, 2)
        else:
            color = BEST_DINO_COLOR if is_best else self.color
            pygame.draw.rect(screen, color, self.rect)
            if is_best: pygame.draw.rect(screen, BLACK, self.rect, 2)

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
            pygame.draw.rect(screen, BLACK, self.rect)

# --- Genetic Algorithm ---
def next_generation(old_population):
    old_population.sort(key=lambda x: x.score, reverse=True)
    new_population = []
    keep_count = AI["elitism_count"]
    
    for i in range(keep_count):
        if i < len(old_population):
            champ = Dino()
            champ.weights = copy.deepcopy(old_population[i].weights)
            champ.bias = old_population[i].bias
            new_population.append(champ)
    
    while len(new_population) < len(old_population):
        parent = random.choice(old_population[:keep_count*2])
        baby = Dino()
        baby.weights = copy.deepcopy(parent.weights)
        baby.bias = parent.bias
        mutate(baby)
        new_population.append(baby)
    return new_population

def mutate(dino):
    rate = AI["mutation_rate"]
    power = AI["mutation_power"]
    for i in range(3):
        if random.random() < rate: dino.weights[i] += random.uniform(-power, power)
    if random.random() < rate: dino.bias += random.uniform(-power, power)

def main():
    pop_size = AI["population_size"]
    dinos = [Dino() for _ in range(pop_size)]
    cacti = []
    spawn_timer = 0 
    generation = 1
    
    # --- Score Tracking Variables ---
    all_time_high_score = 0
    current_score = 0
    
    running = True
    while running:
        screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        # Get Current Best
        current_best_dino = max(dinos, key=lambda d: d.score, default=dinos[0])
        current_score = current_best_dino.score
        
        # Update All Time High Score
        if current_score > all_time_high_score:
            all_time_high_score = current_score

        # Speed Logic
        current_speed = min(GAME["max_speed"], GAME["base_speed"] + (current_score // GAME["speed_increase_interval"]))
        
        # Spawn Logic
        spawn_timer += 1
        spawn_threshold = max(30, 100 - current_speed * 2) 
        if len(cacti) == 0 or (cacti[-1].x < SCREEN_WIDTH - 250 and spawn_timer > spawn_threshold and random.randint(0, 50) == 0):
            cacti.append(Cactus(current_speed))
            spawn_timer = 0
        if len(cacti) > 0 and cacti[0].x < -50: cacti.pop(0)

        # AI Inputs
        target = None
        for c in cacti:
            if c.x + c.width > 50:
                target = c
                break
        dist = target.x - 50 if target else 1000

        # Update Entities
        alive_count = 0
        for dino in dinos:
            if dino.alive:
                alive_count += 1
                dino.think(dist, current_speed)
                dino.update()
                for c in cacti:
                    if dino.rect.colliderect(c.rect): dino.alive = False

        # Draw Entities
        for c in cacti: c.update(current_speed); c.draw(screen)
        
        if alive_count > 0:
            for d in dinos: d.draw(screen, is_best=(d == current_best_dino))
        else:
            dinos = next_generation(dinos)
            cacti = []
            spawn_timer = 0
            generation += 1
            print(f"Generation {generation} starting...")

        # --- NEW UI DISPLAY ---
        # 1. Stats (Top Left)
        stats_left = [
            f"Gen: {generation}", 
            f"Alive: {alive_count}/{pop_size}",
            f"Speed: {int(current_speed)}"
        ]
        for i, text in enumerate(stats_left):
            screen.blit(font.render(text, True, GRAY), (10, 10 + i * 20))

        # 2. Scores (Top Right)
        # Format: HI 00000  00000
        score_text = f"{int(current_score):05d}"
        high_score_text = f"HI {int(all_time_high_score):05d}"
        
        # Draw High Score (Gray)
        hs_surface = font_big.render(high_score_text, True, GRAY)
        screen.blit(hs_surface, (SCREEN_WIDTH - 280, 10))
        
        # Draw Current Score (Black)
        s_surface = font_big.render(score_text, True, BLACK)
        screen.blit(s_surface, (SCREEN_WIDTH - 110, 10))

        pygame.draw.line(screen, GRAY, (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 2)
        pygame.display.flip()
        clock.tick(GAME["fps"])

    pygame.quit()

if __name__ == "__main__":
    main()