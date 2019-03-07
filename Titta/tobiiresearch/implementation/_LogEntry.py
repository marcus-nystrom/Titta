

class _LogEntry(object):
    def __init__(self, data):
        if not isinstance(data, dict):
            raise ValueError("You shouldn't create _LogEntry objects yourself.")

        self.__system_time_stamp = data["system_time_stamp"]
        self.__source = data["source"]
        self.__level = data["level"]
        self.__message = data["message"]

    @property
    def system_time_stamp(self):
        return self.__system_time_stamp

    @property
    def source(self):
        return self.__source

    @property
    def level(self):
        return self.__level

    @property
    def message(self):
        return self.__message
