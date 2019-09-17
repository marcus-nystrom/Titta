# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 08:50:57 2019

@author: Marcus
"""

from titta.TalkToProLab import TalkToProLab
import numpy as np

media_name = 'c.mp4'
media_type = 'video'

 # Read image as binary, each element in 'f' represents a byte
with open(media_name, "rb") as imageFile:
    f = imageFile.read()
      
# Prepare Server to receive media content (image or video) as binary data          
media_size = len(f)
        

#%% Talk to Pro Lab  
ttl = TalkToProLab()


ttl.upload_media(media_name, media_type)
