# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 10:57:23 2019

@author: Jonathan
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

def plotResults(data,fix,res=[1920,1080]):
    '''
    Plots the results of the I2MC function
    '''
    
    time = data['time']
    Xdat = np.array([])
    Ydat = np.array([])
    klr  = []
    if 'L_X' in data.keys():
        Xdat = data['L_X']
        Ydat = data['L_Y']
        klr.append('g')
    if 'R_X' in data.keys():
        if len(Xdat) == 0:
            Xdat = data['R_X']
            Ydat = data['R_Y']
        else:
            Xdat = np.vstack([Xdat, data['R_X']])
            Ydat = np.vstack([Ydat, data['R_Y']])
        klr.append('r')
    if 'average_X' in data.keys() and not 'L_X' in data.keys() and not 'R_X' in data.keys():
        if len(Xdat) == 0:
            Xdat = data['average_X']
            Ydat = data['average_Y']
        else:
            Xdat = np.vstack([Xdat, data['average_X']])
            Ydat = np.vstack([Ydat, data['average_Y']])
        klr.append('b')   
    
    # Plot settings
    myfontsize = 10
    myLabelSize = 12
    traceLW = 0.5
    fixLW= 2
    
    font = {'size': myfontsize}
    matplotlib.rc('font', **font)
    
    ## plot layout
    f = plt.figure(figsize=(10, 6), dpi=300)
    ax1 = plt.subplot(2,1,1)
    ### Plot x position
    for p in range(Xdat.shape[0]):
        ax1.plot(time,Xdat[p,:],klr[p]+'-', linewidth = traceLW)
    
    # add fixations
    for b in range(len(fix['startT'])):
        ax1.plot([fix['startT'][b], fix['endT'][b]], [fix['xpos'][b], fix['xpos'][b]],'k-', linewidth = fixLW)
    
    ax1.set_ylabel('Horizontal position (pixels)', size = myLabelSize)
    ax1.set_xlim([0, time[-1]])
    ax1.set_ylim([0, res[0]])

    ### Plot Y posiiton
    ax2 = plt.subplot(2,1,2,sharex=ax1)
    for p in range(Ydat.shape[0]):
        ax2.plot(time,Ydat[p,:],klr[p]+'-', linewidth = traceLW)

    # add fixations
    for b in range(len(fix['startT'])):
        ax2.plot([fix['startT'][b], fix['endT'][b]], [fix['ypos'][b], fix['ypos'][b]],'k-', linewidth = fixLW)
    
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Vertical position (pixels)', size = myLabelSize)
    ax2.set_ylim([0, res[1]])

    return f

