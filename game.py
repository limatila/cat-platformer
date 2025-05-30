#space-arrivers -- um jogo platformer 
#! Atenção: pela documentação do pgzero, 'music' pode não estar disponível para algumas distros linux. se bugar, use windows.
from random import choice, randint, choices
from math import floor
import pgzrun

from pygame import Rect #for enemy hitboxes
from pygame.mixer import Sound #! necessário, ou os sons de Sfx ficariam muito altos.

DEBUG = True #show debug text ingame

#* PgZero Init
TITLE = 'Space Arrivers'
WIDTH = 700
HEIGHT = 500
game_state: str = "menu" #menu | game | end
BG_COLORS = {
    "menu": (96, 125, 242),
    "game": (147, 246, 255),
    "end": (4, 5, 60),
}
#music
currentVolume = 0.3     #TODO: change default
music.set_volume(currentVolume)
music.play("menu") #menu, initial theme

#* Needed Values
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
for sfx in soundEffects.values():
    sfx.set_volume(currentVolume)

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
helpTexts = ["Esc to quit", "Page Up increase volume", "Page Down decrease volume", "Up to jump", "Down to fall down", "Left and Right to move",
                             "The objective is get the most points possible, killing ENEMYs,",
                             "You kill enemys by jumping in their heads,",
                             "You can take DAMAGE, and will HEAL with Blue FRIENDs,",
                             "The game ends after you lose all LIFES",
                             "You'll win medals for the most POINTs you get!"]
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
hero.lifes: int = 1     #TODO: change default
hero.points: int = 0    #20: bronze, 50: silver, 100: gold!, 150: platinum!
hero.invincible: bool = False

NPCs: list['Actor'] = []

#movement and gravity measures
heroMovementVelocity = 3
heroVerticalVelocity = 0
gravityAceleration = 0.3
jumpAcceleration = -13

#npcs
npcMovementVelocitys = [1, 1.5, 2, 3, 5] 
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
    10: "honorable mention",
    20: "bronze",
    50: "silver",
    100: "gold",
    150: "platinum",
    200: "ok you need to stop."
}

#* end menu


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

    #TODO: hero invincible if spawned too much close

    NPCs.append(newChar)

