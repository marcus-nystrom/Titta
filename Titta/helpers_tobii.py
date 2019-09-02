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
from matplotlib.patches import Ellipse
import sys

if sys.version_info[0] == 2: # if Python 2:
    range = xrange
    pass

    
#%%
def tobii2norm(pos):
    ''' Converts from Tobiis coordinate system [0, 1] to PsychoPy's 'norm' (-1, 1).
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center.
    y = -1 in PsychoPy coordinates means bottom of screen
    Args:   pos: N x 2 array with positions
    '''
    
    pos_temp = copy.deepcopy(pos[:]) # To avoid that the called parameter is changed
    
    # Convert between coordinate system
    pos_temp[:, 0] = 2.0 * (pos_temp[:, 0] - 0.5)
    pos_temp[:, 1] = 2.0 * (pos_temp[:, 1] - 0.5) * -1
    
    return pos_temp

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
    
def tobii2deg(pos, mon):
    ''' Converts Tobiis coordinate system [0, 1 to degrees.
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    Assumes pixels are square
    Args:   pos: N x 2 array with calibratio position in [0, 1]
            screen_height: height of screen in cm            
    '''
    
    pos_temp = copy.deepcopy(pos[:]) # To avoid that the called parameter is changed
    
    # Center
    pos_temp[:, 0] = pos_temp[:, 0] - 0.5
    pos_temp[:, 1] = (pos_temp[:, 1] - 0.5) * -1
           
    # Cenvert to psychopy coordinates (center)
    pos_temp[:, 0] = pos_temp[:, 0] * mon.getWidth() 
    pos_temp[:, 1] = pos_temp[:, 1] * mon.getWidth() * (float(mon.getSizePix()[1]) / \
                                              float(mon.getSizePix()[0]))
    
    # Convert to deg.
    pos_deg = cm2deg(pos_temp, mon, correctFlat=False)    
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
                 outer_color = 'black', inner_color = 'white',units = 'deg'):
        '''
        Class to generate a stimulus dot with 
        units are derived from the window
        '''
    
        # Set propertis of dot 
        outer_dot = visual.Circle(win,fillColor = outer_color, radius = outer_diameter/2,
                                  units = units)
        inner_dot = visual.Circle(win,fillColor = outer_color, radius = inner_diameter/2,
                                  units = units)
        line_vertical = visual.Rect(win, width=inner_diameter, height=outer_diameter, 
                                    fillColor=inner_color, units = units)
        line_horizontal = visual.Rect(win, width=outer_diameter, height=inner_diameter, 
                                    fillColor=inner_color, units = units)        
              
    
        self.outer_dot = outer_dot
        self.inner_dot = inner_dot
        self.line_vertical = line_vertical
        self.line_horizontal = line_horizontal
    
    
    def set_size(self, size):
        ''' Sets the size of the stimulus as scaled by 'size'
        That is, if size == 1, the size is not altered.
        '''
        self.outer_dot.radius = size / 2
        self.line_vertical.height = size
        self.line_horizontal.width = size
        
    def set_pos(self, pos):
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
    
    def get_size(self):
        '''
        get size of dot
        '''
        
        return self.outer_dot.size
    
    
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
def ellipse(xy = (0, 0), width=1, height=1, angle=0, n_points=50):
    ''' Generates edge points for an ellipse
    Args:
        xy - center of ellipse
        width - width of ellipse
        height - height of ellipse
        angle - angular rotation of ellipse (in radians)
        n_points - number of points to generate
        
    Return:
        points - n x 2 array with ellipse points
    '''
    
    xpos,ypos=xy[0], xy[1]
    radm,radn=width,height
    an=angle
    
    co,si=np.cos(an),np.sin(an)
    the=np.linspace(0,2*np.pi,n_points)
    X=radm*np.cos(the)*co-si*radn*np.sin(the)+xpos 
    Y=radm*np.cos(the)*si+co*radn*np.sin(the)+ypos 
    
    points = np.vstack((X, Y)).T 
    
    return points        
