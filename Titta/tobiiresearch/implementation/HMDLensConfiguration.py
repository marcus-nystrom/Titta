class HMDLensConfiguration(object):
    '''	Represents the lens configuration of the HMD device.

    Return value from EyeTracker.get_hmd_lens_configuration.
    '''

    def __init__(self, left=None, right=None):
        if ((not isinstance(left, tuple) or
             not isinstance(right, tuple))):
            raise ValueError(
                "HMDLensConfiguration requires the position in millimeters of both left and right lenses.")

        self.__left = tuple(float(_) for _ in left)
        self.__right = tuple(float(_) for _ in right)

    @property
    def left(self):
        '''The point in HMD coordinate system that defines the position of the left lens (in millimeters).
        '''
        return self.__left

    @property
    def right(self):
        '''The point in HMD coordinate system that defines the position of the right lens (in millimeters).
        '''
        return self.__right
