##
# @namespace tobii_research All functionality is in this module.

##
# Indicates that the calibration process failed.
#
# Value for CalibrationResult.status and return value of collect_data
CALIBRATION_STATUS_FAILURE = "calibration_status_failure"

##
# Indicates that the calibration process succeeded for both eyes.
#
# Value for CalibrationResult.status and return value of collect_data
CALIBRATION_STATUS_SUCCESS = "calibration_status_success"

##
# Indicates that the calibration process succeeded for the left eye.
#
# Value for CalibrationResult.status and return value of collect_data
CALIBRATION_STATUS_SUCCESS_LEFT_EYE = "calibration_status_success_left_eye"

##
# Indicates that the calibration process succeeded for the right eye.
#
# Value for CalibrationResult.status and return value of collect_data
CALIBRATION_STATUS_SUCCESS_RIGHT_EYE = "calibration_status_success_right_eye"

##
# The eye tracking failed or the calibration eye data is invalid.
#
# Value for CalibrationEyeData.validity
VALIDITY_INVALID_AND_NOT_USED = "validity_invalid_and_not_used"

##
# Eye tracking was successful, but the calibration eye data was not used in calibration e.g. gaze was too far away.
#
# Value for CalibrationEyeData.validity
VALIDITY_VALID_BUT_NOT_USED = "validity_valid_but_not_used"

##
# The calibration eye data was valid and used in calibration.
#
# Value for CalibrationEyeData.validity
VALIDITY_VALID_AND_USED = "validity_valid_and_used"

# This must match _tobii_pro_calibration_failure and _tobii_pro_calibration_success in interop.py
_calibration_status = (CALIBRATION_STATUS_FAILURE, CALIBRATION_STATUS_SUCCESS, CALIBRATION_STATUS_SUCCESS_LEFT_EYE,
                       CALIBRATION_STATUS_SUCCESS_RIGHT_EYE)
