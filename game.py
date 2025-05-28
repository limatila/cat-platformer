#space-arrivers -- um jogo platformer 
from random import choice
from math import floor
import pgzrun

from pygame import Rect

#* Init
TITLE = 'Space Arrivers'
WIDTH = 700
HEIGHT = 500
BG_COLOR = (147, 246, 255)

#music
currentVolume = 0.2     #! change later
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
    "enemy1_1": "enemy_0000",
    "enemy1_2": "enemy_0001",
    "enemy2_1": "enemy_0002",
    "enemy2_2": "enemy_0003"
}

#for text
defaultShadow = (0.5, 0.5) #shadow= arg

#initial states
hero = Actor(characterTiles["hero_0"])
hero.topleft = (WIDTH // 2, GROUND_HEIGHT - 24)
hero.fps = 2

enemys: list['Actor'] = []

#gravity
heroMovementVelocity = 3
heroVerticalVelocity = 0
gravityAceleration = 0.3
jumpAcceleration = -13


#* Actions & Main
def generateRandomEnemy():
    randEnemyChoice = choice(['enemy1', 'enemy2', ''])
    newEnemy = Actor(randEnemyChoice)

def alternateHeroPoses():
    if floor(hero.y) < TOP_GROUND_HEIGHT: #floating
        hero.image = characterTiles["hero_0"]
    elif hero.image == characterTiles["hero_0"]:
        hero.image = characterTiles["hero_1"]
    elif hero.image == characterTiles["hero_1"]:
        hero.image = characterTiles["hero_0"]

clock.schedule_interval(alternateHeroPoses, 0.6)

def alternateEnemyPosed(): ...

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

#other bindings
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


pgzrun.go()