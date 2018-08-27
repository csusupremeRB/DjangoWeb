# coding=utf-8
__author__ = 'renbo'
__date__ = '2018/3/7 8:49'
from random import Random
from users.models import EmailVerifyRecord

from django.core.mail import send_mail
from MxOnline.settings import EMAIL_FROM


def random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def send_register_email(email, send_type="register"):
    email_record = EmailVerifyRecord()
    if send_type == "update_email":
        code = random_str(4)
    else:
        code = random_str(16)
    email_record.code = code
    email_record.email =email
    email_record.send_type = send_type
    email_record.save()     #将事先要发送的code保存到数据库中
                            # 在用户的链接中后台生成一个随机字符串code，用户在点击时将code取出来，查询数据库做对比，存在就激活
    if send_type == "register":
        email_title = "慕学在线网注册激活链接"
        email_body = "请点击下面的链接激活你的帐号：http://127.0.0.1:8000/active/{0}".format(code)
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:      #利用django内置的函数发送邮件
            pass

    elif send_type == "forget":
        email_title = "慕学在线网密码重置链接"
        email_body = "请点击下面的链接重置你的帐号：http://127.0.0.1:8000/reset/{0}".format(code)
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass

    elif send_type == "update_email":
        email_title = "慕学在线网邮箱修改链接"
        email_body = "你的邮箱验证码为：{0}".format(code)
        send_status = send_mail(email_title, email_body, EMAIL_FROM, [email])
        if send_status:
            pass