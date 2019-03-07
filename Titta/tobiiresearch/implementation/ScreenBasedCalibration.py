##
# @namespace tobii_research All functionality is in this module.

from tobiiresearch.implementation.EyeTracker import EyeTracker, CAPABILITY_CAN_DO_SCREEN_BASED_CALIBRATION
from tobiiresearch.implementation.Calibration import CALIBRATION_STATUS_SUCCESS, CALIBRATION_STATUS_FAILURE
from tobiiresearch.implementation.Calibration import CALIBRATION_STATUS_SUCCESS_LEFT_EYE
from tobiiresearch.implementation.Calibration import CALIBRATION_STATUS_SUCCESS_RIGHT_EYE
from tobiiresearch.implementation.Calibration import VALIDITY_VALID_AND_USED, VALIDITY_INVALID_AND_NOT_USED
from tobiiresearch.implementation.Calibration import VALIDITY_VALID_BUT_NOT_USED
from tobiiresearch.implementation.Calibration import _calibration_status
from tobiiresearch.interop import interop


class CalibrationEyeData(object):
    '''Represents the calibration sample data collected for one eye.

    CalibrationEyeData objects are used as values for CalibrationSample.left_eye and CalibrationSample.right_eye.
    '''

    def __init__(self, position_on_display_area, validity):
        if ((not isinstance(position_on_display_area, tuple) or
             not isinstance(validity, int) or
             not (validity == -1 or validity == 0 or validity == 1))):
            raise ValueError(
                "You shouldn't create CalibrationEyeData objects yourself.")

        # This must match TobiiProCalibrationEyeValidity in tobii_pro_calibration.h
        validities = {-1: VALIDITY_INVALID_AND_NOT_USED, 0: VALIDITY_VALID_BUT_NOT_USED, 1: VALIDITY_VALID_AND_USED}

        self.__position_on_display_area = position_on_display_area
        self.__validity = validities[validity]

    @property
    def position_on_display_area(self):
        '''Gets the eye sample position on the active display area as a two valued tuple.
        '''
        return self.__position_on_display_area

    @property
    def validity(self):
        '''Gets information about if the sample was used or not in the calculation.

        Valid values are @ref VALIDITY_INVALID_AND_NOT_USED, @ref VALIDITY_VALID_BUT_NOT_USED
        and @ref VALIDITY_VALID_AND_USED.
        '''
        return self.__validity


class CalibrationSample(object):
    '''Represents the data collected for a calibration sample.

    A tuple of CalibrationSample objects are used as value for CalibrationPoint.calibration_samples.
    '''

    def __init__(self, left_eye, right_eye):
        if ((not isinstance(left_eye, CalibrationEyeData) or
             not isinstance(right_eye, CalibrationEyeData))):
            raise ValueError(
                "You shouldn't create CalibrationSample objects yourself.")

        self.__left_eye = left_eye
        self.__right_eye = right_eye

    @property
    def left_eye(self):
        '''Gets the calibration sample data for the left eye as a CalibrationEyeData object.
        '''
        return self.__left_eye

    @property
    def right_eye(self):
        '''Gets the calibration sample data for the right eye as a CalibrationEyeData object.
        '''
        return self.__right_eye


class CalibrationPoint(object):
    '''Represents the calibration point and its collected calibration samples.

    A tuple of CalibrationPoint objects are used as value for CalibrationResult.calibration_points.
    '''

    def __init__(self, position_on_display_area, calibration_samples):
        if ((not isinstance(position_on_display_area, tuple) or
             not isinstance(calibration_samples, tuple))):
            raise ValueError(
                "You shouldn't create CalibrationPoint objects yourself.")

        self.__position_on_display_area = position_on_display_area
        self.__calibration_samples = calibration_samples

    @property
    def position_on_display_area(self):
        '''Gets the position of the calibration point on the active display area as a two valued tuple.
        '''
        return self.__position_on_display_area

    @property
    def calibration_samples(self):
        '''Gets a tuple of collected CalibrationSample samples for the calibration.
        '''
        return self.__calibration_samples


