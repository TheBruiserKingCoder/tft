# TFT Pygame – komplet prototype med origin- og class-traits, shop, drag-n-drop, kamp og buffs

import pygame
import random

pygame.init()

# --- KONSTANTER ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# --- FARVER ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE  = (0, 150, 255)
GREEN = (0, 255, 0)
RED   = (255, 0, 0)

# --- SLOT POSITIONS ---
MAX_BOARD_SLOTS = 5
MAX_BENCH_SLOTS = 9
BENCH_SLOT_POSITIONS = [(20 + i*60 + i*10, 380) for i in range(MAX_BENCH_SLOTS)]
BOARD_SLOT_POSITIONS = [(100 + i*120, 450) for i in range(MAX_BOARD_SLOTS)]

# --- ØKONOMI ---
XP_PER_BUY = 4
GOLD_PER_XP = 4

def xp_to_next_level(level: int) -> int:
    return 8 + 2 * (level - 1)

# --- TRAIT BUFF DEFINITION (Origins + Classes) ---
TRAIT_BUFFS = {
    # Origins
    "Astral":      {"bps":[2],          "effects":{2:{"mana":5}}},
    "Bilgewater":  {"bps":[2,3,5],      "effects":{2:{"gold_kill":1},3:{"gold_kill":2},5:{"gold_kill":3,"lifesteal":0.10}}},
    "Freljord":    {"bps":[2,3,4],      "effects":{2:{"armor":30},3:{"armor":50},4:{"armor":70,"slow":2}}},
    "Ionia":       {"bps":[2,3,5],      "effects":{2:{"dodge":0.12},3:{"dodge":0.18},5:{"dodge":0.25,"lifesteal":0.08}}},
    "Mystic":      {"bps":[2,4,6],      "effects":{2:{"mr":15},4:{"mr":25},6:{"mr":35}}},
    "Pirate":      {"bps":[3,5,7],      "effects":{3:{"component_on_win":1},5:{"chest":1},7:{"chest":2}}},
    "Shurima":     {"bps":[2,3,4],      "effects":{2:{"towers":1},3:{"towers":2},4:{"tower_hp_mult":1.5,"root":1}}},
    "Shadow Isles":{"bps":[2,3,5,6],    "effects":{2:{"shade_hp":0.2},3:{"shade_hp":0.3},5:{"shade_lifesteal":0.10},6:{"shade_lifesteal":0.15}}},
    "Targon":      {"bps":[2,3,5,6],    "effects":{2:{"shield":0.15},3:{"shield":0.20},5:{"shield":0.25,"heal":0.10},6:{"shield":0.35,"heal":0.15}}},
    "Undead":      {"bps":[2,4],        "effects":{2:{"zombie_hp":0.20},4:{"zombie_hp":0.30,"zombie_dmg":0.10}}},
    "Void":        {"bps":[2,3,5],      "effects":{2:{"ignore_def":0.20},3:{"ignore_def":0.30},5:{"ignore_def":0.45}}},
    # Classes
    "Assassin":    {"bps":[2,4,6],      "effects":{2:{"dmg_mul":1.4},4:{"dmg_mul":1.5},6:{"dmg_mul":1.75}}},
    "Brawler":     {"bps":[2,4,6],      "effects":{2:{"hp_bonus":150},4:{"hp_bonus":200},6:{"hp_bonus":250,"reflect":0.10}}},
    "Sharpshooter":{"bps":[2,4,6],      "effects":{2:{"splash":0.15},4:{"splash":0.20},6:{"splash":0.25,"bounce":1}}},
    "MysticClass": {"bps":[2,4,6],      "effects":{2:{"mr":20},4:{"mr":30},6:{"mr":40,"shield":0.10}}},
    "Colossus":    {"bps":[2,4],        "effects":{2:{"dmg_red":0.20},4:{"dmg_red":0.30}}},
    "Duelist":     {"bps":[2,4,6],      "effects":{2:{"atk_spd":0.10},4:{"atk_spd":0.15},6:{"atk_spd":0.20}}},
    "Enchanter":   {"bps":[2,4],        "effects":{2:{"heal_all":0.10},4:{"heal_all":0.15,"regen":5}}},
    "Artillery":   {"bps":[2,4],        "effects":{2:{"range":0.15},4:{"range":0.20,"aoe":0.10}}},
}

