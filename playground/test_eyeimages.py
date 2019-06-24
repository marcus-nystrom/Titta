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
import numpy as np
from PIL import Image
em = []

EYE_IMAGE_SIZE_PIX = (175, 496)
EYE_IMAGE_SIZE_PIX_FULL_FRAME = (512, 640)
 
if sys.version_info[0] == 3: # if Python 3:
    #from io import StringIO
    from io import BytesIO as StringIO
else: # else Python 2
    from cStringIO import StringIO
 
def get_eye_image(im_info):
    ''' Converts an eye image returned from the Tobii SDK to
    a numpy array
    
    Args:
        im_info - dict with info about image as returned by the SDK
        
    Returns:
        nparr
        
    '''
    temp_im = StringIO(im_info['image_data'])
    tim = Image.open(temp_im)
    nparr = np.array(list(tim.getdata()))
    

    
    # Full frame or zoomed in image
    if im_info['image_type'] == 'eye_image_type_full':
        eye_image_size = EYE_IMAGE_SIZE_PIX_FULL_FRAME
        #tim.save("temp_full.gif","GIF")
    elif im_info['image_type'] == 'eye_image_type_cropped':
        eye_image_size = EYE_IMAGE_SIZE_PIX
        #tim.save("temp_small.gif","GIF")
    else:
        eye_image_size = [512, 512]
        nparr_t = np.zeros((512* 512))
        nparr_t[:len(nparr)] = nparr
        nparr = nparr_t.copy()
    nparr = np.reshape(nparr, eye_image_size)
    nparr = np.rot90(nparr, k = 2)
    nparr = (nparr / float(nparr.max()) * 2.0) - 1
    
    #print(im_info['image_type'], nparr.shape)
   
    return nparr 

def gaze_callback(gaze):
    pass
    
def eye_image_callback(eye_image_data):
    print("System time: {0}, Device time {1}, Camera id {2}".format(eye_image_data['system_time_stamp'],
                                         eye_image_data['device_time_stamp'],
                                         eye_image_data['camera_id']))
 
    #print(eye_image_data['image_data'])
    
    np_image = get_eye_image(eye_image_data)
    em.append(np_image)

 
 
def eye_images(eyetracker):
    
    print("Subscribing to eye images for eye tracker with serial number {0}.".format(eyetracker.serial_number))
    
    eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA, gaze_callback, as_dictionary=True)
    eyetracker.subscribe_to(tr.EYETRACKER_EYE_IMAGES, eye_image_callback, as_dictionary=True)
 
    # Wait for eye images.
    time.sleep(5)
 
    eyetracker.unsubscribe_from(tr.EYETRACKER_EYE_IMAGES, eye_image_callback)
    eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, gaze_callback)
    
    print("Unsubscribed from eye images.")
    
 # <EndExample>
 
 
eyetracker = tr.EyeTracker('tet-tcp://169.254.5.182')
print("Address: " + eyetracker.address)
print("Serial number: " + eyetracker.serial_number)
execute(eyetracker)


for e in em:
    print("width {}, height {}".format(e.shape, e.shape))
   
print(len(em))   
