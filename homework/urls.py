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
from . import views
from .views import signup_view
from django.urls import path
from . import views
from django.urls import path





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
    # homework/urls.py



    path('accounts/login/', auth_views.LoginView.as_view(template_name='homework/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('accounts/signup/', signup_view, name='signup'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('event_template/add/', views.add_event_template_view, name='add_event_template'),
    path('event_template/<int:template_id>/delete/', views.delete_event_template_view, name='delete_event_template'),  # 🔥 これ追加！

    path('subject/templates/', views.subject_template_list, name='subject_template_list'),
    # homework/urls.py
    path('subject/delete/<int:pk>/', views.delete_subject, name='delete_subject'),


    path('course/templates/', views.course_template_list, name='course_template_list'),
    path('course/delete/<int:pk>/', views.delete_course, name='delete_course'),


    path('subject/templates/homework/', views.homework_subject_template_list, name='homework_subject_template_list'),
    path('subject/templates/homework/delete/<int:pk>/', views.delete_homework_subject_template, name='delete_homework_subject_template'),
    
    path('course/templates/homework/', views.homework_course_template_list, name='homework_course_template_list'),
    path('course/templates/homework/delete/<int:pk>/', views.delete_homework_course, name='delete_homework_course'),

    path('problem_type/templates/', views.homework_problem_type_template_list, name='homework_problem_type_template_list'),
    path('problem_type/templates/delete/<int:pk>/', views.delete_homework_problem_type, name='delete_homework_problem_type'),


    path('problem_count/setting/',views.homework_problem_count_setting_view,name='homework_problem_count_setting'),


    path('homework/wizard/step1/', views.homework_wizard_step1, name='homework_wizard_step1'),
    path('homework/wizard/step2/', views.homework_wizard_step2, name='homework_wizard_step2'),
    path('homework/wizard/step3/', views.homework_wizard_step3, name='homework_wizard_step3'),
    path('homework/wizard/step4/', views.homework_wizard_step4, name='homework_wizard_step4'),
    path('homework/wizard/step5/', views.homework_wizard_step5, name='homework_wizard_step5'),
    path('homework/wizard/step6/', views.homework_wizard_step6, name='homework_wizard_step6'),
    path('homework/wizard/step7/', views.homework_wizard_step7, name='homework_wizard_step7'),
    
    
    path('add_event/step1/', views.add_event_step1, name='add_event_step1'),
    path('add_event/step2/', views.add_event_step2, name='add_event_step2'),
    path('add_event/step3/', views.add_event_step3, name='add_event_step3'),
    
    path('lesson/wizard/step1/', views.lesson_wizard_step1, name='lesson_wizard_step1'),
    path('lesson/wizard/step2/', views.lesson_wizard_step2, name='lesson_wizard_step2'),
    path('lesson/wizard/step3/', views.lesson_wizard_step3, name='lesson_wizard_step3'),

    path('homework/delete_line/<int:detail_id>/<str:date_str>/', views.delete_homework_line, name='delete_homework_line'),

]

