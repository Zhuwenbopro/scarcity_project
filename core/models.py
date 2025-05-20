from django.db import models
from django.contrib.auth.models import User  # Django内置用户模型
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


# --- 用户偏好设置相关模型 (与之前设计类似) ---
class UserSetting(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="用户")
    daily_work_hours = models.FloatField(
        default=8.0, validators=[MinValueValidator(0.1), MaxValueValidator(24.0)], verbose_name="每日计划工作时长 (小时)"
    )
    daily_energy_budget = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1)], verbose_name="每日能量预算 (点数)"
    )
    daily_bandwidth_budget = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1)], verbose_name="每日带宽预算 (点数)"
    )
    work_window_minutes = models.PositiveIntegerField(
        default=60, validators=[MinValueValidator(5)], verbose_name="工作窗口时长 (分钟)"
    )
    rest_window_minutes = models.PositiveIntegerField(
        default=5, validators=[MinValueValidator(1)], verbose_name="休息窗口时长 (分钟)"
    )
    last_modified = models.DateTimeField(auto_now=True, verbose_name="最后修改时间")

    def __str__(self):
        return f"{self.user.username}的偏好设置"

    class Meta:
        verbose_name = "用户偏好设置"
        verbose_name_plural = "用户偏好设置"


# (可选) 自动为新创建的User创建UserSetting记录 - 确保这个信号处理器在models.py或者apps.py的ready方法中
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_or_update_user_setting(sender, instance, created, **kwargs):
    if created:
        UserSetting.objects.create(user=instance)
    # 如果需要在User对象保存时也触发UserSetting的保存（例如更新last_modified），
    # 可以添加 instance.usersetting.save()，但通常OneToOneField会自动处理。
    # 确保 instance.usersetting 存在 (例如，通过上面的create)
    try:
        instance.usersetting.save()  # 确保UserSetting的last_modified更新等
    except UserSetting.DoesNotExist:
        # 这种情况理论上不应发生，因为上面created时会创建
        UserSetting.objects.create(user=instance)


class BandwidthTagCost(models.Model):
    user_setting = models.ForeignKey(
        UserSetting, on_delete=models.CASCADE, related_name="bandwidth_tag_costs", verbose_name="所属用户设置"
    )
    tag_name = models.CharField(max_length=100, verbose_name="标签名称")
    cost = models.PositiveIntegerField(default=1, verbose_name="带宽成本")

    def __str__(self):
        return f"标签 '{self.tag_name}': 成本 {self.cost} (用户: {self.user_setting.user.username})"

    class Meta:
        verbose_name = "标签带宽成本"
        verbose_name_plural = "标签带宽成本"
        unique_together = ('user_setting', 'tag_name')


class FixedSchedule(models.Model):
    class RecurrenceType(models.TextChoices):
        DAILY = 'DAILY', '每日'
        WEEKLY = 'WEEKLY', '每周'
        MONTHLY = 'MONTHLY', '每月'
        WORKDAY = 'WORKDAY', '工作日'
        WEEKEND = 'WEEKEND', '休息日'

    user_setting = models.ForeignKey(
        UserSetting, on_delete=models.CASCADE, related_name="fixed_schedules", verbose_name="所属用户设置"
    )
    name = models.CharField(max_length=255, verbose_name="日程名称")
    start_time = models.TimeField(verbose_name="开始时间 (HH:MM)")
    duration_minutes = models.PositiveIntegerField(verbose_name="时长 (分钟)")
    recurrence_type = models.CharField(
        max_length=10, choices=RecurrenceType.choices, default=RecurrenceType.DAILY, verbose_name="重复类型"
    )
    days_of_week = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="星期几 (0-6, 逗号分隔, 仅用于每周)",
        help_text="0=周一, ..., 6=周日。仅当类型为'每周'时有效。"
    )
    day_of_month = models.PositiveIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(31)],
        verbose_name="几号 (1-31, 仅用于每月)", help_text="仅当类型为'每月'时有效。"
    )

    def __str__(self):
        return f"{self.name} ({self.get_recurrence_type_display()}) - 用户: {self.user_setting.user.username}"

    class Meta:
        verbose_name = "固定日程"
        verbose_name_plural = "固定日程"