class CalibrationResult(object):
    '''Represents the result of the calculated calibration.

    Return value from ScreenBasedCalibration.compute_and_apply.
    '''

    def __init__(self, status, calibration_points):
        if (not isinstance(status, str) or
            not isinstance(calibration_points, tuple) or
            (status not in [CALIBRATION_STATUS_FAILURE, CALIBRATION_STATUS_SUCCESS, CALIBRATION_STATUS_SUCCESS_LEFT_EYE,
                            CALIBRATION_STATUS_SUCCESS_RIGHT_EYE])):
            raise ValueError(
                "You shouldn't create CalibrationResult objects yourself.")

        self.__status = status
        self.__calibration_points = calibration_points

    @property
    def status(self):
        '''Gets the status of the calculation.

        @ref CALIBRATION_STATUS_SUCCESS on success for both eyes.
        @ref CALIBRATION_STATUS_SUCCESS_LEFT_EYE on success for the left_eye.
        @ref CALIBRATION_STATUS_SUCCESS_RIGHT_EYE on success for the right eye.
        @ref CALIBRATION_STATUS_FAILURE on failure.
        '''
        return self.__status

    @property
    def calibration_points(self):
        '''Gets a tuple of CalibrationPoint objects and their collected calibration samples.
        '''
        return self.__calibration_points


class ScreenBasedCalibration(object):
    '''Provides methods and properties for managing calibrations for screen based eye trackers.
    '''

    def __init__(self, eyetracker):
        '''Initialize a new ScreenBasedCalibration object from an existing EyeTracker object.
        '''
        if not isinstance(eyetracker, EyeTracker):
            raise ValueError("A ScreenBasedCalibration object must be initialized with an EyeTracker.")
        if CAPABILITY_CAN_DO_SCREEN_BASED_CALIBRATION not in eyetracker.device_capabilities:
            raise ValueError("A ScreenBasedCalibration object must be initialized with an EyeTracker\
                            that supports screen based calibration.")

        self.__core_eyetracker = eyetracker._EyeTracker__core_eyetracker

    def enter_calibration_mode(self):
        '''Enters the calibration mode and the eye tracker is made ready for
        collecting data and calculating new calibrations.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        interop.calibration_enter_calibration_mode(self.__core_eyetracker)

    def leave_calibration_mode(self):
        '''Leaves the calibration mode.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        interop.calibration_leave_calibration_mode(self.__core_eyetracker)

    def collect_data(self, x, y):
        '''Starts collecting data for a calibration point.

        The argument used is the point the calibration user is assumed to be looking at
        and is given in the active display area coordinate system.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>calibration.py</CodeExample>
        Args:
        x: Normalized x coordinate on the active display area.
        y: Normalized y coordinate on the active display area.

        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError

        Returns:
        @ref CALIBRATION_STATUS_SUCCESS on success.
        @ref CALIBRATION_STATUS_FAILURE on failure.
        '''
        x, y = (float(_) for _ in (x, y))
        return _calibration_status[interop.screen_based_calibration_collect_data(self.__core_eyetracker, x, y)]

    def discard_data(self, x, y):
        '''Removes the collected data associated with a specific calibration point.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>calibration.py</CodeExample>
        Args:
        x: Normalized x coordinate on the active display area.
        y: Normalized y coordinate on the active display area.

        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        x, y = (float(_) for _ in (x, y))
        interop.screen_based_calibration_discard_data(self.__core_eyetracker, x, y)

    def compute_and_apply(self):
        '''Uses the data in the temporary buffer and tries to compute calibration parameters.

        If the call is successful, the data is copied from the temporary buffer to the active buffer.
        If there is insufficient data to compute a new calibration or if the collected data is not
        good enough then an exception will be raised.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError

        Returns:
        A CalibrationResult object.
        '''
        interop_result = interop.screen_based_calibration_compute_and_apply(self.__core_eyetracker)

        status = _calibration_status[interop_result[0]]
        if (status != CALIBRATION_STATUS_SUCCESS):
            return CalibrationResult(status, ())

        position = None
        calibration_points = []
        calibration_samples = []
        for interop_point in interop_result[1]:
            cur_position = interop_point.position

            if position is not None and cur_position != position:
                calibration_points.append(CalibrationPoint(position, tuple(calibration_samples)))
                calibration_samples = []

            calibration_samples.append(CalibrationSample(
                CalibrationEyeData(interop_point.left_sample_position, interop_point.left_validity),
                CalibrationEyeData(interop_point.right_sample_position, interop_point.right_validity)))

            position = cur_position

        calibration_points.append(CalibrationPoint(position, tuple(calibration_samples)))

        return CalibrationResult(CALIBRATION_STATUS_SUCCESS, tuple(calibration_points))
