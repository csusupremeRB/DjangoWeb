# coding=utf-8
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect
import json
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse

from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm, UploadImageForm, UserInfoForm
from utils.email_send import send_register_email
from utils.mixin_utils import LoginRequiredMixin
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from courses.models import Course
from .models import Banner


class CustomBackend(ModelBackend):      # 自定义authenticate认证方法
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username) | Q(email=username)) # 利用Q这个类完成并集的查询 既可用用户名登录，也可用邮箱
            if user.check_password(password):  # 该方法将明文加密并且将传进去的password和数据库中做对比
                return user
        except Exception as e:
            return None


class ActiveUserView(View):
    """激活"""
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")


class RegisterView(View):
    """用户注册"""
    def get(self, request):
        register_form = RegisterForm()   # captcha会自动生成一个验证码，并生成相应的hashkey,用户输入验证码后会在数据库中作比对
        return render(request, "register.html", {"register_form": register_form})

    def post(self, request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get("email", "")
            if UserProfile.objects.filter(email=user_name):   # 验证用户是否已经存在
                return render(request, "register.html", {"register_form": register_form, "msg": "用户已经存在"})
            pass_word = request.POST.get("password", "")
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            user_profile.password = make_password(pass_word) # 利用make_password函数将明文加密
            user_profile.save()

            # 写入欢迎注册的消息
            user_message = UserMessage()
            user_message.user = user_profile.id
            user_message.message = "欢迎注册慕学在线教育网！"
            user_message.save()

            send_register_email(user_name, "register")   # 发送邮件进行验证
            return render(request, "login.html")
        else:
            return render(request, "register.html", {"register_form": register_form})


class LogoutView(View):
    """用户登出"""
    def get(self, request):
        logout(request)     # 利用django提供的logout函数
        # from django.core.urlresolvers import reverse  #django内置函数，可以将url名称反解成url地址
        return HttpResponseRedirect(reverse("index"))


class LoginView(View):
    """用户登录"""
    def get(self, request):
        return render(request, "login.html", {})

    def post(self, request):
        login_form = LoginForm(request.POST)  # 声明一个form的实例,将前端中username和password字段对应到form中进行验证
        if login_form.is_valid():    # 调用该方法判断form中条件是否满足，满足则进行数据库的查询对比
            user_name = request.POST.get("username", "")
            pass_word = request.POST.get("password", "")
            user = authenticate(username=user_name, password=pass_word)  # 向数据库发起验证用户名密码是否正确,并没有登录,
                                                                        # 如果验证成功就返回一个user对象
            if user is not None:
                if user.is_active:
                    login(request, user)  # 利用django内置login方法完成登录(利用用户信息生成一个sessionID和一段随机字符串,去数据库中做对比)
                    return HttpResponseRedirect(reverse("index"))
                else:
                    return render(request, "login.html", {"msg": "用户未激活"})
            else:
                return render(request, "login.html", {"msg": "用户名或密码错误!"})
        else:
            return render(request, "login.html", {"login_form": login_form})


class ForgetPwdView(View):
    """忘记密码"""
    def get(self, request):
        forget_form = ForgetForm()
        return render(request, "forgetpwd.html", {"forget_form": forget_form})

    def post(self, request):
        forget_form = ForgetForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get("email", "")
            send_register_email(email, "forget")
            return render(request, "send_success.html")
        else:
            return render(request, "forgetpwd.html", {"forget_form": forget_form})


class ResetView(View):
    """重置页面"""
    def get(self, request, active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                return render(request, "password_reset.html", {"email": email})
        else:
            return render(request, "active_fail.html")
        return render(request, "login.html")


class ModifyPwdView(View):
    """修改用户密码"""
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if pwd1 != pwd2:
                return render(request, "password_reset.html", {"email": email, "msg": "密码不一致"})
            user = UserProfile.objects.get(email=email)
            user.password = make_password(pwd2)
            user.save()
            return render(request, "login.html")
        else:
            email = request.POST.get("email", "")
            return render(request, "password_reset.html", {"email": email, "modify_form": modify_form})


class UserInfoView(LoginRequiredMixin, View):
    """用户个人信息"""
    def get(self, request):
        current_page = "info"
        return render(request, 'usercenter-info.html', {
            "current_page": current_page
        })

    def post(self, request):
        user_info_form = UserInfoForm(request.POST, instance=request.user)   # 对form表单进行修改 需要将当前的用户传递进来
        if user_info_form.is_valid():
            user_info_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(user_info_form.errors), content_type='application/json')


class UploadImageView(LoginRequiredMixin, View):
    """用户修改头像"""
    def post(self, request):      # 利用modelform  这个image将用户上传的文件保存到这个UploadImageForm中
        image_form = UploadImageForm(request.POST, request.FILES, instance=request.user)  #instance为实例化对象，指代form中的UserProfile
        if image_form.is_valid():
            image_form.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail"}', content_type='application/json')


class UpdatePwdView(View):
    """个人中心修改用户密码"""
    def post(self, request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            pwd1 = request.POST.get("password1", "")
            pwd2 = request.POST.get("password2", "")
            if pwd1 != pwd2:
                return HttpResponse('{"status":"success", "msg":"密码不一致"}', content_type='application/json')
            user = request.user
            user.password = make_password(pwd2)
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse(json.dumps(modify_form.errors), content_type='application/json')
            # 因为modify_form是一个dict 可以调用json的dumps函数将它的错误信息转换成字符串


class SendEmailCodeView(LoginRequiredMixin, View):
    """发送邮箱验证码"""
    def get(self, request):
        email = request.GET.get('email', '')

        if UserProfile.objects.filter(email=email):     # 判断邮箱是否已经被注册
            return HttpResponse('{"email":"邮箱已存在"}', content_type='application/json')
        send_register_email(email, "update_email")
        return HttpResponse('{"status":"success"}', content_type='application/json')


class UpdateEmailView(LoginRequiredMixin, View):
    """修改个人邮箱"""
    def post(self, request):
        email = request.POST.get('email', '')
        code = request.POST.get('code', '')

        existed_records = EmailVerifyRecord.objects.filter(email=email, code=code, send_type="update_email")
        if existed_records:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type='application/json')
        else:
            return HttpResponse('{"email":"验证码错误"}', content_type='application/json')


class MyCourseView(LoginRequiredMixin, View):
    """我的课程"""
    def get(self, request):
        current_page = "course"
        user_courses = UserCourse.objects.filter(user=request.user)

        return render(request, "usercenter-mycourse.html", {
            "user_courses": user_courses,
            "current_page": current_page,
        })


class MyFavOrgView(LoginRequiredMixin, View):
    """我收藏的课程机构"""
    def get(self, request):
        current_page = "fav"
        # 定义一个机构的列表
        org_list = []
        fav_orgs = UserFavorite.objects.filter(user=request.user, fav_type=2)  #因为UserFavorite中只存有fav_id 并没有外键
        # 遍历出所有机构的id
        for fav_org in fav_orgs:
            org_id = fav_org.fav_id
        # 取出相应的机构
            org = CourseOrg.objects.get(id=org_id)
            org_list.append(org)

        return render(request, "usercenter-fav-org.html", {
            "org_list": org_list,
            "current_page": current_page,
        })


class MyFavTeacherView(LoginRequiredMixin, View):
    """我收藏的授课教师"""
    def get(self, request):
        current_page = "fav"
        # 定义一个教师的列表
        teacher_list = []
        fav_teachers = UserFavorite.objects.filter(user=request.user, fav_type=3)
        # 遍历出所有教师的id
        for fav_teacher in fav_teachers:
            teacher_id = fav_teacher.fav_id
        # 取出相应的教师
            teacher = Teacher.objects.get(id=teacher_id)
            teacher_list.append(teacher)

        return render(request, "usercenter-fav-teacher.html", {
            "teacher_list": teacher_list,
            "current_page": current_page,
        })


class MyFavCourseView(LoginRequiredMixin, View):
    """我收藏的课程"""
    def get(self, request):
        current_page = "fav"
        # 定义一个课程的列表
        course_list = []
        fav_courses= UserFavorite.objects.filter(user=request.user, fav_type=1)
        # 遍历出所有课程的id
        for fav_course in fav_courses:
            course_id = fav_course.fav_id
        # 取出相应的课程
            course = Course.objects.get(id=course_id)
            course_list.append(course)

        return render(request, "usercenter-fav-course.html", {
            "course_list": course_list,
            "current_page": current_page,
        })


class MymessageView(LoginRequiredMixin, View):
    """我的消息"""
    def get(self, request):
        current_page = "message"
        all_messages = UserMessage.objects.filter(user=request.user.id)

        # 对消息进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_messages, 5, request=request)
        messages = p.page(page)
        return render(request, "usercenter-message.html", {
            "messages": messages,
            "current_page": current_page,
        })


class IndexView(View):
    """在线网的首页"""
    def get(self, request):
        # print (1/0)
        # 取出轮播图,并且根据index字段排序
        all_banners = Banner.objects.all().order_by("index")
        # 取出非广告位的课程
        courses = Course.objects.filter(is_banner=False)[:6]
        # 取出广告位的课程
        banner_courses = Course.objects.filter(is_banner=True)[:3]
        # 取出课程机构
        course_orgs = CourseOrg.objects.all()[:15]
        return render(request, "index.html", {
            "all_banners": all_banners,
            "courses": courses,
            "banner_courses": banner_courses,
            "course_orgs": course_orgs,
        })


def page_not_found(request):
    """全局404处理函数"""
    from django.shortcuts import render_to_response
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    """全局500处理函数"""
    from django.shortcuts import render_to_response
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response