def generateRandNpcAttributes(npc: 'Actor'):
    global NPCDirections
    haveSpeed = True
    haveDirection = True

    #assigning a speed
    if not hasattr(npc, "speed"):
        haveSpeed = False
        if 'enemy' in npc.image:
            npc.speed = float(choices(
                npcMovementVelocitys,
                weights=(1, 2, 3, 2, 1)    
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
        print(f"spawned one {'Enemy' if 'enemy' in npc.image else 'Friend'} going {npc.direction}, at initial speed {npc.speed}")

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
    if floor(hero.y) < TOP_GROUND_HEIGHT: #floating
        hero.image = characterTiles["hero_0"]
    hero.image = characterTiles[next(heroGenerator)]

def alternateNPCPoses():
    for npc in NPCs:
        npc.image = characterTiles[next(npc.frameGenerator)]

#Actions and more
def isTopCollision(npc: 'Actor', size: int = 8) -> bool:
    hitbox = Rect(
        npc.left - 8, npc.top - 4, 
        npc.width + (size*2), 8
    )
    return hero.colliderect(hitbox) and heroVerticalVelocity > 0 #check if it's falling

def changeHeroInvicibility(changeTo: bool = False):
    hero.invincible = changeTo if changeTo == True else False
    clock.schedule_unique(changeHeroInvicibility, 2)

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
            print("INCREASING DIFFICULTY!")
            break; 


def scheduleCharacterSpawnings():
    clock.schedule_unique(generateRandomChar, 2)
    clock.schedule_unique(generateRandomChar, 1)

    clock.schedule_interval(generateRandomChar, randint(6,12))
    clock.schedule_interval(checkForHarderScores, 3)
    print("spawnings scheduled!")

def scheduleCharacterAnimations():
    clock.schedule_interval(alternateHeroPoses, 0.6)
    clock.schedule_interval(alternateNPCPoses, 1)
    print("animations scheduled!")

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
                # drawY = HEIGHT - 18
                drawY = HEIGHT // 5 * 3
                # for text in helpTexts:
                #     if text.startswith("The objective"):
                #         drawY = HEIGHT - 18
                #         drawX = WIDTH // 6 * 3
                #     screen.draw.text(str(text), (drawX, drawY), shadow=(titleTextShadow))
                #     drawY -= 16
                for text in helpTexts:
                    if text.startswith("The objective"): drawY += 16
                    screen.draw.text(str(text), (0, drawY), shadow=titleTextShadow)
                    drawY += 16
            

        #** game match
        case "game": 
            for ground in groundsToDraw:
                ground.draw()

            #drawing characters/objects
            hero.draw()

            for npc in NPCs:
                npc.draw()
                
                if DEBUG:
                    hitbox = Rect(
                        npc.left - 8, npc.top - 4, 
                        npc.width + 16, 8
                    )
                    screen.draw.rect(hitbox, (200, 0, 0))
            
            if DEBUG:
                screen.draw.text("y: " + str(hero.y), (0,0), shadow=debugTextShadow)
                screen.draw.text("v: " + str(heroVerticalVelocity), (0,15), shadow=debugTextShadow)
                screen.draw.text("NPC count: " + str(len(NPCs)), (0,30), shadow=debugTextShadow)
                screen.draw.text("volume: " + str(round(currentVolume*10)), (0,60), shadow=debugTextShadow)

                screen.draw.text("invincible: " + str(hero.invincible), (WIDTH - WIDTH // 4.5, 0), shadow=(0.8, 0.5))
                screen.draw.text("lifes: " + str(hero.lifes), (WIDTH - WIDTH // 4.5, 30), shadow=(0.8, 0.5))
                screen.draw.text("POINTS: " + str(hero.points), (WIDTH - WIDTH // 4.5, 60), shadow=(0.8, 0.5))
            else:
                ... 
                #TODO: draw lifes, points

        #** game ending
        case "end": 
                screen.draw.text("Game Over", center=(WIDTH // 2, (HEIGHT // 5) * 1), shadow=(titleTextShadow), fontsize=buttonTextSize + 32, color=(234, 78, 60))

                medalText: str = None
                for score, medal in scoreMedals.items():
                    if hero.points >= score:
                        medalText = str(medal)

                if medalText:
                    screen.draw.text(f"You got a {medalText.title()} medal!", center=(WIDTH // 2, (HEIGHT // 5) * 2), shadow=(titleTextShadow), fontsize=buttonTextSize)
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

                    if npc.direction != lastDirection and wasTired: print(f"{npc.image} changed direction to: {npc.direction}, at speed {npc.speed}{", and was tired out!" if wasTired else ""}")
    
            heroLifesBefore = hero.lifes
            wasHit = False
            #collisions with npcs (soul of the game)
            for npc in NPCs:
                if hero.colliderect(npc):
                    if 'enemy' in npc.image:
                        #collision at top: kills
                        if isTopCollision(npc, size=10):
                            soundEffects["kill"].play()
                            NPCs.remove(npc)
                            hero.points += 1
                        else:  
                            #side collision: hurts
                            if not wasHit and not hero.invincible: #invencibility frames
                                soundEffects["hurt"].play()
                                hero.lifes -= 1
                                changeHeroInvicibility(True)
                                wasHit = True
                    elif 'friend' in npc.image:
                        soundEffects["heal"].play()
                        hero.lifes += 1 if hero.lifes + 1 <= 5 else 0
                        NPCs.remove(npc)
                        print('friend met!')

            if heroLifesBefore > hero.lifes:
                changeHeroInvicibility(True)

            #game ending
            if hero.lifes <= 0:
                print("died!")
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
                for sfx in soundEffects.values():
                    sfx.set_volume(currentVolume)
        case keys.PAGEDOWN:
            if currentVolume - 0.1 >= 0.0:
                currentVolume -= 0.1
                currentVolume = currentVolume
                music.set_volume(currentVolume)
                for sfx in soundEffects.values():
                    sfx.set_volume(currentVolume)

#Clicks
volumeBeforeMute: int
def on_mouse_down(pos):
    global game_state, currentVolume, volumeBeforeMute, drawHelpText

    #sound button - mute/unmute
    match(game_state):
        case "menu":
            if soundButton.collidepoint(pos):
                if currentVolume > 0: 
                    print("mute")
                    volumeBeforeMute = currentVolume
                    currentVolume = 0
                else: 
                    print("mute")
                    currentVolume = volumeBeforeMute

                music.set_volume(currentVolume)
                for sfx in soundEffects.values():
                    sfx.set_volume(currentVolume)
            
            elif startButton.collidepoint(pos):
                game_state = "game"
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