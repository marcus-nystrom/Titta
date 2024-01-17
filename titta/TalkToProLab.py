# -*- coding: utf-8 -*-
"""
Created on Thu Dec  6 14:37:06 2018

@author: Marcus
ToDo: upload information in chunks of 64 KB
"""

# import relevant libs
from websocket import create_connection
import json
import os
import time
import numpy as np
import threading


status_codes = {0: 'Operation successful',
                100: 'Bad request',
                101: 'Invalid parameter',
                102: 'Operation was unsuccessful',
                103: 'Operation cannot be executed in current state',
                104: 'Access to the service is forbidden',
                105: 'Authorization during connection to a service has not been provided',
                201: 'Recording finalization failed'}

class TalkToProLab(threading.Thread):
    """ A class for talking to Tobii Pro Lab.
    Tested with Python 2.7 and 3.6
    """

    #%%
    def __init__(self, project_name=None, dummy_mode=False):

        if dummy_mode:
            from titta import TalkToProLab_dummy
            self.__class__ = TalkToProLab_dummy.TalkToProLab_dummy
            self.__class__.__init__(self)
        else:
            # Connect to servers
            self.clock_address = create_connection('ws://localhost:8080/clock?client_id=RemoteClient')
            self.external_presenter_address = create_connection('ws://localhost:8080/record/externalpresenter?client_id=RemoteClient')
            self.project_address = create_connection('ws://localhost:8080/project?client_id=RemoteClient')

            # Make sure the desired project is opened (if project name is given)
            if project_name:
                assert project_name == self.get_project_info()['project_name'], \
                "Wrong project opened in Lab. Should be {}".format(project_name)


            # Start new thread that takes care of keeping the connection alive
            threading.Thread.__init__(self)
            self.__stop = False
            self.start()

    #%%s
    def run(self):
        ''' Ping/pong the server every 15 s to keep the connection alive.
        Starts the thread that keeps the connection alive.
        Otherwise, if there is not communication between the server and client,
        the connection dies after 30 sec.
        '''

        while True:
            self.clock_address.ping()
            self.clock_address.pong("pong")

            self.external_presenter_address.ping()
            self.external_presenter_address.pong("pong")

            self.project_address.ping()
            self.project_address.pong("pong")

            time.sleep(15)

            if self.__stop == True:
                break

    #%%
    def send_message(self, address, msg_dict, to_json=True):
        ''' Send message to server and return response
        '''

        # Convert message dictionary to json
        if to_json:
            msg_dict = json.dumps(msg_dict)

        # Send data and wait for response
        address.send(msg_dict)
        response = address.recv()

        # Return dict
        if to_json:
            return json.loads(response)
        else:
            return response

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
        response = self.send_message(self.clock_address,
                                     {"operation": "GetApiVersion"})


        assert response['status_code'] == 0, response
        return response

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

        response = self.send_message(self.clock_address,
                                     {"operation": "GetTimestamp"})

        assert response['status_code'] == 0, response

        return response
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

        # Make sure that the participant id does not already exist in Lab
        assert not self.find_participant(participant_name), "Participant {} already exists in Lab".format(participant_name)

        response = self.send_message(self.project_address,
                                     {"operation": "AddParticipant",
                                      "participant_name": participant_name})

        assert response['status_code'] == 0, response

        return response

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

        response = self.send_message(self.project_address,
                                     { "operation": "GetProjectInfo"})

        assert response['status_code'] == 0, response

        return response

    #%%
    def find_participant(self, participant_name):
        ''' Finds whether participant_name already has been uploaded to lab

        Args:
            participant_name - string with participant name (e.g., P04)

        Returns:
            exists - boolean
        '''

        exists = False
        uploaded_participants = self.list_participants()['participant_list']
        for m in uploaded_participants:
            if m['participant_name'] == participant_name:
                exists = True

        return exists

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

        response = self.send_message(self.project_address,
                                     { "operation": "ListParticipants"})

        assert response['status_code'] == 0, response

        return response

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

        response = self.send_message(self.project_address,
                                     { "operation": "ListMedia"})

        assert response['status_code'] == 0, response

        return response


    #%%
    def find_media(self, media_name):
        ''' Finds whether media_name already has been uploaded to lab

        Args:
            media_name - string with media name (e.g., image.png)

        Returns:
            exists - boolean
        '''

        exists = False
        uploaded_media = self.list_media()['media_list']
        for m in uploaded_media:
            if m['media_name'] == media_name.split('.')[0]:
                exists = True

        return exists

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

        # Read image as binary, each element in 'f' represents a byte
        with open(media_name, "rb") as imageFile:
          f = imageFile.read()

        # Prepare Server to receive media content (image or video) as binary data
        media_size = len(f)
        response = self.send_message(self.project_address,
                                     {"operation": "UploadMedia",
                                      "mime_type": '/'.join([media_type,
                                                             file_ext]),
                                      "media_name": media_name,
                                      "media_size": str(media_size)})
        assert response['status_code'] == 0, response

        # Send data to server (Should be sent in 64KB chunks)
        c_idx = np.arange(0, media_size, 64000)
        for i in np.arange(len(c_idx))[:-1]:
            self.project_address.send_binary(f[c_idx[i] : (c_idx[i + 1])])

        # Send last bits
        self.project_address.send_binary(f[c_idx[-1] : media_size])


        # self.project_address.send_binary(f)

        # Wait for verification that all bytes were received by lab
        response =  json.loads(self.project_address.recv())
        '''
        response:
        {
        "operation": "UploadMedia",
        "status_code": 0,
        "md5_checksum": "7815696ecbf1c96e6894b779456d330e",
        "media_id": "2A86C895-F8B6-4786-9C4B-CB889C3449F0"
        }
        '''


        assert response['status_code'] == 0, response

        return response

    #%% TODO: remove?
    def upload_media_abort(self):
        ''' Project data API
        request:
        {"operation": "UploadMediaAbort"}

        response:
        {"operation": "UploadMediaAbort",
        "status_code": 0}
        '''

        response = self.send_message(self.project_address,
                                      {"operation": "UploadMediaAbort"})

        assert response['status_code'] == 0, response

        return response

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

        s = ''
        for i, k in enumerate(key_frame_vertices):

            if i == (len(key_frame_vertices) - 1):
                s = s + '{"x": %s, "y": %s}'
            else:
                s = s + '{"x": %s, "y": %s},'


        a = (media_id, aoi_name, aoi_color, str(key_frame_active).lower(),
                                key_frame_seconds) + \
                                tuple([x for b in key_frame_vertices for x in b]) + \
                                (group_name, tag_name, merge_mode)




        operation = '''{
                        "operation": "AddAois",
                        "media_id": "%s",
                        "aois": [{
                                "name": "%s",
                                "color": "%s",
                                "key_frames": [{
                                        "is_active": %s,
                                        "seconds": %s,
                                        "vertices": [''' + \
                                        s + \
                        '''
                                                ]
                                        }],
                                "tags": [
                                         {
                                            "group_name": "%s",
                                            "tag_name": "%s"
                                            }
                                        ]
                                }],
                                        "merge_mode": "%s"
                        }'''



        operation = str(operation)
        operation = operation.replace('\t', '')
        operation = operation.replace('\n', '')
        operation = operation.replace(' ', '')

        operation = operation % a


        response = json.loads(self.send_message(self.project_address,
                                      operation, to_json=False))
        assert response['status_code'] == 0, response

        return response

   #%%
    def add_aois_to_video(self, media_id, aoi_name, aoi_color,
                  key_frame_vertices, time_onset=0, time_offset=1000000,
                  tag_name='',
                  group_name='', merge_mode='replace_aois'):
        '''
        Example args:
            media_id = "9ed058e9-d551-452f-9ff2-1ae8a6986414"
            aoi_name = 'test'
            aoi_color =  'AAC333'
            key_frame_vertices = ((100, 100),
                                   (100, 200),
                                   (200, 200),
                                   (200, 100))
            tag_name = 'test_tag'
            group_name = 'test_group'
            time_onset=0 # in mircoseconds
            time_offset=1000000

        Project data API
        example request:

        {
          "operation": "AddAois",
          "media_id": "9ed058e9-d551-452f-9ff2-1ae8a6986414",
          "aois": [
            {
              "name": "test5",
              "color": "FF0000",
              "key_frames": [
                {
                  "is_active": true,
                  "time": 0,
                  "vertices": [
                    {"x": 500, "y": 500},
                    {"x": 600, "y": 500},
                    {"x": 600, "y": 600},
                    {"x": 500, "y": 600}]
                },
                {
                  "is_active": false,
                  "time": 1000000,
                  "vertices": [
                    {"x": 500, "y": 500},
                    {"x": 600, "y": 500},
                    {"x": 600, "y": 600},
                    {"x": 500, "y": 600}]
                }
              ],
              "tags": []
            }
          ],
          "merge_mode": "replace_aois"
        }
        '''


        s = ''
        for i, k in enumerate(key_frame_vertices):

            if i == (len(key_frame_vertices) - 1):
                s = s + '{"x": %s, "y": %s}'
            else:
                s = s + '{"x": %s, "y": %s},'


        a = (media_id, aoi_name, aoi_color,
            str(time_onset)) + \
            tuple([x for b in key_frame_vertices for x in b]) + \
            tuple([str(time_offset)]) + \
            tuple([x for b in key_frame_vertices for x in b]) + \
            (group_name, tag_name, merge_mode)

        operation = '''{
                        "operation": "AddAois",
                        "media_id": "%s",
                        "aois": [{
                                "name": "%s",
                                "color": "%s",
                                "key_frames": [
                                        {
                                        "is_active": true,
                                        "time": "%s",
                                        "vertices": [''' + \
                                        s + \
                        '''
                                                ]
                                        }
                                        {
                                        "is_active": false,
                                        "time": "%s",
                                        "vertices": [''' + \
                                        s + \
                        '''
                                                ]
                                        }
                                            ],
                                "tags": [{
                                            "group_name": "%s",
                                            "tag_name": "%s",
                                         }]
                                }],
                                        "merge_mode": "%s"
                        }'''

        operation = str(operation)
        operation = operation.replace('\t', '')
        operation = operation.replace('\n', '')
        operation = operation.replace(' ', '')

        operation = operation % a

        response = json.loads(self.send_message(self.project_address,
                                      operation, to_json=False))
        assert response['status_code'] == 0, response

        return response

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

        response = self.send_message(self.external_presenter_address,
                                      {"operation": "GetState"})

        assert response['status_code'] == 0, response

        return response

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

        response = self.send_message(self.external_presenter_address,
                                     {"operation": "StartRecording",
                                      "recording_name": recording_name,
                                      "participant_id": participant_id,
                                      "screen_latency": screen_latency,
                                      "screen_width": screen_width,
                                      "screen_height": screen_height})

        assert response['status_code'] == 0, response

        return response
    #%%
    def stop_recording(self):
        ''' External presenter API
        request:
        {"operation": "StopRecording"}

        response:
        {"operation": "StopRecording",
        "status_code": 0}
        '''

        response = self.send_message(self.external_presenter_address,
                                      {"operation": "StopRecording"})

        assert response['status_code'] == 0, response

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

        request =  {"operation": "SendStimulusEvent",
            "recording_id": recording_id,
            "start_timestamp": start_timestamp,
            "media_id": media_id}

        if end_timestamp:
            request =  {"operation": "SendStimulusEvent",
                "recording_id": recording_id,
                "start_timestamp": start_timestamp,
                'end_timestamp': end_timestamp,
                "media_id": media_id}

        if  media_position:
            request['media_position'] = media_position

        if background:
            request['background'] = background

        response = self.send_message(self.external_presenter_address,
                                     request)

        assert response['status_code'] == 0, response
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

        response = self.send_message(self.external_presenter_address,
                                     {"operation": "FinalizeRecording",
                                      "recording_id": recording_id})
        assert response['status_code'] == 0, response

        # Stop ping ponging to keep the connection alive
        self.__stop = True

    #%%
    def disconnect(self):
        ''' Closes the websocket connection
        '''
        self.clock_address.close()
        self.external_presenter_address.close()
        self.project_address.close()


