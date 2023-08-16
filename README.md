Titta is a toolbox for using eye trackers from Tobii Pro AB with Python,
specifically offering integration with [PsychoPy](https://www.psychopy.org/). A Matlab version
that integrates with PsychToolbox is also available from
https://github.com/dcnieho/Titta. For a similar toolbox for SMI eye trackers, please see www.github.com/marcus-nystrom/SMITE.

Titta is an alternative to using the eye tracking functionality already available in PsychoPy (through ioHub), but instead of a general interface to many eye trackers, it is specifically designed to offer full access to the Tobii Pro SDK, has an intuitive calibration interface, and includes scripts for analysis of eye-tracking data.

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
### The `Titta.Connect` and `Tobii.MyTobii` classes
The Titta module (which utilizes the Tobii module) is the main workhorse of this toolbox, providing a wrapper around the Tobii Pro SDK, and a convenient graphical user interface (rendered through PsychoPy) for participant setup, calibration and validation. Only the `Titta.calibrate()` participant setup and calibration interface requires PsychoPy.

These modules connect to Tobii via `TittaPy`. Although `TittaPy` is located at the [Matlab version of Titta](https://github.com/dcnieho/Titta), documentation for it is included here since it is powering the `Titta` and `Tobii` modules here.
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
    |Tobii Pro Spark|`Tobii Pro Spark`|	
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

## API
### `Titta` module
#### Module-level methods
The below method can be called on the Titta module directly.

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`get_defaults()`|<ol><li>`et_name`: one of the supported eye tracker model names, [see above](#usage)</li></ol>|<ol><li>`settings`: object with all supported settings for a specific model of eyeTracker</li></ol>|Gets all supported settings with defaulted values for the indicated eyeTracker, can be modified and used for constructing an instance of Titta. See the [supported options](#supported-options) section below.|

#### Construction
An instance of Titta.Connect is constructed by calling `Titta.Connect()` with either the name of a specific supported eye tracker model (in which case default settings for this model will be used) or with a settings struct retrieved from `Titta.get_defaults()`, possibly with changed settings (passing the settings object unchanged is equivalent to using the eye tracker model name as input argument).

#### Methods
The following method calls are available on a `Titta.Connect` instance:

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`init()`|<ol><li>`in_arg`: (optional) string indicating eye tracker name or 'settings' from `get_defaults`. If no input argument is given, then it defaults to intializing in dummy mode.||Connect to the Tobii eye tracker and initialize it according to the requested settings|

#### Supported options
The `get_defaults()` method call returns the appropriate set of options for the indicated eye tracker.

| Option name | Explanation |
| --- | --- |
|`settings.SAMPLING_RATE`|Sampling frequency|

### `Tobii` module
#### Methods
The following methods are available for an instance of `Tobii.MyTobii` (and, by extension, `Titta.Connect`).

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`init()`|<ol><li>`settings`: (optional) 'settings' from `get_defaults`.||Connect to the Tobii eye tracker and initialize it according to the requested settings|
|`calibrate()`|<ol><li>`win`: PsychoPy window object</li><li>`win_operator`: (optional) PsychoPy window object for the operator's screen</li><li>`eye`: (optional) 'left', 'right' or 'both'. Default: 'both'.</li><li>`calibration_number`: (optional) used to indicate if we need to wait for another calibration i.e. if 'first', then will not exit until 'second' calibration has finished. Default: 'second'</ol>||Do participant setup, calibration and validation.|
|`start_recording()`|<ol><li>`gaze`: (optional) Default: false.</li><li>`time_sync`: (optional) Default: false.</li><li>`eye_image`: (optional) Default: false.</li><li>`notifications`: (optional) Default: false.</li><li>`external_signal`: (optional) Default: false.</li><li>`positioning`: (optional) Default: false.</li></ol>||Begin recording the specified kind of data. If none of the input parameters are set to true, then this method does nothing.|
|`stop_recording()`|<ol><li>`gaze`: (optional) Default: false.</li><li>`time_sync`: (optional) Default: false.</li><li>`eye_image`: (optional) Default: false.</li><li>`notifications`: (optional) Default: false.</li><li>`external_signal`: (optional) Default: false.</li><li>`positioning`: (optional) Default: false.</li></ol>||Stop recording the specified kind of data. If none of the input parameters are set to true, then this method does nothing.|
|`send_message()`|<ol><li>`msg`: Message to be written into data file</li><li>`ts`: (optional) timestamp of the message (in seconds, will be stored as microseconds)</li></ol>||Store timestamped message|
|`save_data()`|<ol><li>`filename`: (optional) filename (including path) where HDF5 container will be stored</li><li>`append_version`: (optional) boolean indicating whether version numbers (`_1`, `_2`, etc) will automatically get appended to the filename if the destination file already exists. Default: True</li></ol>||Save data to HDF5 container at specified location|
||||
|`calibration_history()`||<ol><li>`all_validation_results`: a list, where each list entry contains the accuracy values in degrees from 0. left eye x, 1. left eye y, 2. right eye x, and 3. right eye y.  The last entry [4] tells whether the calibration was used (1) or not used (0).</li></ol>|Get the calibration history thus far.|
|`system_info()`||A dictionary containing all the information included in [`TittaPy`'s properties](#properties), plus `python_version`, `psychopy_version`, `TittaPy_version`, and `titta_version`.|Get information about the system and connected eye tracker.|
|`get_system_time_stamp()`||<ol><li> An int64 scalar denoting Tobii system time in microseconds.</li></ol>|Get the current system time through the Tobii Pro SDK.|
|`set_sample_rate()`|<ol><li>`Fs`: the desired frequency value</li></ol>||Set the sampling rate of the connected eye tracker (if it is a supported frequency).|
|`get_sample_rate()`||<ol><li>`frequency`: the current frequency value</li></ol>|Get the sampling rate of the connected eye tracker.|

### `TittaPy` class

These methods can be accessed via `Tobii.MyTobii`, which itself can be accessed via `Titta.Connect`.

#### Module-level methods
|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`get_SDK_version`||<ol><li> `SDK_version`: a string indicating the version.</li></ol>|Get the version of the Tobii Pro SDK dynamic library that is used by `TittaPy`.|
|`get_system_timestamp`||<ol><li>`system_timestamp`: an int64 scalar denoting Tobii system time in microseconds.</li></ol>|Get the current system time through the Tobii Pro SDK.|
|`find_all_eye_trackers()`||<ol><li>`eye_tracker_list`: An array of structs with information about the connected eye trackers.</li></ol>|Gets the eye trackers that are connected to the system, as listed by the Tobii Pro SDK.|
|`start_logging()`|<ol><li>`initial_buffer_size`: (optional) value indicating for how many event memory should be allocated</li></ol>|<ol><li>`success`: a boolean indicating whether logging was started successfully</li></ol>|Start listening to the eye tracker's log stream, store any events to buffer.|
|`get_log()`|<ol><li>`clear_log`: (optional) boolean indicating whether the log buffer should be cleared</li></ol>|<ol><li>`data`: struct containing all events in the log buffer, if available. If not available, an empty struct is returned.</li></ol>|Return and (optionally) remove log events from the buffer.|
|`stop_logging()`|||Stop listening to the eye tracker's log stream.|

#### Construction and initialization
An instance of TittaPy is constructed by calling `TittaPy.EyeTracker()`. Before it becomes fully functional, its `init()` method should be called to provide it with the address of an eye tracker to connect to. A list of connected eye trackers is provided by calling the static function `TittaPy.find_all_eye_trackers()`.

#### Methods
The following method calls are available on a `TittaPy.EyeTracker` instance:

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`init()`|<ol><li>`address`: address of the eye tracker to connect to</li></ol>||Connect to the TittaPy class instance to the Tobii eye tracker and prepare it for use.|
|||||
|`apply_licenses()`|<ol><li>`licenses`: a cell array of licenses (`char` of `uint8` representations of the license file read in binary mode).</li></ol>|<ol><li>`apply_results`: a cell array of strings indicating whether license(s) were successfully applied.</li></ol>|Apply license(s) to the connected eye tracker.|
|`clear_licenses()`|||Clear all licenses that may have been applied to the connected eye tracker. Refreshes the eye tracker's info, so use `getConnectedEyeTracker()` to check for any updated capabilities.|
|||||
|`has_stream()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li></ol>|<ol><li>`supported`: a boolean indicating whether the connected eye tracker supports providing data of the requested stream type.</li></ol>|Check whether the connected eye tracker supports providing a data stream of a specified type.|
|`set_include_eye_openness_in_gaze()`|<ol><li>`include`: a boolean, indicating whether eye openness samples should be provided in the recorded gaze stream or not. Default false.</li></ol>|<ol><li>`previousState`: a boolean indicating the previous state of the include setting.</li></ol>|Set whether calls to start or stop the gaze stream should also start or stop the eye openness stream. An error will be raised if set to true, but the connected eye tracker does not provide an eye openness stream. If set to true, calls to start or stop the eyeOpenness stream will also start or stop the gaze stream.|
|`start()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li><li>`initial_buffer_size`: (optional) value indicating for how many samples memory should be allocated</li><li>`as_gif`: an (optional) boolean that is ignored unless the stream type is `eyeImage`. It indicates whether eye images should be provided gif-encoded (true) or a raw grayscale pixel data (false).</li></ol>|<ol><li>`success`: a boolean indicating whether streaming to buffer was started for the requested stream type</li></ol>|Start streaming data of a specified type to buffer. The default initial buffer size should cover about 30 minutes of recording gaze data at 600Hz, and longer for the other streams. Growth of the buffer should cause no performance impact at all as it happens on a separate thread. To be certain, you can indicate a buffer size that is sufficient for the number of samples that you expect to record. Note that all buffers are fully in-memory. As such, ensure that the computer has enough memory to satify your needs, or you risk a recording-destroying crash.|
|`is_recording()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li></ol>|<ol><li>`status`: a boolean indicating whether data of the indicated type is currently being streamed to buffer</li></ol>|Check if data of a specified type is being streamed to buffer.|
|`consume_N()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li><li>`N_samples`: (optional) number of samples to consume from the start of the buffer. Defaults to all.</li><li>`side`: (optional) a string, possible values: `first` and `last`. Indicates from which side of the buffer to consume N samples. Default: `first`.</li></ol>|<ol><li>`data`: struct containing data from the requested buffer, if available. If not available, an empty struct is returned.</li></ol>|Return and remove data of the specified type from the buffer.|
|`consume_time_range()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync` and `notification`.</li><li>`time_start`: (optional) timestamp indicating start of interval for which to return data. Defaults to start of buffer.</li><li>`time_end`: (optional) timestamp indicating end of interval for which to return data. Defaults to end of buffer.</li></ol>|<ol><li>`data`: struct containing data from the requested buffer in the indicated time range, if available. If not available, an empty struct is returned.</li></ol>|Return and remove data of the specified type from the buffer.|
|`peek_N()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li><li>`N_samples`: (optional) number of samples to peek from the end of the buffer. Defaults to 1.</li><li>`side`: (optional)a string, possible values: `first` and `last`. Indicates from which side of the buffer to peek N samples. Default: `last`.</li></ol>|<ol><li>`data`: struct containing data from the requested buffer, if available. If not available, an empty struct is returned.</li></ol>|Return but do not remove data of the specified type from the buffer.|
|`peek_time_range()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync` and `notification`.</li><li>`time_start`: (optional) timestamp indicating start of interval for which to return data. Defaults to start of buffer.</li><li>`time_end`: (optional) timestamp indicating end of interval for which to return data. Defaults to end of buffer.</li></ol>|<ol><li>`data`: struct containing data from the requested buffer in the indicated time range, if available. If not available, an empty struct is returned.</li></ol>|Return but do not remove data of the specified type from the buffer.|
|`clear()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li></ol>||Clear the buffer for data of the specified type.|
|`clear_time_range()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync` and `notification`.</li><li>`time_start`: (optional) timestamp indicating start of interval for which to clear data. Defaults to start of buffer.</li><li>`time_end`: (optional) timestamp indicating end of interval for which to clear data. Defaults to end of buffer.</li></ol>||Clear data of the specified type within specified time range from the buffer.|
|`stop()`|<ol><li>`stream`: a string, possible values: `gaze`, `eyeOpenness`, `eyeImage`, `externalSignal`, `timeSync`, `positioning` and `notification`.</li><li>`clear_buffer`: (optional) boolean indicating whether the buffer of the indicated stream type should be cleared</li></ol>|<ol><li>`success`: a boolean indicating whether streaming to buffer was stopped for the requested stream type</li></ol>|Stop streaming data of a specified type to buffer.|
|||||
|`enter_calibration_mode()`|<ol><li>`do_monocular`: boolean indicating whether the calibration is monocular or binocular</li></ol>|<ol><li>`has_enqueued_enter`: boolean indicating whether a request to enter calibration mode has been sent to worker thread. Will return false if already in calibration mode through a previous call to this interface (it does not detect if other programs/code have put the eye tracker in calibration mode).</li></ol>|Queue request for the tracker to enter into calibration mode.|
|`is_in_calibration_mode()`|<ol><li>`issue_error_if_not_`: (optional) throws error if not in calibration mode. Default `false`.</li></ol>|<ol><li>`is_in_calibration_mode`: Boolean indicating whether eye tracker is in calibration mode.</li></ol>|Check whether eye tracker is in calibration mode.|
|`leave_calibration_mode()`|<ol><li>`force`: (optional) set to true if you want to be completely sure that the tracker is not in calibration mode after this call: this also ensures calibration mode is left if code other than this interface put the eye tracker into calibration mode</li></ol>|<ol><li>`has_enqueued_leave`: boolean indicating whether a request to leave calibration mode has been sent to worker thread. Will return false if force leaving or if not in calibration mode through a previous call to this interface.</li></ol>|Queue request for the tracker to leave the calibration mode.|
|`calibration_collect_data()`|<ol><li>`coordinates`: the coordinates of the point that the participant is asked to fixate, 2-element array with values in the range [0,1]</li><li>`eye`: (optional) the eye for which to collect calibration data. Possible values: `left` and `right`</li></ol>||Queue request for the tracker to collect gaze data for a single calibration point.|
|`calibration_discard_data()`|<ol><li>`coordinates`: the coordinates of the point for which calibration data should be discarded, 2-element array with values in the range [0,1]</li><li>`eye`: (optional) the eye for which collected calibration data should be discarded. Possible values: `left` and `right`</li></ol>||Queue request for the tracker to discard any already collected gaze data for a single calibration point.|
|`calibration_compute_and_apply()`|||Queue request for the tracker to compute the calibration function and start using it.|
|`calibration_get_data()`|||Request retrieval of the computed calibration as an (uninterpretable) binary stream.|
|`calibration_apply_data()`|<ol><li>`cal_data`: a binary stream as gotten through `calibrationGetData()`</li></ol>||Apply the provided calibration data.|
|`calibration_get_status()`||<ol><li>`status`: a string, possible values: `NotYetEntered`, `AwaitingCalPoint`, `CollectingData`, `DiscardingData`, `Computing`, `GettingCalibrationData`, `ApplyingCalibrationData` and `Left`</li></ol>|Get the current state of TittaPy's calibration mechanism.|
|`calibration_retrieve_result()`||<ol><li>`result`: a struct containing a submitted work item and the associated result, if any compelted work items are available</li></ol>|Get information about tasks completed by TittaPy's calibration mechanism.|

#### Properties
The following **read-only** properties are available for a `TittaPy.EyeTracker` instance:

|Property|Description|
| --- | --- |
|`info`|Get connected eye tracker's basic stats.|
|`serial_number`|Get connected eye tracker's serial number.|
|`model`|Get connected eye tracker's model name.|
|`firmware_version`|Get connected eye tracker's firmware version.|
|`runtime_version`|Get connected eye tracker's runtime version.|
|`address`|Get connected eye tracker's address.|
|`capabilities`|Get connected eye tracker's exposed capabilities.|
|`supported_frequencies`|Get connected eye tracker's supported sampling frequencies.|
|`supported_modes`|Get connected eye tracker's supported tracking modes.|
|`track_box`|Get connected eye tracker's track box.|
|`display_area`|Get connected eye tracker's display area.|

The following **settable** properties are available for a `TittaPy.EyeTracker` instance:

|Property|Description|
| --- | --- |
|`device_name`|Get or set connected eye tracker's device name.|
|`frequency`|Get or set connected eye tracker's sampling frequency.|
|`tracking_mode`|Get or set connected eye tracker's tracking mode.|


### `TalkToProLab` class
#### Construction
An instance of TalkToProLab is constructed by calling `TalkToProLab()` and optionally providing two constructor arguments:
- `project_name`: (optional) the name of the External Presenter project that should be opened in Pro Lab
- `dummy_mode`: (optional) a bool indicating whether to run in dummy mode. Default: false.


#### Methods
The following method calls are available on a TalkToProLab instance.  The majority of return types are the `response` dictionary, containing the operation name, the status code, and however many useful variables relevant to this operation.  The status codes are as follows:  
0: 'Operation successful',  
100: 'Bad request',  
101: 'Invalid parameter',  
102: 'Operation was unsuccessful',  
103: 'Operation cannot be executed in current state',  
104: 'Access to the service is forbidden',  
105: 'Authorization during connection to a service has not been provided',  
201: 'Recording finalization failed'.  

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`add_participant()`|<ol><li>`participant_name`: name of the participant</li></ol>|`response`, a dictionary containing: <ol><li>`operation`: "AddParticipant"</li><li>`status_code`</li><li>`participant_id`: string: a unique ID for identifying the participant in the Pro Lab project</li></ol>|Create a new participant in the Tobii Pro Lab project.|
|`find_participant()`|<ol><li>`participant_name`: name of the participant</li></ol>|<ol><li>`exists`: a boolean</li></ol>|Find whether a participant already exists in the Tobii Pro Lab project.|
|`list_participants()`||`response`, a dictionary containing: <ol><li>`operation`: "ListParticipants"</li><li>`status_code`</li><li>A list of participants, with each entry being a dictionary containing:<ol><li>`participant_name`: a string: the name that was provided to Pro Lab for the participant</li><li>`participant_id`: string: a unique ID for identifying the participant in the Pro Lab project</li></ol></li></ol>|List all participants in the Tobii Pro Lab project.|
|`upload_media()`|<ol><li>`media_name`: name of the file to upload (including the file extension). Understood media types when a filename is provided are `bmp`, `jpg`, `jpeg`, `png`, `gif`, `mp4` and `avi`</li><li>`media_type`: 'image' or 'video'</li></ol>||Upload media to the Tobii Pro Lab project.|
|`find_media()`|<ol><li>`media_name`: name of the media to find (case sensitive)</li></ol>|<ol><li>`exists`: a boolean indicating whether the media exists</li></ol>|Find media by name in the Tobii Pro Lab project.|
|`list_media()`||`response`, a dictionary containing: <ol><li>`operation`: "ListMedia"</li><li>`status_code`</li><li>A list of media, with each entry being a dictionary containing:<ol><li>`media_name`: a string: the name that was provided to Pro Lab for the media</li><li>`media_id`: string: a unique ID for identifying the media in the Pro Lab project</li><li>`md5_checksum`: (only present for some values) the hash value that can be used to verify the file</li><li>`mime_type`: a string: the type of the media file, in the format "image" or "video" / file extension e.g. "image/jpeg"</li><li>`media_size`: the size of the file</li><li>`width`</li><li>`height`</li><li>`duration`: 0 for images</li></ol></li></ol>|List all media in the Tobii Pro Lab project.|
|`add_aois_to_image`|<ol><li>`media_id`: id of the media in Pro Lab to define an AOI for</li><li>`aoi_name`: name of the AOI</li><li>`aoi_color`: color in which to show the AOI in Pro Lab (RGB, 0-255)</li><li>`key_frame_vertices`: 2xN matrix of vertices of the AOI</li><li>`key_frame_active`: (optional) Default: true.</li><li>`key_frame_seconds`: (optional) Default: 0.</li><li>`tag_name`: (optional) name of tag for identifying the AOI in Pro Lab. Default: empty string.</li><li>`group_name`: (optional) the name of the tag group. Default: empty string.</li><li>`merge_mode`: (optional) Default: `replace_aois`.</li></ol>|`response`, a dictionary containing: <ol><li>`operation`: "sendAois"</li><li>`status_code`</li><li>`imported_aoi_count`</li></ol>|Define an AOI for a specific media in the Pro Lab project.|
|`add_aois_to_video`|<ol><li>`media_id`: id of the media in Pro Lab to define an AOI for</li><li>`aoi_name`: name of the AOI</li><li>`aoi_color`: color in which to show the AOI in Pro Lab (RGB, 0-255)</li><li>`key_frame_vertices`: 2xN matrix of vertices of the AOI</li><li>`key_frame_active`: (optional) Default: true.</li><li>`key_frame_seconds`: (optional) Default: 0.</li><li>`tag_name`: (optional) name of tag for identifying the AOI in Pro Lab. Default: empty string.</li><li>`group_name`: (optional) the name of the tag group. Default: empty string.</li><li>`merge_mode`: (optional) Default: `replace_aois`.</li></ol>|`response`, a dictionary containing: <ol><li>`operation`: "sendAois"</li><li>`status_code`</li><li>`imported_aoi_count`</li></ol>|Define an AOI for a specific media in the Pro Lab project.|
|||||
|`get_state()`||`response`, a dictionary containing: <ol><li>`operation`: "GetState"</li><li>`status_code`</li><li>`state`: The current state</li></ol>|Get the state of the external presenter service in Pro Lab.|
|`start_recording()`|<ol><li>`recording_name`: name by which the recording will be identified in Pro Lab</li><li>`participant_id`: the ID (from Pro Lab) of the participant associated with this recording</li><li>`screen_width`: width of the screen in pixels</li><li>`screen_height`: height of the screen in pixels</li><li>`screen_latency`: (optional) numeric value indicating delay between drawing commands being issued and the image actually appearing on the screen. Default: 10000.</li></ol>|`response`, a dictionary containing: <ol><li>`operation`: "StartRecording"</li><li>`status_code`</li><li>`recording_id`: A unique identifier for the new recording</li></ol>|Tell Pro Lab to start a recording.|
|`stop_recording()`|||Stop a currently ongoing recording of Tobii Pro Lab.|
|`finalize_recording()`|<ol><li>`recording_id`: the ID (from Pro Lab) of the recording that was just stopped</li></ol>||Finalize the stopped recording in Tobii Pro Lab. Note: after this call, you must still click ok in the Pro Lab user interface.|
|||||
|`send_stimulus_event()`|<ol><li>`recording_id`: the ID (from Pro Lab) of the recording</li><li>`start_timestamp`: timestamp (in seconds or microseconds) at which stimulus presentation started.</li><li>`end_timeStamp`: (optional) timestamp (in seconds or microseconds) of when presentation of this stimulus ended. If empty, it is assumed stimulus remained on screen until start of the next stimulus</li><li>`media_id`: unique identifier by which shown media stimulus is identified in Pro Lab</li><li>`media_position`: (optional) location of the stimulus on screen in pixels, format: `[left top right bottom]`</li><li>`background`: (optional) color of background (RGB: 0-255) on top of which stimulus was shown</li></ol>||Inform Pro Lab when and where a media (stimulus) was shown.|
|`send_custom_event()`|<ol><li>`recording_id`: the ID (from Pro Lab) of the recording</li><li>`timestamp`: (optional) timestamp (in s) at which event occured. If empty, current time is taken as event time</li><li>`event_type`: string: event type name</li><li>`value`: (optional) string, the value of the event</li></ol>||Add an event to Pro Lab's timeline.|
|`disconnect()`|||Disconnect from Tobii Pro Lab.|
