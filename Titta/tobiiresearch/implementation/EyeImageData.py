##
# Indicates that the eye tracker could not identify the eyes, and the image is the full image.
#
# Value for EyeImageData.image_type
EYE_IMAGE_TYPE_FULL = "eye_image_type_full"

##
# Indicates that the image is cropped and shows the eyes.
#
# Value for EyeImageData.image_type
EYE_IMAGE_TYPE_CROPPED = "eye_image_type_cropped"

##
# Indicates an unknown image type.
#
# Value for EyeImageData.image_type
EYE_IMAGE_TYPE_UNKNOWN = "eye_image_type_unknown"


class EyeImageData(object):
    '''Provides data for the eye image callback.

    You will get an object of this type to the callback you supply in EyeTracker.subscribe_to with
    @ref EYETRACKER_EYE_IMAGES.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create EyeImageData objects yourself.")

        self.__device_time_stamp = data["device_time_stamp"]
        self.__system_time_stamp = data["system_time_stamp"]
        self.__camera_id = data["camera_id"]
        self.__image_type = data["image_type"]
        self.__image_data = data["image_data"]

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

    @property
    def camera_id(self):
        '''Gets which camera generated the image.
        '''
        return self.__camera_id

    @property
    def image_type(self):
        '''Gets the type of eye image as a string.

        Valid values are @ref EYE_IMAGE_TYPE_FULL and @ref EYE_IMAGE_TYPE_CROPPED.
        '''
        return self.__image_type

    @property
    def image_data(self):
        '''Gets the image data sent by the eye tracker in GIF format.
        '''
        return self.__image_data
