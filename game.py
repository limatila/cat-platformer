#space-arrivers -- um jogo platformer 
from random import choice, randint, choices
from math import floor
import pgzrun

from pygame import Rect

#* Init
TITLE = 'Space Arrivers'
WIDTH = 700
HEIGHT = 500
BG_COLOR = (147, 246, 255)

#music
currentVolume = 0.0     #! change later
music.set_volume(currentVolume)
music.play("menu") #menu, initial theme

grassHeightRatio = 5 #where the grass begins
GROUND_HEIGHT: int = HEIGHT - HEIGHT // grassHeightRatio
TOP_GROUND_HEIGHT: int = GROUND_HEIGHT - 12

# including used images
sceneTiles: dict = {
    "dirt": "tile_0000",
    "dirtConnected": "tile_0002",
    "grass": "tile_0016",
    "grassConnected": "tile_0018",
    "mud": "tile_0040",
    "mudConnected": "tile_0104"
}
characterTiles: dict = {
    #good
    "hero_0": "hero_0000",
    "hero_1": "hero_0001",
    "friend_0": "friend_0000",
    "friend_1": "friend_0001",
    
    #bad
    "enemy1_0": "enemy_0000",
    "enemy1_1": "enemy_0001",
    "enemy2_0": "enemy_0002",
    "enemy2_1": "enemy_0003"
}

#for text
defaultShadow = (0.5, 0.5) #shadow= arg

