from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import User

class LoginForm(forms.Form):
    phone = forms.IntegerField(label="Your phone number")
    password = forms.CharField(widget=forms.PasswordInput)

class VerifyForm(forms.Form):
    key = forms.IntegerField(label="Please enter code here")

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password",widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('phone',)

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        qs = User.objects.filter(phone=phone)
        if qs.exists():
            raise forms.ValidationError("Phone is taken")
        return phone

    def clean_password2(self):
        password1 = self.changed_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")

        return password2

class TempregisterForm(forms.Form):
    phone = forms.IntegerField()
    otp = forms.IntegerField()

class SetPasswordForm(forms.Form):
    password = forms.CharField(label='Password',widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation",widget=forms.PasswordInput)

class UserAdminCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password",widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation",widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('phone',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserAdminCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()

        return user

class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('phone','password','active','admin')

    def clean_password(self):
        return self.initial['password']

# For the public authentication
class PhoneForm(forms.Form):
    phone = forms.IntegerField(label='', widget=forms.NumberInput(attrs={'class':"form-control",'placeholder': '+8801XXXXXXXXX','required':True}))

class PhoneVarificationForm(forms.Form):
    # phone = forms.IntegerField(label='', widget=forms.NumberInput(attrs={'class':"form-control",'placeholder': '01XXXXXXXXX','required':True}))
    otp = forms.IntegerField(label='', widget=forms.NumberInput(attrs={'class':"form-control",'placeholder': 'Code','required':True}))

class CreatePasswordForm(forms.Form):
    password1 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'class':"form-control",'placeholder': 'Password','required':True}))
    password2 = forms.CharField(label='', widget=forms.PasswordInput(attrs={'class':"form-control",'placeholder': 'Confirm Password','required':True}))

class PasswordForm(forms.Form):
    password = forms.CharField(label='', widget=forms.PasswordInput(attrs={'class':"form-control",'placeholder': 'Password','required':True}))
