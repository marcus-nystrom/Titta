from tobiiresearch.implementation.DisplayArea import DisplayArea


class CalibrationModeEnteredData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_CALIBRATION_MODE_ENTERED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_CALIBRATION_MODE_ENTERED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create CalibrationModeEnteredData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class CalibrationModeLeftData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_CALIBRATION_MODE_LEFT callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_CALIBRATION_MODE_LEFT
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create CalibrationModeLeftData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class ConnectionLostData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_CONNECTION_LOST callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_CONNECTION_LOST
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create ConnectionLostData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class ConnectionRestoredData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_CONNECTION_RESTORED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_CONNECTION_RESTORED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create ConnectionRestoredData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class DisplayAreaChangedData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_DISPLAY_AREA_CHANGED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_DISPLAY_AREA_CHANGED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create DisplayAreaChangedData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]
        self.__display_area = DisplayArea(data["display_area"])

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp

    @property
    def display_area(self):
        '''Gets the new display area as a DisplayArea object.
        '''
        return self.__display_area


class GazeOutputFrequencyChangedData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_GAZE_OUTPUT_FREQUENCY_CHANGED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_GAZE_OUTPUT_FREQUENCY_CHANGED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create GazeOutputFrequencyChangedData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]
        self.__gaze_output_frequency = data["gaze_output_frequency"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp

    @property
    def gaze_output_frequency(self):
        '''Gets the new output frequency.
        '''
        return self.__gaze_output_frequency


class TrackBoxChangedData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_TRACK_BOX_CHANGED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_TRACK_BOX_CHANGED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create TrackBoxChangedData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class CalibrationChangedData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_CALIBRATION_CHANGED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_CALIBRATION_CHANGED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create CalibrationChangedData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class EyeTrackingModeChangedData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_EYE_TRACKING_MODE_CHANGED callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_EYE_TRACKING_MODE_CHANGED
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create EyeTrackingModeChangedData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp


class DeviceFaultsData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_DEVICE_FAULTS callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_DEVICE_FAULTS
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create DeviceFaultsData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]
        self.__faults = data["faults"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp

    @property
    def faults(self):
        '''Gets the new faults as a comma separeted string.
        '''
        return self.__faults


class DeviceWarningsData:
    '''Provides data the @ref EYETRACKER_NOTIFICATION_DEVICE_WARNINGS callback.

    You will get data of this type when you subscribe to @ref EYETRACKER_NOTIFICATION_DEVICE_WARNINGS
    with EyeTracker.subscribe_to.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create DeviceWarningssData objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]
        self.__warnings = data["warnings"]

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp

    @property
    def warnings(self):
        '''Gets the new warnings as a comma separeted string.
        '''
        return self.__warnings
