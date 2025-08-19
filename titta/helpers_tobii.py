# -*- coding: utf-8 -*-
"""
Created on Tue Jun 06 16:20:36 2017

@author: marcus
"""
from psychopy import visual
import numpy as np
import copy
import warnings
import abc

HAS_PSYCHOPY = False
try:
    from psychopy.tools.monitorunittools import cm2deg, deg2pix
except:
    pass
else:
    HAS_PSYCHOPY = True


#%%
def tobii2norm(pos):
    ''' Converts from Tobiis coordinate system [0, 1] to PsychoPy's 'norm' (-1, 1).
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center.
    y = -1 in PsychoPy coordinates means bottom of screen
    Args:   pos: N x 2 array with positions
    '''

    pos_temp = copy.deepcopy(pos) # To avoid that the called parameter is changed

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
    pos_temp = copy.deepcopy(pos) # To avoid that the called parameter is changed

    # Convert between coordinate system
    pos_temp[:, 0] = pos_temp[:, 0] / 2.0 + 0.5
    pos_temp[:, 1] = pos_temp[:, 1]/ -2.0 + 0.5


    return pos_temp

def tobii2deg(pos, mon):
    ''' Converts Tobiis coordinate system [0, 1 to degrees.
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    Assumes pixels are square
    Args:   pos: N x 2 array with calibratio position in [0, 1]
            screen_height: height of screen in cm
    '''

    pos_temp = copy.deepcopy(pos) # To avoid that the called parameter is changed

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

def deg2tobii(pos, mon):
    ''' Converts from degrees to Tobiis coordinate system [0, 1].
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    '''

    # First convert from deg to pixels
    pos[:, 0] = deg2pix(pos[:, 0], mon, correctFlat=False)
    pos[:, 1] = deg2pix(pos[:, 1], mon, correctFlat=False)

    # Then normalize data -1,1
    pos[:, 0] = pos[:, 0] / float(mon.getSizePix()[0])/2
    pos[:, 1] = pos[:, 1] / float(mon.getSizePix()[1])/2

    #.. finally shift to tobii coordinate system
    return norm2tobii(pos)

def tobii2pix(pos, win):
    ''' Converts from  Tobiis coordinate system [0, 1] to pixles.
    Note that the Tobii coordinate system start in the upper left corner
    and screen coordinate in the upper left corner
    Args:   pos: N x 2 array with calibratio position in [0, 1]
            screen_height: height of screen in cm
    '''

    pos_temp = copy.deepcopy(pos)     # Center

    # Center
    pos_temp[:, 0] = pos_temp[:, 0] - 0.5
    pos_temp[:, 1] = (pos_temp[:, 1] - 0.5) * -1

	# Convert to pixels
    pos_temp[:, 0] = pos_temp[:, 0] * win.size[0]
    pos_temp[:, 1] = pos_temp[:, 1] * win.size[1]

    # Convert to deg.
    return pos_temp

def pix2tobii(pos, mon):
    ''' Converts from PsychoPy pixels to Tobiis coordinate system [0, 1].
    Note that the Tobii coordinate system start in the upper left corner
    and the PsychoPy coordinate system in the center
    '''
    # Normalize data -1,1
    pos[:, 0] = pos[:, 0] / (float(mon.getSizePix()[0]) / 2.0)
    pos[:, 1] = pos[:, 1] / (float(mon.getSizePix()[1]) / 2.0)

    #.. finally shift to tobii coordinate system
    return norm2tobii(pos)

# %%
class TargetBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_for_win(self, win):
        pass
    @abc.abstractmethod
    def get_size(self, position):
        # NB: sizes for the object should be in 'pix' units
        pass
    @abc.abstractmethod
    def get_size(self):
        pass
    @abc.abstractmethod
    def set_size(self, target_size):
        pass
    @abc.abstractmethod
    def draw(self):
        pass

