from django.shortcuts import render, redirect
from .forms import HomeworkForm
from django.http import HttpResponse
import datetime
from collections import defaultdict
from django.shortcuts import render
from .forms import EventForm
from .models import Homework, Event
from .forms import HomeworkForm, HomeworkDetailFormSet
from datetime import date  # ← これを追加！
from .models import Lesson
from django.shortcuts import redirect
from .models import Homework, HomeworkDetail  # ← HomeworkDetail を追加！
from .models import LessonTemplate
from .models import Subject
from django.shortcuts import get_object_or_404
from .models import HomeworkSubjectTemplate  # ← ファイルの先頭に追加
from .models import HomeworkCourse  # ← 追加
from .models import HomeworkProblemType  # ← 忘れずに追加！
from .models import HomeworkProblemCountSetting 
from django.db import connection  # ← 追加する



def home_view(request):
    return render(request, 'homework/home.html')



def homework_create_view(request):
    import datetime
    from collections import defaultdict

    # 📅 カレンダーデータ作成
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    start_date = week_start - datetime.timedelta(weeks=1)
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]

    # 📌 最大問題数の設定を取得（デフォルトは30）
    latest_setting = HomeworkProblemCountSetting.objects.last()
    max_count = latest_setting.max_count if latest_setting else 30
    
    # 授業・宿題・イベントデータ
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        lessons_by_day[lesson.date].append(lesson)

    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " in line:
                    day_str, task = line.split(": ", 1)
                    day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        events_by_day[ev.date].append(ev)

    # 📝 フォーム処理
    if request.method == 'POST':
        form = HomeworkForm(request.POST)

        # 🔥 hiddenフィールドから値取得
        subject = request.POST.get('subject')
        cycles = request.POST.get('cycles')
        course = request.POST.get('course')
        problem_type = request.POST.get('problem_type')
        problem_count = request.POST.get('problem_count')

        # 🔥 日付取得
        selected_dates = []
        raw_dates = request.POST.get('selected_dates', '')
        if raw_dates:
            selected_dates = [
                datetime.datetime.strptime(date.strip(), "%Y-%m-%d").date()
                for date in raw_dates.split(',')
                if date
            ]
        
            # ✅ ここに配置（form.is_valid() の直後）
        print('form.is_valid:', form.is_valid())
        
        
        print('form.errors:', form.errors)
        print('subject:', subject)
        print('cycles:', cycles)
        print('course:', course)
        print('problem_type:', problem_type)
        print('problem_count:', problem_count)
        print('selected_dates:', selected_dates)
            
        # 🔥 バリデーション
        if form.is_valid() and subject and cycles and course and problem_type and problem_count and selected_dates:
            homework = form.save(commit=False)
            homework.subject = HomeworkSubjectTemplate.objects.get(id=subject)
            homework.save()
            
            detail = HomeworkDetail(
                homework=homework,
                course=course,
                problem_type=problem_type,
                problem_count=int(problem_count)
            )

            tasks = distribute_homework(detail.problem_count, selected_dates, int(cycles))
            scheduled_summary = "\n".join([f"{day}: {task}" for day, task in tasks])
            detail.scheduled_task = scheduled_summary
            detail.save()

            return redirect('add_homework')
    else:
        form = HomeworkForm()  # GET時だけフォーム作成

    # レンダリング
    return render(request, 'homework/homework_form.html', {
        'form': form,
        'calendar_days': calendar_days,
        'homeworks_by_day': homeworks_by_day,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'today': today,
        'range_1_max': range(1, max_count + 1),  # ✅ 新たに追加
        'homework_subject_templates': HomeworkSubjectTemplate.objects.all(),  
        'homework_courses': HomeworkCourse.objects.all(),  # ← これを追加
        'homework_problem_types': HomeworkProblemType.objects.all(), 

    })


from django.utils import timezone


from django.shortcuts import render
from django.utils import timezone
from collections import defaultdict
from datetime import datetime, timedelta, date
from .models import HomeworkDetail, Lesson, Event

def get_second_sunday(year, month):
    d = date(year, month, 1)
    sundays = []
    while d.month == month:
        if d.weekday() == 6:  # Sunday
            sundays.append(d)
        d += timedelta(days=1)
    return sundays[1] if len(sundays) > 1 else sundays[0]

