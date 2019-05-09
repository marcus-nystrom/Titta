def execute(eyetracker):
     if eyetracker is not None:
         eye_images(eyetracker)
     else:
         print("No tracker with eye images to run example.")
 
 
 # <BeginExample>
 
import sys
import base64
import time
import tobii_research as tr
 
if sys.version_info[0] == 3:
    from tkinter import Tk, PhotoImage
else:
    from Tkinter import Tk, PhotoImage
 
 
def gaze_callback(gaze):
    pass
    
def eye_image_callback(eye_image_data):
    print("System time: {0}, Device time {1}, Camera id {2}".format(eye_image_data['system_time_stamp'],
                                         eye_image_data['device_time_stamp'],
                                         eye_image_data['camera_id']))
 
    image = PhotoImage(data=base64.standard_b64encode(eye_image_data['image_data']))
    print("{0} width {1}, height {2}".format(image, image.width(), image.height()))
 
 
def eye_images(eyetracker):
    root = Tk()
    print("Subscribing to eye images for eye tracker with serial number {0}.".format(eyetracker.serial_number))
    
    eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_callback, as_dictionary=True)
    eyetracker.subscribe_to(tr.EYETRACKER_EYE_IMAGES, eye_image_callback, as_dictionary=True)
 
    # Wait for eye images.
    time.sleep(4)
 
    eyetracker.unsubscribe_from(tr.EYETRACKER_EYE_IMAGES, eye_image_callback)
    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_callback)
    
    print("Unsubscribed from eye images.")
    root.destroy()
 # <EndExample>
 
 
eyetracker = tr.EyeTracker('tet-tcp://169.254.10.20')
print("Address: " + eyetracker.address)
print("Serial number: " + eyetracker.serial_number)
execute(eyetracker)