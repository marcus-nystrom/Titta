##
# @namespace tobii_research All functionality is in this module.

from tobiiresearch.implementation.EyeTracker import EyeTracker, CAPABILITY_CAN_DO_MONOCULAR_CALIBRATION
from tobiiresearch.implementation.EyeTracker import CAPABILITY_CAN_DO_SCREEN_BASED_CALIBRATION
from tobiiresearch.implementation.Calibration import CALIBRATION_STATUS_FAILURE
from tobiiresearch.implementation.Calibration import _calibration_status
from tobiiresearch.implementation.ScreenBasedCalibration import CalibrationEyeData, CalibrationSample
from tobiiresearch.implementation.ScreenBasedCalibration import CalibrationPoint, CalibrationResult
from tobiiresearch.interop import interop


##
# Indicates that left eye was selected.
#
# Value for the input of ScreenBasedMonocularCalibration methods
SELECTED_EYE_LEFT = "selected_eye_left"

##
# Indicates that right eye was selected.
#
# Value for the input of ScreenBasedMonocularCalibration methods
SELECTED_EYE_RIGHT = "selected_eye_right"

##
# Indicates that both eyes were selected.
#
# Value for the input of ScreenBasedMonocularCalibration methods
SELECTED_EYE_BOTH = "selected_eye_both"

_selected_eye = (SELECTED_EYE_LEFT, SELECTED_EYE_RIGHT, SELECTED_EYE_BOTH)


class ScreenBasedMonocularCalibration(object):
    '''	 Provides methods and properties for managing monocular and bi-monocular calibrations for screen
    based eye trackers. This type of calibration is not supported by all eye trackers.
    Check the DeviceCapabilities of the eye tracker first!
    '''

    def __init__(self, eyetracker):
        '''Initialize a new ScreenBasedMonocularCalibration object from an existing EyeTracker object.
        '''
        if not isinstance(eyetracker, EyeTracker):
            raise ValueError("A ScreenBasedMonocularCalibration object must be initialized with an EyeTracker.")
        if CAPABILITY_CAN_DO_MONOCULAR_CALIBRATION not in eyetracker.device_capabilities or\
                CAPABILITY_CAN_DO_SCREEN_BASED_CALIBRATION not in eyetracker.device_capabilities:
            raise ValueError("A ScreenBased_Monocular_Calibration object must be initialized with an EyeTracker\
                            that supports screen based and monocular calibration.")

        self.__core_eyetracker = eyetracker._EyeTracker__core_eyetracker

    def enter_calibration_mode(self):
        '''Enters the calibration mode and the eye tracker is made ready for
        collecting data and calculating new calibrations.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>monocular_calibration.py</CodeExample>
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
        <CodeExample>monocular_calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        interop.calibration_leave_calibration_mode(self.__core_eyetracker)

    def collect_data(self, x, y, eye_to_calibrate):
        '''	Collects data for a calibration point for the selected eye(s).
        The point argument is the point on the display the user is assumed to be looking at and is given in the active
        display area coordinate system.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>monocular_calibration.py</CodeExample>
        Args:
        x: Normalized x coordinate on the active display area.
        y: Normalized y coordinate on the active display area.
        eye_to_calibrate: Selected eye for data collection.

        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError

        Returns:
        @ref CALIBRATION_STATUS_SUCCESS on success for both eyes.
        @ref CALIBRATION_STATUS_SUCCESS_LEFT_EYE on success for the left_eye.
        @ref CALIBRATION_STATUS_SUCCESS_RIGHT_EYE on success for the right eye.
        @ref CALIBRATION_STATUS_FAILURE on failure.
        '''
        x, y = (float(_) for _ in (x, y))

        if eye_to_calibrate not in _selected_eye:
            raise ValueError("eye_to_calibrate argument is invalid!")
        selected_eye = _selected_eye.index(eye_to_calibrate)

        status = interop.screen_based_monocular_calibration_collect_data(self.__core_eyetracker, x, y, selected_eye)

        # 214 - Operation failed error code
        if status == 214:
            return CALIBRATION_STATUS_FAILURE

        return _calibration_status[status]

    def discard_data(self, x, y, eye_to_calibrate):
        '''Removes the collected data for the specified eye(s) and calibration point.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>monocular_calibration.py</CodeExample>
        Args:
        x: Normalized x coordinate on the active display area.
        y: Normalized y coordinate on the active display area.
        eye_to_calibrate: Selected eye for data discarding.

        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        x, y = (float(_) for _ in (x, y))
        if eye_to_calibrate not in _selected_eye:
            raise ValueError("eye_to_calibrate argument is invalid!")
        selected_eye = _selected_eye.index(eye_to_calibrate)
        interop.screen_based_monocular_calibration_discard_data(self.__core_eyetracker, x, y, selected_eye)

    def compute_and_apply(self):
        '''Uses the collected data and tries to compute calibration parameters.
        If the calculation is successful, the result is applied to the eye tracker. If there is insufficient data to
        compute a new calibration or if the collected data is not good enough then calibration fails and will not
        be applied.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>monocular_calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError

        Returns:
        A CalibrationResult object.
        '''
        interop_result = interop.screen_based_monocular_calibration_compute_and_apply(self.__core_eyetracker)

        # 214 - Operation failed error code
        if interop_result[0] == 214:
            status = CALIBRATION_STATUS_FAILURE
        else:
            status = _calibration_status[interop_result[0]]

        if (status == CALIBRATION_STATUS_FAILURE):
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

        return CalibrationResult(status, tuple(calibration_points))
