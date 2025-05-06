from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from homework.views import home_view  # トップページ用ビューを読み込む


urlpatterns = [
    path('', home_view, name='home'), 
    path('admin/', admin.site.urls),
    path('homework/', include('homework.urls')),  # ← 追加！
]

