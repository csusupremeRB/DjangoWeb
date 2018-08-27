# coding=utf-8
__author__ = 'renbo'
__date__ = '2018/3/6 19:25'

from django import forms
from captcha.fields import CaptchaField
from .models import UserProfile


# form组件  将用户提交过来的表单进行一部分的预处理，以便减轻数据库的负担

class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True, min_length=5)


class RegisterForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, min_length=5)
    captcha = CaptchaField(error_messages={"invalid": u"验证码错误"})
    # captcha是django的一款开发库，专门用于做验证码


class ForgetForm(forms.Form):
    email = forms.EmailField(required=True)
    captcha = CaptchaField(error_messages={"invalid": u"验证码错误"})


class ModifyPwdForm(forms.Form):
    password1 = forms.CharField(required=True, min_length=5)
    password2 = forms.CharField(required=True, min_length=5)


# 专门用来处理头像文件的上传
class UploadImageForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["image"]


class UserInfoForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["nick_name", "gender", "birday", "address", "mobile"]
