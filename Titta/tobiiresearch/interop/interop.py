'''
Created on 29 juli 2016

'''

import atexit
import threading
import sys

if sys.version_info[0] == 3:
    from tobiiresearch.interop.python3 import tobii_research_interop
else:
    from tobiiresearch.interop.python2 import tobii_research_interop

from tobiiresearch.implementation.DisplayArea import DisplayArea
from tobiiresearch.implementation.HMDLensConfiguration import HMDLensConfiguration
from tobiiresearch.implementation.TrackBox import TrackBox
from tobiiresearch.implementation.Errors import EyeTrackerOperationFailedError
from tobiiresearch.implementation.Errors import _on_error_raise_exception
from tobiiresearch.implementation.License import FailedLicense

_tobii_pro_calibration_failure = 0
_tobii_pro_calibration_success = 1
_tobii_pro_calibration_success_left_eye = 2
_tobii_pro_calibration_success_right_eye = 3

_tobii_pro_selected_eye_left = 0
_tobii_pro_selected_eye_right = 1
_tobii_pro_selected_eye_both = 2


class TobiiProResultCallback(object):
    def __init__(self):
        self.__has_result = threading.Event()
        self.__result = None

    def get_result(self):
        self.__has_result.wait()
        return self.__result

    def __call__(self, result):
        self.__result = result
        self.__has_result.set()


def __call_function(function_name, arguments):
    result_callback = TobiiProResultCallback()
    call_result = tobii_research_interop.call_function(function_name, arguments, result_callback)
    _on_error_raise_exception(call_result)
    return result_callback.get_result()


def __shutdown():
    __call_function("terminate", ())
    tobii_research_interop.cleanup()


tobii_research_interop.startup()
atexit.register(__shutdown)


class TobiiProEyeTrackerData(object):
    def __init__(self, dictionary):
        self.address = dictionary["address"]
        self.device_name = dictionary["device_name"]
        self.serial_number = dictionary["serial_number"]
        self.model = dictionary["model"]
        self.firmware_version = dictionary["firmware_version"]
        self.device_capabilities = dictionary["device_capabilities"]
        self.core_eyetracker = dictionary["core_eyetracker"]


class TobiiProCalibrationPoint(object):
    def __init__(self, dictionary):
        self.position = dictionary["position"]
        self.left_sample_position = dictionary["left_sample_position"]
        self.left_validity = dictionary["left_validity"]
        self.right_sample_position = dictionary["right_sample_position"]
        self.right_validity = dictionary["right_validity"]


class TobiiProCallback(object):
    def __init__(self, core_eyetracker, stream_name, user_callback):
        self.__core_eyetracker = core_eyetracker
        self.__stream_name = stream_name
        self.__user_callback = user_callback

    def __call__(self, dictionary_with_data):
        try:
            self.__user_callback(dictionary_with_data)
        except Exception as e:
            if len(self.__stream_name) > 0:
                __call_function("report_stream_error",
                                (self.__core_eyetracker,
                                 "User {0} callback raised exception {1}. Message: {2}".
                                 format(self.__stream_name, type(e).__name__, str(e))))


__callbacks = {}
__callback_lock = threading.RLock()
__subscribe_lock = threading.RLock()


def __subscription_callback(subscription_type, core_eyetracker, data):
    global __callbacks
    global __callback_lock
    callbacks = []
    with __callback_lock:
        for callback in __callbacks.get((subscription_type, core_eyetracker), {}).values():
            callbacks.append(callback)
    for callback in callbacks:
        callback(data)


def find_all_eyetrackers():
    result = __call_function("find_all_eyetrackers", ())
    _on_error_raise_exception(result[0])
    return [TobiiProEyeTrackerData(x) for x in result[1]]


def get_device(address):
    result = __call_function("get_device", (address,))
    _on_error_raise_exception(result[0])
    return TobiiProEyeTrackerData(result[1])


