##
# @namespace tobii_research All functionality is in this module.

from tobiiresearch.implementation.EyeTracker import EyeTracker, CAPABILITY_CAN_DO_HMD_BASED_CALIBRATION
from tobiiresearch.implementation.Calibration import CALIBRATION_STATUS_SUCCESS, CALIBRATION_STATUS_FAILURE
from tobiiresearch.implementation.Calibration import _calibration_status
from tobiiresearch.interop import interop


class HMDCalibrationResult(object):
    '''Represents the result of the HMD based calibration.

    Return value from HMDBasedCalibration.compute_and_apply.
    '''

    def __init__(self, status):
        if (not isinstance(status, str) or
            (status != CALIBRATION_STATUS_FAILURE and
             status != CALIBRATION_STATUS_SUCCESS)):
            raise ValueError(
                "You shouldn't create CalibrationResult objects yourself.")

        self.__status = status

    @property
    def status(self):
        '''Gets the status of the calculation.

        @ref CALIBRATION_STATUS_SUCCESS on success.
        @ref CALIBRATION_STATUS_FAILURE on failure.
        '''
        return self.__status


class HMDBasedCalibration(object):
    '''Represents the calibration data used by the eye tracker.
    '''

    def __init__(self, eyetracker):
        '''Initialize a new HMDBasedCalibration object from an existing EyeTracker object.
        '''
        if not isinstance(eyetracker, EyeTracker):
            raise ValueError("A HMDBasedCalibration object must be initialized with an EyeTracker.")
        if CAPABILITY_CAN_DO_HMD_BASED_CALIBRATION not in eyetracker.device_capabilities:
            raise ValueError("A HMDBasedCalibration object must be initialized with an EyeTracker\
                            that supports HMD based calibration.")

        self.__core_eyetracker = eyetracker._EyeTracker__core_eyetracker

    def enter_calibration_mode(self):
        '''Enters the calibration mode and the eye tracker is made ready for
        collecting data and calculating new calibrations.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>hmd_calibration.py</CodeExample>
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
        <CodeExample>hmd_calibration.py</CodeExample>
        Raises:
        EyeTrackerConnectionFailedError
        EyeTrackerFeatureNotSupportedError
        EyeTrackerInvalidOperationError
        EyeTrackerLicenseError
        EyeTrackerInternalError
        '''
        interop.calibration_leave_calibration_mode(self.__core_eyetracker)

    def collect_data(self, x, y, z):
        '''Starts collecting data for a calibration point.
        The argument used is the point the calibration user is assumed to be looking at
        and is given in the HMD coordinate system.

        See @ref find_all_eyetrackers or EyeTracker.__init__ on how to create an EyeTracker object.
        <CodeExample>hmd_calibration.py</CodeExample>
        Args:
        x: x coordinate in the HMD coordinate system.
        y: y coordinate in the HMD coordinate system.
        z: z coordinate in the HMD coordinate system.

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
        x, y, z = (float(_) for _ in (x, y, z))
        return _calibration_status[interop.hmd_based_calibration_collect_data(self.__core_eyetracker, x, y, z)]

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
        interop_result = interop.hmd_based_calibration_compute_and_apply(self.__core_eyetracker)

        return HMDCalibrationResult(_calibration_status[interop_result[0]])
