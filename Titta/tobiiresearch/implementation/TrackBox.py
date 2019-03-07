class TrackBox(object):
    '''Represents the eight corners in user coordinate system that together forms the track box.

    Returned by EyeTracker.get_track_box
    '''

    ##
    # @cond EXCLUDE
    def __init__(self, coordinates):
        if ((not isinstance(coordinates, dict) or
             not isinstance(coordinates["back_lower_left"], tuple) or
             not isinstance(coordinates["back_lower_right"], tuple) or
             not isinstance(coordinates["back_upper_left"], tuple) or
             not isinstance(coordinates["back_upper_right"], tuple) or
             not isinstance(coordinates["front_lower_left"], tuple) or
             not isinstance(coordinates["front_lower_right"], tuple) or
             not isinstance(coordinates["front_upper_left"], tuple) or
             not isinstance(coordinates["front_upper_right"], tuple))):
            raise ValueError(
                "You shouldn't create TrackBox objects yourself.")

        self.__back_lower_left = coordinates["back_lower_left"]
        self.__back_lower_right = coordinates["back_lower_right"]
        self.__back_upper_left = coordinates["back_upper_left"]
        self.__back_upper_right = coordinates["back_upper_right"]
        self.__front_lower_left = coordinates["front_lower_left"]
        self.__front_lower_right = coordinates["front_lower_right"]
        self.__front_upper_left = coordinates["front_upper_left"]
        self.__front_upper_right = coordinates["front_upper_right"]
    ##
    # @endcond

    @property
    def back_lower_left(self):
        '''Gets the back lower left corner of the track box.
        '''
        return self.__back_lower_left

    @property
    def back_lower_right(self):
        '''Gets the back lower right corner of the track box.
        '''
        return self.__back_lower_right

    @property
    def back_upper_left(self):
        '''Gets the back upper left corner of the track box.
        '''
        return self.__back_upper_left

    @property
    def back_upper_right(self):
        '''Gets the back upper right corner of the track box.
        '''
        return self.__back_upper_right

    @property
    def front_lower_left(self):
        '''Gets the front lower left corner of the track box.
        '''
        return self.__front_lower_left

    @property
    def front_lower_right(self):
        '''Gets the front lower right corner of the track box.
        '''
        return self.__front_lower_right

    @property
    def front_upper_left(self):
        '''Gets the front upper left corner of the track box.
        '''
        return self.__front_upper_left

    @property
    def front_upper_right(self):
        '''Gets the front upper right corner of the track box.
        '''
        return self.__front_upper_right
