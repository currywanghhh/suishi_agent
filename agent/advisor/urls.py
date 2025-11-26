from django.urls import path
from . import views, views_v2

urlpatterns = [
    # V1 原版 - 流式响应模式
    path('', views.index, name='index'),
    path('ask/', views.ask_advisor, name='ask_advisor'),
    
    # V2 新版 - 多轮对话模式
    path('v2/', views_v2.index_v2, name='index_v2'),
    path('v2/start/', views_v2.start_conversation, name='start_conversation'),
    path('v2/continue/', views_v2.continue_conversation, name='continue_conversation'),
    path('v2/quick/', views_v2.quick_answer, name='quick_answer'),
]
