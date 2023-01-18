Titta is a toolbox for using eye trackers from Tobii Pro AB with Python,
specifically offering integration with [PsychoPy](https://www.psychopy.org/). A Matlab version
that integrates with PsychToolbox is also available from
https://github.com/dcnieho/Titta. For a similar toolbox for SMI eye trackers, please see www.github.com/marcus-nystrom/SMITE.

Cite as:
[Niehorster, D.C., Andersson, R. & Nystrom, M. (2020). Titta: A toolbox for creating PsychToolbox and Psychopy experiments with Tobii eye trackers. Behavior Research Methods. doi: 10.3758/s13428-020-01358-8](https://doi.org/10.3758/s13428-020-01358-8)

For questions, bug reports or to check for updates, please visit
https://github.com/marcus-nystrom/Titta. 

To minimize the risk of missing samples, the current repository uses TittaPy (`pip install TittaPy`), a [C++ wrapper](https://github.com/dcnieho/Titta/tree/master/SDK_wrapper/TittaPy) around the Tobii SDK, to pull samples made available from the eye tracker. 


## To get started
`pip install titta`

or

`python -m pip install titta`

Then run `read_me.py` from the 'demos' folder (first change the monitor settings and the eye tracker name in `read_me.py`).


### To get started with the Tobii Pro Lab integration
1. Open read_read_me_TalkToProLab.py in PsychoPy.
1. Download [Tobii Pro Lab](https://www.tobiipro.com/product-listing/tobii-pro-lab/)
1. Open a new External Presenter Project in Pro Lab. The Project name must be the same as the project name in read_read_me_TalkToProLab.py.
1. In PsychoPy, run read_read_me_TalkToProLab.py (first change the monitor settings and the eye tracker name).

Tested on Windows 10 using PsychoPy 2022.1.3 using Python 3.8. Ideally, make sure that the eye tracker is detected and works in 
the [Tobii Eye Tracker Manager](https://www.tobiipro.com/product-listing/eye-tracker-manager/) before trying to use it with Titta.

## Contents
The toolbox consists of two main parts:
### The `Titta` class
The Titta class is the main workhorse of this toolbox, providing a wrapper around the Tobii Pro SDK, and a convenient graphical user interface (rendered through PsychoPy) for participant setup, calibration and validation. Only the `Titta.calibrate()` participant setup and calibration interface requires PsychoPy.
### The `TalkToProLab` class
The `TalkToProLab` class provides an implementation of [Tobii Pro Lab](https://www.tobiipro.com/product-listing/tobii-pro-lab/)'s External Presenter interface, allowing experiments to be created and run from Python with PsychoPy or other presentation methods, while recording, project management, recording playback/visualization and analysis can be performed in Tobii Pro Lab.

## Usage
As demonstrated in the demo scripts, the toolbox is configured through
the following interface:
1. Retrieve (default) settings for eye tracker of interest: `settings =
Titta.getDefaults('tracker model name');` Supported eye trackers and their corresponding model names in the Tobii Pro SDK/Titta are:

    |Eye tracker|Model name|
    |---|---|
    |**Tobii Pro Spectrum**|`Tobii Pro Spectrum`|
    |**Tobii Pro Fusion**|`Tobii Pro Fusion`|
    |Tobii Pro TX300|`Tobii TX300`|
    |Tobii Pro T60 XL|`Tobii T60 XL`|
    |**Tobii Pro Nano**|`Tobii Pro Nano`|
    |**Tobii Pro X3-120**|`Tobii Pro X3-120` or `Tobii Pro X3-120 EPU`|
    |Tobii Pro X2-60|`X2-60_Compact`|
    |**Tobii Pro X2-30**|`X2-30_Compact`|
    |Tobii Pro X60|`Tobii X60`|
    |Tobii Pro X120|`Tobii X120`|
    |Tobii Pro T60|`Tobii T60`|
    |Tobii Pro T120|`Tobii T120`|
    |**Tobii 4C (Upgrade Key required)**|`IS4_Large_Peripheral`|
  
    Eye trackers marked in **bold** font have been tested. Note that the VR eye trackers are not supported by Titta. Also note that the Tobii 4C cannot be used for research purposes without buying the Pro Upgrade Key, and is compatible with Titta only after this purchase. Unfortunately, the Pro Upgrade Key is no longer sold by Tobii.
  
2. Change settings from their defaults if wanted.
3. Create a Titta instance using this settings struct: `tracker = Titta(settings);`
4. Interact with the eye tracker using the Titta API.
5. When calling `Titta.calibrate()`, a participant setup and calibration interface is shown. For each screen, several keyboard hotkeys are available to activate certain functionality. By default, the hotkey for each button is printed in the button's label. 
