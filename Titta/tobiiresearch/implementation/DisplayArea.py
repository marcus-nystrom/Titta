class DisplayArea(object):
    '''Represents the corners in space of the active display area, and its size.
    BottomRight, Height, and Width are calculated values.

    Return value from EyeTracker.get_display_area.
    '''

    def __init__(self, display_area):
        if ((not isinstance(display_area, dict) or
             not isinstance(display_area["bottom_left"], tuple) or
             not isinstance(display_area["top_left"], tuple) or
             not isinstance(display_area["top_right"], tuple))):
            raise ValueError(
                """DisplayArea requires a dictionary with the coordinates of the
                display area (top_left, top_right, bottom_left).""")

        self.__bottom_left = tuple(float(_) for _ in display_area["bottom_left"])
        self.__top_left = tuple(float(_) for _ in display_area["top_left"])
        self.__top_right = tuple(float(_) for _ in display_area["top_right"])

        # bottom_right = top_right - top_left + bottom_left
        self.__bottom_right = tuple(a - b + c for a, b, c in zip(self.__top_right, self.__top_left, self.__bottom_left))
        # norm of (top_left - top_right)
        self.__width = (sum((a - b)**2 for a, b in zip(self.__top_left, self.__top_right)))**0.5
        # norm of (top_left - bottom_left)
        self.__height = (sum((a - b)**2 for a, b in zip(self.__top_left, self.__bottom_left)))**0.5

    def __eq__(self, other):
        return (type(self) == type(other) and self.__bottom_left == other.bottom_left and
                self.__top_left == other.top_left and
                self.__top_right == other.top_right)

    @property
    def bottom_left(self):
        '''Gets the bottom left corner of the active display area as a three valued tuple.
        '''
        return self.__bottom_left

    @property
    def bottom_right(self):
        '''Gets the bottom left corner of the active display area as a three valued tuple.
        '''
        return self.__bottom_right

    @property
    def height(self):
        '''Gets the height in millimeters of the active display area.
        '''
        return self.__height

    @property
    def top_left(self):
        '''Gets the top left corner of the active display area as a three valued tuple.
        '''
        return self.__top_left

    @property
    def top_right(self):
        '''Gets the top right corner of the active display area as a three valued tuple.
        '''
        return self.__top_right

    @property
    def width(self):
        '''Gets the width in millimeters of the active display area.
        '''
        return self.__width
