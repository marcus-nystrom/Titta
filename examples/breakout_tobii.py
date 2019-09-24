"""
 Sample Breakout Game
 
 Sample Python/Pygame Programs
 Simpson College Computer Science
 http://programarcadegames.com/
 http://simpson.edu/computer-science/
 
 Adaped to PsychoPy by Marcus Nystrom.
"""
 
# --- Import libraries used for this program
 
import math
import numpy as np
from psychopy import core, event, misc, visual, monitors, data, gui
import pandas as pd
from titta import Titta, helpers_tobii as helpers


#%% Monitor/geometry 
MY_MONITOR                  = 'testMonitor' # needs to exists in PsychoPy monitor center
FULLSCREEN                  = True
SCREEN_RES                  = [1920, 1080]
SCREEN_WIDTH                = 52.7 # cm
VIEWING_DIST                = 63 #  # distance from eye to center of screen (cm)

mon = monitors.Monitor(MY_MONITOR)  # Defined in defaults file
mon.setWidth(SCREEN_WIDTH)          # Width of screen (cm)
mon.setDistance(VIEWING_DIST)       # Distance eye / monitor (cm)
mon.setSizePix(SCREEN_RES)


#%% Connect to eye tracker and open PsychoPy window
# Get exp settings
settings = Titta.get_defaults('Tobii Pro Spectrum')
             
# Show dialogue box
info = {'Enter your name':'your name', 'Dummy mode':[False, True]}

dictDlg = gui.DlgFromDict(dictionary=info,
        title='Breakout')
if dictDlg.OK:
    print(info)
else:
    print('User Cancelled')
    core.quit()
    
info['dateStr']= data.getDateStr()    
player_name = '_'.join([info['Enter your name'], info['dateStr']])

                    
c = core.Clock()
my_clock = core.Clock()
         
# Change any of the default dettings?
settings.FILENAME = 'my_test.tsv'

# Connect to eye tracker
tracker = Titta.Connect(settings) 
if info['Dummy mode'] == 'True':
    tracker.set_dummy_mode()
tracker.init()

# Window set-up (this color will be used for calibration)
win = visual.Window(monitor = mon, fullscr = FULLSCREEN,
                    screen=1, size=SCREEN_RES, units = 'pix')

# mouse = event.Mouse(win=win)
# mouse.setVisible(False)
instruction_text = visual.TextStim(win,text='', wrapWidth = 600, height = 20)     
    
tracker.calibrate(win)
    
# Start eye tracker
tracker.start_recording(gaze_data=True,
                        store_data=False)
    
tracker.start_sample_buffer(sample_buffer_length=10)

# Define some colors
black = (0, 0, 0)
white = (1, 1, 1)
blue = (0, 0, 1)
 
screen_size = SCREEN_RES
game_rect = visual.Rect(win, SCREEN_RES[0], SCREEN_RES[1], units = 'pix')
# mouse.setPos((0, -screen_size[1]/2 + 100))

# information about block position
nBlockRows = 3
 
# Number of blocks to create
blockcount = 16.0

block_width = screen_size[0] / blockcount
block_height = screen_size[1] / 20.0

#%%
def generate_blocks():
    blocks = []
    top = screen_size[1] / 2.0 - block_height * 2

    for row in range(nBlockRows):
        # 32 columns of blocks
        for column in range(0, int(blockcount-1)):
            # Create a block (color,x,y)
            block = Block(blue, (column + 1) * (block_width + 2)  - screen_size[0]/2, top)
            blocks.append(block)
#            block.image.draw()
        # Move the top of the next row down
        top -= block_height - 2
        
    return blocks
 
#%% 
class Block():
    """This class represents each block that will get knocked out by the ball
    """
 
    def __init__(self, color, x, y):
        """ Constructor. Pass in the color of the block,
            and its x and y position. """

        # Create the image of the block of appropriate size
        # The width and height are sent as a list for the first parameter.
        self.image = visual.Rect(win, block_width, block_height)
 
        # Fill the image with the appropriate color
        self.image.fillColor = color
 
        # Fetch the rectangle object that has the dimensions of the image
        self.image.pos = (x, y)
  
 
class Ball():
    """ This class represents the ball
    """
 
    # Constructor. Pass in the color of the block, and its x and y position
    def __init__(self):
        
        # Speed in pixels per cycle
        self.speed = 10.0
     
        # Floating point representation of where the ball is
        self.x = 0
        self.y = 0 + screen_size[1] *0.05
     
        # Direction of ball (in degrees)
        self.direction = 200 + 180
     
        self.radius =  screen_size[0] * 0.01
 
        # Create the image of the ball
        self.image = visual.Circle(win, self.radius)
 
        # Color the ball
        self.image.fillColor = white
        self.image.pos = (self.x, self.y)