#%%
class MyDot2(TargetBase):
    '''
    Generates the best fixation target according to Thaler et al. (2013)
    '''
    def __init__(self, outer_diameter=50, inner_diameter=10,
                 outer_color='black', inner_color='white', units='pix', win=None):
        super().__init__()
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.outer_color    = outer_color
        self.inner_color    = inner_color
        self.units          = units
        if win is not None:
            self.create_for_win(win)

    def create_for_win(self, win):
        # Set properties of dot
        self.outer_dot = visual.Circle(win, fillColor = self.outer_color, radius = self.outer_diameter/2,
                                       units = self.units)
        self.inner_dot = visual.Circle(win, fillColor = self.outer_color, radius = self.inner_diameter/2,
                                       units = self.units)
        self.line_vertical = visual.Rect(win, width=self.inner_diameter, height=self.outer_diameter,
                                         fillColor=self.inner_color, units = self.units)
        self.line_horizontal = visual.Rect(win, width=self.outer_diameter, height=self.inner_diameter,
                                           fillColor=self.inner_color, units = self.units)

    def set_size(self, size):
        ''' Sets the size of the stimulus
        '''
        self.outer_diameter = size
        self.outer_dot.radius = self.outer_diameter/2
        self.line_vertical.size = (self.line_vertical.width, self.outer_diameter)
        self.line_horizontal.size = (self.outer_diameter, self.line_horizontal.height)

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
        return self.outer_dot.pos

    def get_size(self):
        '''
        get size of dot
        '''
        return self.outer_diameter

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
        inverts (swaps) the colors of the dot
        '''
        self.inner_dot.fillColor, self.outer_dot.fillColor = self.outer_dot.fillColor, self.inner_dot.fillColor
        self.inner_color, self.outer_color                 = self.outer_color, self.inner_color

    def set_color(self, outer_color, inner_color):
        self.outer_color, self.inner_color = outer_color, inner_color
        self.outer_dot.lineColor = self.outer_color
        self.outer_dot.fillColor = self.outer_color
        self.inner_dot.fillColor = self.outer_color
        self.inner_dot.lineColor = self.outer_color
        self.line_vertical.lineColor = self.inner_color
        self.line_horizontal.fillColor = self.inner_color
        self.line_vertical.fillColor = self.inner_color
        self.line_horizontal.lineColor = self.inner_color


#%%
class MyDot3(TargetBase):
    '''
    Black circle
    '''
    def __init__(self, outer_diameter=50, inner_diameter=10,
                 outer_color='black', inner_color='gray', units='pix', win=None):
        super().__init__()
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.outer_color    = outer_color
        self.inner_color    = inner_color
        self.units          = units
        if win is not None:
            self.create_for_win(win)

    def create_for_win(self, win):
        # Set properties of dot
        self.outer_dot = visual.Circle(win,fillColor = self.outer_color, radius = self.outer_diameter/2,
                                       units = self.units)
        self.inner_dot = visual.Circle(win,fillColor = self.inner_color, radius = self.inner_diameter/2,
                                       units = self.units)

    def set_size(self, size):
        ''' Sets the size of the stimulus
        '''
        self.outer_diameter = size
        self.outer_dot.radius = self.outer_diameter/2

    def set_pos(self, pos):
        '''
        sets position of dot
        pos = [x,y]
        '''
        self.outer_dot.pos = pos
        self.inner_dot.pos = pos

    def get_pos(self):
        '''
        get position of dot
        '''
        return self.outer_dot.pos

    def get_size(self):
        '''
        get size of dot
        '''
        return self.outer_diameter

    def draw(self):
        '''
        draws the dot
        '''
        self.outer_dot.draw()
        self.inner_dot.draw()

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

    def __init__(self, win, HEAD_BOX_CENTER, HEAD_POS_CIRCLE_FIXED_COLOR, HEAD_POS_CIRCLE_MOVING_COLOR):
        '''
        Args:
            win - psychopy window handle
            HEAD_BOX_CENTER - center of headbox, e.g., [x, y, z] = [0, 0, 700]
        '''
        self.win = win

        # Head parameters
        HEAD_POS_CIRCLE_FIXED_COLOR = HEAD_POS_CIRCLE_FIXED_COLOR
        HEAD_POS_CIRCLE_FIXED_RADIUS = 0.20
        self.HEAD_POS_ELLIPSE_MOVING_HEIGHT = 0.20
        self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT = 0.05

        # Eye parameters
        self.EYE_SIZE = 0.03

        # Center of headbox (in positioning stream [0, 1])
        if len(HEAD_BOX_CENTER) == 0:
            self.center_of_headbox = np.array([0.5, 0.5, 0.5])
            self.use_positioning_stream = True  # For head positioning
        else:
            self.center_of_headbox = HEAD_BOX_CENTER
            self.use_positioning_stream = False
            # What is the position of HEAD_BOX_CENTER in positioning stream?

        # Setup control circles for head position
        self.static_circ = visual.Circle(win, radius = HEAD_POS_CIRCLE_FIXED_RADIUS,
                                         lineColor = HEAD_POS_CIRCLE_FIXED_COLOR,
                                         fillColor = None,
                                         lineWidth=6, units='height')

        # Size=None (If None is specified, the size will be set with values passed to width and height)
        self.moving_ellipse = visual.ShapeStim(win,  lineColor = HEAD_POS_CIRCLE_MOVING_COLOR,
                                         lineWidth=6, units='height',
                                         size=None,
                                         fillColor=HEAD_POS_CIRCLE_MOVING_COLOR, opacity=0.5)

        # Ellipses for eyes
        self.eye_l = visual.ShapeStim(win,  lineColor = 'white', fillColor='white',
                                         lineWidth=2, units='height')
        self.eye_r = visual.ShapeStim(win,  lineColor = 'white', fillColor='white',
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

        # state variables
        self.latest_valid_yaw = 0.
        self.latest_valid_roll = 0.
        self.previous_binocular_sample_valid = True
        self.latest_valid_binocular_avg = self.center_of_headbox
        self.offset = np.array([0., 0., 0.])


    def update(self, sample, sample_user_pos, eye='both'):
        '''
        Args:
            sample - a dict containing information about the sample

                relevant info in sample is [UCS, unit (mm)]

                sample['left_gaze_origin_in_user_coordinates_y']
                sample.right.gaze_origin.in_user_coordinate_system
                sample.left.gaze_origin.in_trackbox_coordinate_system
                sample.right.gaze_origin.in_trackbox_coordinate_system
                sample.left.pupil_diameter
                sample.right.pupil_diameter

            sample_user_pos

                relevant info in sample is [UCS, norm [0, 1]]

                sample_user_pos.left.user_position
                sample_user_pos.left.user_validity.valid.value
                sample_user_pos.right.user_position
                sample_user_pos.left.user_validity.valid.value

            eye - track, both eyes, left eye, or right eye
                  the non-tracked eye will be indicated by a cross

            latest_binocular_avg
        '''

        self.eye = eye # Which eye(s) should be tracked

        # Indicate that eye is not used by red color
        if 'right' in self.eye:
            self.eye_l_closed.fillColor = (1, -1, -1) # Red

        if 'left' in self.eye:
            self.eye_r_closed.fillColor = (1, -1, -1)

        #%% 1. Compute the average position of the head ellipse
        # if self.use_positioning_stream:
        xyz_pos_eye_l = (sample_user_pos['left_user_position_x'][0],
                         sample_user_pos['left_user_position_y'][0],
                         sample_user_pos['left_user_position_z'][0])

        xyz_pos_eye_r = (sample_user_pos['right_user_position_x'][0],
                         sample_user_pos['right_user_position_y'][0],
                         sample_user_pos['right_user_position_z'][0])
        # else: # Use User coordinate system (in mm)

        if not self.use_positioning_stream:
            xyz_pos_eye_l_ucs = (sample['left_gaze_origin_in_user_coordinates_x'][0],
                             sample['left_gaze_origin_in_user_coordinates_y'][0],
                             sample['left_gaze_origin_in_user_coordinates_z'][0])

            xyz_pos_eye_r_ucs = (sample['right_gaze_origin_in_user_coordinates_x'][0],
                             sample['right_gaze_origin_in_user_coordinates_y'][0],
                             sample['right_gaze_origin_in_user_coordinates_z'][0])


        # Valid data from the eyes?
        self.right_eye_valid = np.sum(np.isnan(xyz_pos_eye_r)) == 0 # boolean
        self.left_eye_valid = np.sum(np.isnan(xyz_pos_eye_l)) == 0

        # Compute the average position of the eyes
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            # if self.use_positioning_stream:
            avg_pos = np.nanmean([xyz_pos_eye_l, xyz_pos_eye_r], axis=0)
            # else:

            if not self.use_positioning_stream:
                avg_pos_ucs = np.nanmean([xyz_pos_eye_l_ucs, xyz_pos_eye_r_ucs], axis=0)

        # If one eye is closed, the center of the circle is moved,
        # Try to prevent this by compensating by an offset

        if eye == 'both':
            if self.left_eye_valid and self.right_eye_valid: # if both eyes are open
                self.latest_valid_binocular_avg = avg_pos[:]
                self.previous_binocular_sample_valid = True
                self.offset = np.array([0., 0., 0.])
            elif self.left_eye_valid or self.right_eye_valid:
                if self.previous_binocular_sample_valid:
                    self.offset = self.latest_valid_binocular_avg - avg_pos

                self.previous_binocular_sample_valid = False

        #(0.5, 0.5, 0.5)  means the eye is in the center of the box
        if self.use_positioning_stream:
            self.moving_ellipse.pos = ((avg_pos[0] - self.center_of_headbox[0]) * -1 - self.offset[0] ,
                                       (avg_pos[1] - self.center_of_headbox[1]) * -1 - self.offset[1])
        else:
            self.moving_ellipse.pos = ((avg_pos_ucs[0] - self.center_of_headbox[0]) / 300 - self.offset[0] ,
                                       (avg_pos_ucs[1] - self.center_of_headbox[1]) / 300 - self.offset[1])

        # Compute roll and yaw data from 3D information about the eyes
        # in the headbox (if both eyes are valid)
        if self.left_eye_valid and self.right_eye_valid:
            roll = np.tan((xyz_pos_eye_l[1] - xyz_pos_eye_r[1]) / \
                          (xyz_pos_eye_l[0] - xyz_pos_eye_r[0]))
            yaw =  np.tan((xyz_pos_eye_l[2] - xyz_pos_eye_r[2]) / \
                          (xyz_pos_eye_l[0] - xyz_pos_eye_r[0])) *-1

            self.latest_valid_roll = roll
            self.latest_valid_yaw = yaw

        else: # Otherwise use latest valid measurement
            roll = self.latest_valid_roll
            yaw = self.latest_valid_yaw
        self.latest_valid_roll_deg = roll * 180 / np.pi * -1

        # Compute the ellipse height and width
        # The width should be zero if yaw = pi/2 rad (90 deg)
        # The width should be equal to the height if yaw = 0
        if self.use_positioning_stream:
            ellipse_height = (avg_pos[2] - self.center_of_headbox[2]) *-1 * 0.2 + \
                              self.HEAD_POS_ELLIPSE_MOVING_HEIGHT
        else:
            ellipse_height = (avg_pos_ucs[2] - self.center_of_headbox[2]) / 200 *-1 * 0.2 + \
                              self.HEAD_POS_ELLIPSE_MOVING_HEIGHT


        # Control min size of head ellipse
        if ellipse_height < self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT:
            ellipse_height = self.HEAD_POS_ELLIPSE_MOVING_MIN_HEIGHT

        self.head_width = ellipse_height - \
                          np.abs(yaw) / np.pi * (ellipse_height)

        # Get head ellipse points to draw
        ellipse_points_head = ellipse(xy = (0, 0),
                                      width= self.head_width,
                                      height=ellipse_height,
                                      angle=roll, n_points=100)

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
        self.pupil_l.pos = self.eye_l.pos
        self.pupil_l.vertices = self.eye_l.vertices * (sample['left_pupil_diameter'][0] - 1)*2 / 16

        self.pupil_r.pos = self.eye_r.pos
        self.pupil_r.vertices = self.eye_r.vertices * (sample['right_pupil_diameter'][0] - 1)*2 / 16

        return self.latest_valid_binocular_avg, self.previous_binocular_sample_valid, self.latest_valid_roll, self.latest_valid_yaw, self.offset

    def draw(self):
        ''' Draw all requested features
        '''

        # draw reference
        self.static_circ.draw()

        # early out if nothing else to draw
        if not (self.right_eye_valid or self.left_eye_valid):
            return

        # Draw head, eyes, and pupils
        self.moving_ellipse.draw()

        if 'both' in self.eye or 'right' in self.eye:
            if self.right_eye_valid:
                self.eye_r.draw()
                self.pupil_r.draw()
            else:
                self.eye_r_closed.pos = self.eye_r.pos
                self.eye_r_closed.ori = self.latest_valid_roll_deg
                self.eye_r_closed.size = (self.head_width / 2.0, self.head_width / 8.0)
                self.eye_r_closed.draw()

            if 'right' in self.eye:
                # Indicate that the left eye is not used
                self.eye_l_closed.pos = self.eye_l.pos
                self.eye_l_closed.ori = self.latest_valid_roll_deg
                self.eye_l_closed.size = (self.head_width / 2.0, self.head_width / 8.0)
                self.eye_l_closed.draw()


        if 'both' in self.eye or 'left' in self.eye:
            if self.left_eye_valid:
                self.eye_l.draw()
                self.pupil_l.draw()
            else:
                self.eye_l_closed.pos = self.eye_l.pos
                self.eye_l_closed.ori = self.latest_valid_roll_deg
                self.eye_l_closed.size = (self.head_width / 2.0, self.head_width / 8.0)
                self.eye_l_closed.draw()

            if 'left' in self.eye:
                # Indicate that the right eye is not used
                self.eye_r_closed.pos = self.eye_r.pos
                self.eye_r_closed.ori = self.latest_valid_roll_deg
                self.eye_r_closed.size = (self.head_width / 2.0, self.head_width / 8.0)
                self.eye_r_closed.draw()


#%%
class AnimatedCalibrationDisplay(object):
    """ A class for drawing animated targets"""
    def __init__(self, win, target, move_duration):
        self.win = win
        if not isinstance(target,TargetBase):
            raise ValueError('Provided target should be an instance of a class derived from helpers_tobii.TargetBase')
        self.target = target
        self.target_size = target.get_size()
        self.move_duration = move_duration
        self.screen_refresh_rate = float(win.getActualFrameRate() or 60)

    def animate_point(self, point_number, position, tick):
        ''' Animates calibration point with a certain point_number and position
        tick increases by 1 for each call
        Args:
            position - (x, y)
        '''
        target_size = np.abs(self.target_size - self.target_size * np.sin(3 * tick / self.screen_refresh_rate + 4*np.pi/2)) + self.target_size / 5
        self.target.set_size(target_size)
        self.target.set_pos(position)
        self.target.draw()

    def move_point(self, old_position, new_position, tick):
        ''' Animates movement between two positions
        '''
        move_completed = False

        # The target should have a fixed size when moving
        self.target.set_size(2 * self.target_size)

        # How many ticks should the movement be (one screen unit in one second)?
        n_steps = int(self.screen_refresh_rate * self.move_duration)
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
    rms = np.sqrt(np.nanmean(np.square(np.diff(x))))
    return rms

#%%
def sd(x):
    return np.nanstd(x)