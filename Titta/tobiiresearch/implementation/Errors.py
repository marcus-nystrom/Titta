
from tobiiresearch.internal.Enum import _enum


@_enum
class __TobiiProStatus(object):
    ok = 0

    fatal_error = 1
    initialize_failed = 2
    terminate_failed = 3
    localbrowser_create_failed = 4
    localbrowser_poll_failed = 5
    zeroconfbrowser_create_failed = 6
    zeroconfbrowser_poll_failed = 7
    filebrowser_create_failed = 8
    filebrowser_poll_failed = 9
    invalid_parameter = 10
    invalid_operation = 11
    uninitialized = 12
    out_of_bounds = 13
    display_area_not_valid = 14
    buffer_too_small = 15
    not_initialized = 16
    already_initialized = 17
    saved_license_failed_to_apply = 18

    se_internal = 200
    se_insufficient_license = 201
    se_not_supported = 202
    se_not_available = 203
    se_connection_failed = 204
    se_timed_out = 205
    se_allocation_failed = 206
    se_already_initialized = 207
    se_not_initialized = 208
    se_invalid_parameter = 209
    se_calibration_already_started = 210
    se_calibration_not_started = 211
    se_already_subscribed = 212
    se_not_subscribed = 213
    se_operation_failed = 214
    se_conflicting_api_instances = 215
    se_calibration_busy = 216
    se_callback_in_progress = 217
    se_too_many_subscribers = 218
    se_unknown = 1000


class EyeTrackerConnectionFailedError(Exception):
    '''Is thrown when connection to an eye tracker is lost or could not be established.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerFeatureNotSupportedError(Exception):
    '''Is thrown when a feature is not supported for an eye tracker.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerInternalError(Exception):
    '''Is thrown on internal errors in the API.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerInvalidOperationError(Exception):
    '''Is thrown when the user tries to do an invalid operation.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerLicenseError(Exception):
    '''Is thrown when there is an insufficient license level when using a restricted feature.

    The solution is to contact Tobii customer support and request a suitable license file.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerOperationFailedError(Exception):
    '''Is thrown when an eye tracker cannot execute a requested operation.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerUnavailableError(Exception):
    '''Is thrown if the eye tracker is unavailable.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerDisplayAreaNotValidError(Exception):
    '''Is thrown if the display area isn't valid.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class EyeTrackerSavedLicenseFailedToApplyError(Exception):
    '''Is thrown if the eye tracker has a license saved, but it failed to apply.

    If you get this error, the license on the device has probably expired.
    '''

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def _on_error_raise_exception(value):
    status = __TobiiProStatus(value)

    if status == __TobiiProStatus.ok or status == __TobiiProStatus.se_timed_out:
        return  # Does not indicate an error
    elif status == __TobiiProStatus.invalid_operation:
        raise EyeTrackerInvalidOperationError("The operation is invalid in this context. " + str(status))
    elif status == __TobiiProStatus.out_of_bounds:
        raise ValueError("The value is out of bounds. " + str(status))
    elif status == __TobiiProStatus.invalid_parameter:
        raise ValueError("An invalid parameter has been sent to the API. " + str(status))
    elif status == __TobiiProStatus.saved_license_failed_to_apply:
        raise EyeTrackerSavedLicenseFailedToApplyError("The license saved on the device failed to apply. " +
                                                       "It has probably expired." + str(status))
    elif status == __TobiiProStatus.se_insufficient_license:
        raise EyeTrackerLicenseError("Insufficient license level when using a restricted feature. " + str(status))
    elif status == __TobiiProStatus.se_not_supported:
        raise EyeTrackerFeatureNotSupportedError("The feature is not supported by the eye tracker. " + str(status))
    elif status == __TobiiProStatus.se_not_available:
        raise EyeTrackerUnavailableError("No device is available. " + str(status))
    elif status == __TobiiProStatus.se_connection_failed:
        raise EyeTrackerConnectionFailedError("The connection to the eye tracker failed. " + str(status))
    elif status == __TobiiProStatus.display_area_not_valid:
        raise EyeTrackerDisplayAreaNotValidError("The display area is not valid. " + str(status))
    elif status == __TobiiProStatus.se_calibration_already_started:
        raise EyeTrackerInvalidOperationError("The calibration has already been started. " + str(status))
    elif status == __TobiiProStatus.se_calibration_not_started:
        raise EyeTrackerInvalidOperationError("Calibration has not been started. " + str(status))
    elif status == __TobiiProStatus.se_already_subscribed:
        raise EyeTrackerInvalidOperationError("Eye tracker internal error. Already subscribed. " + str(status))
    elif status == __TobiiProStatus.se_not_subscribed:
        raise EyeTrackerInvalidOperationError("Eye tracker internal error. Not subscribed. " + str(status))
    elif status == __TobiiProStatus.se_operation_failed:
        raise EyeTrackerOperationFailedError("The operation failed. " + str(status))
    elif status == __TobiiProStatus.se_conflicting_api_instances:
        raise EyeTrackerOperationFailedError("Conflicting api instances. " + str(status))
    elif status == __TobiiProStatus.se_calibration_busy:
        raise EyeTrackerOperationFailedError("Calibration busy. " + str(status))
    elif status == __TobiiProStatus.se_callback_in_progress:
        raise EyeTrackerOperationFailedError("Callback in progress. " + str(status))
    elif status == __TobiiProStatus.se_too_many_subscribers:
        raise EyeTrackerOperationFailedError("Too many users subscribed to a stream. " + str(status))
    elif status == __TobiiProStatus.se_invalid_parameter:
        raise EyeTrackerInternalError("An invalid parameter has been sent to the API. " + str(status))
    elif status == __TobiiProStatus.se_allocation_failed:
        raise EyeTrackerInternalError("Memory could not be allocated. " + str(status))
    elif status == __TobiiProStatus.se_already_initialized or status == __TobiiProStatus.already_initialized:
        raise EyeTrackerInternalError("API has already been initialized. " + str(status))
    elif status == __TobiiProStatus.se_not_initialized or status == __TobiiProStatus.not_initialized:
        raise EyeTrackerInternalError("API has not been initialized. " + str(status))
    elif status == __TobiiProStatus.buffer_too_small:
        raise EyeTrackerInternalError("The buffer is too small. " + str(status))
    else:
        raise EyeTrackerInternalError("An unspecified internal error occurred. " + str(status))
