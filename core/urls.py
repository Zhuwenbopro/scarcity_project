from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    LongTermGoalViewSet, ShortTermGoalViewSet, TaskViewSet, EnergyLogViewSet,
    BandwidthTagCostViewSet, FixedScheduleViewSet, TodayTaskViewSet
)

router = DefaultRouter()
router.register(r'long_term_goals', LongTermGoalViewSet, basename='longtermgoal')
router.register(r'short_term_goals', ShortTermGoalViewSet, basename='shorttermgoal')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'energy_log', EnergyLogViewSet, basename='energy')
router.register(r'bandwidth_tag_costs', BandwidthTagCostViewSet, basename='bandwidthtagcost')
router.register(r'fixed_schedules', FixedScheduleViewSet, basename='fixedschedule')
router.register(r'today_tasks', TodayTaskViewSet, basename='todaytask')

urlpatterns = [
    path('', include(router.urls)),
]