# --- HJÆLPE-FUNKTIONER ---
def draw_text(surface, text, x, y, size=24, color=BLACK):
    font = pygame.font.SysFont(None, size)
    surface.blit(font.render(text, True, color), (x, y))

def draw_health_bar(surface, x, y, current_hp, max_hp, width=40, height=6):
    if max_hp <= 0: return
    hp_ratio = max(0, current_hp / max_hp)
    pygame.draw.rect(surface, RED, (x, y, width, height))
    pygame.draw.rect(surface, GREEN, (x, y, int(width * hp_ratio), height))

# --- CHAMPION-KLASSE ---
class Champion:
    def __init__(self, name, cost, hp, dmg, origin, klass, star=1):
        self.name, self.cost = name, cost
        self.base_hp, self.base_dmg = hp, dmg
        self.origin, self.klass = origin, klass
        self.star = star
        self.max_hp = self.base_hp * (self.star * 0.75)
        self.current_hp = self.max_hp
        self.damage = self.base_dmg * self.star
        self.x = self.y = 0
        # Stats for buffs
        self.armor = 0; self.mr = 0; self.shield = 0
        self.lifesteal = 0; self.dodge = 0; self.mana = 0

    def apply_traits(self, trait_counts):
        # Origin buffs
        if trait_counts.get(self.origin, 0) > 0:
            tb = TRAIT_BUFFS.get(self.origin, {})
            for bp in tb.get("bps", []):
                if trait_counts[self.origin] >= bp:
                    for k, v in tb["effects"][bp].items(): setattr(self, k, getattr(self, k, 0) + v)
        # Class buffs
        class_key = self.klass if self.klass != "Mystic" else "MysticClass"
        if trait_counts.get(self.klass, 0) > 0 or (self.klass == "Mystic" and trait_counts.get(self.klass, 0) > 0):
            tb = TRAIT_BUFFS.get(class_key, {})
            for bp in tb.get("bps", []):
                if trait_counts.get(self.klass, 0) >= bp:
                    for k, v in tb["effects"][bp].items(): setattr(self, k, getattr(self, k, 0) + v)

    def attack(self, target):
        # Dodge
        if random.random() < target.dodge:
            print(f"{target.name} dodger angrebet!")
            return
        dmg = self.damage * getattr(self, "dmg_mul", 1)
        heal = dmg * self.lifesteal
        self.current_hp = min(self.max_hp, self.current_hp + heal)
        # Shield absorption
        if target.shield > 0:
            if target.shield >= dmg: target.shield -= dmg; dmg = 0
            else: dmg -= target.shield; target.shield = 0
        target.current_hp = max(0, target.current_hp - dmg)
        print(f"{self.name} slår {target.name}: {dmg} dmg, heal {heal}")

    def draw(self, surface):
        pygame.draw.rect(surface, BLUE, (self.x, self.y, 40, 40))
        draw_text(surface, f"{self.name}({self.star}★)", self.x, self.y-15, size=18)
        draw_health_bar(surface, self.x, self.y-8, self.current_hp, self.max_hp)

