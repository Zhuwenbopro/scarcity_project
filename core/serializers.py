from rest_framework import serializers
from .models import (
    BandwidthTagCost, FixedSchedule, TodayTask,
    LongTermGoal, ShortTermGoal, Task, EnergyLog
)
class LongTermGoalSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = LongTermGoal
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'username']


class ShortTermGoalSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = ShortTermGoal
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'username']


class TaskSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    short_term_goal_name = serializers.StringRelatedField(source='short_term_goal_ref', read_only=True)
    long_term_goal_name = serializers.StringRelatedField(source='long_term_goal_ref', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'user', 'short_term_goal_name', 'long_term_goal_name']


class EnergyLogSerializer(serializers.ModelSerializer):
    username = serializers.StringRelatedField(source='user', read_only=True)

    class Meta:
        model = EnergyLog
        fields = '__all__'
        read_only_fields = ['id', 'timestamp', 'username']


class BandwidthTagCostSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source='user_setting.user', read_only=True)

    class Meta:
        model = BandwidthTagCost
        fields = '__all__'
        read_only_fields = ['id', 'user']


class FixedScheduleSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source='user_setting.user', read_only=True)

    class Meta:
        model = FixedSchedule
        fields = '__all__'
        read_only_fields = ['id', 'user']


class TodayTaskSerializer(serializers.ModelSerializer):
    # 可以选择嵌套TaskSerializer以显示任务详情，或者只显示task_id并在前端单独获取任务详情
    task_details = TaskSerializer(source='task', read_only=True)  # 读取时显示任务详情
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())  # 写入时接收Task ID

    class Meta:
        model = TodayTask
        fields = '__all__'
        read_only_fields = ['user', 'added_at', 'id', 'task_details']

    # 在create或update时，需要确保task属于当前用户
    def validate_task(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.user != request.user:
                raise serializers.ValidationError("你只能选择你自己的任务添加到每日待办。")
        return value

    def create(self, validated_data):
        # 确保user字段被正确设置
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)