import pygame, sys
import time
import os
from colors import *
import math
from pygame import mixer
from pygame.locals import QUIT
import random

# Systems Init
pygame.init() # Initialize Pygame
mixer.init()  # Initialize Mixer Elements

# Basic Display Setup
SW = 400  # Screen Width
SH = 720  # Screen Height
screen = pygame.display.set_mode((SW, SH))
ESCAPELAYER = pygame.sprite.Group()
pygame.display.set_caption('Flappy Python!')
clock = pygame.time.Clock()  # Intialize The Clock Object For FPS Counting

# Basic Game Variables (Not UI Modifiers)
runningGame = True # Declare Intial runningGame State Of The Game
beginMenu = True # Intial Game State Is In Menu
escapeMenu = False # Waiting Menu Function
FPS = 60  # Declare Screen Initial Clock Rate Speed (Frame Rate)

# Image Asset Loading
bg = pygame.image.load("assets/images/background.png")
start  = pygame.image.load("assets/images/start.png")
gnd = pygame.image.load("assets/images/ground.png")
bird = pygame.image.load("assets/images/birdidle.png")
soundOn = pygame.image.load("assets/images/unmuted.png")
soundOff = pygame.image.load("assets/images/muted.png")
ds = pygame.image.load("assets/images/deathscreen.png")
gear = pygame.image.load("assets/images/settings.png")
returnButton = pygame.image.load("assets/images/return.png")
dif1 = pygame.image.load("assets/images/1.png")
dif2 = pygame.image.load("assets/images/2.png")
dif3 = pygame.image.load("assets/images/3.png")
p_bot = pygame.image.load("assets/images/pipe_bottom.png")
p_top = pygame.transform.flip(p_bot, False, True)

# Image Heights Loading
bg_width = bg.get_width()
gnd_height = gnd.get_height()
tile = math.ceil(SW / bg_width) + 1 # Add Extra Tile As Buffer To Avoid Mess On Screen
font = pygame.font.Font('freesansbold.ttf', 15 )
fBird = pygame.font.Font('assets/fonts/FlappyBirdy.ttf', 25)


# Set Initial Mixer Music And Channels
channels = 4  # 2 Simultaneous Music Channels For Music (L+R)
pygame.mixer.set_num_channels(channels) # Set Number Of Channels From Earlier Value
mixer.music.set_volume(0.2) # Set Global Volume For Music
pygame.mixer.Channel(0).play(pygame.mixer.Sound('assets/sounds/bgm.mp3')) # Setup And Play Background Music

# Game Variables
havePrintedGear = False
settingsRect = 0
pointsPerScore = 1
nextIndex = 0
difficulty = 1
muted = False
hasIntersected = False
deathScreen = False
scroll_pos = 0 #  Scrolling Background Position
scroll_rate = 1 # Scrolling Speed Rate
changed_bird = False # Variable Storing Weather Or Not The Bird's Position Changed
fr_count = 0 # Frames To Store Upwards Bird Image
fr_count2 = 0
bird_start_y = 35
descent_rate = 0.2 # Descent Rate Of Bird
ascent_rate = 35  # Ascent Rate OF Bird
ticks = 0 # Initial Tick Count
pipeFrequency = 200 # Frequency At Which To Generate A Pipe Pair (Each Count Is 16.67 Msec Frame Time) (PFreq*16.67 MSec = Time Delay)
pipeXs = [SW] # List Of X-Coordinate For Each Pipe Pair On Screen
gap_l = 100
gap_u = 200
gaps = [random.randint(gap_l, gap_u)] # List Of Gaps (In PX) For Each Pipe Pair On Screen
topYs = [random.randint(0, 250)]  # Bottom-Left Y Coordinate For Each Pipe Pair
nextInterSect = [0,0,0]  # Top, Bottom, And Middle Rectangles Of Upcoming Pipes
points = 0  # Global Point Counter For The Entire Game And User
initialCollide = True # Flag For Checking If The Bird Has Initially Collided With The Permissable Area In The Pipe Pair

def gameReset():
  pygame.display.quit()
  pygame.quit()  
  script_name = os.path.basename(__file__)
  os.system(script_name)


def writeText(text, x, y, color, w, h):
  '''
    Function: Simplifying Blitting Text To Screen
    Args:
      text -> Text To Display
      x -> X-Coordinate Of Text Rectangle
      y -> Y-Coordinate Of Text Rectangle
      color -> Color Of Text
      w -> Width Of Text Box
      h -> Height Of Text Box
  '''
  maintext = font.render(text, True, color)
  mainTextBox = pygame.Rect(x, y, w, h)
  screen.blit(maintext, mainTextBox)
  return None

