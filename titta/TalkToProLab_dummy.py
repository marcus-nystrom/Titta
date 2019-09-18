# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:37:06 2018

@author: Marcus
ToDo: upload information in chunks of 64 KB
"""

status_codes = {0: 'Operation successful',
                100: 'Bad request',
                101: 'Invalid parameter',
                102: 'Operation was unsuccessful',
                103: 'Operation cannot be executed in current state',
                104: 'Access to the service is forbidden',
                105: 'Authorization during connection to a service has not been provided',
                201: 'Recording finalization failed'}

class TalkToProLab_dummy(object):
    """ A dummy class for talking to Tobii Pro Lab. 
    """     
    
    #%%
    def __init__(self):
        
        print('Dummy class init')

    #%%
    def get_api_version(self):
        ''' Get version of api 
         Available for all Services. 
        request:
        {"operation": "GetApiVersion"}
        
        response:
        {"operation": "GetApiVersion",
        "status_code": 0,
        "version": "1.0"}        
        '''
        print('get_api_version')

        return {'operation': 'GetApiVersion', 'status_code': 0, 'version': 'dummy'}        
        
    #%%          
    def get_time_stamp(self):
        ''' Clock API
        request:
        {"operation": "GetTimestamp"}
        
        response:
        {"operation": "GetTimestamp",
        "status_code": 0,
        "timestamp": "128606207528320000"}
        
        Note: timestamp in microseconds
        '''
        
        print('get_time_stamp')

        return {"operation": "GetTimestamp", "status_code": 0, "timestamp": "dummy_ts"}  
    #%%
    def add_participant(self, participant_name):
        ''' Project data API
        request:
        {"operation": "AddParticipant",
        "participant_name": "John Doe"}
        
        response:
        {"operation": "AddParticipant",
        "status_code": 0,
        "participant_id": "2A86C895-F8B6-4786-8C4B-CB889C3449F1"}
        '''   
        
        print('add_participant')

        return {"operation": "AddParticipant", "status_code": 0, 
                "participant_id": "dummy_participant_id"}    
        
    #%%
    def get_project_info(self):
        ''' Project data API
        request:
        { "operation": "GetProjectInfo"}
        
        response:
        {"operation": "GetProjectInfo",
        "status_code": 0,
        "project_id": "8928673C-B1D5-4941-A592-39597742B1E5",
        "project_name": "SocialInteraction test"}
        '''    
        print('get_project_info')

        return {"operation": "GetProjectInfo",
                "status_code": 0,
                "project_id": "dummy_project_id",
                "project_name": "dummy_name"}       
    
    #%%
    def find_participant(self, participant_name):
        ''' Finds whether participant_name already has been uploaded to lab
        
        Args:
            participant_name - string with participant name (e.g., P04)
        
        Returns:
            exists - boolean 
        '''
        
        print('find_participant')
        
        return False
    
    #%% 
    def list_participants(self):
        ''' Project data API
        Returns information about the participants of the currently opened project in Pro Lab.
        
        request:
        {
        "operation": "ListParticipants"
        } 
        response:
        {
        "operation": "ListParticipants",
        "status_code": 0,
        "participant_list": [{
        "participant_name": "John Doe",
        "participant_id": "2A86C895-F8B6-4786-8C4B-CB889C3449F1"
        }]
        }        
        '''
        
        print('find_participant')
        
        return {
                "operation": "ListParticipants",
                "status_code": 0,
                "participant_list": [{
                        "participant_name": "dummy_participant",
                        "participant_id": "dummy_participant_id"
                        }]
                }          
    
    #%% 
    def list_media(self):
        ''' Project data API
        Returns information about the uploaded media of the currently opened project in Pro Lab.
        
        request:
        {
        "operation": "ListMedia"
        }        
        
        response:
        {
        "operation": "ListMedia",
        "status_code": 0,
        "media_list": [{
            "media_name": "CuteCats",
            "media_id": "b2548e0e-4056-4d36-a4f5-86b3194866f7",
            "mime_type": "image/jpeg",
            "media_size": 3536263,
            "width": 2512,
            "height": 1884,
            "duration": 0,
        },
        {
            "media_name": "CuteCatsRunningAround",
            "media_id": "21BA2272-473D-478F-9E23-A1FA8ABFF65D",
            "md5_checksum": "0dbc22fddaff860ac1bf0d092c909d4e",
            "mime_type": "video/mp4",
            "media_size": 3536263,
            "width": 640,
            "height": 480,
            "duration": 5.250
        }]
        }   
        '''
        
        print('list_media')
        
        return {
                "operation": "ListMedia",
                "status_code": 0,
                "media_list": [{
                    "media_name": "dummy_media_name_1",
                    "media_id": "dummy_media_id_1",
                    "mime_type": "image/jpeg",
                    "media_size": 3536263,
                    "width": 2512,
                    "height": 1884,
                    "duration": 0,
                                }]
                }     
       
        
    #%%
    def find_media(self, media_name):
        ''' Finds whether media_name already has been uploaded to lab
        
        Args:
            media_name - string with media name (e.g., image.png)
        
        Returns:
            exists - boolean 
        '''
        
        print('find_media')
        
        return False
        
    #%%
    def upload_media(self, media_name, media_type):
        ''' 
        
        Prepares Server to receive media content (image or video) as binary data.
        The response will be sent once immediately after request and once at the end of the upload
        operation, regardless the reason of upload operation completion. After a success response to an
        initial request, chunked binary data is expected to be sent.
        The whole operation of receiving media could be ended due to the following reasons:
            
        1. The Server received an amount of binary data equal to media_size parameter.
        The operation has been aborted by  
        2. UploadMediaAbort request.
        3. The time between the Server received two consecutive chunks exceeded timeout.  
            -> status 103
            
        Args:
            media_name - name of media.ext (e.g., image.png)
            media_type - 'image' or 'video'
            
        
        
        -----        
        Project data API
        request:
        {"operation": "UploadMedia",
        "mime_type": "video/mp4",
        "media_name": "SocialInteractionDemoVideo.mp4",
        "media_size": "37201059"}
        
        response:
        {"operation": "UploadMedia",
        "status_code": 0}
        '''   
        
        # File extension
        file_ext = media_name.split('.')[1]
        
        # Check that media format is supported
        assert(len([i for i in ['bmp','jpeg', 'png','gif','mp4', 'x-msvideo'] \
                    if file_ext == i]) > 0), "File type not supported"
        
        print('upload_media')
        
        return {"operation": "UploadMedia",
                "status_code": 0}
          
    #%% TODO: remove?
    def upload_media_abort(self):
        ''' Project data API
        request:
        {"operation": "UploadMediaAbort"}
        
        response:
        {"operation": "UploadMediaAbort",
        "status_code": 0}
        '''    
                
        print('upload_media_abort')
        
        return {"operation": "UploadMediaAbort",
                "status_code": 0}
 
    #%%
    def add_aois_to_image(self, media_id, aoi_name, aoi_color, 
                  key_frame_vertices, key_frame_active = True, 
                  key_frame_seconds = 0, tag_name = '',
                  group_name='', merge_mode='replace_aois'):
        
        
        ''' Project data API
        request:
    
        {
        "operation": "AddAois",
        "media_id": "b3418558-b245-4185-9bdc-725fb6a23a88",
        "aois":  {'name:' : 'test',
                  'color' : 'AACC33',
                  'key_frames' : {'is_active' : true,
                                  'seconds' : 0,
                                  'vertices' : {{100, 100},
                                                {100, 200},
                                                {200, 200},
                                                {200, 100}}},
                  'tags': {'tag_name' : 'vehicle',
                          'group_name' : 'Brand'}},
        "merge_mode": "ReplaceAois"
        }  
                
        response:
        {
        "operation": "sendAois",
        "imported_aoi_count": 1
        }            
        ''' 
        
        print('add_aois_to_image')
        
        return {"operation": "sendAois",
                "imported_aoi_count": 1
                } 
    
   #%%
    def add_aois_to_video(self, media_id, aoi_name, aoi_color, 
                  key_frame_vertices, key_frame_active = True, 
                  key_frame_seconds = 0, tag_name = '',
                  group_name='', merge_mode='replace_aois'):
        ''' 
        
        Placeholder for adding AOIs to video. RTFM!
        
        Project data API
        request:
    
        {
        "operation": "AddAois",
        "media_id": "b3418558-b245-4185-9bdc-725fb6a23a88",
        "aois":  {'name:' : 'test',
                  'color' : 'AACC33',
                  'key_frames' : {'is_active' : true,
                                  'seconds' : 0,
                                  'vertices' : {{100, 100},
                                                {100, 200},
                                                {200, 200},
                                                {200, 100}}},
                  'tags': {'tag_name' : 'vehicle',
                          'group_name' : 'Brand'}},
        "merge_mode": "ReplaceAois"
        }  
                
        response:
        {
        "operation": "sendAois",
        "imported_aoi_count": 1
        }            
        '''     
    #%%
    def get_state(self):
        ''' External presenter API.
        Returns the current state of External Presenter workflow.
        
        request:
        {
        "operation": "GetState"
        }
        response:
        {
        "operation": "GetState",
        "status_code": 0,
        "state": "unmet"
        }        
        '''
		
        print('get_state')
        
        return {
                "operation": "GetState",
                "status_code": 0,
                "state": "ready"
                }

    #%%           
    def start_recording(self, recording_name, participant_id, screen_width,
                        screen_height, screen_latency=10000):
        ''' External presenter API     
        request:
        {"operation": "StartRecording",
        "recording_name": "Waterfall",
        "participant_id": "3E6C3751-389A-47F0-861D-7A09D744FC23",
        "screen_latency": 10000,
        "screen_width": 1024,
        "screen_height": 768}
        
        response:
        {"operation": "StartRecording",
        "status_code": 0,
        "recording_id": "4B7F3751-389A-47D0-861D-7A09D744FC12"}
        
        Note: Participant identifier (returned in
                                      AddParticipant operation
                                      response)
        '''
        
        print('start_recording')
        
        return {"operation": "StartRecording",
                "status_code": 0,
                "recording_id": "dummy_recording_id"}
    #%%           
    def stop_recording(self):
        ''' External presenter API     
        request:
        {"operation": "StopRecording"}
        
        response:
        {"operation": "StopRecording",
        "status_code": 0}
        '''   
        
        
        print('stop_recording')
        
        return {"operation": "StopRecording",
                "status_code": 0}
        
    #%%           
    def send_stimulus_event(self, recording_id, start_timestamp, 
                            media_id, media_position=None, background=None,
                            end_timestamp=None):
                            
        ''' External presenter API.
        Timestamps should be in microseconds
        
        request:
        {"operation": "SendStimulusEvent",
        "recording_id": "4B7F3751-389A-47D0-861D-7A09D744FC12",
        "start_timestamp": "123123123123213123",
        "end_timestamp": "321321321321321321",
        "media_id": "2A86C895-F8B6-4786-9C4B-CB889C3449F0",
        "media_position":  {"left": 10,
                            "top": 20,
                            "right": 850,
                            "bottom": 1100},
        "background": "AA91C0"}
        
        response:
        {"operation": "SendStimulusEvent",
        "status_code": 0}
        '''       
        
        print('send_stimulus_event')
        
    #%%           
    def send_custom_event(self):
        ''' External presenter API     
        request:
        {"operation": "SendCustomEvent",
        "recording_id": "4B7F3751-389A-47D0-861D-7A09D744FC12",
        "timestamp": "123123123123213123",
        "event_type": "ERROR_SEM_OWNER_DIED",
        "value": "105 (0x69)"}
        
        response:
        {"operation": "SendCustomEvent",
        "status_code": 0}
        
        '''         
        
        print('send_custom_event')
        
    #%%           
    def finalize_recording(self, recording_id):
        ''' Finalizes the recording and makes it ready for analysis in the 
        application.
        
        If validation of data was sent, Server responds with status code 201. 
        Once the root cause of a validation failure has been fixed, 
        the command can be executed again.        
        
        External presenter API.  
        request:
        {"operation": "FinalizeRecording",
        "recording_id": "4B7F3751-389A-47D0-861D-7A09D744FC12"}
        
        response:
        {"operation": "FinalizeRecording",
        "status_code": 0}
        
        Note: recording_id is returned from start_recording
        '''             
        
        print('finalize_recording')
                
        
    #%% 
    def disconnect(self):
        ''' Closes the websocket connection
        '''
        print('disconnect')
                
        
        