#%%
class EThead(object):
    """ A class to handle head animation in Titta
    The animated head should reflect a mirror image of the participants 
    head.
    """
    
    def __init__(self, win): 
        '''
        Args:
            win - psychopy window handle
        '''
        
        self.win = win
        
        # Define colors
        blue = tuple(np.array([37, 97, 163]) / 255.0 * 2 - 1)
        green = tuple(np.array([0, 120, 0]) / 255.0 * 2 - 1)
        red = tuple(np.array([150, 0, 0]) / 255.0 * 2 - 1)
        yellow = tuple(np.array([255, 255, 0]) / 255.0 * 2 - 1)
        yellow_linecolor = tuple(np.array([255, 255, 0]) / 255.0 * 2 - 1)  
        
        # Head parameters
        HEAD_POS_CIRCLE_FIXED_COLOR = blue
        HEAD_POS_CIRCLE_FIXED_RADIUS = 0.25
        self.HEAD_POS_ELLIPSE_MOVING_HEIGHT = 0.25
        self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT = 0.05 
        
        # Eye parameters
        self.EYE_SIZE = 0.03
        EYE_COLOR_VALID = green        
        
      
        # Setup control circles for head position
        self.static_circ = visual.Circle(win, radius = HEAD_POS_CIRCLE_FIXED_RADIUS, 
                                         lineColor = HEAD_POS_CIRCLE_FIXED_COLOR,
                                         lineWidth=4, units='height')
        self.moving_ellipse = visual.ShapeStim(win,  lineColor = yellow_linecolor,
                                         lineWidth=4, units='height', 
                                         fillColor=yellow, opacity=0.1)        
                                                 
        
        # Ellipses for eyes
        self.eye_l = visual.ShapeStim(win,  lineColor = EYE_COLOR_VALID,
                                         lineWidth=2, units='height')
        self.eye_r = visual.ShapeStim(win,  lineColor = EYE_COLOR_VALID,
                                         lineWidth=2, units='height')  
        
        # Ellipses for pupils
        self.pupil_l = visual.ShapeStim(win,  fillColor = 'black',
                                        lineColor = 'black',
                                        units='height')
        self.pupil_r = visual.ShapeStim(win,  fillColor = 'black',
                                        lineColor = 'black',
                                        units='height')         
        
        self.eye_l_closed = visual.Rect(win, fillColor=(1,1,1), 
                                        lineColor=(1,1,1), units='height')
        self.eye_r_closed = visual.Rect(win, fillColor=(1,1,1), 
                                        lineColor=(1,1,1), units='height') 
        
        self.head_width = 0.25
        self.head_height = 0.25        
                     
    
    def update(self, sample, latest_valid_binocular_avg,
               previous_binocular_sample_valid,
               latest_valid_roll, 
               latest_valid_yaw, 
               offset, eye='both'):
        '''
        Args:
            sample - a dict containing information about the sample
            
                relevant info in sample is
                
                'left_gaze_origin_in_user_coordinate_system'  
                'right_gaze_origin_in_user_coordinate_system'              
                'left_gaze_origin_in_trackbox_coordinate_system' 
                'right_gaze_origin_in_trackbox_coordinate_system'
                'left_pupil_diameter'
                'right_pupil_diameter'
                
            eye - track, both eyes, left eye, or right eye
                  the non-tracked eye will be indicated by a cross
                  
            latest_binocular_avg
        '''   
        
        self.eye = eye # Which eye(s) should be tracked      
        self.latest_valid_roll = latest_valid_roll * 180 / np.pi * -1
                
        # Indicate that eye is not used by red color
        if 'right' in self.eye:
            self.eye_l_closed.fillColor = (1, -1, -1) # Red
            
        if 'left' in self.eye:
            self.eye_r_closed.fillColor = (1, -1, -1)         
        
        #%% 1. Compute the average position of the head ellipse
        xyz_pos_eye_l = sample['left_gaze_origin_in_trackbox_coordinate_system']
        xyz_pos_eye_r = sample['right_gaze_origin_in_trackbox_coordinate_system']
      
        # Valid data from the eyes?
        self.right_eye_valid = np.sum(np.isnan(xyz_pos_eye_r)) == 0 # boolean
        self.left_eye_valid = np.sum(np.isnan(xyz_pos_eye_l)) == 0
        
        # Compute the average position of the eyes
        avg_pos = np.nanmean([xyz_pos_eye_l, xyz_pos_eye_r], axis=0)
        # print('avg pos  {:f} {:f} {:f}'.format(avg_pos[0], avg_pos[1], avg_pos[2]))
        
        # If one eye is closed, the center of the circle is moved, 
        # Try to prevent this by compensating by an offset  
        
        if eye == 'both':
            if self.left_eye_valid and self.right_eye_valid: # if both eyes are open
                latest_valid_binocular_avg = avg_pos[:]
                previous_binocular_sample_valid = True
                offset = np.array([0, 0, 0])          
            elif self.left_eye_valid or self.right_eye_valid: 
                
                if previous_binocular_sample_valid:
                    offset = latest_valid_binocular_avg - avg_pos
                    
                previous_binocular_sample_valid = False
            
        #(0.5, 0.5, 0.5)  means the eye is in the center of the box
        self.moving_ellipse.pos = ((avg_pos[0] - 0.5) * -1 - offset[0] , 
                                (avg_pos[1] - 0.5) * -1 - offset[1]) 
                  
        self.moving_ellipse.height = (avg_pos[2] - 0.5)*-1 + self.HEAD_POS_ELLIPSE_MOVING_HEIGHT

        # Control min size of head ellipse
        if self.moving_ellipse.height < self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT:
            self.moving_ellipse.height = self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT
     
        # Compute roll and yaw data from 3D information about the eyes
        # in the headbox (if both eyes are valid)
        if self.left_eye_valid and self.right_eye_valid:
            roll = np.math.tan((xyz_pos_eye_l[1] - xyz_pos_eye_r[1]) / \
                               (xyz_pos_eye_l[0] - xyz_pos_eye_r[0])) 
            yaw =  np.math.tan((xyz_pos_eye_l[2] - xyz_pos_eye_r[2]) / \
                               (xyz_pos_eye_l[0] - xyz_pos_eye_r[0])) *-1
            
            latest_valid_roll = roll
            latest_valid_yaw = yaw
            
        else: # Otherwise use latest valid measurement
            roll = latest_valid_roll
            yaw = latest_valid_roll    
            
