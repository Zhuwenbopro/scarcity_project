from django.contrib import admin
from .models import (
    UserSetting, BandwidthTagCost, FixedSchedule,
    LongTermGoal, ShortTermGoal, Task, WorkLog, EnergyLog
)

admin.site.register(UserSetting)
admin.site.register(BandwidthTagCost)
admin.site.register(FixedSchedule)
admin.site.register(LongTermGoal)
admin.site.register(ShortTermGoal)
admin.site.register(Task)
admin.site.register(WorkLog)
admin.site.register(EnergyLog)