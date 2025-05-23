from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import (
    LongTermGoal, ShortTermGoal, Task, EnergyLog,
    BandwidthTagCost, FixedSchedule, UserSetting, TodayTask
)
from .serializers import (
    LongTermGoalSerializer, ShortTermGoalSerializer, TaskSerializer, TodayTaskSerializer,
    EnergyLogSerializer, BandwidthTagCostSerializer, FixedScheduleSerializer
)
from django.middleware.csrf import get_token
from django.http import JsonResponse

def get_csrf_token(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

def home(request):
    return render(request, 'index.html')


class LongTermGoalViewSet(viewsets.ModelViewSet):
    serializer_class = LongTermGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只返回当前登录用户的数据
        return LongTermGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 自动绑定当前登录用户
        serializer.save(user=self.request.user)


class ShortTermGoalViewSet(viewsets.ModelViewSet):
    serializer_class = ShortTermGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShortTermGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        print("====== ShortTermGoalViewSet: create ======")  # 添加一个标记，方便定位
        print("Request Method:", request.method)
        print("Request Headers:", request.headers)  # 可以看看 Content-Type
        print("Request data RECEIVED:", request.data)  # <--- 关键输出1

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            print("Serializer ERRORS:", serializer.errors)  # <--- 关键输出2
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post', 'get', 'put', 'patch', 'delete']  # 你原来只允许 post，我帮你加全了

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EnergyLogViewSet(viewsets.ModelViewSet):
    serializer_class = EnergyLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post', 'get']  # 允许创建和查看

    def get_queryset(self):
        return EnergyLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BandwidthTagCostViewSet(viewsets.ModelViewSet):
    serializer_class = BandwidthTagCostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 只显示当前用户的 UserSetting 下的标签
        return BandwidthTagCost.objects.filter(user_setting__user=self.request.user)

    def perform_create(self, serializer):
        # 自动获取当前用户的 UserSetting 对象并绑定
        user_setting = UserSetting.objects.get(user=self.request.user)
        serializer.save(user_setting=user_setting)


class FixedScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = FixedScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FixedSchedule.objects.filter(user_setting__user=self.request.user)

    def perform_create(self, serializer):
        user_setting = UserSetting.objects.get(user=self.request.user)
        serializer.save(user_setting=user_setting)


class TodayTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TodayTaskSerializer
    permission_classes = [permissions.IsAuthenticated] # 确保用户已登录

    def get_queryset(self):
        queryset = TodayTask.objects.filter(user=self.request.user)
        date_param = self.request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date=date_param)
        return queryset.order_by('added_at')

    def perform_create(self, serializer):
        task_id = serializer.validated_data.get('task').id
        try:
            task_instance = Task.objects.get(id=task_id, user=self.request.user)
            serializer.save(user=self.request.user, task=task_instance)
        except Task.DoesNotExist:
            # 可以在序列化器层面处理这个校验，或者在这里返回错误
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"task": "指定的任务不存在或不属于您。"})