def weekly_view(request):
    print("【Render実行中】使用中のDB設定:", connection.settings_dict)  # ← 追加する
    today = date.today()
    view_mode = request.GET.get('view_mode', '3weeks')
    print("選択された表示形式:", view_mode)

    # ✅ 表示範囲を決定（start_date / end_date）
    if view_mode == '3weeks':
        week_start = today - timedelta(days=today.weekday())
        start_date = week_start - timedelta(weeks=1)
        end_date = start_date + timedelta(days=20)

    elif view_mode == 'month':
        start_date = today.replace(day=1)
        if start_date.weekday() != 0:
            start_date -= timedelta(days=start_date.weekday())
        next_month = (today.month % 12) + 1
        next_month_year = today.year + (today.month // 12)
        end_date = date(next_month_year, next_month, 1) - timedelta(days=1)
        if end_date.weekday() != 6:
            end_date += timedelta(days=(6 - end_date.weekday()))

    elif view_mode == 'test':
        year, month = today.year, today.month
        second_sunday = get_second_sunday(year, month)
        if today > second_sunday:
            month += 1
            if month > 12:
                month = 1
                year += 1
            second_sunday = get_second_sunday(year, month)
        start_date = today
        if start_date.weekday() != 0:
            start_date -= timedelta(days=start_date.weekday())
        end_date = second_sunday

    elif view_mode == 'div':
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        week_days = [monday + timedelta(days=i) for i in range(7)]
        start_date = monday
        end_date = monday + timedelta(days=6)
    else:
        # fallback
        start_date = today
        end_date = today + timedelta(days=6)
        week_days = []

    print("カレンダー表示範囲:", start_date, "〜", end_date)

    # 📅 共通の週・日付リスト
    days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    weeks = [days[i:i+7] for i in range(0, len(days), 7)]

    # div 表示用の week_days（今週の7日間）
    if view_mode == 'div':
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        week_days = [monday + timedelta(days=i) for i in range(7)]
    else:
        week_days = []

    # 授業データ
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(start_date, end_date)):
        lessons_by_day[lesson.date].append(lesson)

    # 宿題データ
    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ':' in line:
                    try:
                        day_str, task = line.split(':', 1)
                        day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                        if start_date <= day <= end_date:
                            homeworks_by_day[day].append({'detail': detail, 'task': task.strip()})
                    except ValueError:
                        continue

    # イベントデータ
    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(start_date, end_date)):
        events_by_day[ev.date].append(ev)

    # 🔚 コンテキストに渡す
    context = {
        'weeks': weeks,
        'week_days': week_days,
        'view_mode': view_mode,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'events_by_day': events_by_day,
        'today': today,
    }

    return render(request, 'homework/weekly_view.html', context)





from django.shortcuts import render, redirect
from .models import Event, EventTemplate
import datetime
from collections import defaultdict
from .models import Lesson, HomeworkDetail

def add_event_view(request):
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    start_date = week_start - datetime.timedelta(weeks=1)
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]

    templates = EventTemplate.objects.filter(user=request.user)

    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        events_by_day[ev.date].append(ev)

    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        lessons_by_day[lesson.date].append(lesson)

    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " in line:
                    day_str, task = line.split(": ", 1)
                    day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    # 🔥 POST処理
    if request.method == 'POST':
        name = request.POST.get('name')
        selected_date = request.POST.get('selected_date')
        if name and selected_date:
            Event.objects.create(
                user=request.user,
                name=name,
                date=selected_date
            )
            return redirect('add_event')

    return render(request, 'homework/add_event.html', {
        'calendar_days': calendar_days,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'today': today,
        'templates': templates,
    })



def schedule_homework(problem_count, start_date):
    from datetime import timedelta
    block_size = problem_count // 2  # 前半・後半

    schedule = [
        (start_date, f"1周目：1〜{block_size}問"),
        (start_date + timedelta(days=1), f"1周目：{block_size + 1}〜{problem_count}問"),
        (start_date + timedelta(days=2), f"2周目：1〜{block_size}問"),
        (start_date + timedelta(days=3), f"2周目：{block_size + 1}〜{problem_count}問"),
        (start_date + timedelta(days=4), f"総復習：1〜{problem_count}問"),
    ]

    return schedule


# 例：今日の日付を渡す
#for day, task in zip(['月', '火', '水', '木', '金'], schedule_homework(16, date.today())):
#   print(day, task)

