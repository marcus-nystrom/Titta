[![Downloads](https://static.pepy.tech/badge/titta)](https://pepy.tech/project/titta)
[![Citation Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fapi.juleskreuer.eu%2Fcitation-badge.php%3Fshield%26doi%3D10.3758%2Fs13428-020-01358-8&color=blue)](https://scholar.google.com/citations?view_op=view_citation&citation_for_view=uRUYoVgAAAAJ:J_g5lzvAfSwC)
[![PyPI Latest Release](https://img.shields.io/pypi/v/titta.svg)](https://pypi.org/project/titta/)
[![image](https://img.shields.io/pypi/pyversions/titta.svg)](https://pypi.org/project/titta/)
[![DOI](https://zenodo.org/badge/DOI/10.3758/s13428-020-01358-8.svg)](https://doi.org/10.3758/s13428-020-01358-8)

Titta is a toolbox for using eye trackers from Tobii Pro AB with Python,
specifically offering integration with [PsychoPy](https://www.psychopy.org/). A Matlab version
that integrates with PsychToolbox is also available from
https://github.com/dcnieho/Titta. For a similar toolbox for SMI eye trackers, please see www.github.com/marcus-nystrom/SMITE.

Titta is an alternative to using the eye tracking functionality already available in PsychoPy (through ioHub). Instead of the general interface ioHub provides to many eye trackers, Titta is specifically designed to offer full access to the functionality of Tobii eye trackers, has an intuitive participant setup and calibration interface, and includes scripts for analysis of eye-tracking data.

Cite as:
[Niehorster, D.C., Andersson, R. & Nystrom, M. (2020). Titta: A toolbox for creating PsychToolbox and Psychopy experiments with Tobii eye trackers. Behavior Research Methods. doi: 10.3758/s13428-020-01358-8](https://doi.org/10.3758/s13428-020-01358-8)

For questions, bug reports or to check for updates, please visit
https://github.com/marcus-nystrom/Titta. 

To minimize the risk of missing samples, the current repository uses [TittaPy](#tittapy-class) (`pip install TittaPy`), a C++ wrapper around the Tobii SDK, to pull samples made available from the eye tracker. 


## To get started
If you know what you are doing, install Titta using: `pip install titta` or `python -m pip install titta`.

If you use a standalone PsychoPy installation, do the following steps:
1. Go to `C:\Program Files\PsychoPy` (or wherever you installed PsychoPy) and open a command prompt in the same folder as where you find `python.exe` (should be the main PsychoPy install folder). So the command prompt you have should start with something like `C:\Program Files\PsychoPy>`
1. Here you can then pip-install titta, by issuing a command like `python -m pip install titta --upgrade`.

Then run `read_me.py` from the 'demos' folder (first change the monitor settings and the eye tracker name in `read_me.py`). Reading through `read_me.py` should provide a good starting point for most users of Titta.


### To get started with the Tobii Pro Lab integration
1. Open read_read_me_TalkToProLab.py in PsychoPy.
1. Download [Tobii Pro Lab](https://www.tobiipro.com/product-listing/tobii-pro-lab/)
1. Open a new External Presenter Project in Pro Lab. The Project name must be the same as the project name in read_read_me_TalkToProLab.py.
1. In PsychoPy, run read_read_me_TalkToProLab.py (first change the monitor settings and the eye tracker name).

Tested on Windows 10 using PsychoPy 2022.1.3 using Python 3.8. Ideally, make sure that the eye tracker is detected and works in 
the [Tobii Eye Tracker Manager](https://www.tobii.com/products/software/applications-and-developer-kits/tobii-pro-eye-tracker-manager) before trying to use it with Titta.

## Contents
The toolbox consists of two main parts:
### The `Titta.Connect` and `Tobii.MyTobii` classes
The Titta module (which utilizes the Tobii module) is the main workhorse of this toolbox, providing a wrapper around the Tobii Pro SDK, and a convenient graphical user interface (rendered through PsychoPy) for participant setup, calibration and validation. Only the `Titta.calibrate()` participant setup and calibration interface requires PsychoPy.

These modules connect to Tobii via `TittaPy`. Although `TittaPy` is located in a separate repository, documentation for it is included here since it is powering the `Titta` and `Tobii` modules here.
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
    |**Tobii Pro Spark**|`Tobii Pro Spark`|	
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
#### Module-level functions
The below method can be called on the Titta module directly.

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`get_defaults()`|<ol><li>`et_name`: one of the supported eye tracker model names, [see above](#usage)</li></ol>|<ol><li>`settings`: object with all supported settings for a specific model of eyeTracker</li></ol>|Gets all supported settings with defaulted values for the indicated eyeTracker, can be modified and used for constructing an instance of Titta. See the [supported options](#supported-options) section below.|

#### Construction
An instance of Titta for interaction with the eye tracker (a `Titta.MyTobii` instance) is constructed by calling the module-level constructor `Titta.Connect()` with either the name of a specific supported eye tracker model (in which case default settings for this model will be used) or with a settings struct retrieved from `Titta.get_defaults()`, possibly with changed settings (passing the settings object unchanged is equivalent to using the eye tracker model name as input argument).

#### Supported options
The `get_defaults()` method call returns the appropriate set of options for the indicated eye tracker.

| Option name | Explanation |
| --- | --- |
|`settings.SAMPLING_RATE`|Sampling frequency|

### `Tobii` module
#### Properties
The following methods are available for an instance of `Tobii.MyTobii` (as created by calling `Titta.Connect`).
|Property|Description|
| --- | --- |
|`buffer`|Initialized by call to `init()`. Returns handle to a [TittaPy instance](#tittapy-class) for interaction with the eye tracker's data streams. This handle can furthermore be used for directly interacting with the eye tracker through the Tobii Pro SDK, but note that this is at your own risk. Titta should have minimal assumptions about eye-tracker state, but I cannot guarantee that direct interaction with the eye tracker does not interfere with later use of Titta in the same session.|
#### Methods
The following methods are available for an instance of `Tobii.MyTobii` (as created by calling `Titta.Connect`).

|Call|Inputs|Outputs|Description|
| --- | --- | --- | --- |
|`init()`|||Connect to the Tobii eye tracker and initialize it according to the requested settings (provided optionally when calling `Titta.Connect()`).|
|`calibrate()`|<ol><li>`win`: PsychoPy window object</li><li>`win_operator`: (optional) PsychoPy window object for the operator's screen</li><li>`eye`: (optional) 'left', 'right' or 'both'. Default: 'both'.</li><li>`calibration_number`: (optional) used to indicate if we need to wait for another calibration i.e. if 'first', then will not exit until 'second' calibration has finished. Default: 'second'</ol>||Do participant setup, calibration and validation.|
|`start_recording()`|<ol><li>`gaze`: (optional) Default: false.</li><li>`time_sync`: (optional) Default: false.</li><li>`eye_image`: (optional) Default: false.</li><li>`notifications`: (optional) Default: false.</li><li>`external_signal`: (optional) Default: false.</li><li>`positioning`: (optional) Default: false.</li></ol>||Begin recording the specified kind of data. If none of the input parameters are set to true, then this method does nothing.|
|`stop_recording()`|<ol><li>`gaze`: (optional) Default: false.</li><li>`time_sync`: (optional) Default: false.</li><li>`eye_image`: (optional) Default: false.</li><li>`notifications`: (optional) Default: false.</li><li>`external_signal`: (optional) Default: false.</li><li>`positioning`: (optional) Default: false.</li></ol>||Stop recording the specified kind of data. If none of the input parameters are set to true, then this method does nothing.|
|`send_message()`|<ol><li>`msg`: Message to be written into data file</li><li>`ts`: (optional) timestamp of the message (in seconds, will be stored as microseconds)</li></ol>||Store timestamped message|
|`save_data()`|<ol><li>`filename`: (optional) filename (including path) where HDF5 container will be stored</li><li>`append_version`: (optional) boolean indicating whether version numbers (`_1`, `_2`, etc) will automatically get appended to the filename if the destination file already exists. Default: True</li></ol>||Save data to HDF5 container at specified location|
||||
|`calibration_history()`||<ol><li>`all_validation_results`: a list, where each list entry contains the accuracy values in degrees from 0. left eye x, 1. left eye y, 2. right eye x, and 3. right eye y.  The last entry [4] tells whether the calibration was used (1) or not used (0).</li></ol>|Get the calibration history thus far.|
|`system_info()`||<ol><li>A dictionary containing all the information included in [`TittaPy`'s properties](#properties), plus `python_version`, `psychopy_version`, `TittaPy_version`, and `titta_version`.|Get information about the system and connected eye tracker.|
|`get_system_time_stamp()`||<ol><li> An int64 scalar denoting Tobii system time in microseconds.</li></ol>|Get the current system time through the Tobii Pro SDK.|
|`set_sample_rate()`|<ol><li>`Fs`: the desired frequency value</li></ol>||Set the sampling rate of the connected eye tracker (if it is a supported frequency).|
|`get_sample_rate()`||<ol><li>`frequency`: the current frequency value</li></ol>|Get the sampling rate of the connected eye tracker.|

### `TittaPy` class
The TittaPy class can be used for interaction with the eye tracker's data streams. It is accessed via `Tobii.MyTobii`'s `buffer` property.  For instance, if `tracker` is your `Tobii.MyTobii` instance, then you can retrieve the recorded samples using `tracker.buffer.consume_N()`. The TittaPy methods and properties are documented in the [TittaPy repository](https://github.com/dcnieho/Titta#titta-tittamex-tittapy-classes).


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
