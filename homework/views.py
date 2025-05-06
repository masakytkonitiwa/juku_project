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

from django.shortcuts import get_object_or_404


def home_view(request):
    return render(request, 'homework/home.html')


def homework_create_view(request):
    import datetime
    from collections import defaultdict

    # 📅 カレンダーデータ作成（POSTでもGETでも必要）

    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    start_date = week_start - datetime.timedelta(weeks=1)  # 先週の月曜

    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]  # 先週〜来週まで
    
    # 授業データ追加
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        lessons_by_day[lesson.date].append(lesson)

    # 🔥 宿題データを HomeworkDetail から取得
    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " in line:  # ← ここ！
                    day_str, task = line.split(": ", 1)
                    day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    # イベントデータ
    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        events_by_day[ev.date].append(ev)

    # 📝 フォーム処理

def homework_create_view(request):
    import datetime
    from collections import defaultdict

    # 📅 カレンダーデータ作成
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    start_date = week_start - datetime.timedelta(weeks=1)
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]
    
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
        
        # 🔥 バリデーション
        if form.is_valid() and subject and cycles and course and problem_type and problem_count and selected_dates:
            homework = form.save()
            
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

            return redirect('weekly_view')
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
        'range_0_30': range(0, 31),
    })



def weekly_view(request):
    import datetime
    from collections import defaultdict

    today = datetime.date.today()
    view_mode = request.GET.get('view_mode', '3weeks')  # デフォルトは3週間
    view_mode = request.GET.get('view_mode', '3weeks')  # デフォルトは3weeks
    print("選択された表示形式:", view_mode)

    if view_mode == '3weeks':
        week_start = today - datetime.timedelta(days=today.weekday())  # 今週の月曜
        start_date = week_start - datetime.timedelta(weeks=1)  # 先週の月曜
        end_date = start_date + datetime.timedelta(days=20)  # 3週間（21日間）

    elif view_mode == 'month':
        start_date = today.replace(day=1)
        # 月初が月曜じゃなければ、前の月曜に戻す
        weekday = start_date.weekday()
        if weekday != 0:
            start_date -= datetime.timedelta(days=weekday)

        # 月末
        next_month = (today.month % 12) + 1
        next_month_year = today.year + (today.month // 12)
        end_date = datetime.date(next_month_year, next_month, 1) - datetime.timedelta(days=1)
        # 月末が日曜じゃなければ、次の日曜まで延ばす
        weekday = end_date.weekday()
        if weekday != 6:
            end_date += datetime.timedelta(days=(6 - weekday))

    elif view_mode == 'test':
        # 第二日曜まで
        month = today.month
        year = today.year
        second_sunday = get_second_sunday(year, month)
        if today > second_sunday:
            # 翌月の第二日曜日
            month += 1
            if month > 12:
                month = 1
                year += 1
            second_sunday = get_second_sunday(year, month)
        start_date = today
        # スタートを月曜始まりに戻す
        weekday = start_date.weekday()
        if weekday != 0:
            start_date -= datetime.timedelta(days=weekday)
        end_date = second_sunday
        
    print("カレンダー表示範囲:", start_date, "〜", end_date)


    # 日付リスト
    days = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    weeks = [days[i:i+7] for i in range(0, len(days), 7)]
    


    # 授業データ
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(start_date, end_date)):
        lessons_by_day[lesson.date].append(lesson)

    # 宿題データ
    homeworks_by_day = defaultdict(list)
    details = HomeworkDetail.objects.all()
    for detail in details:
        if detail.scheduled_task:
            for line in detail.scheduled_task.split('\n'):
                if ':' in line:
                    day_str, task = line.split(':', 1)
                    try:
                        day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                        if start_date <= day <= end_date:
                            homeworks_by_day[day].append({'detail': detail, 'task': task.strip()})
                    except ValueError:
                        pass

    # イベントデータ
    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(start_date, end_date)):
        events_by_day[ev.date].append(ev)

    # コンテキスト
    context = {
        'weeks': weeks,
        'view_mode': view_mode,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'events_by_day': events_by_day,
        'today': today,
    }


    # 今までのデータ取得処理（省略）
    context = {
        'weeks': weeks,
        'view_mode': view_mode,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'events_by_day': events_by_day,
        'today': today,
    }
    return render(request, 'homework/weekly_view.html', context)

def get_second_sunday(year, month):
    import datetime
    day = datetime.date(year, month, 1)
    sundays = []
    while day.month == month:
        if day.weekday() == 6:  # 日曜日
            sundays.append(day)
        day += datetime.timedelta(days=1)
    return sundays[1]  # 第二日曜






def add_event_view(request):
    import datetime
    from collections import defaultdict
    from .models import Lesson, HomeworkDetail, Event  # モデル読み込み
    from .models import EventTemplate

    # 📅 カレンダーデータ作成


    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())  # 今週の月曜
    start_date = week_start - datetime.timedelta(weeks=1)  # 先週の月曜
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(21)]  # 先週〜来週

    # 🔥 ここを追加！（ユーザーごとのテンプレート取得）
    templates = EventTemplate.objects.filter(user=request.user)


    # 📅 イベントデータ
    events_by_day = defaultdict(list)
    for ev in Event.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        events_by_day[ev.date].append(ev)

    # 🏫 授業データ
    lessons_by_day = defaultdict(list)
    for lesson in Lesson.objects.filter(date__range=(calendar_days[0], calendar_days[-1])):
        lessons_by_day[lesson.date].append(lesson)

    # 📋 宿題データ
    homeworks_by_day = defaultdict(list)
    for detail in HomeworkDetail.objects.all():
        if detail.scheduled_task:
            for line in detail.scheduled_task.splitlines():
                if ": " in line:
                    day_str, task = line.split(": ", 1)
                    day = datetime.datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    # フォーム処理
    if request.method == 'POST':
        form = EventForm(request.POST)
        selected_date = request.POST.get('selected_date')
        if selected_date:
            form.instance.date = selected_date

        if form.is_valid():
            form.save()
            return redirect('weekly_view')
    else:
        form = EventForm()

    # 🔥 授業・宿題データも渡す
    return render(request, 'homework/add_event.html', {
        'form': form,
        'calendar_days': calendar_days,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,  # ← 追加！
        'homeworks_by_day': homeworks_by_day,  # ← 追加！
        'today': today,  # 🔥 追加！
        'templates': templates,  # 🔥 テンプレートを渡す！
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
                
            return redirect('weekly_view')
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
    return redirect('weekly_view')



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

    return render(request, 'homework/add_lesson_template.html', {
        'form': form,
        'templates': templates,  # 一覧も渡す
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