def checkCollision(f1, f2, f3, p1, obj, first):
  global nextInterSect
  global initialCollide
  global hasIntersected
  global bird
  if (obj.colliderect(f3)):  # If Bird Collides With Ground, End Game And Play Death Sound
    print("Bird Hit Ground. Game Over!")
    bird = pygame.image.load("assets/images/birddead.png")
    screen.blit(bird, (184, bird_start_y))
    pygame.display.update()
    pygame.mixer.Channel(2).play(pygame.mixer.Sound('assets/sounds/die.mp3'))
    time.sleep(2) # Display Delay
    return True
  elif (obj.colliderect(f1) or obj.colliderect(f2)):  # If Bird Collides With Top Or Bottom Pipe Rectangles, End Game And Play Death Sound
    print("Bird Intercepted Upper Or Lower Pipe. Game Over!")
    bird = pygame.image.load("assets/images/birddead.png")
    screen.blit(bird, (184, bird_start_y))  
    pygame.display.update()
    pygame.mixer.Channel(2).play(pygame.mixer.Sound('assets/sounds/die.mp3')) 
    time.sleep(2) # Display Delay
    return True
  elif (obj.colliderect(p1)):  # If Permissable Between Tubes Collides With Birds, Meaning That You Passed Through Pipes
     
    if (first == True):
      if (initialCollide == True):  # Single Point Gain Trigger When User Begins
        initialCollide = False # Set Collide To False 
        pygame.mixer.Channel(3).play(pygame.mixer.Sound('assets/sounds/point.mp3')) # Play Point Sound
        return False
  else:
    if (first == True):
      initialCollide = True
    else:
      pass

def selectDifficulty(difficulty):
  global pipeFrequency
  global scroll_rate 
  global gap_u, gap_l
  global pointsPerScore

  if (difficulty == "Easy"):
    pipeFrequency = 200
    scroll_rate = 1
    gap_u, gap_l = 200,  100
    pointsPerScore = 1
  elif (difficulty == "Medium"):
    pipeFrequency = 100
    scroll_rate = 2
    gap_u, gap_l = 200, 120
    pointsPerScore = 3
  elif (difficulty == "Hard"):
    pipeFrequency = 65
    scroll_rate = 3
    gap_u, gap_l = 200, 150
    pointsPerScore = 5




def create_Pipe_Pair(gap, xs, topY):
  '''
    Function: Create A Pair Of Pipes On Screen
    Args, 3 Ints: (gap, xs, topY)
      gap -> 'int' = Gap Size Between Pipes
      xs -> 'int' = X Position To Draw Pipe Pair At
      topY -> 'int' = Y Position To Draw Bottom Left Of Top Pipe
    Returns Tuple: topRect, bottomRect, middleRect
      topRect -> Rectangle Of Upper Pipe
      bottomRect -> Rectangle Of Lower Pipe
      middleRect -> Rectangle Of Inter-Pipe Gap (Permissable Area)
      
  '''
  # Blit Images To Screen, While Storing Their Rectangles
  topRect = screen.blit(p_top, (xs,(topY-p_top.get_height()))) 
  bottomrect = screen.blit(p_bot, (xs, (topY+gap)))
  middleRect = pygame.Rect(xs, topY, p_top.get_width(), gap)
  return topRect, bottomrect, middleRect  # Rectangles For Pipe Objects

def gameIntro():
  global deathScreen
  global beginMenu
  global escapeMenu
  '''
    Function To Wait And Catch User Input For Begenning Game
    Args:
      None
    Returns:
      None. Manipulates 'beginMenu' Variable
  '''
  for event in pygame.event.get():  # Check User Events
      if (event.type == pygame.QUIT): # Allow User To End Game And Exit
        print("User Hit 'X' Button. Stopping!")
        beginMenu = False
        sys.exit()
      elif (event.type == pygame.MOUSEBUTTONDOWN):
        x,y = event.pos
        if (settingsRect.collidepoint(x,y)):
          beginMenu = False
          escapeMenu = True
      elif (event.type == pygame.KEYDOWN):  # If Space (Start) Is Pressed, Allow User To Play Game
        if (event.key == pygame.K_SPACE):
          beginMenu = False