# --- ALL CHAMPIONS ---
ALL_CHAMPIONS = [
    ("Ziggs",1,120,30,"Astral","Invoker"),("Kled",1,130,35,"Noxian","Duelist"),
    ("Tristana",1,110,40,"Pirate","Sharpshooter"),("Yorick",1,140,25,"Undead","Colossus"),
    ("Vex",1,125,28,"Undead","Enchanter"),("Olaf",1,135,32,"Freljord","Brawler"),
    ("Senna",1,100,45,"Shadow Isles","Sharpshooter"),("Maokai",1,150,20,"Freljord","Brawler"),
    ("Pyke",1,115,38,"Bilgewater","Assassin"),("Malzahar",1,105,42,"Void","Invoker"),
    ("Sett (baby)",1,145,22,"Ionia","Brawler"),("Neeko",1,128,30,"Ionia","Mystic"),
    ("Lux",2,250,60,"Demacia","Invoker"),("Illaoi",2,270,55,"Bilgewater","Colossus"),
    ("Twitch",2,240,65,"Ionia","Assassin"),("Rakan",2,260,58,"Ionia","Warden"),
    ("Diana",2,230,70,"Targon","Assassin"),("Kalista",2,220,75,"Shadow Isles","Sharpshooter"),
    ("Pantheon",2,280,50,"Targon","Duelist"),("Annie",2,245,62,"Astral","Invoker"),
    ("Nautilus",2,290,48,"Shadow Isles","Colossus"),("Quinn",2,235,68,"Demacia","Sharpshooter"),
    ("Warwick",2,265,59,"Bilgewater","Brawler"),("Taliyah",2,255,63,"Shurima","Artillery"),
    ("Cassiopeia",3,350,80,"Shurima","Warden"),("Rek'Sai",3,370,75,"Void","Colossus"),
    ("Miss Fortune",3,345,85,"Bilgewater","Artillery"),("Lillia",3,360,78,"Ionia","Mystic"),
    ("Sivir",3,330,88,"Shurima","Sharpshooter"),("Braum",3,380,70,"Freljord","Warden"),
    ("Swain",3,350,82,"Noxian","Invoker"),("Varus",3,340,86,"Void","Artillery"),
    ("Poppy",3,375,74,"Demacia","Colossus"),("Talon",3,335,90,"Noxian","Assassin"),
    ("Zyra",3,320,92,"Targon","Mystic"),("Zilean",3,300,95,"Targon","Invoker"),
    ("Kindred",4,450,100,"Shadow Isles","Sharpshooter"),("Lissandra",4,430,102,"Freljord","Invoker"),
    ("Mordekaiser",4,470,98,"Shadow Isles","Warden"),("Tryndamere",4,460,99,"Freljord","Duelist"),
    ("Jhin",4,440,104,"Ionia","Sharpshooter"),("Udyr",4,480,95,"Freljord","Brawler"),
    ("Orianna",4,410,115,"Piltover","Enchanter"),("Darius",4,455,101,"Noxian","Warden"),
    ("Kai'Sa",4,425,108,"Void","Artillery"),("Cho'Gath",4,485,94,"Void","Colossus"),
    ("Viego",4,435,103,"Shadow Isles","Assassin"),("Aurelion Sol",5,550,130,"Astral","Invoker"),
    ("Sion",5,580,125,"Shadow Isles","Colossus"),("Katarina",5,540,135,"Noxian","Assassin"),
    ("Yuumi",5,520,140,"Piltover","Enchanter"),("Gangplank",5,560,128,"Bilgewater","Duelist"),
    ("Naafiri",5,530,132,"Shadow Isles","Assassin"),("Soraka",5,510,138,"Targon","Mystic"),
    ("")
]

# --- SHOP ---
class Shop:
    def __init__(self, gold): self.gold, self.reroll_cost, self.shop_slots = gold,2,5; self.choices=[]
    def reroll(self, level):
        if self.gold < self.reroll_cost: return
        self.gold -= self.reroll_cost
        cap = 1 if level<=1 else 2 if level<=3 else 3 if level<=5 else 4 if level<=7 else 5
        allowed = [c for c in ALL_CHAMPIONS if c[1]<=cap]
        self.choices = random.choices(allowed, k=self.shop_slots)
    def can_buy(self, champ): return self.gold>=champ[1]
    def buy(self, champ, bench):
        if len(bench)>=MAX_BENCH_SLOTS or not self.can_buy(champ): return False
        self.gold -= champ[1]; bench.append(Champion(*champ)); return True

