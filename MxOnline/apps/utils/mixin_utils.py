# coding=utf-8
__author__ = 'renbo'
__date__ = '2018/3/12 13:29'

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class LoginRequiredMixin(object):                     # 调用django的login_required装饰器，用于验证登陆状态,一种权限的认证
    @method_decorator(login_required(login_url='/login/'))
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)