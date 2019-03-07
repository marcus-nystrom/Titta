STREAM_ERROR_SOURCE_USER = "stream_error_source_user"
STREAM_ERROR_SOURCE_STREAM_PUMP = "stream_error_source_stream_pump"
STREAM_ERROR_SOURCE_SUBSCRIPTION_GAZE_DATA = "stream_error_source_subscription_gaze_data"
STREAM_ERROR_SOURCE_SUBSCRIPTION_EXTERNAL_SIGNAL = "stream_error_source_subscription_external_signal"
STREAM_ERROR_SOURCE_SUBSCRIPTION_TIME_SYNCHRONIZATION_DATA = \
    "stream_error_source_subscription_time_synchronization_data"
STREAM_ERROR_SOURCE_SUBSCRIPTION_EYE_IMAGE = "stream_error_source_subscription_eye_image"
STREAM_ERROR_SOURCE_SUBSCRIPTION_NOTIFICATION = "stream_error_source_subscription_notification"

STREAM_ERROR_CONNECTION_LOST = "stream_error_connection_lost"
STREAM_ERROR_INSUFFICIENT_LICENSE = "stream_error_insufficient_license"
STREAM_ERROR_NOT_SUPPORTED = "stream_error_not_supported"
STREAM_ERROR_TOO_MANY_SUBSCRIBERS = "stream_error_too_many_subscribers"
STREAM_ERROR_INTERNAL_ERROR = "stream_error_internal_error"
STREAM_ERROR_USER_ERROR = "stream_error_user_error"


class StreamErrorData(object):
    '''Provides information about a stream error.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create StreamErrorData objects yourself.")

        self._system_time_stamp = data["system_time_stamp"]
        self._error = data["error"]
        self._source = data["source"]
        self._message = data["message"]

    @property
    def system_time_stamp(self):
        return self._system_time_stamp

    @property
    def source(self):
        return self._source

    @property
    def error(self):
        return self._error

    @property
    def message(self):
        return self._message
