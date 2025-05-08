from django.db import models
from django.contrib.auth.models import User


# 🌟 共通の選択肢（Lesson, LessonTemplate 共用）
SUBJECT_CHOICES = [
    ('japanese', '国語'),
    ('math', '算数'),
    ('science', '理科'),
    ('social', '社会'),
    ('english', '英語'),
    ('other', 'その他'),
]

COURSE_CHOICES = [
    ('master', 'マスターコース'),
    ('top_level', '最高レベル特訓'),
    ('second', '2nd'),
]



class Homework(models.Model):

    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_subject_display()} ({self.planned_date})"

class HomeworkDetail(models.Model):


    PROBLEM_CHOICES = [
        ('practice', '練習問題'),
        ('b_problem', 'B問題'),
        ('c_problem', 'C問題'),
    ]

    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, related_name='details')
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    problem_type = models.CharField(max_length=20, choices=PROBLEM_CHOICES)
    problem_count = models.PositiveIntegerField()
    scheduled_task = models.CharField(max_length=200, blank=True) 

    def __str__(self):
        return f"{self.get_course_display()} - {self.get_problem_type_display()} {self.problem_count}問"

from django.contrib.auth.models import User

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 🔥これを追加
    name = models.CharField(max_length=100)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.date})"

from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField("科目名", max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
class Course(models.Model):
    name = models.CharField("コース名", max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Lesson(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject.name} / {self.course.name} {self.date} {self.start_time}〜{self.end_time}"


class LessonTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.ForeignKey('homework.Subject', on_delete=models.CASCADE)  # ← これ！
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.get_subject_display()} / {self.get_course_display()} {self.start_time}〜{self.end_time}"



from django.contrib.auth.models import User

class EventTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField("イベントの名前", max_length=100)

    def __str__(self):
        return self.name


class HomeworkSubjectTemplate(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class HomeworkCourse(models.Model):
    name = models.CharField("コース名", max_length=100)

    def __str__(self):
        return self.name
    
class HomeworkProblemType(models.Model):
    name = models.CharField("問題タイプ名", max_length=100)

    def __str__(self):
        return self.name
    

class HomeworkProblemCountSetting(models.Model):
    max_count = models.PositiveIntegerField("最大問題数")

    def __str__(self):
        return f"最大 {self.max_count} 問"
