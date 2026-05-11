import random
from django.core.mail import EmailMessage
from django.conf import settings
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from rest_framework.generics import (
    CreateAPIView,UpdateAPIView
    )
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,HTTP_203_NON_AUTHORITATIVE_INFORMATION,HTTP_204_NO_CONTENT,
    HTTP_208_ALREADY_REPORTED,
    )
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .serializers import AuthTokenSerializer

from profiles.api.serializers import ProfileSerializer
from profiles.models import Profile
from accounts.models import User, PhoneOTP
from fcm.models import FCMDeviceToken
from devices.models import UserDeviceBlocked

def create_profile_for_google_login(new_user, login_type, full_name, email, uid, photo_url, request):
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
        return create_profile_for_google_login(new_user, login_type, full_name, email, uid, photo_url, request)

    serializer_profile = ProfileSerializer(instance=new_user.profile, context={"request": request})

    token, created = Token.objects.get_or_create(user=new_user)
    return Response({'token': token.key, 'profile': serializer_profile.data}, status=HTTP_201_CREATED)


def create_profile_for_phone_login(new_user, login_type, full_name, phone_code, uid, request):
    profile_obj = Profile()
    profile_obj.user = new_user
    profile_obj.login_type = login_type
    profile_obj.full_name = full_name
    profile_obj.phone_code = phone_code
    profile_obj.uid = uid
    try:
        profile_obj.save()
    except:
        # full_name = f"{full_name} {full_name}"
        full_name = f"Dummy Name {new_user.id}"
        # if len(full_name) > 200:
        #     full_name = full_name[:200]
        return create_profile_for_phone_login(new_user, login_type, full_name, phone_code, uid, request)

    serializer_profile = ProfileSerializer(instance=new_user.profile, context={"request": request})

    token, created = Token.objects.get_or_create(user=new_user)
    return Response({'token': token.key, 'profile': serializer_profile.data}, status=HTTP_201_CREATED)

# class CreateTokenView(ObtainAuthToken):
#     serializer_class = AuthTokenSerializer
#     renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

#     def post(self, request, *args, **kwargs):
#         method_dict = request.GET
#         device_id = method_dict.get('device_id',None)
#         # checking for device block
#         if device_id:
#             if UserDeviceBlocked.objects.filter(device_id = device_id).first():
#                 return Response(status=HTTP_208_ALREADY_REPORTED)

#         serializer = self.get_serializer(data=request.data)
#         if not serializer.is_valid():
#             return Response({},status=HTTP_204_NO_CONTENT)
#         user_obj = serializer.validated_data['user']
#         if not user_obj:
#             return Response({},status=HTTP_204_NO_CONTENT)
#         profile_serializer = ProfileSerializer(instance=user_obj.profile,context={"request": request})
     
#         token, created = Token.objects.get_or_create(user=user_obj)
#         return Response({'token': token.key,'profile':profile_serializer.data}, status=HTTP_200_OK)

# class RegisterWithProfileCreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = []

#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         method_dict = request.GET
#         device_id = method_dict.get('device_id',None)

#         # checking for device block
#         if device_id:
#             if UserDeviceBlocked.objects.filter(device_id = device_id).first():
#                 return Response(status=HTTP_208_ALREADY_REPORTED)

#         full_name = data_obj.get('full_name',None)
#         # email = data_obj.get('email',None)
#         # birthday = data_obj.get('birthday',None)
#         # gender = data_obj.get('gender',None)
#         mobile_number = data_obj.get('mobile_number',None)
#         password = data_obj.get('password',None)

#         # 'iso_code','iso3_code','phone_code','country_name'
#         phone_code = data_obj.get('phone_code',None)

#         if full_name is None or mobile_number is None or password is None or phone_code is None:
#             return Response({},status=HTTP_204_NO_CONTENT)

#         # # 2014-08-14T00:00:00.000
#         # birthday = birthday.split('T')[0]
#         # birthday_list = birthday.split('-')
#         # birthday = date(int(birthday_list[0]),int(birthday_list[1]),int(birthday_list[2]))

#         old_user = User.objects.filter(phone=mobile_number).first()
#         if old_user:
#             try:
#                 if old_user.profile:
#                     return Response({},status=HTTP_204_NO_CONTENT)
#             except:
#                 return create_profile(old_user,full_name,password,phone_code,request)
        
#         try:
#             new_user = User.objects.create_user(phone=mobile_number, password=password)
#             return create_profile(new_user,full_name,password,phone_code,request)
#         except:
#             return Response({},status=HTTP_204_NO_CONTENT)
        
