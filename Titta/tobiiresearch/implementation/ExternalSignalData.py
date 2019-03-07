##
# Indicates that the value sent to the eye tracker has changed.
#
# Value for ExternalSignalData.change_type
EXTERNAL_SIGNAL_CHANGE_TYPE_VALUE_CHANGED = "external_signal_change_type_value_changed"

##
# Indicates that the value is the initial value, and is received when starting a subscription.
#
# Value for ExternalSignalData.change_type
EXTERNAL_SIGNAL_CHANGE_TYPE_INITIAL_VALUE = "external_signal_change_type_initial_value"

##
# Indicates that there has been a connection lost and now it is restored and the value is the current value.
#
# Value for ExternalSignalData.change_type
EXTERNAL_SIGNAL_CHANGE_TYPE_CONNECTION_RESTORED = "external_signal_change_type_connection_restored"


class ExternalSignalData(object):
    '''Provides data for external signal.

    You will get an object of this type to the callback you supply in EyeTracker.subscribe_to with
    @ref EYETRACKER_EXTERNAL_SIGNAL.
    '''

    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create ExternalSignalData objects yourself.")

        self.__value = data["value"]
        self.__change_type = data["change_type"]
        self.__device_time_stamp = data["device_time_stamp"]
        self.__system_time_stamp = data["system_time_stamp"]

    @property
    def value(self):
        '''Gets the value of the external signal port on the eye tracker (on supported models).
        '''
        return self.__value

    @property
    def change_type(self):
        '''Gets the type of value change.

        Valid values are @ref EXTERNAL_SIGNAL_CHANGE_TYPE_VALUE_CHANGED, @ref EXTERNAL_SIGNAL_CHANGE_TYPE_INITIAL_VALUE
        and @ref EXTERNAL_SIGNAL_CHANGE_TYPE_CONNECTION_RESTORED.
        '''
        return self.__change_type

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
