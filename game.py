#space-arrivers -- um jogo platformer 
from random import randint
from math import floor

from pygame import Rect

#* Init
WIDTH = 700
HEIGHT = 500
BG_COLOR = (147, 246, 255)

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
    "hero_0": "hero_0000",
    "hero_1": "hero_0001",
    "enemy_1": "",
    "enemy_2": ""
}

#initial states
hero = Actor(characterTiles["hero_0"])
hero.topleft = (WIDTH // 2, GROUND_HEIGHT - 24)

#gravity
heroMovementVelocity = 3
heroVerticalVelocity = 0
gravityAceleration = 0.3
jumpAcceleration = -20


#* Actions & Main
def generateRandomEnemy(): ...

def alternateHeroPoses():
    if hero.image == characterTiles["hero_0"]:
        hero.image == characterTiles["hero_1"]
    elif hero.image == characterTiles["hero_1"]:
        hero.image == characterTiles["hero_0"]

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

def update(): #process
    
    global heroVerticalVelocity

    #* movement
    if keyboard.right:
        hero.x += heroMovementVelocity
    if keyboard.left:
        hero.x -= heroMovementVelocity
    #jumping
    if keyboard.up and floor(hero.y) == TOP_GROUND_HEIGHT:
        print("jump")
        heroVerticalVelocity = jumpAcceleration
    if hero.y < TOP_GROUND_HEIGHT and keyboard.down:
        print("going down")
        heroVerticalVelocity += 2

    #* collision w/ ground and gravity
    if hero.y > TOP_GROUND_HEIGHT:
        hero.y = TOP_GROUND_HEIGHT
        heroVerticalVelocity = 0

    if hero.x > WIDTH - 10:
        hero.x = WIDTH - 10
    elif hero.x < 10:
        hero.x = 10

    #apply gravity
    heroVerticalVelocity += gravityAceleration
    hero.y += heroVerticalVelocity

