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


class Event(models.Model):
    REPEAT_CHOICES = [
        ('none', '繰り返しなし'),
        ('weekly', '毎週'),
        ('monthly', '毎月'),
    ]

    name = models.CharField(max_length=100)  # イベント名
    date = models.DateField()                # 日付
    repeat = models.CharField(max_length=10, choices=REPEAT_CHOICES, default='none')  # 繰り返し
    notes = models.TextField(blank=True)     # メモ（任意）

    def __str__(self):
        return f"{self.name} ({self.date})"
    

class Lesson(models.Model):
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
    
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.get_subject_display()} / {self.get_course_display()} {self.date} {self.start_time}〜{self.end_time}"

class LessonTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ユーザーごとに管理
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    course = models.CharField(max_length=20, choices=COURSE_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.get_subject_display()} / {self.get_course_display()} {self.start_time}〜{self.end_time}"

from django.contrib.auth.models import User

class EventTemplate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ユーザーごとに管理
    name = models.CharField(max_length=100)  # イベント名
    repeat = models.CharField(
        max_length=10,
        choices=[
            ('none', '繰り返しなし'),
            ('weekly', '毎週'),
            ('monthly', '毎月')
        ],
        default='none'
    )
    notes = models.TextField(blank=True)  # メモ

    def __str__(self):
        return f"{self.name}（{self.get_repeat_display()}）"