#        print('test', latest_valid_binocular_avg, roll, yaw)
                
        # Compute the ellipse height and width
        # The width should be zero if yaw = pi/2 rad (90 deg)
        # The width should be equal to the height if yaw = 0
        self.head_width = self.moving_ellipse.height - \
                          np.abs(yaw) / np.pi * (self.moving_ellipse.height)
                          
#        print(self.moving_ellipse.pos, self.moving_ellipse.height,
#              self.head_width, roll, yaw)              

        # Get head ellipse points to draw
        ellipse_points_head = ellipse(xy = (0, 0), 
                                      width= self.head_width, 
                                      height=self.moving_ellipse.height, 
                                      angle=roll)  
        
        # update position and shape of head ellipse
        self.moving_ellipse.vertices = ellipse_points_head
        
        #%% Compute the position and size of the eyes (roll)
        eye_head_distance = self.head_width / 2
        self.eye_l.pos = (self.moving_ellipse.pos[0] - np.cos(roll) * eye_head_distance,
                          self.moving_ellipse.pos[1] - np.sin(roll) * eye_head_distance)
        self.eye_l.vertices = ellipse_points_head / (5.0 - yaw)
        
        self.eye_r.pos = (self.moving_ellipse.pos[0] + np.cos(roll) * eye_head_distance,
                          self.moving_ellipse.pos[1] + np.sin(roll) * eye_head_distance)
        self.eye_r.vertices = ellipse_points_head / (5.0 + yaw)
        
        #%% Compute the position and size of the pupils
#        print(self.eye_l.pos)
        self.pupil_l.pos = self.eye_l.pos
        self.pupil_l.vertices = self.eye_l.vertices * (sample['left_pupil_diameter']- 1)**2  / 16
        
        self.pupil_r.pos = self.eye_r.pos
        self.pupil_r.vertices = self.eye_r.vertices * (sample['right_pupil_diameter'] - 1)**2 / 16
        
