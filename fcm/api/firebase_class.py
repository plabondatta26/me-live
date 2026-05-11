# import requests
# import json 


# # # PROJECT_ID = 'moon-live-7ab3d'

# '''
# ※FCM Request
# {
#     "to": "your fcm token ",
#     "notification": {
#          "body": "I am body ",
#          "title": "I am title ",
#          "sound": "default"
#     },
#     "data":{
#             "functionID":"A"
#     },
#     "priority": "high"
# }
# '''

# class Firebase:
#     def __init__(self):
#         pass

#     def send(self,device_token, message):
#         fields = {
#             'to' : device_token,
#             'data' : message,
#         }
#         return self.send_push_notification(fields)
    
#     def send_multicast(self,registrations_ids, message):
#         fields = {
#             'registration_ids' : registrations_ids,
#             'data' : message,
#         }
#         return self.send_push_notification(fields)

#     def send_push_notification(self,fields):

#         # firebase server url to send the curl request
#         url = 'https://fcm.googleapis.com/fcm/send'

#         # building headers for the request
#         headers = {
#             'Content-Type': 'application/json',
#             'Authorization': 'key=' + SERVER_TOKEN,
#         }

#         data = json.dumps(fields)
#         response = requests.post(url,headers=headers, data=data,)
#         return True
 