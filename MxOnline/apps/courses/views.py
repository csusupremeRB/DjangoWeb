# coding=utf-8
from django.shortcuts import render
from django.views.generic.base import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse,JsonResponse
from .models import Course, CourseResource, Video
from operation.models import UserFavorite, CourseComments, UserCourse
from utils.mixin_utils import LoginRequiredMixin
from django.db.models import Q
# Create your views here.


class CourseListView(View):
    def get(self, request):
        all_courses = Course.objects.all().order_by("-add_time")  #根据添加时间默认降序排序   也就是课程列表页上最新展示的

        hot_courses = Course.objects.all().order_by("-click_nums")[:3]  #根据点击数对热门课程进行降序排序

       #课程搜索
        search_keywords = request.GET.get("keywords", "")
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords) |
                                             Q(desc__icontains=search_keywords) |
                                             Q(detail__icontains=search_keywords))
        #通过icontains (i代表不区分大小写)   name__双下划线代表在name上进行操作 django的model会把它转换成sql的Like语句

        #课程排序
        sort = request.GET.get("sort", "")
        if sort:
            if sort == "students":
                all_courses = all_courses.order_by("-students")  # 根据参与学习人数的多少倒序排列
            elif sort == "hot":
                all_courses = all_courses.order_by("-click_nums")  # 根据课程点击量来排序，只要点击了封面就算

        # 对课程进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_courses, 3, request=request)
        courses = p.page(page)

        return render(request, "course-list.html", {
            "all_courses": courses,
            "sort": sort,
            "hot_courses": hot_courses,
        })


class VideoPlayView(View):
    """视频播放页面"""
    def get(self, request, video_id):
        video = Video.objects.get(id=int(video_id))
        course = video.lesson.course    #通过外键查找对应课程
        course.students += 1
        course.save()

        #查询用户是否关联了该课程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        #找出学过这门课程的同学
        user_courses = UserCourse.objects.filter(course=course)
        #找出他们的id
        user_ids = [user_course.user.id for user_course in user_courses]
        #找出他们所学的所有课程
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)   #django model的用法  __in传进去的是一个list
        #取出所有课程id
        course_ids = [user_course.course.id for user_course in all_user_courses]
        #获取学过该用户学过的其他的所有课程
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:3]

        #取出当前课程的课程资源
        all_resources = CourseResource.objects.filter(course=course)
        return render(request, "course-play.html", {
            "course": course,
            "course_resources": all_resources,
            "relate_courses": relate_courses,
            "video": video,

        })


class CourseDetailView(View):
    """课程详情页"""
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))

        #增加课程点击数
        course.click_nums += 1
        course.save()

        has_fav_course = False   #判断课程与课程机构的收藏状态  反馈到前端页面
        has_fav_org = False

        if request.user.is_authenticated():     #先判断用户是否登录,登录了才可以进行收藏状态的改变
            if UserFavorite.objects.filter(user=request.user, fav_id=course.id, fav_type=1):
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user, fav_id=course.course_org.id, fav_type=2):
                has_fav_org = True

        #通过Course中的tag字段做相关课程推荐
        tag = course.tag
        if tag:
            relate_courses = Course.objects.filter(tag=tag)[:2]
        else:
            relate_courses = []  #如果tag为空,则传递一个空的数组，防止for循环出错

        return render(request, "course-detail.html", {
            "course": course,
            "relate_courses": relate_courses,
            "has_fav_course": has_fav_course,
            "has_fav_org": has_fav_org,
        })


class CourseInfoView(LoginRequiredMixin, View):
    """课程章节信息"""
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))
        course.students += 1
        course.save()

        #查询用户是否关联了该课程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        #取出学过这门课程的所有用户信息
        user_courses = UserCourse.objects.filter(course=course)
        #取出所有学过该课程的用户的id
        user_ids = [user_course.user.id for user_course in user_courses]
        #取出学过该课程的所有用户学过的所有课程信息
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)   #django model的用法  __in传进去的是一个list
        #取出学过该课程的所有用户学过的所有课程的id
        course_ids = [user_course.course.id for user_course in all_user_courses]
        #取出学过该用户学过的其他的课程(按点击量显示前3个)
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:3]

        #取出当前课程的课程资源
        all_resources = CourseResource.objects.filter(course=course)
        return render(request, "course-video.html", {
            "course": course,
            "course_resources": all_resources,
            "relate_courses": relate_courses

        })


class CommentsView(LoginRequiredMixin, View):
    """课程评论"""
    def get(self, request, course_id):
        course = Course.objects.get(id=int(course_id))

        #查询用户是否关联了该课程
        user_courses = UserCourse.objects.filter(user=request.user, course=course)
        if not user_courses:
            user_course = UserCourse(user=request.user, course=course)
            user_course.save()

        #取出学过这门课程的所有用户信息
        user_courses = UserCourse.objects.filter(course=course)
        #取出所有学过该课程的用户的id
        user_ids = [user_course.user.id for user_course in user_courses]
        #取出学过该课程的所有用户学过的所有课程信息
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)   #django model的用法  __in传进去的是一个list
        #取出学过该课程的所有用户学过的所有课程的id
        course_ids = [user_course.course.id for user_course in all_user_courses]
        #取出学过该用户学过的其他的课程(按点击量显示前3个)
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:3]

        #取出当前课程的课程资源
        all_resources = CourseResource.objects.filter(course=course)
        #取出所有评论信息
        all_comments = CourseComments.objects.all()
        return render(request, "course-comment.html", {
            "course": course,
            "course_resources": all_resources,
            "all_comments": all_comments,
            "relate_courses": relate_courses

        })


class AddCommentsView(View):
    """用户添加课程评论(利用ajax请求)"""
    def post(self, request):
        if not request.user.is_authenticated():    #判断用户是否登录 ，登录了才可以进行评论
            return HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')

        course_id = request.POST.get("course_id", 0)   #获取要评论的课程的id
        comments = request.POST.get("comments", "")    #获取要评论的内容
        if course_id > 0 and comments:              #id>0并且评论不为空
            course_comments = CourseComments()
            course = Course.objects.get(id=int(course_id))
            course_comments.course = course               #将数据保存到数据库中
            course_comments.comments = comments
            course_comments.user = request.user
            course_comments.save()
            return HttpResponse('{"status":"success", "msg":"添加成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"添加失败"}', content_type='application/json')


