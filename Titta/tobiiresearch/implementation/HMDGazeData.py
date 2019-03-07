from tobiiresearch.implementation.GazeData import PupilData


class HMDPupilPosition(object):
    '''Provides properties for the HMD pupil position.

    A HMDPupilPosition object is used as value for HMDEyeData.pupil_position.
    '''

    def __init__(self,
                 pupil_position_in_tracking_area,
                 pupil_position_validity):
        if ((not isinstance(pupil_position_in_tracking_area, tuple) or
             not isinstance(pupil_position_validity, int))):
            raise ValueError(
                "You shouldn't create HMDPupilPosition objects yourself.")

        self.__position_in_tracking_area = pupil_position_in_tracking_area
        self.__validity = bool(pupil_position_validity)

    @property
    def position_in_tracking_area(self):
        '''Gets the (normalizes) 2D coordinates that describes the pupil's position
        in the HMD's tracking area as a two valued tuple.
        '''
        return self.__position_in_tracking_area

    @property
    def validity(self):
        '''Gets the validity of the pupil position data.

        True if valid. False if invalid.
        '''
        return self.__validity


class HMDGazeOrigin(object):
    '''Provides properties for the HMD gaze origin

    A HMDGazeOrigin object is used as value for HMDEyeData.gaze_origin.
    '''

    def __init__(self,
                 gaze_origin_position_in_hmd_coordinates,
                 gaze_origin_validity):
        if ((not isinstance(gaze_origin_position_in_hmd_coordinates, tuple) or
             not isinstance(gaze_origin_validity, int))):
            raise ValueError(
                "You shouldn't create HMDGazeOrigin objects yourself.")

        self.__position_in_hmd_coordinates = gaze_origin_position_in_hmd_coordinates
        self.__validity = bool(gaze_origin_validity)

    @property
    def position_in_hmd_coordinates(self):
        '''Gets the 3D coordinates that describes the gaze origin in mm as a three valued tuple.
        '''
        return self.__position_in_hmd_coordinates

    @property
    def validity(self):
        '''Gets the validity of the HMD gaze origin data.

        True if valid. False if invalid.
        '''
        return self.__validity


class HMDGazeDirection(object):
    '''Provides properties for the HMD gaze direction.

    A HMDGazeDirection object is used as value for HMDEyeData.gaze_direction.
    '''

    def __init__(self,
                 gaze_direction_unit_vector,
                 gaze_direction_validity):
        if ((not isinstance(gaze_direction_unit_vector, tuple) or
             not isinstance(gaze_direction_validity, int))):
            raise ValueError(
                "You shouldn't create HMDGazeDirection objects yourself.")

        self.__unit_vector = gaze_direction_unit_vector
        self.__validity = bool(gaze_direction_validity)

    @property
    def unit_vector(self):
        '''Gets the 3D unit vector that describes the gaze direction as a three valued tuple.
        '''
        return self.__unit_vector

    @property
    def validity(self):
        '''Gets the validity of the gaze direction data.

        True if valid. False if invalid.
        '''
        return self.__validity


class HMDEyeData(object):
    '''Provides properties for the eye data when gotten from an HMD based device.

    HMDEyeData objects are used as values for HMDGazeData.left_eye and HMDGazeData.right_eye.
    '''

    def __init__(self,
                 gaze_direction_unit_vector,
                 gaze_direction_validity,
                 gaze_origin_position_in_hmd_coordinates,
                 gaze_origin_validity,
                 pupil_diameter,
                 pupil_validity,
                 pupil_position_in_tracking_area,
                 pupil_position_validity):
        self.__gaze_direction = HMDGazeDirection(gaze_direction_unit_vector, gaze_direction_validity)

        self.__gaze_origin = HMDGazeOrigin(gaze_origin_position_in_hmd_coordinates, gaze_origin_validity)

        self.__pupil = PupilData(pupil_diameter, pupil_validity)

        self.__pupil_position = HMDPupilPosition(pupil_position_in_tracking_area, pupil_position_validity)

    @property
    def gaze_direction(self):
        '''Gets the gaze direction data as a HMDGazeDirection object.
        '''
        return self.__gaze_direction

    @property
    def pupil(self):
        '''Gets the pupil data as a PupilData object.
        '''
        return self.__pupil

    @property
    def gaze_origin(self):
        '''Gets the gaze origin data as a HMDGazeOrigin object.
        '''
        return self.__gaze_origin

    @property
    def pupil_position(self):
        '''Gets the pupil position in HMD track box as a HMDGazeOrigin object.
        '''
        return self.__pupil_position


class HMDGazeData(object):
    '''Provides data for the HMD gaze.

    You will get an object of this type to the callback you supply in EyeTracker.subscribe_to with
    @ref EYETRACKER_HMD_GAZE_DATA.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create HMDGazeData objects yourself.")

        self.__left = HMDEyeData(
            data["left_gaze_direction_unit_vector"],
            data["left_gaze_direction_validity"],
            data["left_gaze_origin_position_in_hmd_coordinates"],
            data["left_gaze_origin_validity"],
            data["left_pupil_diameter"],
            data["left_pupil_validity"],
            data["left_pupil_position_in_tracking_area"],
            data["left_pupil_position_validity"])

        self.__right = HMDEyeData(
            data["right_gaze_direction_unit_vector"],
            data["right_gaze_direction_validity"],
            data["right_gaze_origin_position_in_hmd_coordinates"],
            data["right_gaze_origin_validity"],
            data["right_pupil_diameter"],
            data["right_pupil_validity"],
            data["right_pupil_position_in_tracking_area"],
            data["right_pupil_position_validity"])

        self.__device_time_stamp = data["device_time_stamp"]

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def left_eye(self):
        '''Gets the gaze data for the left eye as an HMDEyeData object.
        '''
        return self.__left

    @property
    def right_eye(self):
        '''Gets the gaze data for the right eye as an HMDEyeData object.
        '''
        return self.__right

    @property
    def device_time_stamp(self):
        '''Gets the time stamp according to the eye tracker's internal clock.
        '''
        return self.__device_time_stamp

    @property
    def system_time_stamp(self):
        '''Gets the time stamp according to the computer's internal clock.
        '''
        return self.__system_time_stamp