def pauseMenu():
  global escapeMenu
  global runningGame
  global muted
  global difficulty
  global returnRect
  screen.fill(WHITE)
  returnRect = screen.blit(returnButton, (5, 5))
  writeText("Paused Menu", 150, 32, RED, 35, 35)
  writeText("Use 'M' Key To Mute Music!",105, 55, BLACK, 35, 35)
  writeText("Select '1', '2', or '3' For Difficulty!", 80, 170, BLACK, 35, 35)
  writeText("Instructions:", 150, 400, BLACK, 50, 50)
  writeText("1.) Use 'SPACE' Key To Make Birdy Jump!", 60, 425, BLACK, 100, 100)
  writeText("2.) Avoid The Top And Bottom Obstacles", 60, 445, BLACK, 100, 100)
  writeText("3.) Aim For Between Both Pipes!", 60, 465, BLACK, 100, 100)
  writeText("Press 'ESC' To Return To Game!", 90, 10, GREEN, 50, 50)
  writeText("Current Difficulty Level:", 115, 190, BLACK, 35, 35)

  for event in pygame.event.get():
    if (event.type == pygame.QUIT):
      escapeMenu = False
      runningGame = False
    elif (event.type == pygame.MOUSEBUTTONDOWN):
        x,y = event.pos
        if (returnRect.collidepoint(x,y)):
          escapeMenu = False
    elif (event.type == pygame.KEYDOWN):
      if (event.key == pygame.K_ESCAPE):
        escapeMenu = False
      elif (event.key == pygame.K_m):
        muted = not muted
        print(muted)
      elif (event.key == pygame.K_1):
        difficulty = 1
        selectDifficulty("Easy")
      elif (event.key == pygame.K_2):
        difficulty = 2
        print("Difficulty 2")
        selectDifficulty("Medium")       
      elif (event.key == pygame.K_3):
        difficulty = 3
        print("Difficulty 3")
        selectDifficulty("Hard")

    
  if (muted == True):
    screen.blit(soundOff, (155, 80))
    writeText("Music Is Muted!", 140, 150, BLACK, 50, 50)
    pygame.mixer.pause()

  else:
    screen.blit(soundOn, (155, 80))
    writeText("Music Is Unmuted!", 130, 150, BLACK, 50, 50)
    pygame.mixer.unpause()

  if (difficulty == 1):
    screen.blit(dif1, (160, 220))
  elif (difficulty == 2):
    screen.blit(dif2, (150, 220))
  elif (difficulty == 3):
    screen.blit(dif3, (150, 220))

  
  pygame.display.update()

def deathMenu():
  global points
  global runningGame
  global deathScreen
  '''
    Function: Print User's Info And Options When They Fail
    Args:
      -> None
    Returns
      -> None
  '''
  screen.blit(ds, (0,120))
  writeText(str(points), 190, 290, BLACK, 35, 35)
  
  for event in pygame.event.get():
    if (event.type == pygame.KEYDOWN):
      if (event.key == pygame.K_ESCAPE):
        deathScreen = False
        runningGame = False
      elif (event.key == pygame.K_SPACE): 
        deathScreen = False
        gameReset()
    elif (event.type == pygame.QUIT):
      deathScreen = False
      runningGame = False
  
  try:
    pygame.display.update()
  except pygame.error:
    sys.exit()


