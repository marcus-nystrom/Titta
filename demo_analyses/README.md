The files in this folder are resources to help users access data and perform common data processing tasks.

To extract trial data, compute data quality, and classify fixation, perform the following steps (in this order):
* Extract trial data (run `extract_trial_data.py`). This will create a folder 'trials' with data organized by participants and trials.
* Compute data quality (run `compute_data_quality.py`). Will output two csv-files with information about data quality during the validation as well as data loss values for each trial.
* Pip install [the I2MC algorithm](https://github.com/dcnieho/I2MC_Python) for fixation detection: execute `pip install I2MC` or `python -m pip install I2MC`
* Adjust the settings in `I2MC_example.py` to match your experimental setup. Check under '# NECESSARY VARIABLES' in the beginning of the file. 
* Run `detect_fixations.py`. This will produce a folder `output` that contains a text file with all the fixations (allfixations.txt) and images visualizing the result of the fixation detection.
* To visualize the recorded data and stimuli, run `plot_scanpath.py`. First create a  `stimulus` folder and put the relevant stimuli images there.

When fixations have been detected, they can be mapped to specific AOIs (see the `AOI_example` folder).

