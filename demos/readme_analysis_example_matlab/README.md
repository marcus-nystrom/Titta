The files in this folder demonstrate performing fixation classification on the data recorded with the readme scripts using the MATLAB algorithm I2MC (https://github.com/royhessels/I2MC). First follow the instructions in `readme_analysis_example/function_library/I2MC/get_I2MC.txt`, then place the `.tsv`-file(s) containing samples recorded with any of the `read_me` files in the folder `readme_analysis_example/data/samples`, the `_msg.tsv`-file(s) containing messages in the folder `readme_analysis_example/data/msgs` and finally run the scripts in the following order:

1. `a_ophakker.m`
2. `b_detFix.m`
3. `c_showFix.m`

When viewing fixation detection with `c_showFix.m`, press any key to go to the next trial. Close the figure window and press any key to stop scrolling through the trials.

the file `a_validationAccuracy.m` can be run in parallel to these scripts