def get_device_data(core_eyetracker):
    result = __call_function("get_device_data", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return TobiiProEyeTrackerData(result[1])


def subscribe_to(subscription_type, stream_name, tracker, core_eyetracker, callback):
    global __callbacks
    global __callback_lock
    global __subscribe_lock
    with __subscribe_lock:
        subscription_tuple = (subscription_type, core_eyetracker)
        with __callback_lock:
            __callbacks.setdefault(subscription_tuple, {})[tracker] =\
                TobiiProCallback(core_eyetracker, stream_name, callback)
            count = len(__callbacks[subscription_tuple])
        if count == 1:
            status = __call_function("subscribe_to", (subscription_type, core_eyetracker,
                                                      lambda x: __subscription_callback(subscription_type,
                                                                                        core_eyetracker, x)))
            _on_error_raise_exception(status[0])


def unsubscribe_from(subscription_type, tracker, core_eyetracker):
    global __callbacks
    global __callback_lock
    global __subscribe_lock
    with __subscribe_lock:
        subscription_tuple = (subscription_type, core_eyetracker)
        unsubscribe = False
        with __callback_lock:
            if subscription_tuple in __callbacks:
                if tracker in __callbacks[subscription_tuple]:
                    del __callbacks[subscription_tuple][tracker]
                if len(__callbacks[subscription_tuple]) == 0:
                    del __callbacks[subscription_tuple]
                    unsubscribe = True
        if unsubscribe:
            status = __call_function("unsubscribe_from", (subscription_type, core_eyetracker))
            _on_error_raise_exception(status[0])


def apply_licenses(core_eyetracker, licenses):
    result = __call_function("apply_licenses", (core_eyetracker, licenses))
    _on_error_raise_exception(result[0])
    return tuple([FailedLicense(key, validation) for key, validation in zip(licenses, result[1]) if validation != 0])


def clear_applied_licenses(core_eyetracker):
    status = __call_function("clear_applied_licenses", (core_eyetracker,))
    _on_error_raise_exception(status[0])


def get_all_gaze_output_frequencies(core_eyetracker):
    result = __call_function("get_all_gaze_output_frequencies", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return tuple(result[1])


def get_gaze_output_frequency(core_eyetracker):
    result = __call_function("get_gaze_output_frequency", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return result[1]


def set_gaze_output_frequency(core_eyetracker, frame_rate):
    status = __call_function("set_gaze_output_frequency", (core_eyetracker, frame_rate))
    _on_error_raise_exception(status[0])


def get_all_eye_tracking_modes(core_eyetracker):
    result = __call_function("get_all_eye_tracking_modes", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return tuple(result[1])


def get_eye_tracking_mode(core_eyetracker):
    result = __call_function("get_eye_tracking_mode", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return result[1]


def set_eye_tracking_mode(core_eyetracker, eye_tracking_mode):
    status = __call_function("set_eye_tracking_mode", (core_eyetracker, eye_tracking_mode))
    _on_error_raise_exception(status[0])


def calibration_enter_calibration_mode(core_eyetracker):
    status = __call_function("calibration_enter_calibration_mode", (core_eyetracker,))
    _on_error_raise_exception(status[0])


def calibration_leave_calibration_mode(core_eyetracker):
    status = __call_function("calibration_leave_calibration_mode", (core_eyetracker,))
    _on_error_raise_exception(status[0])


def screen_based_calibration_collect_data(core_eyetracker, x, y):
    status = __call_function("screen_based_calibration_collect_data", (core_eyetracker, x, y))
    try:
        _on_error_raise_exception(status[0])
        return _tobii_pro_calibration_success
    except EyeTrackerOperationFailedError:
        pass
    return _tobii_pro_calibration_failure


def screen_based_monocular_calibration_collect_data(core_eyetracker, x, y, eye_to_calculate):
    result = __call_function("screen_based_monocular_calibration_collect_data",
                             (core_eyetracker, x, y, eye_to_calculate))
    try:
        _on_error_raise_exception(result[0])
    except EyeTrackerOperationFailedError:
        return result[0]
    calibration_status = _tobii_pro_calibration_failure
    if result[1] == _tobii_pro_selected_eye_left:
        calibration_status = _tobii_pro_calibration_success_left_eye
    elif result[1] == _tobii_pro_selected_eye_right:
        calibration_status = _tobii_pro_calibration_success_right_eye
    elif result[1] == _tobii_pro_selected_eye_both:
        calibration_status = _tobii_pro_calibration_success
    return calibration_status


def screen_based_calibration_discard_data(core_eyetracker, x, y):
    status = __call_function("screen_based_calibration_discard_data", (core_eyetracker, x, y))
    _on_error_raise_exception(status[0])


def screen_based_monocular_calibration_discard_data(core_eyetracker, x, y, eye_to_calculate):
    status = __call_function("screen_based_monocular_calibration_discard_data",
                             (core_eyetracker, x, y, eye_to_calculate))
    _on_error_raise_exception(status[0])


def screen_based_calibration_compute_and_apply(core_eyetracker):
    status = __call_function("calibration_compute_and_apply", (core_eyetracker,))
    try:
        _on_error_raise_exception(status[0])
        result = __call_function("screen_based_calibration_get_calibration_points", (core_eyetracker,))
        _on_error_raise_exception(result[0])
        return (_tobii_pro_calibration_success, [TobiiProCalibrationPoint(x) for x in result[1]])
    except EyeTrackerOperationFailedError:
        pass
    return (_tobii_pro_calibration_failure,)


def screen_based_monocular_calibration_compute_and_apply(core_eyetracker):
    status = __call_function("monocular_calibration_compute_and_apply", (core_eyetracker,))
    try:
        _on_error_raise_exception(status[0])
        result = __call_function("screen_based_calibration_get_calibration_points", (core_eyetracker,))
        _on_error_raise_exception(result[0])
        calibration_status = _tobii_pro_calibration_failure
        if status[1] == _tobii_pro_selected_eye_left:
            calibration_status = _tobii_pro_calibration_success_left_eye
        elif status[1] == _tobii_pro_selected_eye_right:
            calibration_status = _tobii_pro_calibration_success_right_eye
        elif status[1] == _tobii_pro_selected_eye_both:
            calibration_status = _tobii_pro_calibration_success
        return (calibration_status, [TobiiProCalibrationPoint(x) for x in result[1]])
    except EyeTrackerOperationFailedError:
        return (_tobii_pro_calibration_failure,)


def hmd_based_calibration_collect_data(core_eyetracker, x, y, z):
    status = __call_function("hmd_based_calibration_collect_data", (core_eyetracker, x, y, z))
    try:
        _on_error_raise_exception(status[0])
        return _tobii_pro_calibration_success
    except EyeTrackerOperationFailedError:
        pass
    return _tobii_pro_calibration_failure


def hmd_based_calibration_compute_and_apply(core_eyetracker):
    status = __call_function("calibration_compute_and_apply", (core_eyetracker,))
    try:
        _on_error_raise_exception(status[0])
        result = __call_function("hmd_based_calibration_get_calibration_points", (core_eyetracker,))
        _on_error_raise_exception(result[0])
        return (_tobii_pro_calibration_success, [TobiiProCalibrationPoint(x) for x in result[1]])
    except EyeTrackerOperationFailedError:
        pass
    return (_tobii_pro_calibration_failure,)


def calibration_retrieve(core_eyetracker):
    result = __call_function("calibration_retrieve", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return result[1]


def calibration_apply(core_eyetracker, data):
    if not isinstance(data, bytes):
        raise ValueError("Calibration data must be applied with a bytes object.")
    status = __call_function("calibration_apply", (core_eyetracker, data))
    _on_error_raise_exception(status[0])


def get_display_area(core_eyetracker):
    result = __call_function("get_display_area", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return DisplayArea(result[1])


def set_display_area(core_eyetracker, display_area):
    if not isinstance(display_area, DisplayArea):
        raise ValueError("Display area must be a DisplayArea object.")
    status = __call_function("set_display_area", (core_eyetracker,
                                                  display_area.top_left,
                                                  display_area.top_right,
                                                  display_area.bottom_left))
    _on_error_raise_exception(status[0])


def get_hmd_lens_configuration(core_eyetracker):
    result = __call_function("get_hmd_lens_configuration", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return HMDLensConfiguration(result[1]['left'], result[1]['right'])


def set_hmd_lens_configuration(core_eyetracker, lens_configuration):
    if not isinstance(lens_configuration, HMDLensConfiguration):
        raise ValueError("Lens configuration must be a HMDLensConfiguration object.")
    status = __call_function("set_hmd_lens_configuration", (core_eyetracker,
                                                            lens_configuration.left,
                                                            lens_configuration.right))
    _on_error_raise_exception(status[0])


def get_track_box(core_eyetracker):
    result = __call_function("get_track_box", (core_eyetracker,))
    _on_error_raise_exception(result[0])
    return TrackBox(result[1])


def get_system_time_stamp():
    result = __call_function("get_system_time_stamp", ())
    _on_error_raise_exception(result[0])
    return result[1]


def get_sdk_version():
    result = __call_function("get_sdk_version", ())
    _on_error_raise_exception(result[0])
    return result[1]


def set_device_name(core_eyetracker, device_name):
    status = __call_function("set_device_name", (core_eyetracker, device_name))
    _on_error_raise_exception(status[0])
