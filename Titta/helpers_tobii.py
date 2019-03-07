# -*- coding: utf-8 -*-
"""
Created on Tue Jun 06 16:20:36 2017

@author: marcus
"""
from psychopy import visual
from collections import deque
import numpy as np
from psychopy.tools.monitorunittools import cm2deg
import copy
import sys

if sys.version_info[0] == 2: # if Python 2:
    range = xrange
    pass


def tobii2norm(pos):
    ''' Converts from Tobiis coordinate system [0, 1] to PsychoPy's 'norm' (-1, 1).
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center.
    y = -1 in PsychoPy coordinates means bottom of screen
    Args:   pos: N x 2 array with positions
    '''
    
    # Convert between coordinate system
    pos[:, 0] = 2.0 * (pos[:, 0] - 0.5)
    pos[:, 1] = 2.0 * (pos[:, 1] - 0.5) * -1
    
    return pos

def norm2tobii(pos):
    ''' Converts from PsychoPy's 'norm' (-1, 1) to Tobiis coordinate system [0, 1].
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center.
    y = -1 in PsychoPy coordinates means bottom of screen
    Args:   pos: N x 2 array with positions
    '''
    
    # Convert between coordinate system
    pos[:, 0] = pos[:, 0] / 2.0 + 0.5
    pos[:, 1] = pos[:, 1] / -2.0 + 0.5
    
    return pos
    
def tobii2deg(pos, mon, screen_height):
    ''' Converts Tobiis coordinate system [0, 1 to degrees.
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    Args:   pos: N x 2 array with calibratio position in [0, 1]
            screen_height: height of screen in cm            
    '''
#    print(pos)
    # Center
    pos[:, 0] = pos[:, 0] - 0.5
    pos[:, 1] = (pos[:, 1] - 0.5) * -1
           
    # Cenvert to psychopy coordinates (center)
    pos[:, 0] = pos[:, 0] * mon.getWidth() 
    pos[:, 1] = pos[:, 1] * screen_height 
    
    # Convert to deg.
    pos_deg = cm2deg(pos, mon, correctFlat=False)    
#    print(pos, pos_deg)
    return pos_deg
    
def deg2tobii(pos):
    ''' Converts from degrees to Tobiis coordinate system [0, 1].
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    '''
    
    return
    
def tobii2pix(pos, mon):
    ''' Converts from  Tobiis coordinate system [0, 1] to pixles.
    Note that the Tobii coordinate system start in the upper left corner
    and screen coordinate in the upper left corner
    Args:   pos: N x 2 array with calibratio position in [0, 1]
            screen_height: height of screen in cm            
    '''
    
    # Center
    pos[:, 0] = pos[:, 0] * mon.getSizePix()[0]
    pos[:, 1] = pos[:, 1] * mon.getSizePix()[1]
               
    # Convert to deg.
    return pos
#%%
class MyDot2:
    '''
    Generates the best fixation target according to Thaler et al. (2013)
    '''
    def __init__(self, win, outer_diameter=0.5, inner_diameter=0.1,
                 outer_color = 'white', inner_color = 'black',units = 'pix'):
        '''
        Class to generate a stimulus dot with 
        units are derived from the window
        '''
    
        # Set propertis of dot 
        outer_dot = visual.Circle(win,fillColor = outer_color, radius = outer_diameter/2.0,
                                  units = units)
        inner_dot = visual.Circle(win,fillColor = outer_color, radius = inner_diameter/2.0,
                                  units = units)
        line_vertical = visual.Rect(win, width=inner_diameter, height=outer_diameter, 
                                    fillColor=inner_color, units = units)
        line_horizontal = visual.Rect(win, width=outer_diameter, height=inner_diameter, 
                                    fillColor=inner_color, units = units)        
              
    
        self.outer_dot = outer_dot
        self.inner_dot = inner_dot
        self.line_vertical = line_vertical
        self.line_horizontal = line_horizontal
    
    
    def setSize(self, size):
        self.outer_dot.size = size
        self.line_vertical.height *= size
        self.line_horizontal.width *= size
        
    def setPos(self,pos):
        '''
        sets position of dot
        pos = [x,y]
        '''
        self.outer_dot.pos = pos
        self.inner_dot.pos = pos
        self.line_vertical.pos = pos
        self.line_horizontal.pos = pos        
        
    def get_pos(self):
        '''
        get position of dot
        '''
        pos = self.outer_dot.pos 
        
        return pos
    
    
    def draw(self):
        '''
        draws the dot
        '''
        self.outer_dot.draw()
        self.line_vertical.draw()
        self.line_horizontal.draw()           
        self.inner_dot.draw()
     
        
    def invert_color(self):
        '''
        inverts the colors of the dot
        '''
        temp = self.outer_dot.fillColor 
        self.outer_dot.fillColor = self.inner_dot.fillColor
        self.inner_dot.fillColor = temp
        
    def set_color(self, color):
        self.outer_dot.lineColor = 'blue'
        self.outer_dot.fillColor = 'blue'
        self.inner_dot.fillColor = 'blue'
        self.inner_dot.lineColor = 'blue'
        self.line_vertical.lineColor = 'red'
        self.line_horizontal.fillColor = 'red'
        self.line_vertical.fillColor = 'red'
        self.line_horizontal.lineColor = 'red'        
        
