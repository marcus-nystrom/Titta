##
# The license is tampered.
#
# Value for FailedLicense.validation_result
LICENSE_TAMPERED = "license_tampered"

##
# The application signature is invalid.
#
# Value for FailedLicense.validation_result
LICENSE_INVALID_APPLICATION_SIGNATURE = "license_invalid_application_signature"

##
# The application has not been signed.
#
# Value for FailedLicense.validation_result
LICENSE_NONSIGNED_APPLICATION = "license_nonsigned_application"

##
# The license has expired.
#
# Value for FailedLicense.validation_result
LICENSE_EXPIRED = "license_expired"

##
# The license is not yet valid.
#
# Value for FailedLicense.validation_result
LICENSE_PREMATURE = "license_premature"

##
# The process name does not match the license.
#
# Value for FailedLicense.validation_result
LICENSE_INVALID_PROCESS_NAME = "license_invalid_process_name"

##
# The serial number does not match the license.
#
# Value for FailedLicense.validation_result
LICENSE_INVALID_SERIAL_NUMBER = "license_invalid_serial_number"

##
# The model does not match the license.
#
# Value for FailedLicense.validation_result
LICENSE_INVALID_MODEL = "license_invalid_model"

##
# The license validation returned an unexpected result.
#
# Value for FailedLicense.validation_result
LICENSE_UNKNOWN_ERROR = "license_unknown_error"


class LicenseKey(object):
    '''Represents the eye tracker license key.

    A list of LicenseKey object should be sent to EyeTracker.apply_licenses.
    '''

    def __init__(self, key_string):
        '''Supply a license from a license file as bytes.
        '''
        if not isinstance(key_string, bytes):
            raise ValueError("LicenseKey objects must be created with a string!")
        self.__key_string = key_string

    @property
    def key_string(self):
        '''Gets the string that is the actual license key.
        '''
        return self.__key_string


class FailedLicense(object):
    '''Represents a license that failed.

    A tuple of FailedLicense objects will be returned from EyeTracker.apply_licenses.
    '''

    __first_failed_code = 1
    __last_failed_code = 9

    def __init__(self, key_string, validation_result):
        if ((not isinstance(key_string, bytes) or
             not isinstance(validation_result, int) or
             validation_result < FailedLicense.__first_failed_code or
             validation_result > FailedLicense.__last_failed_code)):
            raise ValueError(
                "You shouldn't create FailedLicense objects yourself!")

        # This must match TobiiProLicenseValidationResult in tobii_pro_eyetracker.h
        validation_results = ("", LICENSE_TAMPERED, LICENSE_INVALID_APPLICATION_SIGNATURE,
                              LICENSE_NONSIGNED_APPLICATION, LICENSE_EXPIRED, LICENSE_PREMATURE,
                              LICENSE_INVALID_PROCESS_NAME, LICENSE_INVALID_SERIAL_NUMBER, LICENSE_INVALID_MODEL,
                              LICENSE_UNKNOWN_ERROR)

        self.__license_key = LicenseKey(key_string)
        self.__validation_result = validation_results[validation_result]

    @property
    def license_key(self):
        '''Gets the license key as a LicenseKey object.
        '''
        return self.__license_key

    @property
    def validation_result(self):
        '''Gets the result of the license validation.

        Valid values are @ref LICENSE_TAMPERED, @ref LICENSE_INVALID_APPLICATION_SIGNATURE,
        @ref LICENSE_NONSIGNED_APPLICATION, @ref LICENSE_EXPIRED, @ref LICENSE_PREMATURE,
        @ref LICENSE_INVALID_PROCESS_NAME, @ref LICENSE_INVALID_SERIAL_NUMBER, @ref LICENSE_INVALID_MODEL
        and @ref LICENSE_UNKNOWN_ERROR
        '''
        return self.__validation_result
