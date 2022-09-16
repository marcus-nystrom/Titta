The files in this folder are resources to help users access data and perform common data processing tasks.

To extract trial data and classifiy fixation, perform the following steps (in this order):
* Extract trial data (run *extract_trial_data.py*). This will create a folder 'trials' with data organized by participants and trials.
* Download and extract the I2MC algorithm (https://github.com/dcnieho/I2MC_Python) to the folder resources/I2MC. The name of the extracted folder must be 'I2MC_Python-master'.
* Run *detect_fixations.py*. This will prompt the user to download the I2MC algorithm (if not already done in the previous step), and move trial data to the approriate folder in the I2MC folder structure. 
* Run /I2MC_Python-master/example/I2MC_example.py'. Before running it, adjust the settings in *I2MC_example.py* to match your experimental setup. Check under '# NECESSARY VARIABLES' in the beginning of the file. Also make sure Titta is use when importing data (line 190 in *I2MC_example.py*):
data = imp.Titta(file_name, [opt['xres'], opt['yres']])

When fixations have been detected, they can be mapped to specific AOIs (see the 'AOI_example' folder).

If you prefer Jupyter notebooks, see 'Titta data processing.ipynb' and 'map_fixations_to_aois.ipynb'.

To read result pickles (files ending with .pkl) containing data from a recording using Titta, use 'read_result_pickle.py'
