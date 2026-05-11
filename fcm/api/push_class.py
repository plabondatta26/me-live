class Push:
    # //notification title
    title = ''

    # //notification message 
    message = ''

    # //notification image url 
    image = ''
    
    # //notification peeredUid
    peeredUid = ''

    # //notification peeredName
    peeredName = ''
    
    # //notification callType
    callType = ''
     
    # parameterized constructor
    def __init__(self, title, message, image, peeredUid, peeredName, callType):
        self.title = title
        self.message = message
        self.image = image
        self.peeredUid = peeredUid
        self.peeredName = peeredName
        self.callType = callType
     
    def get_push(self):
        response = {
            'data': {
                'title': self.title,
                'message': self.message,
                'image': self.image,
                'peeredUid': self.peeredUid,
                'peeredName': self.peeredName,
                'callType': self.callType,

            }
        }
        return response