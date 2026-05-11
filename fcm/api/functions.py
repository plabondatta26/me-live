from lib2to3.pgen2 import token
from fcm.models import FCMDeviceToken
    
#storing token in database 
def register_device(user,token):
    device_obj = FCMDeviceToken.objects.filter(user=user).first()
    if device_obj:
        # returning 2 means user already exist
        return 2
    else:
        device_obj = FCMDeviceToken()
        device_obj.user = user
        device_obj.token = token
        try:
            device_obj.save()
            #return 0 means success
            return 0 
        except:
            # return 1 means failure
            return 1

def update_peer_user(user,peer_user):
    device_obj = FCMDeviceToken.objects.filter(user=user).first()
    if device_obj:
        device_obj.peer_user = peer_user
        device_obj.save()
        #return 0 means success
        return 0 
    # return 1 means failure
    return 1

def update_token(user,token):
    device_obj = FCMDeviceToken.objects.filter(user=user).first()
    if device_obj:
        device_obj.token = token
        device_obj.save()
        #return 0 means success
        return 0 
    else:
        device_obj = FCMDeviceToken()
        device_obj.user = user
        device_obj.token = token
        try:
            device_obj.save()
            #return 0 means success
            return 0 
        except:
            # return 1 means failure
            return 1

#getting all tokens to send push to all devices
# public function getAllTokens(){
#     $stmt = $this->con->prepare("SELECT token FROM flutter_devices");
#     $stmt->execute(); 
#     $result = $stmt->get_result();
#     $tokens = array(); 
#     while($token = $result->fetch_assoc()){
#         array_push($tokens, $token['token']);
#     }
#     return $tokens; 
# }
# def get_all_tokens():
#     return FCMDeviceToken.objects.all()

# getting a specified token to send push to selected device
def get_token_by_user(receiver_user,sender_user):
    token = ''
    device_obj = FCMDeviceToken.objects.filter(user=receiver_user).first()
    if device_obj:
        # TODO: May Cause issue (Confused)
        if device_obj.peer_user == sender_user:
            token = ''
        else:
            token = device_obj.token
    return token

# getting a specified token to send push call to selected device
def get_token_by_user_to_send_push_call(user):
    token = ''
    device_obj = FCMDeviceToken.objects.filter(user=user).first()
    if device_obj:
        token = device_obj.token
    return token

# getting all the registered devices from database 
# def get_all_devices():
#     return FCMDeviceToken.objects.all()