# --- MAIN LOOP ---
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("TFT Prototype")
    clock = pygame.time.Clock()
    player_level, player_xp = 1,0
    bench, board = [],[]
    shop=Shop(10); shop.reroll(player_level)
    selected,ox,oy=None,0,0; ticks=0
    running=True
    while running:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
            if e.type==pygame.KEYDOWN:
                if e.key==pygame.K_r: shop.reroll(player_level)
                if e.key==pygame.K_e and shop.gold>=GOLD_PER_XP:
                    shop.gold-=GOLD_PER_XP; player_xp+=XP_PER_BUY
                    if player_xp>=xp_to_next_level(player_level): player_xp-=xp_to_next_level(player_level); player_level+=1
                if e.key in [pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5]:
                    idx=e.key-pygame.K_1
                    if idx<len(shop.choices) and shop.choices[idx]:
                        if shop.buy(shop.choices[idx],bench): shop.choices[idx]=None
            if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
                mx,my=e.pos
                for i,ch in enumerate(bench):
                    bx,by=BENCH_SLOT_POSITIONS[i]
                    if pygame.Rect(bx,by,40,40).collidepoint(mx,my): selected,ox,oy=ch,mx-bx,my-by; break
            if e.type==pygame.MOUSEMOTION and selected: mx,my=e.pos; selected.x,selected.y=mx-ox,my-oy
            if e.type==pygame.MOUSEBUTTONUP and e.button==1 and selected:
                mx,my=e.pos; placed=False
                for j in range(MAX_BOARD_SLOTS):
                    bx,by=BOARD_SLOT_POSITIONS[j]
                    if pygame.Rect(bx,by,40,40).collidepoint(mx,my) and j>=len(board):
                        bench.remove(selected); board.insert(j,selected); selected.x,selected.y=bx,by; placed=True; break
                if not placed: bi=bench.index(selected); selected.x,selected.y=BENCH_SLOT_POSITIONS[bi]
                selected=None
        while len(board)<2 and bench: c=bench.pop(0); board.append(c); idx=len(board)-1; c.x,c.y=BOARD_SLOT_POSITIONS[idx]
        trait_counts={}
        for c in bench+board:
            for t in (c.origin,c.klass): trait_counts[t]=trait_counts.get(t,0)+1
        for c in bench+board: c.apply_traits(trait_counts)
        screen.fill(WHITE)
        draw_text(screen,f"Guld:{shop.gold}",20,20)
        draw_text(screen,f"Lvl:{player_level}",20,50)
        draw_text(screen,f"XP:{player_xp}/{xp_to_next_level(player_level)}",20,80)
        for i,ch in enumerate(shop.choices): x=200+i*140; draw_text(screen,f"{i+1}){ch[0]}({ch[1]}g)" if ch else f"{i+1})(tom)",x,50)
        draw_text(screen,"Bench:",20,340); [ (setattr(ch,"x",BENCH_SLOT_POSITIONS[i][0]), setattr(ch,"y",BENCH_SLOT_POSITIONS[i][1]), ch.draw(screen)) for i,ch in enumerate(bench) ]
        draw_text(screen,"Board:",20,420); [ (setattr(ch,"x",BOARD_SLOT_POSITIONS[i][0]), setattr(ch,"y",BOARD_SLOT_POSITIONS[i][1]), ch.draw(screen)) for i,ch in enumerate(board) ]
        ticks+=1
        if ticks>=FPS and len(board)>=2: a,b=board[0],board[1]; a.attack(b); b.attack(a) if b.current_hp>0 else None; ticks=0
        pygame.display.flip()
    pygame.quit()

if __name__=="__main__": main() 