#initial states
hero = Actor(characterTiles["hero_0"])
hero.topleft = (WIDTH // 2, GROUND_HEIGHT - 30)
hero.lifes = 5
hero.points = 0 # 20: bronze, 50: silver, 100: gold!, 150: platinum!

NPCs: list['Actor'] = []

#movement and gravity measures
heroMovementVelocity = 3
heroVerticalVelocity = 0
gravityAceleration = 0.3
jumpAcceleration = -13

#npcs
npcMovementVelocitys = [1, 1.5, 2, 3, 5] 

#* Actions & Main
def generateRandomChar():
    randCharChoice = str(choices(
        ['enemy1', 'enemy2', 'friend'], 
        weights=(0.4, 0.4, 0.2)
    )[0])
    newChar = Actor(characterTiles[randCharChoice + '_0'])
    newChar.topleft = (randint(30, WIDTH - 30), GROUND_HEIGHT - 24)

    NPCs.append(newChar)

clock.schedule_unique(generateRandomChar, 0)
clock.schedule_unique(generateRandomChar, 0)
clock.schedule_unique(generateRandomChar, 0)

clock.schedule_unique(generateRandomChar, 2) 
clock.schedule_unique(generateRandomChar, 5)
clock.schedule_interval(generateRandomChar, randint(8,12))

def alternateHeroPoses():
    #Hero animations
    if floor(hero.y) < TOP_GROUND_HEIGHT: #floating
        hero.image = characterTiles["hero_0"]
    elif hero.image == characterTiles["hero_0"]:
        hero.image = characterTiles["hero_1"]
    elif hero.image == characterTiles["hero_1"]:
        hero.image = characterTiles["hero_0"]

def alternateNPCPoses():
    for npc in NPCs:
        #could be better using 'from itertools import cycle...'
        if 'friend' in npc.image:
            npc.image = characterTiles["friend_1"] if npc.image == characterTiles["friend_0"] else characterTiles["friend_0"]
        if 'enemy' in npc.image:
            if 'enemy1':
                npc.image = characterTiles["enemy1_1"] if npc.image == characterTiles["enemy1_0"] else characterTiles["enemy1_0"]
            elif 'enemy2':
                npc.image = characterTiles["enemy2_1"] if npc.image == characterTiles["enemy2_0"] else characterTiles["enemy2_0"]

def scheduleCharacterAnimations():
    print("animations scheduled!")
    clock.schedule_interval(alternateHeroPoses, 0.6)
    clock.schedule_interval(alternateNPCPoses, 1)

def draw(): #place in screen
    screen.fill(BG_COLOR) 

    #drawing grass
    for leftPosition in range(WIDTH):
        if leftPosition % 18 == 0: #every 10 pixels?
            newDirt = Actor(sceneTiles["dirtConnected"])
            newDirt.topleft = (leftPosition, GROUND_HEIGHT)
            newDirt.draw()

    #drawing dirt bellow
    initialTopPosition: int = GROUND_HEIGHT #positioning bellow grass
    for topPosition in range(initialTopPosition, HEIGHT):
        if topPosition % 18 == 0:
            for leftPosition in range(WIDTH):
                if leftPosition % 18 == 0: #every 10 pixels?
                    newDirt = Actor(sceneTiles["mudConnected"])
                    newDirt.topleft = (leftPosition, topPosition)
                    newDirt.draw()

    #drawing objects
    hero.draw()

    for npc in NPCs:
        npc.draw()
    
    #drawing debug info
    screen.draw.text("y: " + str(hero.y), (0,0), shadow=defaultShadow)
    screen.draw.text("v: " + str(heroVerticalVelocity), (0,15), shadow=defaultShadow)
    screen.draw.text("m: " + str(heroMovementVelocity), (0,30), shadow=defaultShadow)
    screen.draw.text("j: " + str(jumpAcceleration), (0,45), shadow=defaultShadow)
    screen.draw.text("volume: " + str(round(currentVolume*10)), (0,60), shadow=defaultShadow)

    screen.draw.text("up key: " + str(keyboard.up), (0,90), shadow=(0.3, 0.5))
    screen.draw.text("down key: " + str(keyboard.down), (0,105), shadow=(0.3, 0.5))

def update(): #process
    global heroVerticalVelocity

    #* movement
    if keyboard.right:
        hero.x += heroMovementVelocity
    if keyboard.left:
        hero.x -= heroMovementVelocity
    #jumping
    if keyboard.up and floor(hero.y) == TOP_GROUND_HEIGHT:
        heroVerticalVelocity += jumpAcceleration
    #landing down
    if keyboard.down and hero.y < TOP_GROUND_HEIGHT:
        heroVerticalVelocity += 1

    #* collision w/ ground and gravity
    if hero.y > TOP_GROUND_HEIGHT:
        hero.y = TOP_GROUND_HEIGHT
        heroVerticalVelocity = 0

    #apply gravity
    hero.y += heroVerticalVelocity
    heroVerticalVelocity += gravityAceleration

    #world border
    if hero.x > WIDTH - 10:
        hero.x = WIDTH - 10
    elif hero.x < 10:
        hero.x = 10

    #NPC logic
    for npc in NPCs:
        #assigning a speed
        if not hasattr(npc, "speed"):
            if 'enemy' in npc.image:
                npc.speed = float(choices(
                    npcMovementVelocitys,
                    weights=(1, 2, 3, 2, 1)    
                )[0])
            elif 'friend' in npc.image:
                npc.speed = choice(npcMovementVelocitys[:1])

        #assinging a direction
        directions = ['left', 'right']
        if not hasattr(npc, "direction"):
            if npc.x > WIDTH // 2:
                npc.direction = directions[0]
            if npc.x < WIDTH // 2:
                npc.direction = directions[1]

            print(f"spawned one {'Enemy' if 'enemy' in npc.image else 'Friend'} going {npc.direction}, at initial speed {npc.speed}")

        #movement
        match(npc.direction):
            case 'left':
                npc.x -= npc.speed
            case 'right':
                npc.x += npc.speed

        #only enemy will bounce in walls
        if 'enemy' in npc.image:
            lastDirection: str = npc.direction
            randVelocityModifier = int(choices(
                (-1, 1, 2), 
                weights=(0.4, 0.5, 0.1)
            )[0])
            
            #apply only on bounce event
            if npc.x <= 10:
                npc.direction = directions[1]
                npc.speed += randVelocityModifier
            elif npc.x >= WIDTH - 10:
                npc.direction = directions[0]
                npc.speed += randVelocityModifier

            if not npc.direction == lastDirection: print(f"{npc.image} changed direction to: {npc.direction}, at speed {npc.speed}")

#more bindings
def on_key_down(key):
    global currentVolume

    match(key):
        #escape button - exits game
        case keys.ESCAPE:
            exit()
        #page up/down - volume keys
        case keys.PAGEUP:
            if currentVolume + 0.1 <= 1.0:
                currentVolume += 0.1
                music.set_volume(currentVolume)
        case keys.PAGEDOWN:
            if currentVolume - 0.1 >= 0.0:
                currentVolume -= 0.1
                music.set_volume(currentVolume)

scheduleCharacterAnimations()

pgzrun.go()