def distribute_homework(problem_count, selected_dates, cycles):
    tasks = []
    dates = sorted(selected_dates)
    total_days = len(dates)

    if total_days <= 1:
        # 🔥 1日だけ → 全部まとめてその日に入れる
        task_description = " / ".join([f"{i+1}周目：1〜{problem_count}問" for i in range(cycles)])
        tasks.append((dates[0], task_description))
        return tasks

    # 総復習日以外の日数
    assign_days = total_days - 1
    total_problems = problem_count * cycles

    base_per_day = total_problems // assign_days
    extra = total_problems % assign_days

    current_problem = 1  # 現在の問題番号（通し番号）
    current_cycle = 1  # 現在の周回

    for i in range(assign_days):
        problems_today = base_per_day + (1 if i < extra else 0)

        descriptions = []
        remaining = problems_today

        while remaining > 0:
            # この周回であと何問？
            remaining_in_cycle = problem_count - ((current_problem - 1) % problem_count)
            take = min(remaining, remaining_in_cycle)

            start_in_cycle = ((current_problem - 1) % problem_count) + 1
            end_in_cycle = start_in_cycle + take - 1

            descriptions.append(f"{current_cycle}周目：{start_in_cycle}〜{end_in_cycle}問")

            current_problem += take
            remaining -= take

            # 周回が進む
            if (current_problem - 1) % problem_count == 0:
                current_cycle += 1

        tasks.append((dates[i], " / ".join(descriptions)))

    # 総復習
    tasks.append((dates[-1], f"総復習：1〜{problem_count}問"))

    return tasks



def summary_view(request):
    import datetime

    summary_data = []

    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " not in line:
                    continue  # 空行や不正行をスキップ！
                day_str, task = line.split(": ", 1)
                day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                summary_data.append({
                    'date': day,
                    'subject': detail.homework.get_subject_display(),
                    'course': detail.get_course_display(),
                    'problem_type': detail.get_problem_type_display(),
                    'task': task,
                })

    summary_data.sort(key=lambda x: x['date'])

    return render(request, 'homework/summary.html', {'summary_data': summary_data})





def delete_homework(request, homework_id):
    homework = get_object_or_404(Homework, id=homework_id)
    homework.delete()
    return redirect('weekly_view')

def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('weekly_view')  # カレンダーに戻る

from .forms import LessonForm


def add_lesson_view(request):
    import datetime
    from collections import defaultdict

    # 📅 カレンダー（3週間分）
    
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())  # 今週の月曜
    start_date = week_start - datetime.timedelta(weeks=1)  # 先週の月曜
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]  # 先週〜来週

    
    
    # 授業テンプレート取得（ユーザーごと）
    templates = LessonTemplate.objects.filter(user=request.user)
    
    # 🔥 授業データ追加
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        lessons_by_day[lesson.date].append(lesson)


    # イベント
    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        events_by_day[ev.date].append(ev)

    # 宿題
    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " in line:
                    day_str, task = line.split(": ", 1)
                    day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    # フォーム
    if request.method == 'POST':
        form = LessonForm(request.POST)
        selected_dates = request.POST.get('selected_dates', '').split(',')
        selected_dates = [datetime.datetime.strptime(date.strip(), "%Y-%m-%d").date() for date in selected_dates if date]
        print("POSTデータ:", request.POST)
        print("selected_dates:", selected_dates)
        print("form.is_valid():", form.is_valid())

        if form.is_valid() and selected_dates:
            print("登録処理に入りました！")
            lesson_base = form.save(commit=False)  # フォームデータからベースを作る
            for selected_date in selected_dates:
                lesson = Lesson(  # 新しいインスタンスを作成
                    subject=lesson_base.subject,
                    course=lesson_base.course,
                    start_time=lesson_base.start_time,
                    end_time=lesson_base.end_time,
                    date=selected_date
                )
                lesson.save()
                print("登録された授業:", lesson.subject, lesson.date)
                
            return redirect('add_lesson')
    else:
        form = LessonForm()

    return render(request, 'homework/add_lesson.html', {
        'form': form,
        'calendar_days': calendar_days,
        'events_by_day': events_by_day,
        'homeworks_by_day': homeworks_by_day,
        'lessons_by_day': lessons_by_day,  # ← 追加
        'templates': templates,  # ← 追加！
        'today': today,  # 🔥 追加！
    })

def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    lesson.delete()
    return redirect('add_lesson')



from .models import LessonTemplate
from .forms import LessonTemplateForm
from django.contrib.auth.decorators import login_required