class LongTermGoal(models.Model):
    class GoalStatus(models.TextChoices):
        PURSUING = '持续追求', '持续追求'
        ARCHIVED = '已归档', '已归档'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="long_term_goals", verbose_name="所属用户")
    name = models.TextField(verbose_name="长期目标描述")
    status = models.CharField(
        max_length=50, choices=GoalStatus.choices, default=GoalStatus.PURSUING, verbose_name="目标状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.name} (用户: {self.user.username})"

    class Meta:
        verbose_name = "长期目标"
        verbose_name_plural = "长期目标清单"
        # 可选：确保同一个用户下的长期目标名称唯一（如果需要）
        # unique_together = ('user', 'name')


class ShortTermGoal(models.Model):
    class ShortTermGoalStatus(models.TextChoices):
        NOT_STARTED = '未开始', '未开始'
        IN_PROGRESS = '进行中', '进行中'
        COMPLETED = '已完成', '已完成'
        POSTPONED = '已推迟', '已推迟'
        ABANDONED = '已放弃', '已放弃'
        BLOCKED = '阻塞', '阻塞'

    class PriorityChoices(models.TextChoices):
        HIGH_URGENT = '重要且紧急', '重要且紧急'
        HIGH_NOT_URGENT = '重要不紧急', '重要不紧急'
        LOW_URGENT = '紧急不重要', '紧急不重要'
        LOW_NOT_URGENT = '不重要不紧急', '不重要不紧急'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="short_term_goals", verbose_name="所属用户")
    name = models.TextField(verbose_name="短期目标描述")
    target_date = models.DateField(null=True, blank=True, verbose_name="目标完成日期")
    priority = models.CharField(
        max_length=50, choices=PriorityChoices.choices, default=PriorityChoices.HIGH_NOT_URGENT, verbose_name="优先级"
    )
    status = models.CharField(
        max_length=50, choices=ShortTermGoalStatus.choices, default=ShortTermGoalStatus.NOT_STARTED, verbose_name="目标状态"
    )
    completion_date = models.DateField(null=True, blank=True, verbose_name="实际完成日期")
    estimated_time_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="预估天数")
    actual_time_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="实际天数")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.name} (用户: {self.user.username})"

    class Meta:
        verbose_name = "短期目标"
        verbose_name_plural = "短期目标清单"
        # unique_together = ('user', 'name')

    # (可选) 在保存时校验 long_term_goal_ref 是否属于当前用户
    # def clean(self):
    #     from django.core.exceptions import ValidationError
    #     if self.long_term_goal_ref and self.long_term_goal_ref.user != self.user:
    #         raise ValidationError({'long_term_goal_ref': '关联的长期目标不属于当前用户。'})

class EnergyLevel(models.TextChoices):
    HIGH = '高', '高'
    MEDIUM = '中', '中'
    LOW = '低', '低'
    NONE = '', '未设置'