#%%   
class MyDot:
    '''
    Generates the best fixation target according to Thaler et al. (2013)
    '''
    def __init__(self, win, outer_diameter=0.5, inner_diameter=0.1,
                 outer_color = 'white', inner_color = 'black'):
        '''
        Class to generate a stimulus dot with 
        units are derived from the window
        '''

        # Set propertis of dot 
        outer_dot = visual.Circle(win,fillColor = outer_color, radius = outer_diameter/2.0)
        inner_dot = visual.Circle(win,fillColor = outer_color, radius = inner_diameter/2.0)
        line_vertical = visual.Rect(win, width=inner_diameter, height=outer_diameter, 
                                    fillColor=inner_color)
        line_horizontal = visual.Rect(win, width=outer_diameter, height=inner_diameter, 
                                    fillColor=inner_color)        
              
    
        self.outer_dot = outer_dot
        self.inner_dot = inner_dot
        self.line_vertical = line_vertical
        self.line_horizontal = line_horizontal
    

    def set_pos(self,pos):
        '''
        sets position of dot
        pos = [x,y]
        '''
        self.outer_dot.pos = pos
        self.inner_dot.pos = pos
        self.line_vertical.pos = pos
        self.line_horizontal.pos = pos        
        
    def get_pos(self):
        '''
        get position of dot
        '''
        pos = self.outer_dot.pos 
        
        return pos

    
    def draw(self):
        '''
        draws the dot
        '''
        self.outer_dot.draw()
        self.line_vertical.draw()
        self.line_horizontal.draw()           
        self.inner_dot.draw()
     
        
    def invert_color(self):
        '''
        inverts the colors of the dot
        '''
        temp = self.outer_dot.fillColor 
        self.outer_dot.fillColor = self.inner_dot.fillColor
        self.inner_dot.fillColor = temp
        
#%%         
class RingBuffer(object):
    """ A simple ring buffer based on the deque class"""
    def __init__(self, maxlen=200):        
        # Create que with maxlen 
        self.maxlen = maxlen
        self._b = deque(maxlen=maxlen)  

    def clear(self):
        """ Clears buffer """
        return(self._b.clear())
        
    def get_all(self):
        """ Returns all samples from buffer and empties the buffer"""
        lenb = len(self._b)
        return([self._b.popleft() for i in range(lenb)])
        
    def peek(self):
        """ Returns all samples from buffer without emptying the buffer
        First remove an element, then add it again
        """
        b_temp = copy.copy(self._b)
        c = []
        if len(b_temp) > 0:
            for i in range(len(b_temp)):
                c.append(b_temp.pop())

        return(c)
        
    def append(self, L):
        self._b.append(L)         
        """"Append buffer with the most recent sample (list L)"""    

#%%   
class AnimatedCalibrationDisplay(object):
    """ A class for drawing animated targets"""
    def __init__(self, win, target, function_name):
        ''' The function 'function_name' does the actual drawing
        '''
        self.win = win
        self.function_name = function_name
        self.target = target # psychopy.visual object (should be in 'pix' units)
        self.screen_refresh_rate = float(win.getActualFrameRate())
        
    def animate_target(self, point_number, position, tick):
        ''' Calls the target drawing function 'func'
        '''

        eval(''.join(['self.',self.function_name,'(',str(point_number),',', 
                                        '(',str(position[0][0]),',',
                                            str(position[1][0]), ')' ,',', str(tick),')']))
        
            
    def animate_point(self, point_number, position, tick):
        ''' Animates calibration point with a certain point_number and position
        tick increases by 1 for each call
        Args:
            position - (x, y)
        '''
        
        target_size = np.abs(1 - np.sin(3 * tick / self.screen_refresh_rate + 3*np.pi/2)) + 0.2
        self.target.setSize(target_size)
        self.target.setPos(position)
        self.target.draw()
        
    def move_point(self, old_position, new_position, tick):
        ''' Animates movement between two positions
        '''
        move_completed = False
        
        # The target should have a fixed size when moving
        self.target.setSize(2)
        
        # How many ticks should the movement be (one screen unit in one second)?
        n_steps = self.screen_refresh_rate / 2
        step_pos_x = np.linspace(old_position[0], new_position[0], n_steps)
        step_pos_y = np.linspace(old_position[1], new_position[1], n_steps)
        
        if tick >= len(step_pos_x):
            move_completed = True
        else:       
            self.target.setPos((step_pos_x[tick], step_pos_y[tick]))
            
        self.target.draw()
        
        return move_completed


#%%
def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

#%%
def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))

#%%    
def rms(x):
    rms = np.sqrt(np.mean(np.square(np.diff(x))))
    return rms 

#%% 
    