@login_required
def add_lesson_template_view(request):
    # ユーザーのテンプレート一覧
    templates = LessonTemplate.objects.filter(user=request.user)

    if request.method == 'POST':
        form = LessonTemplateForm(request.POST)
        if form.is_valid():
            lesson_template = form.save(commit=False)
            lesson_template.user = request.user  # ユーザーをセット
            lesson_template.save()
            return redirect('add_lesson_template')
    else:
        form = LessonTemplateForm()
    # 🔽 追加：subject の選択肢を取得してテンプレートに渡す
    subject_choices = Subject.objects.filter(user=request.user).values_list('id', 'name')
    course_choices = form.fields['course'].choices  # ←★ 追加！

    return render(request, 'homework/add_lesson_template.html', {
        'form': form,
        'templates': templates,  # 一覧も渡す
        'subject_choices': subject_choices,  # 🔥追加！
        'course_choices': course_choices,  # ←★ 追加！
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def delete_lesson_template(request, template_id):
    template = get_object_or_404(LessonTemplate, id=template_id, user=request.user)
    template.delete()
    return redirect('add_lesson_template')


from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # ログインも自動で
            return redirect('weekly_view')  # ログイン後のリダイレクト先
    else:
        form = SignUpForm()

    return render(request, 'homework/signup.html', {'form': form})

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def home_view(request):
    if request.user.is_authenticated:
        return redirect('weekly_view')  # ログインしてたらカレンダーへ
    else:
        return redirect('login')  # 未ログインならログインページへ

from .models import EventTemplate
from .forms import EventTemplateForm
from django.shortcuts import redirect

def add_event_template_view(request):
    templates = EventTemplate.objects.filter(user=request.user)  # 🔥 これ追加！

    if request.method == 'POST':
        form = EventTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user  # ログインユーザー紐づけ！
            template.save()
            return redirect('add_event_template')  # テンプレート作成ページにリダイレクト！
    else:
        form = EventTemplateForm()

    return render(request, 'homework/add_event_template.html', {
        'form': form,
        'templates': templates,  # 🔥 これ追加！
    })

# homework/views.py

from django.shortcuts import get_object_or_404, redirect
from .models import EventTemplate

def delete_event_template_view(request, template_id):
    template = get_object_or_404(EventTemplate, id=template_id, user=request.user)
    template.delete()
    return redirect('add_event_template')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Subject
from .forms import SubjectForm

@login_required
def subject_template_list(request):
    subjects = Subject.objects.filter(user=request.user)

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.user = request.user
            subject.save()
            return redirect('subject_template_list')
    else:
        form = SubjectForm()

    return render(request, 'homework/subject_template_list.html', {
        'form': form,
        'subjects': subjects
    })
    
    
from .models import Course
from .forms import CourseForm  # このフォームは後で作成します

@login_required
def course_template_list(request):
    courses = Course.objects.filter(user=request.user)

    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            return redirect('course_template_list')
    else:
        form = CourseForm()

    return render(request, 'homework/course_template_list.html', {
        'form': form,
        'courses': courses
    })
    
@login_required
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk, user=request.user)
    subject.delete()
    return redirect('subject_template_list')

from django.shortcuts import get_object_or_404, redirect
from .models import Course

@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    course.delete()
    return redirect('course_template_list')

# homework/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import HomeworkSubjectTemplate
from .forms import HomeworkSubjectTemplateForm  # 🔥 追加

def homework_subject_template_list(request):
    templates = HomeworkSubjectTemplate.objects.all()

    if request.method == 'POST':
        form = HomeworkSubjectTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homework_subject_template_list')
    else:
        form = HomeworkSubjectTemplateForm()

    return render(request, 'homework/homework_subject_template_list.html', {
        'form': form,
        'subjects': templates,
    })


def delete_homework_subject_template(request, pk):
    subject = get_object_or_404(HomeworkSubjectTemplate, pk=pk)
    subject.delete()
    return redirect('homework_subject_template_list')


from .models import HomeworkCourse
from .forms import HomeworkCourseForm

def homework_course_template_list(request):
    courses = HomeworkCourse.objects.all()

    if request.method == 'POST':
        form = HomeworkCourseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homework_course_template_list')
    else:
        form = HomeworkCourseForm()

    return render(request, 'homework/homework_course_template_list.html', {
        'form': form,
        'courses': courses
    })


def delete_homework_course(request, pk):
    course = get_object_or_404(HomeworkCourse, pk=pk)
    course.delete()
    return redirect('homework_course_template_list')


from .models import HomeworkProblemType
from .forms import HomeworkProblemTypeForm

def homework_problem_type_template_list(request):
    types = HomeworkProblemType.objects.all()

    if request.method == 'POST':
        form = HomeworkProblemTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homework_problem_type_template_list')
    else:
        form = HomeworkProblemTypeForm()

    return render(request, 'homework/homework_problem_type_template_list.html', {
        'form': form,
        'problem_types': types,
    })

def delete_homework_problem_type(request, pk):
    type_obj = get_object_or_404(HomeworkProblemType, pk=pk)
    type_obj.delete()
    return redirect('homework_problem_type_template_list')


from .models import HomeworkProblemCountSetting
from .forms import HomeworkProblemCountSettingForm

def homework_problem_count_setting_view(request):
    latest = HomeworkProblemCountSetting.objects.last()

    if request.method == 'POST':
        form = HomeworkProblemCountSettingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('homework_problem_count_setting')
    else:
        form = HomeworkProblemCountSettingForm()

    return render(request, 'homework/homework_problem_count_setting.html', {
        'form': form,
        'latest': latest,
    })