#        print(self.eye_l.pos, self.eye_r.pos)
        
        return latest_valid_binocular_avg, previous_binocular_sample_valid, latest_valid_roll, latest_valid_yaw, offset
               
    def draw(self):
        ''' Draw all requested features
        '''
        
        # Draw head, eyes, and pupils
        self.static_circ.draw()
        self.moving_ellipse.draw()
        
#        print(self.eye, self.moving_ellipse.pos, self.eye_r.pos, self.pupil_r.vertices)
        if 'both' in self.eye or 'right' in self.eye:
            if self.right_eye_valid:
                self.eye_r.draw()
                self.pupil_r.draw()
            else:
                self.eye_r_closed.pos = self.eye_r.pos
                self.eye_r_closed.ori = self.latest_valid_roll
                self.eye_r_closed.width = self.head_width / 2.0 
                self.eye_r_closed.height = self.eye_r_closed.width / 4.0
                self.eye_r_closed.draw()  
                
            if 'right' in self.eye:
                # Indicate that the left eye is not used
                self.eye_l_closed.pos = self.eye_l.pos
                self.eye_l_closed.ori = self.latest_valid_roll
                self.eye_l_closed.width = self.head_width / 2.0 
                self.eye_l_closed.height = self.eye_l_closed.width / 4.0
                self.eye_l_closed.draw()              
            
                
        if 'both' in self.eye or 'left' in self.eye:
            if self.left_eye_valid:
                self.eye_l.draw()
                self.pupil_l.draw()
            else:
                self.eye_l_closed.pos = self.eye_l.pos
                self.eye_l_closed.ori = self.latest_valid_roll
                self.eye_l_closed.width = self.head_width / 2.0 
                self.eye_l_closed.height = self.eye_l_closed.width / 4.0
                self.eye_l_closed.draw()       
                
            if 'left' in self.eye:
                # Indicate that the right eye is not used
                self.eye_r_closed.pos = self.eye_r.pos
                self.eye_r_closed.ori = self.latest_valid_roll
                self.eye_r_closed.width = self.head_width / 2.0 
                self.eye_r_closed.height = self.eye_r_closed.width / 4.0
                self.eye_r_closed.draw()                          
        

        
        
        
        
                
#%%   
class AnimatedCalibrationDisplay(object):
    """ A class for drawing animated targets"""
    def __init__(self, win, target, function_name):
        ''' The function 'function_name' does the actual drawing
        '''
        self.win = win
        self.function_name = function_name
        self.target = target # psychopy.visual object (should be in 'deg' units)
        self.screen_refresh_rate = float(win.getActualFrameRate())
        
    def animate_target(self, point_number, position, tick):
        ''' Calls the target drawing function 'func'
        '''

        eval(''.join(['self.',self.function_name,'(',str(point_number),',', 
                                        '(',str(position[0]),',',
                                            str(position[1]), ')' ,',', str(tick),')']))
        
            
    def animate_point(self, point_number, position, tick):
        ''' Animates calibration point with a certain point_number and position
        tick increases by 1 for each call
        Args:
            position - (x, y)
        '''
        
        target_size = np.abs(1 - np.sin(3 * tick / self.screen_refresh_rate + 4*np.pi/2)) + 0.2
        self.target.set_size(target_size)
        self.target.set_pos(position)
        self.target.draw()
        
    def move_point(self, old_position, new_position, tick):
        ''' Animates movement between two positions
        '''
        move_completed = False
        
        # The target should have a fixed size when moving
        self.target.set_size(2)
        
        # How many ticks should the movement be (one screen unit in one second)?
        n_steps = self.screen_refresh_rate / 2
        step_pos_x = np.linspace(old_position[0], new_position[0], n_steps)
        step_pos_y = np.linspace(old_position[1], new_position[1], n_steps)
        
        if tick >= len(step_pos_x):
            move_completed = True
        else:       
            self.target.set_pos((step_pos_x[tick], step_pos_y[tick]))
            
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
    