while (runningGame == True):  # Only Run Game During 'runningGame' Flag Set To True

  

  if (muted == True):
    pygame.mixer.pause()
  else:
    pygame.mixer.unpause()
  ticks += 1  # Increase Ticks Counter For Pipe Generation

  for x in range (0, tile): # Put Correct Amount Of Tiles On Screen For GND Image
    screen.blit(bg, ((x * bg_width + scroll_pos), 0))  # Lay Ground Image Overtop Background, At Screen Height - Ground Image Height, But Offset
  
  if (ticks >= pipeFrequency):  # Create New Pipe When Ticks Counter Hits PipeFrequency
    pipeXs.append(SW)
    print("(",gap_l,gap_u,")")
    gaps.append(random.randint(gap_l, gap_u))
    topYs.append(random.randint(0, 250))
    print("Generated New Element")
    ticks = 0

  for x in range (0, len(pipeXs)):
    if (pipeXs[x] > 160+bird.get_width()):
      nextIndex = x
      break
  


  for x in range (0, len(pipeXs)):  # Generate Correct Number Of Pipe Pairs During The Frame, Using Arrays Of Pipe Info
    if (x == nextIndex):  # If We're At Pipe #1, Store The Rectangles Generated For Pipes As Next Intersection
      top, bottom, middle = create_Pipe_Pair(gaps[x], pipeXs[x], topYs[x])
      nextInterSect[0] = top
      nextInterSect[1] = bottom
      nextInterSect[2] = middle
      
    else:
      top, bottom, middle = create_Pipe_Pair(gaps[x], pipeXs[x], topYs[x])

  
  pipeXs = [x - scroll_rate  for x in pipeXs]  # Subtract 1 From X Position Of Every Array (Pipe Pair) Element (Move X Of Pipes)

  if (pipeXs[0] <= -p_top.get_width()): # If The First Pipe Is At The Very Edge Of The Screen, Remove It's Info From All Arrays
    pipeXs.pop(0) # Remove Pipe X From List
    gaps.pop(0) # Remove Pipe Gap From List
    topYs.pop(0)  # Remove Pipe Y From List
    
  scroll_pos -= scroll_rate # Decrease Scrolling Position
  groundRect = screen.blit(gnd, (0, (SH-gnd_height))) # Create Rectangle For The Ground Position

  if (abs(scroll_pos) > bg_width):  # If Scrolling Position Is Greater Than The Screen, Reset It
    scroll_pos = 0

  if (fr_count2 == 0): # If In Neutral Frames, Descent Exponentially
    descent_rate = descent_rate+0.2
    bird_start_y += descent_rate # Bring Bird Towards Ground

  elif (fr_count2 > 0):# If In Ascending Frames, Ascend Gradually
    ascent_rate -= ascent_rate-3  
    bird_start_y -= ascent_rate
    fr_count2 -= 1
  
  settingsRect = screen.blit(gear, (5, 5))

  for event in pygame.event.get():  # Check Pygame User Events
    if (event.type == pygame.QUIT):  # If User Clicks "X" Button, Exit Game    
      print("User Hit 'X' Button. Stopping!")
      runningGame = False
    elif (event.type == pygame.MOUSEBUTTONDOWN):
      x,y = event.pos
      if (settingsRect.collidepoint(x,y)):
        escapeMenu = True
    elif (event.type == pygame.KEYDOWN):  # If Key ESC Is Pressed, Stop RunningGame
      if (event.key == pygame.K_ESCAPE):
        escapeMenu = True
    elif (event.type == pygame.KEYUP):  # If Space Key Is UP, Make Bird Change To Jump Sprite, And Decrease It's Y Position
      if (event.key == pygame.K_SPACE):
        if (bird_start_y - 35 >= 0):  # If We Can Jump Without Hitting Screen Height, Reset Sprite
          bird = pygame.image.load("assets/images/birdup.png")  # Load Jumping Bird Sprite
        else: # If Decreasing The Bird's Position By The Jump Amoutn Makes It Exceede X Positions (Off-Screen), Make The Bird Go To The Maximum Height (0 X)
          bird_start_y = 0  # Make Bird Hit Max Position
          bird = pygame.image.load("assets/images/birdup.png")  # Change Sprite To Jump
        fr_count = 5  # Show Bird Jump For 5 Frames
        fr_count2 = 8 # Have Bird Ascent For 8 Frames
        descent_rate = 0.2  # Reset Descent Rate
        descent_rate = 2  # Bring Up Reset Rate
        ascent_rate = 35  # Reset Ascent Rate For Jump (Will Decrease Exponentially)
        pygame.mixer.Channel(1).play(pygame.mixer.Sound('assets/sounds/jump.mp3'))  # Play Jump Sound On CH.1

  birdRect = screen.blit(bird, (184, bird_start_y)) # Generate Bird's Rectangle And Blit Current Bird Sprite Onto Screen

  # Generate Score Text On Screen For User
  textRect = pygame.Rect(190,5,35,0)
  text = str(points)
  texts = fBird.render(text, True, BLACK)
  screen.blit(texts, textRect)

  if (beginMenu == True): # If We're Starting The Game, Blit The Start Icon To The Screen
    screen.blit(start, (113, 260))
  
  pOf = checkCollision(nextInterSect[0], nextInterSect[1], groundRect, nextInterSect[2], birdRect, True)

  if (pOf == True):
    deathScreen = True
  elif (pOf == False):
    points += pointsPerScore
    print("Intersect")
  
  pygame.display.update() # Update (Refresh) Dispay Buffer And Display Elements On Screen

  while (beginMenu == True):  # If We're Starting And Waiting For User To Start CMD
    gameIntro()
  
  while (escapeMenu == True):
    
    pauseMenu()
  
  while (deathScreen == True):
    deathMenu()

  if (fr_count == 0): # If Frame Count Is Neutral, Change Bird To BIRDDOWN PNG To Provide Visual Feedback
    bird = pygame.image.load("assets/images/birddown.png")
  else:
    fr_count -= 1 # Decrease Frame Count
  
  havePrintedGear = False
  clock.tick(FPS) # Set FrameRate
  