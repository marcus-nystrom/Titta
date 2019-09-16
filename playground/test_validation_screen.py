# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 20:08:24 2019

@author: Marcus
"""

''' Shows validation image after a validation has been completed
        ''' 
        
from psychopy import visual, event
import numpy as np

win = visual.Window(size = [1280, 1024], units='norm',
                    fullscr=False)    
win = visual.Window()                    
        
nCalibrations = 2
selected_calibration = 0
deviations = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]

TEXT_SIZE = 0.04
TEXT_COLOR = 'white' 
blue_active = tuple(np.array([11, 122, 244]) / 255.0 * 2 - 1)
blue = tuple(np.array([37, 97, 163]) / 255.0 * 2 - 1)
        
# Center position of presented calibration values
x_pos_res = 0.55
y_pos_res = 0.2

# information about data quality header
header = ['Quality (deg)', 'L', 'R', 'L_rms', 'R_rms']
header = ['', 'Acc (deg)', 'Prec_RMS (deg)', 'SD (deg)', 'Loss (%)']

x_pos= np.linspace(-0.30, 0.30, num = 5)        

# Prepare rects for buttons, button text, and accuracy values
select_accuracy_rect = []
select_rect_text = []
accuracy_values = []

r=visual.Circle(win, radius=0.1)
r.draw()

y_pos = y_pos_res

accuracy_values_L = []
accuracy_values_R = []

for i in range(nCalibrations):
    select_accuracy_rect.append(visual.Rect(win, width= 0.15, 
                                        height= 0.05, 
                                        units='norm',
                                        pos = (x_pos_res, y_pos)))
                                        
    select_rect_text.append(visual.TextStim(win,
                                            text='Select',
                                            wrapWidth = 1,
                                            height = TEXT_SIZE,
                                            color = TEXT_COLOR,
                                            units='norm',
                                            pos = (x_pos_res, y_pos)))  
            
    
    accuracy_values_L.append(visual.TextStim(win,
                                        text='{4}  {0:.2f}  {0:.2f}  {0:.2f}  {0:.2f}'.format(
                                              deviations[i][0],
                                              deviations[i][1],
                                              deviations[i][2],
                                              deviations[i][3],
                                              'Cal' + str(i+1) + ':'),
                                        wrapWidth = 1,
                                        height = TEXT_SIZE, 
                                        units='norm',
                                        color = TEXT_COLOR,
                                        pos = (x_pos[1], y_pos)))      
    accuracy_values_R.append(visual.TextStim(win,
                                        text='      {4}  {0:.2f}  {0:.2f}  {0:.2f}  {0:.2f}'.format(
                                              deviations[i][0],
                                              deviations[i][1],
                                              deviations[i][2],
                                              deviations[i][3],
                                              '(right eye):'),
                                        wrapWidth = 1,
                                        height = TEXT_SIZE, 
                                        units='norm',
                                        color = TEXT_COLOR,
                                        pos = (x_pos[1], y_pos - 0.04)))                                              
#    # Then prepare the accuracy values for each calibration preceded 
#    # by Cal x (the calibration number)
#    accuracy_values_j = []
#    for j, x in enumerate(x_pos):       
#        if j > 0:
#            accuracy_values_j.append(visual.TextStim(win,
#                                                text='{0:.2f}'.format(deviations[i][j - 1]),
#                                                wrapWidth = 1,
#                                                height = TEXT_SIZE, 
#                                                units='norm',
#                                                color = TEXT_COLOR,
#                                                pos = (x, y_pos)))  
#            print(x, y_pos)              
#        else:
#            accuracy_values_j.append(visual.TextStim(win,
#                                                text='Cal' + str(i+1) + ':',
#                                                wrapWidth = 1,
#                                                height = TEXT_SIZE, 
#                                                units='norm',
#                                                color = TEXT_COLOR,
#                                                pos = (x, y_pos))) 
#            
#    accuracy_values.append(accuracy_values_j)                 
    y_pos -= 0.06
    

# Prepare header
header_text = []    
y_pos = y_pos_res

header_text = visual.TextStim(win,text='  '.join(header),
                                        wrapWidth = 1,
                                        height = TEXT_SIZE, 
                                        units='norm',
                                        pos = (x_pos[2], y_pos_res + 0.06),
                                        color = TEXT_COLOR)
header_text.draw()                                        
                                        
#for j, x in enumerate(x_pos):
#    header_text.append(visual.TextStim(win,text=header[j],
#                                        wrapWidth = 1,
#                                        height = TEXT_SIZE, 
#                                        units='norm',
#                                        pos = (x, y_pos_res + 0.06),
#                                        color = TEXT_COLOR))
#                                        
#
#
#    header_text[j].draw()   
    
# Draw accuracy/precision values and buttons to select a calibration
for i in range(nCalibrations):
    
    # Highlight selected calibrations
    if i == selected_calibration - 1: # Calibration selected
#                    select_rect_text[i].color = self.settings.graphics.blue_active
        select_accuracy_rect[i].fillColor = blue_active
        if nCalibrations > 1:
            select_accuracy_rect[i].draw() 
            select_rect_text[i].draw()     
    else:
#                    select_rect_text[i].color = self.settings.graphics.blue
        select_accuracy_rect[i].fillColor = blue
        select_accuracy_rect[i].draw() 
        select_rect_text[i].draw()  
        
    # Then draw the accuracy values for each calibration preceded 
    # by Cal x (the calibration number)
    
#    for j, x in enumerate(x_pos): 
#                    print(i, j, accuracy_values[i][j] t, accuracy_values[i][j].pos)
    accuracy_values_L[i].draw()    
#    accuracy_values_R[i].draw()                    
    
    
win.flip()    
event.waitKeys()
win.close()

