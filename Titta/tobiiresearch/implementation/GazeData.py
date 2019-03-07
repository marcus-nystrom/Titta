class GazeOrigin(object):
    '''Provides properties for the gaze origin.

    A GazeOrigin object is used as value for EyeData.gaze_origin.
    '''

    def __init__(self,
                 gaze_origin_position_in_user_coordinates,
                 gaze_origin_position_in_track_box_coordinates,
                 gaze_origin_validity):
        if ((not isinstance(gaze_origin_position_in_user_coordinates, tuple) or
             not isinstance(gaze_origin_position_in_track_box_coordinates, tuple) or
             not isinstance(gaze_origin_validity, int))):
            raise ValueError(
                "You shouldn't create GazeOrigin objects yourself.")

        self.__position_in_user_coordinates = gaze_origin_position_in_user_coordinates
        self.__position_in_track_box_coordinates = gaze_origin_position_in_track_box_coordinates
        self.__validity = bool(gaze_origin_validity)

    @property
    def position_in_user_coordinates(self):
        '''Gets the gaze origin position in 3D in the user coordinate system as a three valued tuple.
        '''
        return self.__position_in_user_coordinates

    @property
    def position_in_track_box_coordinates(self):
        '''Gets normalized gaze origin in track box coordinate system as a three valued tuple.
        '''
        return self.__position_in_track_box_coordinates

    @property
    def validity(self):
        '''Gets the validity of the gaze origin data.

        True if valid. False if invalid.
        '''
        return self.__validity


class PupilData(object):
    '''Provides properties for the pupil data.

    A PupilData object is used as value for EyeData.pupil.
    '''

    def __init__(self,
                 pupil_diameter,
                 pupil_validity):
        if ((not isinstance(pupil_diameter, float) or
             not isinstance(pupil_validity, int))):
            raise ValueError(
                "You shouldn't create PupilData objects yourself.")

        self.__diameter = pupil_diameter
        self.__validity = bool(pupil_validity)

    @property
    def diameter(self):
        '''Gets the diameter of the pupil in millimeters.
        '''
        return self.__diameter

    @property
    def validity(self):
        '''Gets the validity of the pupil data.

        True if valid. False if invalid.
        '''
        return self.__validity


class GazePoint(object):
    '''Provides properties for the gaze point.

    A GazePoint object is used as value for EyeData.gaze_point.
    '''

    def __init__(self,
                 gaze_point_position_on_display_area,
                 gaze_point_position_in_user_coordinates,
                 gaze_point_validity):
        if ((not isinstance(gaze_point_position_on_display_area, tuple) or
             not isinstance(gaze_point_position_in_user_coordinates, tuple) or
             not isinstance(gaze_point_validity, int))):
            raise ValueError(
                "You shouldn't create GazePointData objects yourself.")

        self.__position_on_display_area = gaze_point_position_on_display_area
        self.__position_in_user_coordinates = gaze_point_position_in_user_coordinates
        self.__validity = bool(gaze_point_validity)

    @property
    def position_on_display_area(self):
        '''Gets the normalized gaze point position in 2D on the active display area as a two valued tuple.
        '''
        return self.__position_on_display_area

    @property
    def position_in_user_coordinates(self):
        '''Gets the gaze point position in 3D in the user coordinate system as a three valued tuple.
        '''
        return self.__position_in_user_coordinates

    @property
    def validity(self):
        '''Gets the validity of the gaze point data.

        True if valid. False if invalid.
        '''
        return self.__validity


class EyeData(object):
    '''Provides properties for the eye data.

    EyeData objects are used as values for GazeData.left_eye and GazeData.right_eye.
    '''

    def __init__(self,
                 gaze_point_position_on_display_area,
                 gaze_point_position_in_user_coordinates,
                 gaze_point_validity,
                 pupil_diameter,
                 pupil_validity,
                 gaze_origin_position_in_user_coordinates,
                 gaze_origin_position_in_track_box_coordinates,
                 gaze_origin_validity):
        self.__gaze_point = GazePoint(gaze_point_position_on_display_area,
                                      gaze_point_position_in_user_coordinates,
                                      gaze_point_validity)

        self.__pupil_data = PupilData(pupil_diameter, pupil_validity)

        self.__gaze_origin = GazeOrigin(gaze_origin_position_in_user_coordinates,
                                        gaze_origin_position_in_track_box_coordinates,
                                        gaze_origin_validity)

    @property
    def gaze_point(self):
        '''Gets the gaze point data as a GazePoint object.
        '''
        return self.__gaze_point

    @property
    def pupil(self):
        '''Gets the pupil data as a PupilData object.
        '''
        return self.__pupil_data

    @property
    def gaze_origin(self):
        '''Gets the gaze origin data as a GazeOrigin object.
        '''
        return self.__gaze_origin


class GazeData(object):
    '''Provides data for gaze.

    You will get an object of this type to the callback you supply in EyeTracker.subscribe_to with
    @ref EYETRACKER_GAZE_DATA.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create GazeData objects yourself.")

        self.__left = EyeData(
            data["left_gaze_point_on_display_area"],
            data["left_gaze_point_in_user_coordinate_system"],
            data["left_gaze_point_validity"],
            data["left_pupil_diameter"],
            data["left_pupil_validity"],
            data["left_gaze_origin_in_user_coordinate_system"],
            data["left_gaze_origin_in_trackbox_coordinate_system"],
            data["left_gaze_origin_validity"])

        self.__right = EyeData(
            data["right_gaze_point_on_display_area"],
            data["right_gaze_point_in_user_coordinate_system"],
            data["right_gaze_point_validity"],
            data["right_pupil_diameter"],
            data["right_pupil_validity"],
            data["right_gaze_origin_in_user_coordinate_system"],
            data["right_gaze_origin_in_trackbox_coordinate_system"],
            data["right_gaze_origin_validity"])

        self.__device_time_stamp = data["device_time_stamp"]

        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def left_eye(self):
        '''Gets the gaze data for the left eye as an EyeData object.
        '''
        return self.__left

    @property
    def right_eye(self):
        '''Gets the gaze data for the right eye as an EyeData object.
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