class Task(models.Model):
    class TaskStatus(models.TextChoices):
        NOT_STARTED = '未开始', '未开始'
        IN_PROGRESS = '进行中', '进行中'
        COMPLETED = '已完成', '已完成'
        WAITING = '等待中', '等待中'
        POSTPONED = '已推迟', '已推迟'
        CANCELLED = '已取消', '已取消'
        BLOCKED = '阻塞', '阻塞'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tasks", verbose_name="所属用户")
    name = models.CharField(max_length=255, verbose_name="任务名称")
    short_term_goal_ref = models.ForeignKey(
        ShortTermGoal, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="关联的短期目标", related_name="tasks_set"  # related_name不能与User的tasks冲突
    )
    long_term_goal_ref = models.ForeignKey(  # 如果Task也直接关联长期目标
        LongTermGoal, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="关联的长期目标 (直接)", related_name="direct_tasks"
    )
    priority = models.PositiveIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], default=3, verbose_name="优先级(1-5,小优先)"
    )
    energy_level_estimate = models.CharField(
        max_length=10, choices=EnergyLevel.choices, default=EnergyLevel.NONE, blank=True, verbose_name="精力预估"
    )
    tags = models.TextField(blank=True, verbose_name="标签 (逗号分隔)")
    estimated_time_minutes = models.PositiveIntegerField(null=True, blank=True, verbose_name="预估分钟数")
    actual_time_minutes = models.PositiveIntegerField(default=0, verbose_name="实际分钟数")
    start_date = models.DateField(null=True, blank=True, verbose_name="计划开始日期")
    end_date = models.DateField(null=True, blank=True, verbose_name="计划截止日期")
    completion_date = models.DateField(null=True, blank=True, verbose_name="实际完成日期")
    status = models.CharField(
        max_length=50, choices=TaskStatus.choices, default=TaskStatus.NOT_STARTED, verbose_name="任务状态"
    )
    type = models.CharField(max_length=100, blank=True, default="", verbose_name="任务类型 (临时)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    def __str__(self):
        return f"{self.name} (P{self.priority}, 用户: {self.user.username})"

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务清单"
        ordering = ['user', 'priority', 'end_date', 'name']  # 按用户，再按优先级等排序


class WorkLog(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="work_logs", verbose_name="所属用户")
    # 关联到已执行的任务
    task_ref = models.ForeignKey(
        Task,
        on_delete=models.SET_NULL,  # 如果任务被删除，日志中的关联设为NULL，但日志本身保留
        null=True,
        blank=True,
        verbose_name="关联任务对象"
    )
    task_name_snapshot = models.CharField(max_length=255, verbose_name="任务名称 (快照)",
                                          help_text="记录工作时的任务名称，即使原任务被修改或删除")
    task_source = models.CharField(max_length=100, blank=True, null=True, verbose_name="任务来源")
    timestamp_start = models.DateTimeField(verbose_name="会话开始时间")
    timestamp_end = models.DateTimeField(verbose_name="会话结束时间")
    duration_minutes = models.PositiveIntegerField(verbose_name="会话时长(分钟)")
    user_reported_status_at_end = models.CharField(max_length=100, blank=True, null=True,
                                                   verbose_name="用户报告的结束状态")
    energy_cost = models.CharField(
        max_length=10, choices=EnergyLevel.choices, blank=True, null=True, verbose_name="精力消耗评估"
    )
    tags_snapshot = models.TextField(blank=True, null=True, verbose_name="相关标签 (快照)")
    logged_at = models.DateTimeField(auto_now_add=True, verbose_name="日志记录时间")

    def __str__(self):
        return f"Log: {self.task_name_snapshot} ({self.timestamp_start.strftime('%Y-%m-%d %H:%M')}, 用户: {self.user.username})"

    class Meta:
        verbose_name = "工作日志"
        verbose_name_plural = "工作日志"
        ordering = ['user', '-timestamp_start']


class EnergyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="energy_logs", verbose_name="所属用户")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="记录时间")
    energy_level = models.CharField(max_length=10, choices=EnergyLevel.choices, blank=True, null=True,
                                    verbose_name="精力水平")
    current_activity_type = models.CharField(max_length=255, blank=True, null=True, verbose_name="当前活动类型")

    def __str__(self):
        return f"Energy: {self.energy_level} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}, 用户: {self.user.username})"

    class Meta:
        verbose_name = "精力日志"
        verbose_name_plural = "精力日志"
        ordering = ['user', '-timestamp']


class TodayTask(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="today_tasks_entries",
                             verbose_name="所属用户")
    date = models.DateField(verbose_name="日期")
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,  # 如果任务被删除，这条今日任务记录也应该删除
        related_name="listed_in_today_tasks",
        verbose_name="关联的任务"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="添加到今日任务时间")

    def __str__(self):
        return f"{self.user.username} - {self.date.strftime('%Y-%m-%d')} - Task: {self.task.name}"

    class Meta:
        verbose_name = "每日待办任务"
        verbose_name_plural = "每日待办任务"
        unique_together = ('user', 'date', 'task')