def create_profile(new_user,full_name,password,phone_code,request):
    profile_obj = Profile()
    profile_obj.user = new_user
    profile_obj.full_name = full_name
    profile_obj.password = password
    # profile_obj.email = email
    # profile_obj.gender = gender
    profile_obj.phone_code = phone_code
    # profile_obj.birthday = birthday
    try:
        profile_obj.save()
    except:
        # full_name = f"{full_name} {full_name}"
        full_name = f"Dummy Name {new_user.id}"
        # if len(full_name) > 200:
        #     full_name = full_name[:200]
        return create_profile(new_user,full_name,password,phone_code,request)
      
    serializer_profile = ProfileSerializer(instance=new_user.profile,context={"request": request})
 
    token, created = Token.objects.get_or_create(user=new_user)
    return Response({'token': token.key,'profile':serializer_profile.data}, status=HTTP_201_CREATED)

# Generate OPT
# class PasswordResetOtpCreateApiView(CreateAPIView):
#     authentication_classes = []
#     permission_classes = []
 
#     def create(self, request, *args, **kwargs):
#         data_obj = request.data
#         method_dict = request.GET
#         device_id = method_dict.get('device_id',None)
#         # checking for device block
#         if device_id:
#             if UserDeviceBlocked.objects.filter(device_id = device_id).first():
#                 return Response(status=HTTP_208_ALREADY_REPORTED)
                
#         phone = data_obj.get('mobile',None)
#         email = data_obj.get('email',None)
#         subject = data_obj.get('subject','Me Live password reset OTP')
#         body_txt = data_obj.get('body','Your Password Reset OTP is:')

#         # user = User.objects.filter(phone = phone).first()
#         profile_obj = Profile.objects.filter(user__phone=phone,email=email).first()
#         if profile_obj:
#             code = random.randint(100000,999999)

#             old = PhoneOTP.objects.filter(phone__iexact = phone)
#             if old.exists():
#                 old = old.first()
#                 old.otp = code
#                 old.count = old.count + 1
#                 old.save()
#             else:
#                 PhoneOTP.objects.create(
#                     phone = phone,
#                     otp = code,
#                 )
#             # Implementing OTP email system
#             body = f'{body_txt} \n\n{code}'
#             email_obj = EmailMessage(subject=subject,body=body,from_email=settings.EMAIL_HOST_USER,to=[email])
#             email_obj.content_subtype = "html"
#             try:
#                 email_obj.send(fail_silently=False)
#             except:
#                 pass
#             return Response(status=HTTP_201_CREATED,)

#         return Response({},status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

# Reset Forget Password
# class ResetPasswordUpdateApiView(UpdateAPIView):
#     authentication_classes = []
#     permission_classes = [] 

#     def update(self, request, *args, **kwargs):
#         data_obj = request.data
#         phone = data_obj.get('mobile',None)
#         password = data_obj.get('password',None)
#         # otp_sent = data_obj.get('otp',None)
#         user_obj = User.objects.filter(phone = phone).first()
#         # old = PhoneOTP.objects.filter(phone__iexact=phone)

#         if user_obj and password is not None:
#             # old = old.last()
#             # otp = old.otp
#             # if str(otp) == otp_sent:
#             #     PhoneOTP.objects.filter(phone__iexact=phone).delete()
#             # Reset password
#             # set user new password
#             user_obj.set_password(password)
#             user_obj.save()
#             user_obj.profile.password = password
#             user_obj.profile.save()
#             return Response({},status=HTTP_200_OK)

#             # else:
#             #     return Response({},status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#         return Response({},status=HTTP_204_NO_CONTENT)

# class ConfirmRegistrationOtpUpdateApiView(UpdateAPIView):
#     authentication_classes = []
#     permission_classes = [] 

#     def update(self, request, *args, **kwargs):
#         data_obj = request.data
#         phone = data_obj.get('mobile',None)
#         otp_sent = data_obj.get('otp',None)
#         user_obj = User.objects.filter(phone = phone).first()
#         old = PhoneOTP.objects.filter(phone__iexact=phone)

#         if old.exists() and user_obj:
#             old = old.last()
#             otp = old.otp
#             if str(otp) == otp_sent:
#                 PhoneOTP.objects.filter(phone__iexact=phone).delete()
#                 # Activate User
#                 user_obj.active = True
#                 user_obj.save()
#                 return Response({},status=HTTP_200_OK)
#             else:
#                 return Response({},status=HTTP_203_NON_AUTHORITATIVE_INFORMATION)

#         return Response({},status=HTTP_204_NO_CONTENT)