#        
  
    def bounce(self, diff):
        """ This function will bounce the ball
            off a horizontal surface (not a vertical one) """
 
        self.direction = (180 - self.direction) % 360
        self.direction += diff
 
    def update(self):
        """ Update the position of the ball. """
        
        # Sine and Cosine work in degrees, so we have to convert them
        direction_radians = math.radians(self.direction)
 
        # Change the position (x and y) according to the speed and direction
        self.x += self.speed * math.sin(direction_radians)
        self.y -= self.speed * math.cos(direction_radians)
 
        # Move the image (ball) to where our x and y are
        self.image.pos = (self.x, self.y)
 
        # Do we bounce off the top of the screen?
        if self.y >= screen_size[1]/2.0:
            self.bounce(0)
 
        # Do we bounce off the left of the screen?
        if self.x <=  -screen_size[0] / 2.0:
            self.direction = (360 - self.direction) % 360
            self.x = -screen_size[0] / 2.0 + self.radius
 
        # Do we bounce of the right side of the screen?
        if self.x >= screen_size[0] / 2.0:
            self.direction = (360 - self.direction) % 360
            self.x =screen_size[0] / 2.0 - self.radius - 1
 
        # Did we fall off the bottom edge of the screen (or below the paddle)?
        if self.y < - (screen_size[1] / 2.0 + self.radius):
            return True
        else:
            return False
#%% 
class Player():
    """ This class represents the bar at the bottom that the
    player controls. """
 
    def __init__(self):
        """ Constructor for Player. """
 
        self.width = 300
        self.height =15
        self.image = visual.Rect(win, self.width, self.height)
  
        # Color the player
        self.image.fillColor = white
        self.fixed_y = -screen_size[1]/2 + 100
        self.image.pos = (0, self.fixed_y)
        
        
  
    def update(self):
        """ Update the player position. """
                    
        # Peek in the eye tracker buffer
        data = tracker.peek_buffer()
        
        # Convert from Tobii coordinate system to ssv 
        lx = [d['left_gaze_point_on_display_area'][0] for d in data]
        rx = [d['right_gaze_point_on_display_area'][0] for d in data]

        # print(lx)
        # Use the average position (i.e., lowpass filtered)
        pos = np.nanmean([np.nanmean(rx), np.nanmean(lx)])
        pos = helpers.tobii2pix(np.array([[pos, pos]]), mon)[:, 0]
        pos = pos - screen_size[0] / 2
            

        # Set the left side of the player bar to the mouse/gaze position
        if pos > (screen_size[0] / 2 - self.width/2.0):
            pos = screen_size[0] / 2 - self.width/2.0
            
        if pos < (-screen_size[0] / 2 + self.width/2.0):
            pos = -screen_size[0] / 2 + self.width/2.0
            
        
        # Update position of player
        self.image.pos = (pos, self.fixed_y)

#%% 
# Create the player paddle object
player = Player()
ball = Ball()

player.image.draw()
ball.image.draw()

# --- Create blocks
blocks = generate_blocks()
win.flip()

# Is the game over?
game_over = False

# Exit the program?
exit_program = False
score = 0

# Main program loop
i = 1
c.reset()
my_clock.reset()
while not exit_program:
 
    k = event.getKeys()
    if 'escape' in k:
        exit_program = True
        
    # Update the ball and player position as long
    # as the game is not over.
    # Update the player and ball positions
    player.update()
    game_over = ball.update()

    # See if the ball hits the player paddle
    if player.image.overlaps(ball.image) and c.getTime() > 0.5:
        
        # The 'diff' lets you try to bounce the ball left or right
        # depending where on the paddle you hit it
        diff = (player.image.pos[0] - ball.image.pos[0]) / player.width / 2 * 30 
 
        # Set the ball's y position in case
        # we hit the ball on the edge of the paddle
        ball.bounce(diff)
        c.reset()
        
       
    # See if the ball hits a brick
    overlap = [ball.image.overlaps(b.image) for b in blocks]
    if any(overlap):
        # Delete the brick it hits and bounce
       del blocks[np.where(overlap)[0][0]]
       ball.bounce(0)
       score += 5
       
    # Any bricks left?
    if len(blocks) == 0:
        exit_program = True
        
    # Paddel missed the ball
    if ball.image.pos[1] <= player.image.pos[1]:
        exit_program = True

    # Draw all stimuli
    game_rect.draw()
    [b.image.draw() for b in blocks]
    player.image.draw()
    ball.image.draw()
    
    # Draw the score
    instruction_text.text = 'Score: ' + str(score)
    instruction_text.draw()
    win.flip()
    
    # Increase the ball speed at certain intervals
    if my_clock.getTime() > 5 :
        ball.speed *= 1.1
        my_clock.reset()

try:
    df = pd.read_csv('highscore.csv', sep='\t')
        
    # Blink GAME OVER and show score
    instruction_text.pos = (0, 0)
    instruction_text.height = 50
    instruction_text.text = 'GAME OVER'
    for i in range(5):
        instruction_text.draw()
        win.flip()
        core.wait(0.3)
        win.flip()
        core.wait(0.3)
        
    instruction_text.draw()
    instruction_text.pos = (0, - 100)
    instruction_text.text = 'Your score: ' + str(score)
    instruction_text.draw()
    instruction_text.pos = (0, - 200)
    instruction_text.text = 'High score: ' + str(np.max(np.array(df['Score'])))          
    instruction_text.draw()
    win.flip()

    core.wait(3)

    # Stop eye tracker and clean up 
    tracker.stop_sample_buffer()
    tracker.stop_recording(gaze_data=True)
    tracker.de_init()

    # Write results to data frame
    df_player = pd.DataFrame({'Name':[player_name], 'Score':[score]})

    # Add players score to highscore sheet
    with open('highscore.csv', 'a') as f:
        df_player.to_csv(f, sep='\t', header=False)
except Exception as e: 
    # mouse.setVisible (True)
    win.close()
    print(e)

win.close()
core.quit()