class TimeSynchronizationData(object):
    '''Provides data for the time synchronization callback.

    You will get an object of this type to the callback you supply in EyeTracker.subscribe_to with
    @ref EYETRACKER_TIME_SYNCHRONIZATION_DATA.
    '''

    ##
    # @cond EXCLUDE
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create TimeSynchronizationData objects yourself.")

        self.__system_request_time_stamp = data["system_request_time_stamp"]
        self.__device_time_stamp = data["device_time_stamp"]
        self.__system_response_time_stamp = data["system_response_time_stamp"]
    ##
    # @endcond

    @property
    def system_request_time_stamp(self):
        '''Gets the time stamp when the computer sent the request to the eye tracker.
        '''
        return self.__system_request_time_stamp

    @property
    def device_time_stamp(self):
        '''Gets the time stamp when the eye tracker received the request, according to the eye tracker's clock.
        '''
        return self.__device_time_stamp

    @property
    def system_response_time_stamp(self):
        '''Gets the time stamp when the computer received the response from the eye tracker.
        '''
        return self.__system_response_time_stamp
