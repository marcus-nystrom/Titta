Titta is a toolbox for using eye trackers from Tobii Pro AB with Python,
specifically offering integration with [PsychoPy](https://www.psychopy.org/). A Matlab version
that integrates with PsychToolbox is also available from
https://github.com/dcnieho/Titta

Cite as:
Niehorster, D.C., Andersson, R., & Nyström, M., (in prep). Titta: A
toolbox for creating Psychtoolbox and Psychopy experiments with Tobii eye
trackers.

For questions, bug reports or to check for updates, please visit
https://github.com/marcus-nystrom/Titta. 

Titta is licensed under the Creative Commons Attribution 4.0 (CC BY 4.0) license.

`examples/read_me.py` shows a minimal example of using the toolbox's
functionality.

*Note* that this toolbox is in a beta state. The API may change drastically at any time without notice. Work is ongoing, and code may also be in a broken or untested state without warning. That said, the toolbox has already been used in several projects at the Lund University Humanities Lab, Sweden.

To get started on Windows:
1. Download [PsychoPy](https://www.psychopy.org)
1. Open the command window
	1. Go the the PsychoPy folder (e.g., C:\Program Files (x86)\PsychoPy3)
	1. type 'python -m pip install git+https://github.com/marcus-nystrom/Titta.git#egg=Titta' 
1. Download the 'examples' folder and run read_me.py (first change the monitor settings and the eye tracker name in read_me.py).
	
Alternatively:
1. Download [PsychoPy](https://www.psychopy.org)
1. Download or clone the Titta folder
1. Add Titta to path in PsychoPy (under file->preferences)
1. Run read_me.py (first change the monitor settings and the eye tracker name in read_me.py).

Tested with PsychoPy v. 3.1.5 on Windows 10 using Python 3.6. Ideally, make sure that the eye tracker is detected and works in 
the [Tobii Eye Tracker Manager](https://www.tobiipro.com/product-listing/eye-tracker-manager/) before trying to use it with Titta.