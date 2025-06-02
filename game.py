#space-arrivers -- um jogo platformer 
#! Atenção: pela documentação do pgzero, 'music' pode não estar disponível para algumas distros linux. se bugar, use windows.
from random import choice, randint, choices
from math import floor
import pgzrun

from pygame import Rect #for enemy hitboxes
from pygame.mixer import Sound #! necessário, ou os sons de Sfx ficariam muito altos.
import pygame #! linhas usando 'music', compatível com pgzero, estão pedindo pelo init do pygame.
pygame.init()

DEBUG = False #show debug text ingame

#* PgZero Init
TITLE = 'Space Stompers'
WIDTH = 700
HEIGHT = 500
game_state: str = "menu" #menu | game | end
BG_COLORS = {
    "menu": (96, 125, 242),
    "game": (147, 246, 255),
    "end": (4, 5, 60),
}
#music
currentVolume = 0.2
music.set_volume(currentVolume)
music.play("menu") #menu, initial theme

#* Needed Values
grassHeightRatio = 5 #where the grass begins
GROUND_HEIGHT: int = HEIGHT - HEIGHT // grassHeightRatio
TOP_GROUND_HEIGHT: int = GROUND_HEIGHT - 12

# including used images
sceneTiles: dict = {
    "dirtConnected": "tile_0002",
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
soundTiles: dict[bool, str] = {
    True: "sound_on",
    False: "sound_off",
}

# including used sfx
soundsPrefix = "sounds/"
soundsSuffix = ".mp3"
soundEffects: dict[str, Sound] = {
    "fall": Sound(soundsPrefix + "fall" + soundsSuffix),
    "heal": Sound(soundsPrefix + "heal" + soundsSuffix),
    "hurt": Sound(soundsPrefix + "hurt" + soundsSuffix),
    "jump": Sound(soundsPrefix + "jump" + soundsSuffix),
    "kill": Sound(soundsPrefix + "kill" + soundsSuffix),
    "landing": Sound(soundsPrefix + "landing1" + soundsSuffix),
    "spawn": Sound(soundsPrefix + "spawn" + soundsSuffix),
    "start": Sound(soundsPrefix + "start" + soundsSuffix)
}
for key, sfx in soundEffects.items():
    sfx.set_volume(currentVolume)
    if key == "jump":
        sfx.set_volume(max(floor((currentVolume - 0.1) * 10)/10, 0))

#*menu initial states
buttonDefaultSizes = (
    0,#left
    0,#top
    200,#width
    65#height
)
quitButton = Rect(buttonDefaultSizes)
startButton = Rect(buttonDefaultSizes)
helpButton = Rect(buttonDefaultSizes)
soundButton = Actor(soundTiles[True])

#positions
soundButton.topleft = (WIDTH - 80, 50)
startButton.center  = ((WIDTH // 2) - 120, (HEIGHT // 5) * 2.5)
quitButton.center   = ((WIDTH // 2) + 120, (HEIGHT // 5) * 2.5) 
helpButton.center   = (WIDTH // 2, (HEIGHT // 5) * 3.5) 

#text defaults
drawHelpText = False
helpTexts = ["Esc to QUIT", "Page Up to + Volume", "Page Down to- Volume", "Up to Jump", "Down to Fall", "Left and Right to move",
                             "The objective is get the most points killing ENEMYs,",
                             "Kill ENEMYs by jumping in their heads,",
                             "Blue FRIENDs heal, and ENEMYs do damage,",
                             "The game ends after you lose all LIFES",
                             "Play well and win MEDALs!"]
buttonTextSize = 50

buttonTextShadow = (0.3, 0.3)
titleTextShadow = (0.6, 0.6)
debugTextShadow = (0.5, 0.5) #shadow= arg

#*game initial states
groundsToDraw: list['Actor'] = []
#drawing grass
for leftPosition in range(WIDTH):
    if leftPosition % 18 == 0: #every 10 pixels?
        newDirt = Actor(sceneTiles["dirtConnected"])
        newDirt.topleft = (leftPosition, GROUND_HEIGHT)
        groundsToDraw.append(newDirt)

#drawing ground bellow
for topPosition in range(GROUND_HEIGHT, HEIGHT):
    if topPosition % 18 == 0:
        for leftPosition in range(WIDTH):
            if leftPosition % 18 == 0: #every 10 pixels?
                newMud = Actor(sceneTiles["mudConnected"])
                newMud.topleft = (leftPosition, topPosition)
                groundsToDraw.append(newMud)

hero = Actor(characterTiles["hero_0"])
hero.topleft: tuple = (WIDTH // 2, GROUND_HEIGHT - 30)
hero.lifes: int = 3
hero.points: int = 0  #? more points, better medals!
hero.invincible: bool = True

NPCs: list['Actor'] = []

#movement and gravity measures
heroMovementVelocity = 3
heroVerticalVelocity = 0
gravityAceleration = 0.3
jumpAcceleration = -13

#npcs
npcMovementVelocitys = [1, 1.5, 2, 3, 5, 6] 
NPCDirections = ['left', 'right']

harderScoresSchedules: dict[int, bool] = { 
    #as if -- hero.points: state
    6: False,
    12: False,
    30: False,
    40: False,
    70: False,
    100: False,
    200: False,
}
scoreMedals: dict[int, str] = {
    3: "honorable mention",
    20: "bronze",
    40: "silver",
    70: "gold",
    120: "platinum",
    150: "ok you need to stop."
}

#* Actions & Main
#npc generation
def generateRandomChar():
    if len(NPCs) >= 10: return
    else: soundEffects["spawn"].play()

    randCharChoice = str(choices(
        ['enemy1', 'enemy2', 'friend'], 
        weights=(0.45, 0.45, 0.1)
    )[0])
    newChar = Actor(characterTiles[randCharChoice + '_0'])
    newChar.topleft = (randint(30, WIDTH - 30), GROUND_HEIGHT - 24)
    generateRandNpcAttributes(newChar)

    #prevent immediate spawn damage
    if ((newChar.x in range(round(hero.x - WIDTH / 9), round(hero.x + WIDTH / 9))
        and newChar.y in range (round(hero.y - HEIGHT / 8), round(hero.y + HEIGHT / 8)))
        and 'enemy' in newChar.image):
        changeHeroInvicibility(True)
        print("[DEBUG] Enemy spawned too close, enabling invincibility")

    NPCs.append(newChar)

def generateRandNpcAttributes(npc: 'Actor'):
    global NPCDirections
    haveSpeed = True
    haveDirection = True

    #assigning a speed
    if not hasattr(npc, "speed"):
        haveSpeed = False
        if 'enemy' in npc.image:
            isHarderScores = True if hero.points >= 20 else False #then give more speed
            if isHarderScores:
                weightSelected = (0.5, 1, 2, 3, 1.2, 1)
            else: weightSelected = (1, 2, 2, 4, 1, 0.5) 
            npc.speed = float(choices(
                npcMovementVelocitys,
                weights=weightSelected
            )[0])
        elif 'friend' in npc.image:
            npc.speed = choice(npcMovementVelocitys[:1])

    #assigning a direction
    if not hasattr(npc, "direction"):
        haveDirection = False
        if npc.x > WIDTH // 2:
            npc.direction = NPCDirections[0]
        if npc.x < WIDTH // 2:
            npc.direction = NPCDirections[1]

    if not haveSpeed or not haveDirection:
        print(f"[DEBUG] spawned one {'Enemy' if 'enemy' in npc.image else 'Friend'} going {npc.direction}, at initial speed {npc.speed}")

    #assigning a frame cycle
    if not hasattr(npc, "frameGenerator"):
        npcTileKey = str([key for key, value in characterTiles.items()
                          if value == npc.image][0])[:-2]    #hero, enemy1
        newGen = characterFramesCycle(npcTileKey) 
        npc.frameGenerator = newGen

#hero and npc animations
def characterFramesCycle(characterPrefix: str = "hero"): #generator, needs to be instanciated then used with next()
    i = 0
    frameKeys = sorted([
        key for key in characterTiles
        if key.startswith(f"{characterPrefix}_")
    ])

    #not found error
    if not frameKeys:
        raise ValueError(f"No frames found for prefix '{characterPrefix}'.")

    while(i <= len(frameKeys)):
        try:
            yield frameKeys[i]
        except IndexError:
            i = 0
            yield frameKeys[i]
        if i >= len(frameKeys): i == 0 
        else: i += 1

heroGenerator = characterFramesCycle()

def alternateHeroPoses():
    hero.image = characterTiles[next(heroGenerator)]

def alternateNPCPoses():
    for npc in NPCs:
        npc.image = characterTiles[next(npc.frameGenerator)]

#Actions and more
def generateNPCHitbox(npc, size: int = 8) -> Rect:
    return Rect(npc.left - 8, npc.top - 8,  #leftop
                npc.width + (size*2), 8)    #width, height

def isTopCollision(npc: 'Actor', size: int = 8) -> bool:
    hitbox = generateNPCHitbox(npc, size)
    return hero.colliderect(hitbox) and heroVerticalVelocity > 0 #check if it's falling

def changeHeroInvicibility(changeTo: bool = False, addDelay: int = 0):
    hero.invincible = changeTo if changeTo == True else False
    clock.schedule_unique(changeHeroInvicibility, 2 + addDelay)

#Schedulers
def checkForHarderScores():
    for key in sorted(harderScoresSchedules.keys()):
        if harderScoresSchedules[key] == False and hero.points == key:
            match(harderScoresSchedules[key]):
                case 70:
                    clock.schedule_interval(generateRandomChar, 8)
                case 100:
                    clock.schedule_interval(generateRandomChar, 7)
                case 200:
                    clock.schedule_interval(generateRandomChar, 6)
                case _:
                    clock.schedule_interval(generateRandomChar, randint(8, 15))

            #does not continue to next keys
            harderScoresSchedules[key] = True
            print("[INFO] INCREASING DIFFICULTY!")
            break; 


def scheduleCharacterSpawnings():
    generateRandomChar()
    clock.schedule_unique(generateRandomChar, 2)
    clock.schedule_unique(generateRandomChar, 5)
    clock.schedule_unique(generateRandomChar, 9)

    clock.schedule_interval(generateRandomChar, randint(6,12))
    clock.schedule_interval(checkForHarderScores, 3)
    print("[INFO] spawnings scheduled!")

def scheduleCharacterAnimations():
    clock.schedule_interval(alternateHeroPoses, 0.6)
    clock.schedule_interval(alternateNPCPoses, 1)
    print("[INFO] animations scheduled!")

#* PgZero
def draw(): #place in screen
    screen.fill(BG_COLORS[game_state]) 

    match(game_state):
        #** game menu
        case "menu":
            #buttons 
            screen.draw.filled_rect(startButton, (80, 210, 80))
            screen.draw.filled_rect(quitButton, (230, 80, 80))
            screen.draw.filled_rect(helpButton, (255, 220, 170))
            soundButton.draw()

            #text
            screen.draw.text(str(TITLE), center=(WIDTH // 2, (HEIGHT // 5) * 1), shadow=(titleTextShadow), fontsize=buttonTextSize + 32)

            screen.draw.text("Start", center=(startButton.center), shadow=buttonTextShadow, fontsize=buttonTextSize)
            screen.draw.text("Quit", center=(quitButton.center), shadow=buttonTextShadow, fontsize=buttonTextSize)
            screen.draw.text("Help", center=(helpButton.center), shadow=buttonTextShadow, fontsize=buttonTextSize)

            if drawHelpText:
                drawY = HEIGHT // 5 * 3
                for text in helpTexts:
                    if text.startswith("The objective"): drawY += 16
                    screen.draw.text(str(text), (0, drawY), shadow=titleTextShadow)
                    drawY += 16
            

        #** game match
        case "game": 
            for ground in groundsToDraw:
                ground.draw()

            #drawing characters/objects
            for npc in NPCs:
                npc.draw()
                if DEBUG and 'enemy' in npc.image:
                    hitbox = generateNPCHitbox(npc)
                    screen.draw.rect(hitbox, (200, 0, 0))
            hero.draw()

            if DEBUG:
                screen.draw.text("y: " + str(hero.y), (0,0), shadow=debugTextShadow)
                screen.draw.text("v: " + str(heroVerticalVelocity), (0,15), shadow=debugTextShadow)
                screen.draw.text("NPC count: " + str(len(NPCs)), (0,30), shadow=debugTextShadow)
                screen.draw.text("volume: " + str(round(currentVolume*10)), (0,60), shadow=debugTextShadow)

                screen.draw.text("invincible: " + str(hero.invincible), (WIDTH - WIDTH // 4.5, 0), shadow=(0.8, 0.5))
                screen.draw.text("lifes: " + str(hero.lifes), (WIDTH - WIDTH // 4.5, 30), shadow=(0.8, 0.5))
                screen.draw.text("POINTS: " + str(hero.points), (WIDTH - WIDTH // 4.5, 60), shadow=(0.8, 0.5))
            else:
                screen.draw.text(f"Lifes: {hero.lifes}", (0, 20), shadow=buttonTextShadow) #draw hearts for every life
                screen.draw.text(f"Points: {hero.points}", (0, 40), shadow=buttonTextShadow)

                if hero.invincible:
                    screen.draw.text(f"Invincible", center=(WIDTH // 2, (HEIGHT // 4)), shadow=debugTextShadow, color=(255, 248, 73))


        #** game ending
        case "end": 
                screen.draw.text("Game Over", center=(WIDTH // 2, (HEIGHT // 5) * 1), shadow=(titleTextShadow), fontsize=buttonTextSize + 32, color=(234, 78, 60))

                medalText: str = None
                for score, medal in scoreMedals.items():
                    if hero.points >= score:
                        medalText = str(medal)

                if medalText:
                    screen.draw.text(f"You got a {medalText.title()} MEDAL, Nice!", center=(WIDTH // 2, (HEIGHT // 5) * 2), shadow=(titleTextShadow), fontsize=buttonTextSize - 18)
                screen.draw.text(f"{hero.points} points!", center=(WIDTH // 2, (HEIGHT // 5) * 2.6), shadow=(titleTextShadow), fontsize=buttonTextSize)

                screen.draw.filled_rect(quitButton, (230, 80, 80))
                screen.draw.text("Quit", center=(quitButton.center), shadow=buttonTextShadow, fontsize=buttonTextSize)

def update(): #process
    global game_state, heroVerticalVelocity

    match(game_state):
        #** game menu
        case "menu": 
            soundButton.image = soundTiles[True] if floor(currentVolume*10) > 0 else soundTiles[False]

        #** game match
        case "game":
            #hero jumping
            if floor(heroVerticalVelocity) < 0: #floating
                hero.image = characterTiles["hero_0"]
            elif floor(heroVerticalVelocity) > 0:
                hero.image = characterTiles["hero_1"]

            #* movement
            if keyboard.right:
                hero.x += heroMovementVelocity
            if keyboard.left:
                hero.x -= heroMovementVelocity
            #jumping
            if keyboard.up and floor(hero.y) == TOP_GROUND_HEIGHT:
                soundEffects["jump"].play()
                heroVerticalVelocity += jumpAcceleration
            #fall down
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

            #* NPC logic
            for npc in NPCs:
                #movement
                match(npc.direction):
                    case 'left':
                        npc.x -= npc.speed
                    case 'right':
                        npc.x += npc.speed

                #only enemy will bounce in walls
                if 'enemy' in npc.image:
                    lastDirection = str(npc.direction)
                    randVelocityModifier = int(choices(
                        (-1, 1, 2), 
                        weights=(0.4, 0.5, 0.1)
                    )[0])
                    
                    #apply only on bounce event
                    if npc.x <= 10:
                        npc.direction = NPCDirections[1]
                        npc.speed += randVelocityModifier
                    elif npc.x >= WIDTH - 10:
                        npc.direction = NPCDirections[0]
                        npc.speed += randVelocityModifier

                    #tired cap
                    wasTired = False
                    if npc.speed > 15: 
                        npc.speed = 1.5
                        wasTired = True

                    if npc.direction != lastDirection and wasTired: print(f"[DEBUG] {npc.image} changed direction to: {npc.direction}, at speed {npc.speed}{", and was tired out!" if wasTired else ""}")
    
            heroLifesBefore = hero.lifes
            wasHit = False
            #collisions with npcs (soul of the game)
            for npc in NPCs:
                if hero.colliderect(npc):
                    if 'enemy' in npc.image:
                        #collision at top: kills
                        if isTopCollision(npc):
                            soundEffects["kill"].play()
                            NPCs.remove(npc)
                            hero.points += 1
                            if npc.speed >= 6:
                                hero.points += 2 #? maybe create a different sprite for the fast enemy
                        else:  
                            #side collision: hurts
                            if not wasHit and not hero.invincible: #invencibility frames
                                soundEffects["hurt"].play()
                                hero.lifes -= 1
                                changeHeroInvicibility(True)
                                wasHit = True
                                print("[INFO] player hit, -1 life")
                    elif 'friend' in npc.image:
                        soundEffects["heal"].play()
                        hero.lifes += 1 if hero.lifes < 3 else 0
                        hero.points += 1
                        NPCs.remove(npc)
                        print('[INFO] friend met, +1 life!')

            if heroLifesBefore > hero.lifes:
                changeHeroInvicibility(True)

            #game ending
            if hero.lifes <= 0:
                print("[INFO] died, end of game")
                game_state = "end"
            
        #** game ending
        case "end": 
            quitButton.center = helpButton.center

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
                currentVolume = currentVolume
                music.set_volume(currentVolume)
                for key, sfx in soundEffects.items():
                    sfx.set_volume(currentVolume)
                    if key == "jump":
                        sfx.set_volume(max(floor((currentVolume - 0.1) * 10)/10, 0))
        case keys.PAGEDOWN:
            if currentVolume - 0.1 >= 0.0:
                currentVolume -= 0.1
                currentVolume = currentVolume
                music.set_volume(currentVolume)
                for key, sfx in soundEffects.items():
                    sfx.set_volume(currentVolume)
                    if key == "jump":
                        sfx.set_volume(max(floor((currentVolume - 0.1) * 10)/10, 0))

#Clicks
volumeBeforeMute: int
def on_mouse_down(pos):
    global game_state, currentVolume, volumeBeforeMute, drawHelpText

    #sound button - mute/unmute
    match(game_state):
        case "menu":
            if soundButton.collidepoint(pos):
                if currentVolume > 0: 
                    print("[INFO] muted")
                    volumeBeforeMute = currentVolume
                    currentVolume = 0
                else: 
                    print("[INFO] unmuted")
                    currentVolume = volumeBeforeMute

                music.set_volume(currentVolume)
                for sfx in soundEffects.values():
                    sfx.set_volume(currentVolume)
            
            #* init gameplay
            elif startButton.collidepoint(pos):
                game_state = "game"
                clock.schedule_unique(changeHeroInvicibility, 1.5)
                music.play("match")
                scheduleCharacterSpawnings()
                scheduleCharacterAnimations()

            elif quitButton.collidepoint(pos):
                exit()

            elif helpButton.collidepoint(pos):
                drawHelpText = not drawHelpText
        case "end":
            if quitButton.collidepoint(pos):
                exit()
            #? elif retry ???
    

pgzrun.go()