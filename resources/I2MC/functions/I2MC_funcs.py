# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 10:54:00 2019

@author: Jonathan
"""

# =============================================================================
# Import libraries
# =============================================================================
import numpy as np
import scipy
import scipy.interpolate as interp
import scipy.signal
from scipy.cluster.vq import kmeans2
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as patches
import copy

# =============================================================================
# # ToDo 
# =============================================================================
# General stuff 
#- Check all the functions help text (type, description etc)

# Functions (Interpolate)
# - Can we use my implementation? not steffen

# Functions (CLUSTERING)
#- twoClusterWeighting
#   - Downsampling
#   - missing values handeling?
#   - Edges and going back for the latest samples

# Questions
# When getting median gaze position (fixation), the inetrpolated values are ignored. 
#   Is this intended, then whats the point of interpolaiton, besides the clustering?
# Not all results are identical to matlab version
#   for instance, trial 1 pp2, fix5 and 6 have a slight overlap
#   pp2 trial 3,4 and 5 has a fixations thats to short compared to matlab (almost last fixation)


# =============================================================================
# Helper functions
# =============================================================================
def isNumber(s):
    try:
        np.array(s,dtype=float)
        return True
    except ValueError:
        return False    

def checkNumeric(k,v):
    assert isNumber(v), 'The value of "{}" is invalid. Expected input to be one of these types:\n\ndouble, single, uint8, uint16, uint32, uint64, int8, int16, int32, int64\n\nInstead its type was {}.'.format(k, type(v))

def checkScalar(k,v):
    assert np.ndim(v) == 0, 'The value of "{}" is invalid. Expected input to be a scalar.'.format(k)

def checkNumel2(k,v):
    assert np.shape(v) == (2,), 'The value of "{}" is invalid. Expected input to be an array with number of elements equal to 2.'.format(k)

def checkInt(k,v):
    assert np.sum(np.array(v)%1) == 0, 'The value of "{}" is invalid. Expected input to be integer-valued.'.format(k)
    
def checkFun(k, d, s):
    assert k in d.keys(), 'I2MCfunc: "{}" must be specified using the "{}" option'.format(s, k)
    assert isNumber(d[k]), 'I2MCfunc: "{}" must be set as a number using the "{}" option'.format(s, k) 

def angleToPixels(angle, screenDist, screenW, screenXY):
    """
    Calculate the number of pixels which equals a specified angle in visual
    degrees, given parameters. Calculates the pixels based on the width of
    the screen. If the pixels are not square, a separate conversion needs
    to be done with the height of the screen.\n
    "angleToPixelsWH" returns pixels for width and height.

    Parameters
    ----------
    angle : float or int
        The angle to convert in visual degrees
    screenDist : float or int
        Viewing distance in cm
    screenW : float or int
        The width of the screen in cm
    screenXY : tuple, ints
        The resolution of the screen (width - x, height - y), pixels

    Returns
    -------
    pix : float
        The number of pixels which corresponds to the visual degree in angle,
        horizontally

    Examples
    --------
    >>> pix = angleToPixels(1, 75, 47.5, (1920,1080))
    >>> pix
    52.912377341863817
    """
    pixSize = screenW / float(screenXY[0])
    angle = np.radians(angle / 2.0)
    cmOnScreen = np.tan(angle) * float(screenDist)
    pix = (cmOnScreen / pixSize) * 2

    return pix

def getMissing(L_X, R_X, missingx, L_Y, R_Y, missingy):
    """
    Gets missing data and returns missing data for left, right and average
    
    Parameters
    ----------
    L_X : np.array
        Left eye X gaze position data
    R_X : np.array
        Right eye X gaze position data
    missingx : Not defined
        The values reflecting mising values for X coordinates in the dataset
    L_Y : np.array
        Left eye Y gaze position data
    R_Y : np.array
        Right eye Y gaze position data
    missingy : Not defined
        The value reflectings mising values for Y coordinates in the dataset

    Returns
    -------
    qLMiss : np.array - Boolean
        Boolean with missing values for the left eye
    qRMiss : np.array - Boolean
        Boolean with missing values for the right eye
    qBMiss : np.array - Boolean
        Boolean with missing values for both eyes
        
    Examples
    --------
    >>>
    """

    # Get where the missing is
    
    # Left eye
    qLMissX = np.logical_or(L_X == missingx, np.isnan(L_X))
    qLMissY = np.logical_or(L_Y == missingy, np.isnan(L_Y))
    qLMiss = np.logical_and(qLMissX, qLMissY)
    
    # Right
    qRMissX = np.logical_or(R_X == missingx, np.isnan(R_X))
    qRMissY = np.logical_or(R_Y == missingy, np.isnan(R_Y))
    qRMiss = np.logical_and(qRMissX, qRMissY)

    # Both eyes
    qBMiss = np.logical_and(qLMiss, qRMiss)

    return qLMiss, qRMiss, qBMiss


def averageEyes(L_X, R_X, missingx, L_Y, R_Y, missingy):
    """
    Averages data from two eyes. Take one eye if only one was found.
    
    Parameters
    ----------
    L_X : np.array
        Left eye X gaze position data
    R_X : np.array
        Right eye X gaze position data
    missingx : Not defined
        The values reflecting mising values for X coordinates in the dataset
    L_Y : np.array
        Left eye Y gaze position data
    R_Y : np.array
        Right eye Y gaze position data
    missingy : Not defined
        The values reflecting mising values for Y coordinates in the dataset

    Returns
    -------
    xpos : np.array
        The average Y gaze position
    ypos : np.array
        The average X gaze position
    qBMiss : np.array - Boolean
        Boolean with missing values for both eyes
    qLMiss : np.array - Boolean
        Boolean with missing values for the left eye
    qRMiss : np.array - Boolean
        Boolean with missing values for the right eye

    Examples
    --------
    >>>
    """

    xpos = np.zeros(len(L_X))
    ypos = np.zeros(len(L_Y))
    
    # get missing
    qLMiss, qRMiss, qBMiss = getMissing(L_X, R_X, missingx, L_Y, R_Y, missingy)

    q = np.logical_and(np.invert(qLMiss), np.invert(qRMiss))
    xpos[q] = (L_X[q] + R_X[q]) / 2.
    ypos[q] = (L_Y[q] + R_Y[q]) / 2.
    
    q =  np.logical_and(qLMiss, np.invert(qRMiss))
    xpos[q] = R_X[q]
    ypos[q] = R_Y[q]
    
    q = np.logical_and(np.invert(qLMiss), qRMiss)
    xpos[q] = L_X[q]
    ypos[q] = L_Y[q]
    
    xpos[qBMiss] = np.NAN
    ypos[qBMiss] = np.NAN

    return xpos, ypos, qBMiss, qLMiss, qRMiss

def bool2bounds(b):
    """
    Finds all contiguous sections of true in a boolean

    Parameters
    ----------
    data : np.array
        A 1d np.array containing True, False values.
    
    Returns
    -------
    on : np.array
        The array contains the indexes of the first value = True
    off : np.array
        The array contains the indexes of the last value = True in a sequence
    
    Example
    --------
    >>> import numpy as np
    >>> b = np.array([1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0])
    >>> on, off = bool2bounds(b)
    >>> print(on)
    [0 4 8]
    >>> print(off)
    [0 6 9]
    """
    b = np.array(np.array(b, dtype = np.bool), dtype=int)
    b = np.pad(b, (1, 1), 'constant', constant_values=(0, 0))
    D = np.diff(b)
    on  = np.array(np.where(D == 1)[0], dtype=int)
    off = np.array(np.where(D == -1)[0] -1, dtype=int)
    return on, off

def getCluster(b):
    '''
    Splits a np.array with True, False values into clusters. A cluster is 
    defined as adjacent points with the same value, e.g. True or False. 
    The output from this function is used to determine cluster sizes when
    running cluster statistics. 
    
    Parameters
    ----------
    b : np.array
        A 1d np.array containing True, False values.
    
    Returns
    -------
    clusters : list of np.arrays
        The list contains the clusters split up. Each cluster in its own
        np.array. 
    indx : list of np.arrays
        The list contains the indexes for each time point in the clusters.     
    
    Example
    --------
    >>> 
    ''' 
    if b.dtype != 'bool':
       b = np.array(b, dtype = np.bool)
    clusters = np.split(b, np.where(np.diff(b) != 0)[0]+1)
    indx = np.split(np.arange(len(b)), np.where(np.diff(b) != 0)[0]+1)
    size = np.array([len(c) for c in indx])
    offC = np.array([np.sum(c) > 0 for c in clusters])
    onC = np.invert(offC)
    offCluster = [indx[i] for i in range(len(offC)) if offC[i]]
    onCluster = [indx[i] for i in range(len(onC)) if onC[i]]
    
    offSize = size[offC]
    onSize = size[onC]
    
    missStart = np.array([c[0] for c in offCluster], dtype=int)
    missEnd = np.array([c[-1] for c in offCluster], dtype=int)
    
    dataStart = np.array([c[0] for c in onCluster], dtype=int)
    dataEnd = np.array([c[-1] for c in onCluster], dtype=int)
    
    return missStart, missEnd, dataStart, dataEnd, onSize, offSize, onCluster, offCluster

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
    fixLWax1 = res[0]/100
    fixLWax2 = res[1]/100
    
    font = {'size': myfontsize}
    matplotlib.rc('font', **font)
    
    ## plot layout
    f = plt.figure(figsize=(10, 6), dpi=300)
    ax1 = plt.subplot(2,1,1)
    ax1.set_ylabel('Horizontal position (pixels)', size = myLabelSize)
    ax1.set_xlim([0, time[-1]])
    ax1.set_ylim([0, res[0]])

    ### Plot x position
    if len(Xdat.shape) > 1:
        for p in range(Xdat.shape[0]):
            ax1.plot(time,Xdat[p,:],klr[p]+'-', linewidth = traceLW)
    else:
        ax1.plot(time,Xdat,klr[0]+'-', linewidth = traceLW)
    
    ### Plot Y posiiton
    ax2 = plt.subplot(2,1,2,sharex=ax1)
    ax2.set_xlabel('Time (ms)')
    ax2.set_ylabel('Vertical position (pixels)', size = myLabelSize)
    ax2.set_ylim([0, res[1]])
    if len(Xdat.shape)  > 1:
        for p in range(Ydat.shape[0]):
            ax2.plot(time,Ydat[p,:],klr[p]+'-', linewidth = traceLW)
    else:
        ax2.plot(time,Ydat,klr[0]+'-', linewidth = traceLW)
        
    # add fixations, but adds a shaded area instead of line
    for b in range(len(fix['startT'])):
        ax1.add_patch(patches.Rectangle((fix['startT'][b], fix['xpos'][b] - (fixLWax1/2)),
                                       fix['endT'][b] - fix['startT'][b],
                                       abs(fixLWax1), fill=True, alpha = 0.8, color = 'k',
                                       linewidth = 0, zorder=3))
        ax2.add_patch(patches.Rectangle((fix['startT'][b], fix['ypos'][b] - (fixLWax2/2)),
                                       fix['endT'][b] - fix['startT'][b],
                                       abs(fixLWax2), fill=True, alpha = 0.8, color = 'k',
                                       linewidth = 0, zorder=3))

    return f

# =============================================================================
# Interpolation functions 
# =============================================================================
def findInterpWins(xpos, ypos, missing, windowtime, edgesamples, freq, maxdisp):
    """
    Description
    
    Parameters
    ----------
    xpos : np.array
        X gaze position
    ypos : type
        Y gaze position
    missing : type
        Description
    windowtime : float
        Time of window to interpolate over in ms
    edgesamples : int
        Number of samples at window edge used for interpolating in ms
    freq : float
        Frequency of measurement
    maxdisp : float
        maximum dispersion in position signal (i.e. if signal is in pixels, provide maxdisp in n pixels)


    Returns
    -------
    notAllowed : np.array
        Boolean with True where interpolation is not valid           
        
    Examples
    --------
    >>>
    """          
    # get indices of where missing intervals start and end
    missStart, missEnd = bool2bounds(missing)
    dataStart, dataEnd = bool2bounds(np.invert(missing))
    #missStart, missEnd, dataStart, dataEnd, onSize, offSize, onCluster, offCluster = getCluster(missing)
    
    # Determine windowsamples
    windowsamples = round(windowtime/(1./freq))
    
    # for each candidate, check if have enough valid data at edges to execute
    # interpolation. If not, see if merging with adjacent missing is possible
    # we don't throw out anything we can't deal with yet, we do that below.
    # this is just some preprocessing
    k=0  #was K=1 in matlab
    while k<len(missStart):
        # skip if too long
        if missEnd[k]-missStart[k]+1 > windowsamples:
            k = k+1
            continue

        # skip if not enough data at left edge
        if np.sum(dataEnd == missStart[k]-1) > 0:
            datk = int(np.argwhere(dataEnd==missStart[k]-1))
            if dataEnd[datk]-dataStart[datk]+1 < edgesamples:
                k = k+1
                continue
        
        # if not enough data at right edge, merge with next. Having not enough
        # on right edge of this one, means not having enough at left edge of
        # next. So both will be excluded always if we don't do anything. So we
        # can just merge without further checks. Its ok if it then grows too
        # long, as we'll just end up excluding that too below, which is what
        # would have happened if we didn't do anything here
        datk = np.argwhere(dataStart==missEnd[k]+1)
        if len(datk) > 0:
            datk = int(datk)
            if dataEnd[datk]-dataStart[datk]+1 < edgesamples:
                missEnd = np.delete(missEnd, k)
                missStart = np.delete(missStart, k)
                
                # don't advance k so we check this one again and grow it further if
                # needed
                continue

        # nothing left to do, continue to next
        k = k+1
    
    # mark intervals that are too long to be deleted (only delete later so that
    # below checks can use all missing on and offsets)
    missDur = missEnd-missStart+1
    qRemove = missDur>windowsamples
    
    # for each candidate, check if have enough valid data at edges to execute
    # interpolation and check displacement during missing wasn't too large.
    # Mark for later removal as multiple missing close together may otherwise
    # be wrongly allowed
    for p in range(len(missStart)):
        # check enough valid data at edges
        # missing too close to beginning of data
        # previous missing too close
        # missing too close to end of data
        # next missing too close
        if missStart[p]<edgesamples+1 or \
            (p>0 and missEnd[p-1] > missStart[p]-edgesamples-1) or \
            missEnd[p]>len(xpos)-edgesamples or \
            (p<len(missStart)-1 and missStart[p+1] < missEnd[p]+edgesamples+1):
            qRemove[p] = True
            continue
        
        # check displacement, per missing interval
        # we want to check per bit of missing, even if multiple bits got merged
        # this as single data points can still anchor where the interpolation
        # goes and we thus need to check distance per bit, not over the whole
        # merged bit
        idx = np.arange(missStart[p],missEnd[p]+1, dtype = int)
        on,off = bool2bounds(np.isnan(xpos[idx]))
        for q in range(len(on)): 
            lesamps = np.array(on[q]-np.arange(edgesamples)+missStart[p]-1, dtype=int)
            resamps = np.array(off[q]+np.arange(edgesamples)+missStart[p]-1, dtype=int)
            displacement = np.hypot(np.nanmedian(xpos[resamps])-np.nanmedian(xpos[lesamps]), np.nanmedian(ypos[resamps])-np.nanmedian(ypos[lesamps]))
            if displacement > maxdisp:
                qRemove[p] = True
                break

        if qRemove[p]:
            continue
    
    # Remove the missing clusters which cannot be interpolated
    qRemove = np.where(qRemove)[0]
    missStart = np.delete(missStart, qRemove)
    missEnd = np.delete(missEnd, qRemove)

    # update missing vector
    notAllowed = missing.copy()
    for s, e in zip(missStart, missEnd):
        notAllowed[range(s,e+1)] = False
    
    return missStart,missEnd

def windowedInterpolate(xpos, ypos, missing, missStart, missEnd, edgesamples, dev=False):
    """
    Interpolates the missing data, and removes areas which are not allowed 
    to be interpolated
    
    Parameters
    ----------
    xpos : np.array
        X gaze positions
    ypos : type
        Y gaze positions
    missing : np.array
        Boolean vector containing indicating missing values
    notAllowed : np.array
        Boolean vector containing samples to be excluded after interpolation

    Returns
    -------
    xi : np.array
        Interpolated X gaze position
    yi : np.array
        Interpolated Y gaze position
        
    Examples
    --------
    >>>
    """
    missingn = copy.deepcopy(missing)
    
    # Do the interpolating
    for p in range(len(missStart)):
        # make vector of all samples in this window
        outWin = np.arange(missStart[p],missEnd[p]+1)
    
        # get edge samples: where no missing data was observed
        # also get samples in window where data was observed
        outWinNotMissing = np.invert(missingn[outWin])
        validsamps  = np.concatenate((outWin[0]+np.arange(-edgesamples,0), outWin[outWinNotMissing], outWin[-1]+np.arange(1,edgesamples+1)))
        
        # get valid values: where no missing data was observed
        validx      = xpos[validsamps];
        validy      = ypos[validsamps];
        
        # do Steffen interpolation, update xpos, ypos
        xpos[outWin]= steffenInterp(validsamps,validx,outWin)
        ypos[outWin]= steffenInterp(validsamps,validy,outWin)
        
        # update missing: hole is now plugged
        missingn[outWin] = False
    
    # plot interpolated data before (TODO, we didn't update this...)
    if dev:
        f, [ax1, ax2] = plt.subplots(2,1)
        ax1.plot(newX,xi, 'k-')
        ax1.scatter(newX[notMissing], xpos[notMissing], s = 2, color = 'r')
        ax1.scatter(newX[missing], xi[missing], s = 25, color = 'b')
        ax2.plot(newX,yi, 'k-')
        ax2.scatter(newX[notMissing], ypos[notMissing], s = 2, color = 'r')
        ax2.scatter(newX[missing], yi[missing], s = 25, color = 'b')

    return xpos, ypos, missingn

# =============================================================================
# interpolator
# =============================================================================
def steffenInterp(x, y, xi):
    # STEFFEN 1-D Steffen interpolation
    #    steffenInterp[X,Y,XI] interpolates to find YI, the values of the
    #    underlying function Y at the points in the array XI, using
    #    the method of Steffen.  X and Y must be vectors of length N.
    #
    #    Steffen's method is based on a third-order polynomial.  The
    #    slope at each grid point is calculated in a way to guarantee
    #    a monotonic behavior of the interpolating function.  The 
    #    curve is smooth up to the first derivative.

    # Joe Henning - Summer 2014
    # edited DC Niehorster - Summer 2015

    # M. Steffen
    # A Simple Method for Monotonic Interpolation in One Dimension
    # Astron. Astrophys. 239, 443-450 [1990]
    n = len(x)

    # calculate slopes
    yp = np.zeros(n)

    # first point
    h1 = x[1] - x[0]
    h2 = x[2] - x[1]
    s1 = (y[1] - y[0])/h1
    s2 = (y[2] - y[1])/h2
    p1 = s1*(1 + h1/(h1 + h2)) - s2*h1/(h1 + h2)
    if p1*s1 <= 0:
        yp[0] = 0
    elif np.abs(p1) > 2*np.abs(s1):
        yp[0] = 2*s1
    else:
        yp[0] = p1


    # inner points
    for i in range(1,n-1):
        hi = x[i+1] - x[i]
        him1 = x[i] - x[i-1]
        si = (y[i+1] - y[i])/hi
        sim1 = (y[i] - y[i-1])/him1
        pi = (sim1*hi + si*him1)/(him1 + hi)
       
        if sim1*si <= 0:
            yp[i] = 0
        elif (np.abs(pi) > 2*np.abs(sim1)) or (np.abs(pi) > 2*np.abs(si)):
            a = np.sign(sim1)
            yp[i] = 2*a*np.min([np.abs(sim1),np.abs(si)])
        else:
            yp[i] = pi
        


    # last point
    hnm1 = x[n-1] - x[n-2]
    hnm2 = x[n-2] - x[n-3]
    snm1 = (y[n-1] - y[n-2])/hnm1
    snm2 = (y[n-2] - y[n-3])/hnm2
    pn = snm1*(1 + hnm1/(hnm1 + hnm2)) - snm2*hnm1/(hnm1 + hnm2)
    if pn*snm1 <= 0:
         yp[n-1] = 0
    elif np.abs(pn) > 2*np.abs(snm1):
         yp[n-1] = 2*snm1
    else:
         yp[n-1] = pn


    yi = np.zeros(xi.size)
    for i in range(len(xi)):
        # Find the right place in the table by means of a bisection.
        # do this instead of search with find as the below now somehow gets
        # better optimized by matlab's JIT [runs twice as fast].
        klo = 1
        khi = n
        while khi-klo > 1:
            k = int(np.fix((khi+klo)/2.0))
            if x[k] > xi[i]:
                khi = k
            else:
                klo = k
            
        
        
        # check if requested output is in input, so we can just copy
        if xi[i]==x[klo]:
             yi[i] = y[klo]
             continue
        elif xi[i]==x[khi]:
             yi[i] = y[khi]
             continue
        
        
        h = x[khi] - x[klo]
        s = (y[khi] - y[klo])/h

        a = (yp[klo] + yp[khi] - 2*s)/h/h
        b = (3*s - 2*yp[klo] - yp[khi])/h
        c = yp[klo]
        d = y[klo]

        t = xi[i] - x[klo]
        # Use Horner's scheme for efficient evaluation of polynomials
        # y = a*t*t*t + b*t*t + c*t + d
        yi[i] = d + t*(c + t*(b + t*a))

    return yi



# =============================================================================
# Clustering functions
# =============================================================================
def twoClusterWeighting(xpos, ypos, missing, downsamples, downsampFilter, chebyOrder, windowtime, steptime, freq, maxerrors, dev=False):
    """
    Description
    
    Parameters
    ----------
    xpos : type
        Description
    ypos : type
        Description
    missing : type
        Description
    downsamples : type
        Description
    downsampFilter : type
        Description
    chebyOrder : type
        Description
    windowtime : type
        Description
    steptime : type
        Description
    freq : type
        Description
    maxerrors : type
        Description


    Returns
    -------
    finalweights : np.array
        Vector of 2-means clustering weights (one weight for each sample), the higher, the more likely a saccade happened        
        
    Examples
    --------
    >>> 
    """   
    # calculate number of samples of the moving window
    nrsamples = int(windowtime/(1./freq))
    stepsize  = np.max([1,int(steptime/(1./freq))])
    
    # create empty weights vector
    totalweights = np.zeros(len(xpos))
    totalweights[missing] = np.nan
    nrtests = np.zeros(len(xpos))
    
    # stopped is always zero, unless maxiterations is exceeded. this
    # indicates that file could not be analysed after trying for x iterations
    stopped = False
    counterrors = 0
    
    # Number of downsamples
    nd = len(downsamples)
    
    # Downsample 
    if downsampFilter:
        # filter signal. Follow the lead of decimate(), which first runs a
        # Chebychev filter as specified below
        rp = .05 # passband ripple in dB
        b = [[] for i in range(nd)]
        a = [[] for i in range(nd)]
        for p in range(nd):
            b[p],a[p] = scipy.signal.cheby1(chebyOrder, rp, .8/downsamples[p]) 
    
    
    # idx for downsamples
    idxs = []
    for i in range(nd):
        idxs.append(np.arange(nrsamples,0,-downsamples[i],dtype=int)[::-1] - 1)
        
    # see where are missing in this data, for better running over the data
    # below.
    on,off = bool2bounds(missing)
    if on.size > 0:
        #  merge intervals smaller than nrsamples long 
        merge = np.argwhere((on[1:] - off[:-1])-1 < nrsamples).flatten()
        for p in merge[::-1]:
            off[p] = off[p+1]
            off = np.delete(off, p+1)
            on = np.delete(on, p+1)

        # check if intervals at data start and end are large enough
        if on[0]<nrsamples+1:
            # not enough data point before first missing, so exclude them all
            on[0]=0

        if off[-1]>(len(xpos)-nrsamples):
            # not enough data points after last missing, so exclude them all
            off[-1]=len(xpos)-1

        # start at first non-missing sample if trial starts with missing (or
        # excluded because too short) data
        if on[0]==0:
            i=off[0]+1 # start at first non-missing
        else:
            i=0
    else:
        i=0

    eind = i+nrsamples
    while eind<=(len(xpos)):
        # check if max errors is crossed
        if counterrors > maxerrors:
            print('Too many empty clusters encountered, aborting file. \n')
            stopped = True
            finalweights = np.nan
            return finalweights, stopped
        
        # select data portion of nrsamples
        idx = range(i,eind)
        ll_d = [[] for p in range(nd+1)]
        IDL_d = [[] for p in range(nd+1)]
        ll_d[0] = np.vstack([xpos[idx], ypos[idx]])
                
        # Filter the bit of data we're about to downsample. Then we simply need
        # to select each nth sample where n is the integer factor by which
        # number of samples is reduced. select samples such that they are till
        # end of window
        for p in range(nd):
            if downsampFilter:
                ll_d[p+1] = scipy.signal.filtfilt(b[p],a[p],ll_d[0])
                ll_d[p+1] = ll_d[p+1][:,idxs[p]]
            else:
                ll_d[p+1] = ll_d[0][:,idxs[p]]
        
        # do 2-means clustering        
        for p in range(nd+1):
            IDL_d[p] = kmeans2(ll_d[p].T,2, 10, minit='points')            
        
            # If an empty cluster error is encountered, try again next
            # iteration. This can occur particularly in long
            # fixations, as the number of clusters there should be 1,
            # but we try to fit 2 to detect a saccade (i.e. 2 fixations)
            
            # visual explanation of empty cluster errors:
            # http://www.ceng.metu.edu.tr/~tcan/ceng465_s1011/Schedule/KMeansEmpty.html
            if len(np.unique(IDL_d[p][-1])) != 2:
                print('\t\tEmpty cluster error encountered (n={}/100). Trying again on next iteration.'.format(counterrors))
                counterrors += 1
                continue
        
        # detect switches and weight of switch (= 1/number of switches in
        # portion)
        switches = [[] for p in range(nd+1)]
        switchesw = [[] for p in range(nd+1)]
        for p in range(nd+1):
            switches[p] = np.abs(np.diff(IDL_d[p][1]))
            switchesw[p]  = 1./np.sum(switches[p])
           
        # get nearest samples of switch and add weight
        weighted = np.hstack([switches[0]*switchesw[0],0])
        for p in range(nd):
            j = np.array((np.argwhere(switches[p+1]).flatten()+1)*downsamples[p],dtype=int)-1
            for o in range(-1,int(downsamples[p])-1):
                weighted[j+o] = weighted[j+o] + switchesw[p+1]
        
        # add to totalweights
        totalweights[idx] = totalweights[idx] + weighted
        # record how many times each sample was tested
        nrtests[idx] = nrtests[idx] + 1
        
        # update i
        i += stepsize
        eind += stepsize
        missingOn = np.logical_and(on>=i, on<=eind)
        missingOff = np.logical_and(off>=i, off<=eind)
        qWhichMiss = np.logical_or(missingOn, missingOff) 
        if np.sum(qWhichMiss) > 0:
            # we have some missing in this window. we don't process windows
            # with missing. Move back if we just skipped some samples, or else
            # skip whole missing and place start of window and first next
            # non-missing.
            if on[qWhichMiss][0] == (eind-stepsize):
                # continue at first non-missing
                i = off[qWhichMiss][0]+1
            else:
                # we skipped some points, move window back so that we analyze
                # up to first next missing point
                i = on[qWhichMiss][0]-nrsamples
            eind = i+nrsamples
            
        if eind>len(xpos) and eind-stepsize<len(xpos):
            # we just exceeded data bound, but previous eind was before end of
            # data: we have some unprocessed samples. retreat just enough so we
            # process those end samples once
            d = eind-len(xpos)
            eind = eind-d
            i = i-d
            

    # create final weights
    finalweights = totalweights/nrtests
    
    return finalweights, stopped

# =============================================================================
# Fixation detection functions
# =============================================================================
def getFixations(finalweights, timestamp, xpos, ypos, missing, par):
    """
    Description
    
    Parameters
    ----------
    finalweights : type
        2-means clustering weighting
    timestamp : np.array
        Timestamp from Eyetracker (should be in ms!)
    xpos : np.array
        Horizontal coordinates from Eyetracker
    ypos : np.array
        Vertical coordinates from Eyetracker
    missing : np.array
        Vector containing the booleans for mising values
    par : Dictionary containing the following keys and values
        cutoffstd : float
            Number of std above mean clustering-weight to use as fixation cutoff
        onoffsetThresh : float
            Threshold (x*MAD of fixation) for walking forward/back for saccade off- and onsets
        maxMergeDist : float
            Maximum Euclidean distance in pixels between fixations for merging
        maxMergeTime : float
            Maximum time in ms between fixations for merging
        minFixDur : Float
            Minimum duration allowed for fiation


    Returns
    -------
    fix : Dictionary containing the following keys and values
        cutoff : float
            Cutoff used for fixation detection
        start : np.array
            Vector with fixation start indices
        end : np.array
            Vector with fixation end indices
        startT : np.array
            Vector with fixation start times
        endT : np.array
            Vector with fixation end times
        dur : type
            Vector with fixation durations
        xpos : np.array
            Vector with fixation median horizontal position (one value for each fixation in trial)
        ypos : np.array
            Vector with fixation median vertical position (one value for each fixation in trial)
        flankdataloss : bool
            Boolean with 1 for when fixation is flanked by data loss, 0 if not flanked by data loss
        fracinterped : float
            Fraction of data loss/interpolated data
    
    Examples
    --------
    >>> fix = getFixations(finalweights,data['time'],xpos,ypos,missing,par)
    >>> fix
        {'cutoff': 0.1355980099309374,
         'dur': array([366.599, 773.2  , 239.964, 236.608, 299.877, 126.637]),
         'end': array([111, 349, 433, 508, 600, 643]),
         'endT': array([ 369.919, 1163.169, 1443.106, 1693.062, 1999.738, 2142.977]),
         'flankdataloss': array([1., 0., 0., 0., 0., 0.]),
         'fracinterped': array([0.06363636, 0.        , 0.        , 0.        , 0.        ,
                0.        ]),
         'start': array([  2, 118, 362, 438, 511, 606]),
         'startT': array([   6.685,  393.325, 1206.498, 1459.79 , 1703.116, 2019.669]),
         'xpos': array([ 945.936,  781.056, 1349.184, 1243.92 , 1290.048, 1522.176]),
         'ypos': array([486.216, 404.838, 416.664, 373.005, 383.562, 311.904])}
    """    
    ### Extract the required parameters 
    cutoffstd = par['cutoffstd']
    onoffsetThresh = par['onoffsetThresh']
    maxMergeDist = par['maxMergeDist']
    maxMergeTime = par['maxMergeTime']
    minFixDur = par['minFixDur']
        
    ### first determine cutoff for finalweights
    cutoff = np.nanmean(finalweights) + cutoffstd*np.nanstd(finalweights)

    ### get boolean of fixations
    fixbool = finalweights < cutoff
    
    ### get indices of where fixations start and end
    fixstart, fixend = bool2bounds(fixbool)
    
    ### for each fixation start, walk forward until recorded position is below 
    # a threshold of lambda*MAD away from median fixation position.
    # same for each fixation end, but walk backward
    for p in range(len(fixstart)):
        xFix = xpos[fixstart[p]:fixend[p]]
        yFix = ypos[fixstart[p]:fixend[p]]
        xmedThis = np.nanmedian(xFix)
        ymedThis = np.nanmedian(yFix)
        
        # MAD = median(abs(x_i-median({x}))). For the 2D version, I'm using
        # median 2D distance of a point from the median fixation position. Not
        # exactly MAD, but makes more sense to me for 2D than city block,
        # especially given that we use 2D distance in our walk here
        MAD = np.nanmedian(np.hypot(xFix-xmedThis, yFix-ymedThis))
        thresh = MAD*onoffsetThresh

        # walk until distance less than threshold away from median fixation
        # position. No walking occurs when we're already below threshold.
        i = fixstart[p]
        if i>0:  # don't walk when fixation starting at start of data 
            while np.hypot(xpos[i]-xmedThis,ypos[i]-ymedThis)>thresh:
                i = i+1
            fixstart[p] = i
            
        # and now fixation end.
        i = fixend[p]
        if i<len(xpos): # don't walk when fixation ending at end of data
            while np.hypot(xpos[i]-xmedThis,ypos[i]-ymedThis)>thresh:
                i = i-1;
            fixend[p] = i

    ### get start time, end time,
    starttime = timestamp[fixstart]
    endtime = timestamp[fixend]
    
    ### loop over all fixation candidates in trial, see if should be merged
    for p in range(1,len(starttime))[::-1]:
        # get median coordinates of fixation
        xmedThis = np.median(xpos[fixstart[p]:fixend[p]])
        ymedThis = np.median(ypos[fixstart[p]:fixend[p]])
        xmedPrev = np.median(xpos[fixstart[p-1]:fixend[p-1]]);
        ymedPrev = np.median(ypos[fixstart[p-1]:fixend[p-1]]);
        
        # check if fixations close enough in time and space and thus qualify
        # for merging
        # The interval between the two fixations is calculated correctly (see
        # notes about fixation duration below), i checked this carefully. (Both
        # start and end of the interval are shifted by one sample in time, but
        # assuming practicalyl constant sample interval, thats not an issue.)
        if starttime[p]- endtime[p-1] < maxMergeTime and \
            np.hypot(xmedThis-xmedPrev,ymedThis-ymedPrev) < maxMergeDist:
            # merge
            fixend[p-1] = fixend[p];
            endtime[p-1]= endtime[p];
            # delete merged fixation
            fixstart = np.delete(fixstart, p)
            fixend = np.delete(fixend, p)
            starttime = np.delete(starttime, p)
            endtime = np.delete(endtime, p)
            
    ### beginning and end of fixation must be real data, not interpolated.
    # If interpolated, those bit(s) at the edge(s) are excluded from the
    # fixation. First throw out fixations that are all missing/interpolated
    for p in range(len(starttime))[::-1]:
        miss = missing[fixstart[p]:fixend[p]]
        if np.sum(miss) == len(miss):
            fixstart = np.delete(fixstart, p)
            fixend = np.delete(fixend, p)
            starttime = np.delete(starttime, p)
            endtime = np.delete(endtime, p)
    
    # then check edges and shrink if needed
    for p in range(len(starttime)):
        if missing[fixstart[p]]:
            fixstart[p] = fixstart[p] + np.argmax(np.invert(missing[fixstart[p]:fixend[p]]))
            starttime[p]= timestamp[fixstart[p]]
        if missing[fixend[p]]:
            fixend[p] = fixend[p] - (np.argmax(np.invert(missing[fixstart[p]:fixend[p]][::-1]))+1)
            endtime[p] = timestamp[fixend[p]]
    
    ### calculate fixation duration
    # if you calculate fixation duration by means of time of last sample during
    # fixation minus time of first sample during fixation (our fixation markers
    # are inclusive), then you always underestimate fixation duration by one
    # sample because you're in practice counting to the beginning of the
    # sample, not the end of it. To solve this, as end time we need to take the
    # timestamp of the sample that is one past the last sample of the fixation.
    # so, first calculate fixation duration by simple timestamp subtraction.
    fixdur = endtime-starttime
    
    # then determine what duration of this last sample was
    nextSamp = np.min(np.vstack([fixend+1,np.zeros(len(fixend),dtype=int)+len(timestamp)-1]),axis=0) # make sure we don't run off the end of the data
    extratime = timestamp[nextSamp]-timestamp[fixend] 
    
    # if last fixation ends at end of data, we need to determine how long that
    # sample is and add that to the end time. Here we simply guess it as the
    # duration of previous sample
    if not len(fixend)==0 and fixend[-1]==len(timestamp): # first check if there are fixations in the first place, or we'll index into non-existing data
        extratime[-1] = np.diff(timestamp[-3:-1])
    
    # now add the duration of the end sample to fixation durations, so we have
    # correct fixation durations
    fixdur = fixdur+extratime

    ### check if any fixations are too short
    qTooShort = np.argwhere(fixdur<minFixDur)
    if len(qTooShort) > 0:
        fixstart = np.delete(fixstart, qTooShort)
        fixend = np.delete(fixend, qTooShort)
        starttime = np.delete(starttime, qTooShort)
        endtime = np.delete(endtime, qTooShort)
        fixdur = np.delete(fixdur, qTooShort)
        
    ### process fixations, get other info about them
    xmedian = np.zeros(fixstart.shape) # vector for median
    ymedian = np.zeros(fixstart.shape)  # vector for median
    flankdataloss = np.zeros(fixstart.shape) # vector for whether fixation is flanked by data loss
    fracinterped = np.zeros(fixstart.shape) # vector for fraction interpolated
    for a in range(len(fixstart)):
        idxs = range(fixstart[a],fixend[a])
        # get data during fixation
        xposf = xpos[idxs]
        yposf = ypos[idxs]
        # for all calculations below we'll only use data that is not
        # interpolated, so only real data
        qMiss = missing[idxs]
        
        # get median coordinates of fixation
        xmedian[a] = np.median(xposf[np.invert(qMiss)])
        ymedian[a] = np.median(yposf[np.invert(qMiss)])
        
        # determine whether fixation is flanked by period of data loss
        flankdataloss[a] = (fixstart[a]>0 and missing[fixstart[a]-1]) or (fixend[a]<len(xpos)-1 and missing[fixend[a]+1])
        
        # fraction of data loss during fixation that has been (does not count
        # data that is still lost)
        fracinterped[a]  = np.sum(np.invert(np.isnan(xposf[qMiss])))/(fixend[a]-fixstart[a]+1)

    # store all the results in a dictionary
    fix = {}
    fix['cutoff'] = cutoff
    fix['start'] = fixstart
    fix['end'] = fixend
    fix['startT'] = starttime
    fix['endT'] = endtime
    fix['dur'] = fixdur
    fix['xpos'] = xmedian
    fix['ypos'] = ymedian
    fix['flankdataloss'] = flankdataloss
    fix['fracinterped'] = fracinterped
    return fix

def getFixStats(xpos, ypos, missing, pixperdeg = None, fix = {}):
    """
    Description
    
    Parameters
    ----------
    xpos : np.array
        X gaze positions
    ypos : np.array
        Y gaze positions
    missing : np.array - Boolean
        Vector containing the booleans for mising values (originally, before interpolation!) 
    pixperdeg : float
        Number of pixels per visual degree
    fix : Dictionary containing the following keys and values
        fstart : np.array
            fixation start indices
        fend : np.array
            fixation end indices


    Returns
    -------
    fix : the fix input dictionary with the following added keys and values 
        RMSxy : float
            RMS of fixation (precision)
        BCEA : float 
            BCEA of fixation (precision)
        rangeX : float
            max(xpos) - min(xpos) of fixation
        rangeY : float
            max(ypos) - min(ypos) of fixation
        
    Examples
    --------
    >>> fix = getFixStats(xpos,ypos,missing,fix,pixperdeg)
    >>> fix
        {'BCEA': array([0.23148877, 0.23681681, 0.24498942, 0.1571361 , 0.20109245,
            0.23703843]),
     'RMSxy': array([0.2979522 , 0.23306149, 0.27712236, 0.26264146, 0.28913117,
            0.23147076]),
     'cutoff': 0.1355980099309374,
     'dur': array([366.599, 773.2  , 239.964, 236.608, 299.877, 126.637]),
     'end': array([111, 349, 433, 508, 600, 643]),
     'endT': array([ 369.919, 1163.169, 1443.106, 1693.062, 1999.738, 2142.977]),
     'fixRangeX': array([0.41066299, 0.99860672, 0.66199772, 0.49593727, 0.64628929,
            0.81010568]),
     'fixRangeY': array([1.58921528, 1.03885955, 1.10576059, 0.94040142, 1.21936613,
            0.91263117]),
     'flankdataloss': array([1., 0., 0., 0., 0., 0.]),
     'fracinterped': array([0.06363636, 0.        , 0.        , 0.        , 0.        ,
            0.        ]),
     'start': array([  2, 118, 362, 438, 511, 606]),
     'startT': array([   6.685,  393.325, 1206.498, 1459.79 , 1703.116, 2019.669]),
     'xpos': array([ 945.936,  781.056, 1349.184, 1243.92 , 1290.048, 1522.176]),
     'ypos': array([486.216, 404.838, 416.664, 373.005, 383.562, 311.904])}
    """
    ### Extract the required parameters 
    fstart = fix['start']
    fend = fix['end']

    # vectors for precision measures
    RMSxy = np.zeros(fstart.shape)
    BCEA  = np.zeros(fstart.shape)
    rangeX = np.zeros(fstart.shape)
    rangeY = np.zeros(fstart.shape)

    for a in range(len(fstart)):
        idxs = range(fstart[a],fend[a])
        # get data during fixation
        xposf = xpos[idxs]
        yposf = ypos[idxs]
        # for all calculations below we'll only use data that is not
        # interpolated, so only real data
        qMiss = missing[idxs]
        
        ### calculate RMS
        # since its done with diff, don't just exclude missing and treat
        # resulting as one continuous vector. replace missing with nan first,
        # use left-over values
        # Difference x position
        xdif = xposf.copy()
        xdif[qMiss] = np.nan
        xdif = np.diff(xdif)**2; 
        xdif = xdif[np.invert(np.isnan(xdif))]
        # Difference y position
        ydif = yposf.copy()
        ydif[qMiss] = np.nan
        ydif = np.diff(ydif)**2; 
        ydif = ydif[np.invert(np.isnan(ydif))]
        # Distance and RMS measure
        c = xdif + ydif # 2D sample-to-sample displacement value in pixels
        RMSxy[a] = np.sqrt(np.mean(c))
        if pixperdeg:
            RMSxy[a] = RMSxy[a]/pixperdeg # value in degrees visual angle
        
        ### calculate BCEA (Crossland and Rubin 2002 Optometry and Vision Science)
        stdx = np.std(xposf[np.invert(qMiss)])
        stdy = np.std(yposf[np.invert(qMiss)])
        if pixperdeg:
            # value in degrees visual angle
            stdx = stdx/pixperdeg
            stdy = stdy/pixperdeg
    
        if len(yposf[np.invert(qMiss)])<2:
            BCEA[a] = np.nan
        else:
            xx = np.corrcoef(xposf[np.invert(qMiss)],yposf[np.invert(qMiss)])
            rho = xx[0,1]
            P = 0.68 # cumulative probability of area under the multivariate normal
            k = np.log(1./(1-P))
            BCEA[a] = 2*k*np.pi*stdx*stdy*np.sqrt(1-rho**2);
        
        ### calculate max-min of fixation
        if np.sum(qMiss) == len(qMiss):
            rangeX[a] = np.nan
            rangeY[a] = np.nan
        else:
            rangeX[a] = (np.max(xposf[np.invert(qMiss)]) - np.min(xposf[np.invert(qMiss)]))
            rangeY[a] = (np.max(yposf[np.invert(qMiss)]) - np.min(yposf[np.invert(qMiss)]))

        if pixperdeg:
            # value in degrees visual angle
            rangeX[a] = rangeX[a]/pixperdeg;
            rangeY[a] = rangeY[a]/pixperdeg;

    # Add results to fixation dictionary
    fix['RMSxy'] = RMSxy
    fix['BCEA'] = BCEA
    fix['fixRangeX'] = rangeX
    fix['fixRangeY'] = rangeY
    
    return fix

# =============================================================================
# =============================================================================
# # The actual I2MC pipeline function
# =============================================================================
# =============================================================================
def I2MC(gazeData, options = {}):
    '''
    RUNS I2MC 
    
    
    Parameters
    ----------
    data : dict
        Dictionary containing all the data
    opt : dict
        Dictionary containing all the options 
    
    Returns
    -------
    fix : dict
        Dictionary containing all the fixation information
    
    Example
    --------
    >>> 
    '''
    # set defaults
    data = copy.deepcopy(gazeData)
    opt = options.copy()
    par = {}
    
    # Check required parameters 
    checkFun('xres', opt, 'horizontal screen resolution')
    checkFun('yres', opt, 'vertical screen resolution')
    checkFun('freq', opt, 'tracker sampling rate')
    checkFun('missingx', opt, 'value indicating data loss for horizontal position')
    checkFun('missingy', opt, 'value indicating data loss for vertical position')
    
    # required parameters:
    par['xres'] = opt.pop('xres', 1920.)
    par['yres'] = opt.pop('yres', 1080.)
    par['freq'] = opt.pop('freq', 300.)
    par['missingx'] = opt.pop('missingx', -1920)
    par['missingy'] = opt.pop('missingy', -1080)
    par['scrSz'] = opt.pop('scrSz', [50.9174, 28.6411] ) # screen size (e.g. in cm). Optional, specify if want fixation statistics in deg
    par['disttoscreen'] = opt.pop('disttoscreen', 65.0) # screen distance (in same unit as size). Optional, specify if want fixation statistics in deg
    
    #parameters with defaults:
    # CUBIC SPLINE INTERPOLATION
    par['windowtimeInterp'] = opt.pop('windowtimeInterp', .1) # max duration (s) of missing values for interpolation to occur
    par['edgeSampInterp'] = opt.pop('edgeSampInterp', 2.) # amount of data (number of samples) at edges needed for interpolation
    par['maxdisp'] = opt.pop('maxdisp',par['xres']*0.2*np.sqrt(2)) # maximum displacement during missing for interpolation to be possible
    
    # K-MEANS CLUSTERING
    par['windowtime'] = opt.pop('windowtime', .2) # time window (s) over which to calculate 2-means clustering (choose value so that max. 1 saccade can occur)
    par['steptime'] = opt.pop('steptime', .02) # time window shift (s) for each iteration. Use zero for sample by sample processing
    par['downsamples'] = opt.pop('downsamples', [2, 5, 10]) # downsample levels (can be empty)
    par['downsampFilter'] = opt.pop('downsampFilter', 1.) # use chebychev filter when downsampling? 1: yes, 0: no. requires signal processing toolbox. is what matlab's downsampling functions do, but could cause trouble (ringing) with the hard edges in eye-movement data
    par['chebyOrder'] = opt.pop('chebyOrder', 8.) # order of cheby1 Chebyshev downsampling filter, default is normally ok, as long as there are 25 or more samples in the window (you may have less if your data is of low sampling rate or your window is small
    par['maxerrors'] = opt.pop('maxerrors', 100.) # maximum number of errors allowed in k-means clustering procedure before proceeding to next file
    # FIXATION DETERMINATION
    par['cutoffstd'] = opt.pop('cutoffstd', 2.) # number of standard deviations above mean k-means weights will be used as fixation cutoff
    par['onoffsetThresh']  = opt.pop('onoffsetThresh', 3.) # number of MAD away from median fixation duration. Will be used to walk forward at fixation starts and backward at fixation ends to refine their placement and stop algorithm from eating into saccades
    par['maxMergeDist'] = opt.pop('maxMergeDist', 30.) # maximum Euclidean distance in pixels between fixations for merging
    par['maxMergeTime'] = opt.pop('maxMergeTime', 30.) # maximum time in ms between fixations for merging
    par['minFixDur'] = opt.pop('minFixDur', 40.) # minimum fixation duration (ms) after merging, fixations with shorter duration are removed from output
      
    # Development parameters (plotting intermediate steps), Change these to False when not developing
    par['dev_interpolation'] = opt.pop('dev_interpolation', False)
    par['dev_cluster'] = opt.pop('dev_cluster', False)
    par['skip_inputhandeling'] = opt.pop('skip_inputhandeling', False)
    
    # =============================================================================
    # # Input handeling and checking
    # =============================================================================
    ## loop over input
    if not par['skip_inputhandeling']:
        for key, value in par.items():
            if key in ['xres','yres','freq','missingx','missingy','disttoscreen','windowtimeInterp','maxdisp','windowtime','steptime','cutoffstd','onoffsetThresh','maxMergeDist','maxMergeTime','minFixDur']:
                checkNumeric(key,value)
                checkScalar(key,value)
            elif key in ['downsampFilter','chebyOrder','maxerrors','edgeSampInterp']:
                checkInt(key,value)
                checkScalar(key,value)
            elif key == 'scrSz':
                checkNumeric(key,value)
                checkNumel2(key,value)
            elif key == 'downsamples':
                checkInt(key,value)
            else:
                if type(key) != str:
                    assert False, 'Key "{}" not recognized'.format(key)
        
    # check filter
    if par['downsampFilter']:
        nSampRequired = np.max([1,3*par['chebyOrder']])+1  # nSampRequired = max(1,3*(nfilt-1))+1, where nfilt = chebyOrder+1
        nSampInWin = round(par['windowtime']/(1./par['freq']))
        assert nSampInWin>=nSampRequired,'I2MCfunc: Filter parameters requested with the setting ''chebyOrder'' will not work for the sampling frequency of your data. Please lower ''chebyOrder'', or set the setting ''downsampFilter'' to 0'
   
    np.sum(par['freq']%np.array(par['downsamples'])) !=0
    assert np.sum(par['freq']%np.array(par['downsamples'])) ==0,'I2MCfunc: Some of your downsample levels are not divisors of your sampling frequency. Change the option "downsamples"'
    
    # setup visual angle conversion
    pixperdeg = []
    if par['scrSz'] and par['disttoscreen']:
        pixperdeg = angleToPixels(1, par['disttoscreen'], par['scrSz'][0], [par['xres'], par['yres']])

    # =============================================================================
    # Determine missing values and determine X and Y gaze pos
    # =============================================================================
    # deal with monocular data, or create average over two eyes
    if 'L_X' in data.keys() and 'R_X' not in data.keys():
        xpos = data['L_X']
        ypos = data['L_Y']
        # Check for missing values
        missingX = np.logical_or(np.isnan(xpos), xpos == par['missingx'])
        missingY = np.logical_or(np.isnan(ypos) , ypos == par['missingy'])
        missing = np.logical_or(missingX, missingY)
        data['left_missing'] = missing
        q2Eyes = False
        
    elif 'R_X' in data.keys() and 'L_X' not in data.keys():
        xpos = data['R_X']
        ypos = data['R_Y']
        # Check for missing values
        missingX = np.logical_or(np.isnan(xpos), xpos == par['missingx'])
        missingY = np.logical_or(np.isnan(ypos) , ypos == par['missingy'])
        missing = np.logical_or(missingX, missingY)
        data['right_missing'] = missing
        q2Eyes = False
        
    elif 'average_X' in data.keys():
        xpos = data['average_X']
        ypos = data['average_Y']
        missingX = np.logical_or(np.isnan(xpos), xpos == par['missingx'])
        missingY = np.logical_or(np.isnan(ypos) , ypos == par['missingy'])
        missing = np.logical_or(missingX, missingY)
        data['average_missing'] = missing
        q2Eyes = 'R_X' in data.keys() and 'L_X' in data.keys()
        if q2Eyes:
            # we have left and right and average already provided, but we need
            # to get missing in the individual eye signals
            llmiss, rrmiss, bothmiss = getMissing(data['L_X'], data['R_X'], par['missingx'], data['L_Y'], data['R_Y'], par['missingy'])
            data['left_missing']  = llmiss
            data['right_missing'] = rrmiss
        
    else: # we have left and right, average them
        data['average_X'], data['average_Y'], missing, llmiss, rrmiss = averageEyes(data['L_X'], data['R_X'], par['missingx'], data['L_Y'], data['R_Y'], par['missingy'])
        xpos = data['average_X']
        ypos = data['average_Y']
        data['average_missing'] = missing
        data['left_missing']  = llmiss
        data['right_missing'] = rrmiss
        q2Eyes = True
               
    # =============================================================================
    # INTERPOLATION
    # =============================================================================
    # get interpolation windows for average and individual eye signals
    print('\tSearching for valid interpolation windows')
    missStart,missEnd = findInterpWins(xpos, ypos, missing, par['windowtimeInterp'], par['edgeSampInterp'], par['freq'], par['maxdisp'])
    if q2Eyes:
        llmissStart,llmissEnd = findInterpWins(data['L_X'], data['L_Y'], llmiss, par['windowtimeInterp'], par['edgeSampInterp'], par['freq'], par['maxdisp']);
        rrmissStart,rrmissEnd = findInterpWins(data['R_X'], data['R_Y'], rrmiss, par['windowtimeInterp'], par['edgeSampInterp'], par['freq'], par['maxdisp']);
    
    # Use Steffen interpolation and replace values
    print('\tReplace interpolation windows with Steffen interpolation')
    xpos, ypos, missingn = windowedInterpolate(xpos, ypos, missing, missStart, missEnd, par['edgeSampInterp'], par['dev_interpolation'])
    if q2Eyes:
        llx, lly,llmissn = windowedInterpolate(data['L_X'], data['L_Y'], data['left_missing'], llmissStart, llmissEnd, par['edgeSampInterp'], par['dev_interpolation'])
        rrx, rry,rrmissn = windowedInterpolate(data['R_X'], data['R_Y'], data['right_missing'], rrmissStart, rrmissEnd, par['edgeSampInterp'], par['dev_interpolation'])       
        
    # =============================================================================
    # 2-MEANS CLUSTERING
    # =============================================================================
    ## CALCULATE 2-MEANS CLUSTERING FOR SINGLE EYE
    if not q2Eyes:        
        # get kmeans-clustering for averaged signal
        print('\t2-Means clustering started for averaged signal')
        finalweights, stopped = twoClusterWeighting(xpos, ypos, missingn, par['downsamples'], par['downsampFilter'], par['chebyOrder'],par['windowtime'], par['steptime'],par['freq'],par['maxerrors'],par['dev_cluster'])
        
        # check whether clustering succeeded
        if stopped:
            print('\tClustering stopped after exceeding max errors, continuing to next file \n')
            return False
        
    ## CALCULATE 2-MEANS CLUSTERING FOR SEPARATE EYES
    elif q2Eyes:
        # get kmeans-clustering for left eye signal
        print('\t2-Means clustering started for left eye signal')
        finalweights_left, stopped = twoClusterWeighting(llx, lly, llmissn, par['downsamples'], par['downsampFilter'], par['chebyOrder'],par['windowtime'], par['steptime'],par['freq'],par['maxerrors'],par['dev_cluster'])
        
        # check whether clustering succeeded
        if stopped:
            print('Clustering stopped after exceeding max errors, continuing to next file \n')
            return False
        
        # get kmeans-clustering for right eye signal
        print('\t2-Means clustering started for right eye signal')
        finalweights_right, stopped = twoClusterWeighting(rrx, rry, rrmissn, par['downsamples'], par['downsampFilter'], par['chebyOrder'],par['windowtime'], par['steptime'],par['freq'],par['maxerrors'],par['dev_cluster'])
        
        # check whether clustering succeeded
        if stopped:
            print('\tClustering stopped after exceeding max errors, continuing to next file')
            return False
        
        ## AVERAGE FINALWEIGHTS OVER COMBINED & SEPARATE EYES
        finalweights = np.nanmean(np.vstack([finalweights_left, finalweights_right]), axis=0)
    
    # =============================================================================
    #  DETERMINE FIXATIONS BASED ON FINALWEIGHTS_AVG
    # =============================================================================
    print('\tDetermining fixations based on clustering weight mean for averaged signal and separate eyes + 2*std')      
    fix = getFixations(finalweights,data['time'],xpos,ypos,missing,par)
    fix = getFixStats(xpos,ypos,missing,pixperdeg,fix)
  
    return fix,data,par
    
    