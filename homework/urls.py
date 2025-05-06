from django.urls import path
from .views import homework_create_view
from .views import homework_create_view # ← 追加
from .views import weekly_view
from .views import home_view
from .views import add_event_view, add_lesson_view # イベント登録ビューを読み込む
from .views import summary_view  # ← 追加
from . import views
from .views import add_lesson_template_view, delete_lesson_template
from django.contrib.auth import views as auth_views

from .views import signup_view


urlpatterns = [
    path('', home_view, name='home'),  # ← トップページとして表示
    path('add/', homework_create_view, name='add_homework'),
    path('add_event/', add_event_view, name='add_event'),  # ← イベント登録ページ
    path('event/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),

    path('week/', weekly_view, name='weekly_view'),
    path('summary/', summary_view, name='homework_summary'),
    path('delete/<int:homework_id>/', views.delete_homework, name='delete_homework'),  # 🆕 追加！
    path('lesson/delete/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),

    path('homework/add_lesson/', add_lesson_view, name='add_lesson'),
    
    path('lesson_template/add/', add_lesson_template_view, name='add_lesson_template'),
    path('lesson_template/<int:template_id>/delete/', delete_lesson_template, name='delete_lesson_template'),

    path('accounts/login/', auth_views.LoginView.as_view(template_name='homework/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/signup/', signup_view, name='signup'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('event_template/add/', views.add_event_template_view, name='add_event_template'),
    path('event_template/<int:template_id>/delete/', views.delete_event_template_view, name='delete_event_template'),  # 🔥 これ追加！


]
