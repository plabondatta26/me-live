from django.contrib.auth import authenticate
from rest_framework.generics import (
    CreateAPIView, UpdateAPIView
    )
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.status import (
   HTTP_200_OK, HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    HTTP_208_ALREADY_REPORTED,
    )
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_api_key.permissions import HasAPIKey

from profiles.api.serializers import ProfileSerializer
from profiles.models import Profile
from accounts.models import User
from fcm.models import FCMDeviceToken
from devices.models import UserDeviceBlocked, UserDeviceInfo

class LoginCreateApiView(CreateAPIView):
    authentication_classes = []
    permission_classes = [HasAPIKey]

    def create(self, request, *args, **kwargs):
        method_dict = request.GET
        device_id = method_dict.get('device_id',None)

        # checking for device block
        if device_id:
            if UserDeviceBlocked.objects.filter(device_id = device_id).exists():
                return Response(status=HTTP_208_ALREADY_REPORTED)

        data_obj = request.data
        login_type = data_obj.get('login_type',None)


        if login_type == 'google_login':
            full_name = data_obj.get('full_name',None)
            email = data_obj.get('email',None)
            uid = data_obj.get('uid',None)
            photo_url = data_obj.get('photo_url',None)
            # server_auth_code = data_obj.get('server_auth_code',None)

            old_user = User.objects.filter(phone=email).only('id').select_related('profile').first()
            if old_user:
                # Check user ID is blocked or not
                if UserDeviceBlocked.objects.filter(user_id=old_user.id).exists():
                    return Response({},status=HTTP_204_NO_CONTENT)
                # User already exists
                user_id = old_user.id
                profile_cache = cache.get(f'profile_{user_id}')
                if profile_cache is None:
                    profile_obj = old_user.profile
                    serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
                    profile_cache = serializer_profile.data
                    cache.set(f'profile_{user_id}',profile_cache,timeout=60*60*24*2)
                # serializer_profile = ProfileSerializer(instance=old_user.profile,context={"request": request})

                token, created = Token.objects.get_or_create(user=old_user)
         
                return Response({'token': token.key,'profile':profile_cache}, status=HTTP_201_CREATED)

            else:
                # Create new user
                try:
                    new_user = User.objects.create_user(phone=email, password=email)
                    return create_profile_for_google_login(new_user,login_type,full_name,email,uid,photo_url,request)
                except:
                    return Response({},status=HTTP_204_NO_CONTENT)
        # elif login_type == 'phone_login':
        #     full_name = data_obj.get('full_name',None)
        #     phone_code = data_obj.get('phone_code',None)
        #     mobile_number = data_obj.get('mobile_number',None)
        #     uid = data_obj.get('uid',None)
        #     # creation_time = data_obj.get('creation_time',None)
        #     # last_sign_in_time = data_obj.get('last_sign_in_time',None)
        #     # Need to check firebase using Python Firebase SDK

        #     old_user = User.objects.filter(phone=mobile_number).first()
        #     if old_user:
        #         # User already exists
        #         serializer_profile = ProfileSerializer(instance=old_user.profile,context={"request": request})

        #         token, created = Token.objects.get_or_create(user=old_user)
        #         return Response({'token': token.key,'profile':serializer_profile.data,}, status=HTTP_201_CREATED)

        #     else:
        #         # Create new user
        #         try:
        #             new_user = User.objects.create_user(phone=mobile_number, password=mobile_number)
        #             return create_profile_for_phone_login(new_user,login_type,full_name,phone_code,uid,request)
        #         except:
        #             return Response({},status=HTTP_204_NO_CONTENT)
                
        elif login_type == 'password_login':
            full_name = data_obj.get('full_name',None)
            phone_code = data_obj.get('phone_code',None)
            mobile_number = data_obj.get('mobile_number',None)
            password = data_obj.get('password',None)
            # creation_time = data_obj.get('creation_time',None)
            # last_sign_in_time = data_obj.get('last_sign_in_time',None)
            # Need to check firebase using Python Firebase SDK

           
            if User.objects.filter(phone=mobile_number).exists():
                # User already exists
                auth_user = authenticate(
                    request = request,
                    username = mobile_number,
                    password = password
                )
                if auth_user:
                    if UserDeviceBlocked.objects.filter(user_id=auth_user.pk).exists():
                        return Response({},status=HTTP_204_NO_CONTENT)
                    profile_cache = cache.get(f'profile_{auth_user.pk}')
                    if profile_cache is None:
                        profile_obj = auth_user.profile
                        profile_cache = ProfileSerializer(instance=profile_obj,context={"request": request}).data

                    token, created = Token.objects.get_or_create(user=auth_user)
                    cache.set(f'profile_{auth_user.pk}',profile_cache,timeout=60*60*24*2)
                    return Response({'token': token.key,'profile':profile_cache,}, status=HTTP_201_CREATED)
                
                return Response({'message':'Your credentials are mismatch'},status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

            else:
                # Not allowed Password Login creation
                return Response({},status=HTTP_204_NO_CONTENT)
                # Create new user

        return Response({},status=HTTP_204_NO_CONTENT)

def create_profile_for_google_login(new_user,login_type,full_name,email,uid,photo_url,request):
    profile_obj = Profile()
    profile_obj.user = new_user
    profile_obj.login_type = login_type
    profile_obj.full_name = full_name
    profile_obj.email = email
    profile_obj.uid = uid
    profile_obj.photo_url = photo_url
    try:
        profile_obj.save()
    except:
        # full_name = f"{full_name} {full_name}"
        full_name = f"Dummy Name {new_user.id}"
        # if len(full_name) > 200:
        #     full_name = full_name[:200]
        # return create_profile_for_google_login(new_user,login_type,full_name,email,uid,photo_url,request)
        profile_obj.full_name = full_name
        profile_obj.save()
      
    serializer_profile = ProfileSerializer(instance=profile_obj,context={"request": request})
    profile_cache = serializer_profile.data
    cache.set(f'profile_{new_user.id}',profile_cache,timeout=60*60*24*2)
    # serializer_profile = ProfileSerializer(instance=new_user.profile,context={"request": request})
 
    token, created = Token.objects.get_or_create(user=new_user)
    return Response({'token': token.key,'profile':profile_cache,}, status=HTTP_201_CREATED)

# def create_profile_for_phone_login(new_user,login_type,full_name,phone_code,uid,request):
#     profile_obj = Profile()
#     profile_obj.user = new_user
#     profile_obj.login_type = login_type
#     profile_obj.full_name = full_name
#     profile_obj.phone_code = phone_code
#     profile_obj.uid = uid
#     try:
#         profile_obj.save()
#     except:
#         # full_name = f"{full_name} {full_name}"
#         full_name = f"Dummy Name {new_user.id}"
#         # if len(full_name) > 200:
#         #     full_name = full_name[:200]
#         return create_profile_for_phone_login(new_user,login_type,full_name,phone_code,uid,request)
      
#     serializer_profile = ProfileSerializer(instance=new_user.profile,context={"request": request})
 
#     token, created = Token.objects.get_or_create(user=new_user)
#     return Response({'token': token.key,'profile':serializer_profile.data,}, status=HTTP_201_CREATED)

# def create_profile_for_password_login(new_user,login_type,full_name,phone_code,request,password):
#     profile_obj = Profile()
#     profile_obj.user = new_user
#     profile_obj.login_type = login_type
#     profile_obj.full_name = full_name
#     profile_obj.phone_code = phone_code
#     profile_obj.password = password
#     try:
#         profile_obj.save()
#     except:
#         # full_name = f"{full_name} {full_name}"
#         full_name = f"Dummy Name {new_user.id}"
#         # if len(full_name) > 200:
#         #     full_name = full_name[:200]
#         return create_profile_for_password_login(new_user,login_type,full_name,phone_code,request,password)
      
#     serializer_profile = ProfileSerializer(instance=new_user.profile,context={"request": request})
 
#     token, created = Token.objects.get_or_create(user=new_user)
#     return Response({'token': token.key,'profile':serializer_profile.data,}, status=HTTP_201_CREATED)

class LogoutCreateApiView(CreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated & HasAPIKey]

    def create(self, request, *args, **kwargs):
        user_obj = request.user
        # Auth Token
        Token.objects.filter(user=user_obj).delete()
        # Firebase Cloud Messaging Token
        FCMDeviceToken.objects.filter(user=user_obj).delete()

        return Response(status=HTTP_201_CREATED)

# # Change new Password
# class ChangePasswordUpdateApiView(UpdateAPIView):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated & HasAPIKey]

#     def update(self, request, *args, **kwargs):
#         user_obj = request.user
#         data_obj = request.data
#         old_password = data_obj.get('old_password',None)
#         new_password = data_obj.get('new_password',None)

#         if old_password and new_password:
#             is_password_exists = user_obj.check_password(old_password)
#             if is_password_exists is True:
#                 # set user new password
#                 user_obj.set_password(new_password)
#                 user_obj.save()
#                 profile_obj = user_obj.profile
#                 profile_obj.password = new_password
#                 profile_obj.save()
#                 return Response({}, status=HTTP_200_OK,)
#             else:
#                 return Response({},status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#         return Response({}, status=HTTP_204_NO_CONTENT,)
