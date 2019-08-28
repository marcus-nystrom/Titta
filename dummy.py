# -*- coding: utf-8 -*-
"""
Created on Wed Aug 21 18:02:41 2019

@author: Marcus
"""

from psychopy import visual, event
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np
import helpers_tobii import
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
    
    points = np.vstack((X, Y)).T / 2.0
    
    return points
#%%



win = visual.Window()

# Create ellipse pionts
#ellipse_points = ellipse(xy = (0, 0), width=0.5, height=0.9, angle=0)     
         
#head = visual.ShapeStim(win, vertices = ellipse_points, units='height')
head.draw()
win.flip()
event.waitKeys()

win.close()