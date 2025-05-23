from rest_framework.routers import DefaultRouter
from django.urls import path, include

from . import views

router = DefaultRouter()
router.register(r'long_term_goals', views.LongTermGoalViewSet, basename='longtermgoal')
router.register(r'short_term_goals', views.ShortTermGoalViewSet, basename='shorttermgoal')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'energy_log', views.EnergyLogViewSet, basename='energy')
router.register(r'bandwidth_tag_costs', views.BandwidthTagCostViewSet, basename='bandwidthtagcost')
router.register(r'fixed_schedules', views.FixedScheduleViewSet, basename='fixedschedule')
router.register(r'today_tasks', views.TodayTaskViewSet, basename='todaytask')

urlpatterns = [
    path('', include(router.urls)),
    path('api/get-csrf-token/', views.get_csrf_token, name='get-csrf-token'),
]
