The files in this folder are resources to help users access data and perform common data processing tasks.

To extract trial data, compute data quality, and classifiy fixation, perform the following steps (in this order):
* Extract trial data (run *extract_trial_data.py*). This will create a folder 'trials' with data organized by participants and trials.
* Compute data quality (run *compute_data_quality.py*). Will output two csv-files with information about data quality during the validation as well as data loss values for each trial.
* Pip install the I2MC algorithm for fixation detection: pip install I2MC
* Adjust the settings in *I2MC_example.py* to match your experimental setup. Check under '# NECESSARY VARIABLES' in the beginning of the file. 
* Run *detect_fixations.py*. This will produce a folder 'output' that contains a text file with all the fixations (allfixations.txt) and images visualizing the result of the fixation detection.

If you prefer Jupyter notebooks, 'Titta data processing.ipynb' does the same steps.

When fixations have been detected, they can be mapped to specific AOIs (see the 'AOI_example' folder).


To read result pickles (files ending with .pkl) containing data from a recording using Titta, use 'read_result_pickle.py'


