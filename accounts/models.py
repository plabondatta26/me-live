from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.contrib.auth.models import PermissionsMixin

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self,phone,password=None,is_staff=False,is_active=True,is_admin=False):
        if not phone:
            raise ValueError("User must have a phone number")
        if not password:
            raise ValueError("User must have a password")

        user_obj = self.model(
            phone = phone
        )
        user_obj.set_password(password)
        user_obj.staff = is_staff
        user_obj.admin = is_admin
        user_obj.active = is_active
        user_obj.save(using=self._db)
        return user_obj

    def create_staffuser(self,phone,password=None):
        user = self.create_user(
            phone,
            password=password,
            is_staff=True,
            is_active=True,
        )
        return user

    def create_superuser(self,phone,password=None):
        user = self.create_user(
            phone,
            password=password,
            is_staff=True,
            is_admin=True,
            is_active=True,
        )
        return user

class User(AbstractBaseUser,PermissionsMixin):
    phone = models.CharField(max_length=250, unique=True, help_text='E.g. +8801XXXXXXXXX or Email',
                             verbose_name='Phone / Email')
    # phone = models.CharField(max_length=14,unique=True,help_text='E.g. +8801XXXXXXXXX ( Must include country code with + i.e. +880 )')
    name = models.CharField(max_length=20,blank=True,null=True)
    first_login = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.phone

    def get_full_name(self):
        if self.name:
            return self.name
        return self.phone

    def get_short_name(self):
        return self.phone

    def has_perm(self,perm,obj=None):
        return True

    def has_module_perms(self,app_label):
        return True

    @property
    def is_staff(self):
        return self.staff 

    @property
    def is_admin(self):
        return self.admin

    @property
    def is_active(self):
        return self.active

    @property
    def profile(self):
        return self.profile


class PhoneOTP(models.Model):
    # phone_regex = RegexValidator(regex = r'^\+?1?\d{9,14}$',message="Phone number must be 11 digits")
    # phone = models.CharField(validators=[phone_regex],max_length=11)
    phone = models.CharField(max_length=14,unique=True)
    otp = models.CharField(max_length=9,blank=True,null=True)
    count = models.IntegerField(default=0,help_text="Number of code sent")
    validated = models.BooleanField(default=False)

    def __str__(self):
        return str(self.phone) + ' is sent ' +str(self.otp)
