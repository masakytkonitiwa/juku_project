from django import forms
from .models import Homework
from .models import Event
from django.forms import modelformset_factory
from .models import Homework, HomeworkDetail

from django.core.exceptions import ValidationError



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
        fields = []


class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = ['name']


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
    start_time = forms.TimeField(
        label='開始時刻',
        widget=forms.TimeInput(attrs={'type': 'time', 'step': 300})  # 5分刻み
    )
    end_time = forms.TimeField(
        label='終了時刻',
        widget=forms.TimeInput(attrs={'type': 'time', 'step': 300})
    )
    class Meta:
        model = LessonTemplate
        fields = ['subject', 'course', 'start_time', 'end_time']
        labels = {
            #'subject': '科目',
            'course': 'コース',
        }
        


    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")

        if start and end and start >= end:
            raise ValidationError("終了時刻は開始時刻より後にしてください。")



from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms

class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label="ユーザー名(半角英数字)",
    )
    password1 = forms.CharField(
        label="パスワード(8文字以上の半角英)",
        strip=False,
        widget=forms.PasswordInput,

    )
    password2 = forms.CharField(
        label="パスワード（確認用）",
        widget=forms.PasswordInput,
        strip=False,
        
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

from .models import EventTemplate
from django import forms

class EventTemplateForm(forms.ModelForm):
    class Meta:
        model = EventTemplate
        fields = ['name']

from django import forms
from .models import Subject

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']
        labels = {
            'name': '科目名',
        }


from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name']
        labels = {
            'name': 'コース名'
        }
        

# homework/forms.py
from django import forms
from .models import HomeworkSubjectTemplate

class HomeworkSubjectTemplateForm(forms.ModelForm):

    class Meta:
        model = HomeworkSubjectTemplate
        fields = ['name']
        labels = {
            'name': '科目名',  # ← ここでラベルを上書き
        }
        
from .models import HomeworkCourse

class HomeworkCourseForm(forms.ModelForm):
    class Meta:
        model = HomeworkCourse
        fields = ['name']
        labels = {
            'name': '宿題コース名',
        }
        
from .models import HomeworkProblemType

class HomeworkProblemTypeForm(forms.ModelForm):
    class Meta:
        model = HomeworkProblemType
        fields = ['name']
        labels = {
            'name': '問題タイプ名',
        }


from .models import HomeworkProblemCountSetting
from django import forms

class HomeworkProblemCountSettingForm(forms.ModelForm):
    class Meta:
        model = HomeworkProblemCountSetting
        fields = ['max_count']
        labels = {
            'max_count': '最大問題数',
        }
