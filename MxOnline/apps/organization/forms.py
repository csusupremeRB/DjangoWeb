# coding=utf-8
__author__ = 'renbo'
__date__ = '2018/3/9 20:09'
import re
from django import forms
from operation.models import UserAsk


#利用django的modelform将model直接转换成form(比form更强大)
class UserAskForm(forms.ModelForm):
    class Meta:
        model = UserAsk
        fields = ["name", "mobile", "course_name"]

    #编辑一个以clean开头的函数(必须以clean开头,也就是对mobile这个字段进行进一层的自定义封装),当初始化该form时,会自动调用该函数进行mobile的验证
    def clean_mobile(self):
        """验证手机号码是否合法"""
        mobile = self.cleaned_data["mobile"]
        REGEX_MOBILE = "^1[358]\d{9}$|^147\d{8}$|176\d{8}$"
        p = re.compile(REGEX_MOBILE)
        if p.match(mobile):
            return mobile
        else:
            raise forms.ValidationError(u"手机号码非法", code="mobile_invalid")