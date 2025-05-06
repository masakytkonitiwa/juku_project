from django import forms
from .models import Homework
from .models import Event
from django.forms import modelformset_factory
from .models import Homework, HomeworkDetail


# forms.py

class HomeworkForm(forms.ModelForm):

    
    # 🆕 周回数の選択肢
    CYCLE_CHOICES = [
        (1, '1周のみ'),
        (2, '2周＋総復習'),
        (3, '3周＋総復習'),
    ]
    cycles = forms.ChoiceField(
        choices=CYCLE_CHOICES,
        initial=2,  # デフォルト2周
        label="周回数"
    )

    class Meta:
        model = Homework
        fields = ['subject']


class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['name', 'repeat', 'notes']


class HomeworkDetailForm(forms.ModelForm):
    class Meta:
        model = HomeworkDetail
        fields = ['course', 'problem_type', 'problem_count']

# フォームセット（最大5つまで追加できる）
HomeworkDetailFormSet = modelformset_factory(
    HomeworkDetail,
    form=HomeworkDetailForm,
    extra=1,  # 追加できるフォームの数（お好みで調整可）
)

from .models import Lesson
from django import forms

class LessonForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))  # 時刻入力
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))  # 時刻入力

    class Meta:
        model = Lesson
        fields = ['subject', 'course', 'start_time', 'end_time']

from .models import LessonTemplate
from django import forms

class LessonTemplateForm(forms.ModelForm):
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = LessonTemplate
        fields = ['subject', 'course', 'start_time', 'end_time']


from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label="ユーザー名",
        help_text="150文字以内。半角英数字と @/./+/-/_ が使用可能。"
    )
    password1 = forms.CharField(
        label="パスワード",
        strip=False,
        widget=forms.PasswordInput,
        help_text="8文字以上で設定してください。"
    )
    password2 = forms.CharField(
        label="パスワード（確認用）",
        widget=forms.PasswordInput,
        strip=False,
        help_text="確認のためもう一度入力してください。"
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

from .models import EventTemplate
from django import forms

class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = ['name', 'repeat', 'notes']
