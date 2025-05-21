from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db import connection

from .forms import (
    HomeworkForm,
    EventForm,
    EventTemplateForm,
    HomeworkDetailFormSet,
    LessonTemplateForm,
    SignUpForm,
    HomeworkSubjectTemplateForm,
    CourseForm,
    HomeworkCourseForm,
    HomeworkProblemTypeForm,
    HomeworkProblemCountSettingForm,
    SubjectForm
)

from .models import (
    Homework,
    Event,
    HomeworkDetail,
    Lesson,
    LessonTemplate,
    Subject,
    HomeworkSubjectTemplate,
    HomeworkCourse,
    HomeworkProblemType,
    HomeworkProblemCountSetting,
    EventTemplate,
    Course
)


from collections import defaultdict




def home_view(request):
    return render(request, 'homework/home.html')



def homework_create_view(request):
    import datetime
    from collections import defaultdict

    # 📅 カレンダーデータ作成
    today = datetime.date.today()
    week_start = today - datetime.timedelta(days=today.weekday())
    start_date = week_start - datetime.timedelta(weeks=1)
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(35)]

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




def get_second_sunday(year, month):
    d = date(year, month, 1)
    sundays = []
    while d.month == month:
        if d.weekday() == 6:  # Sunday
            sundays.append(d)
        d += timedelta(days=1)
    return sundays[1] if len(sundays) > 1 else sundays[0]


def weekly_view(request):
    print("【Render実行中】使用中のDB設定:", connection.settings_dict)
    today = date.today()
    view_mode = request.GET.get('view_mode', 'div')
    print("選択された表示形式:", view_mode)

    # ✅ 初期化しておく（すべての view_mode で使えるように）
    week_days = []

    # ✅ 表示範囲を決定
    if view_mode == '3weeks':
        week_start = today - timedelta(days=today.weekday())
        start_date = week_start - timedelta(weeks=1)
        end_date = start_date + timedelta(days=20)
        week_days = [start_date + timedelta(days=i) for i in range(21)]

    elif view_mode == 'month':
        start_date = today.replace(day=1)
        if start_date.weekday() != 0:
            start_date -= timedelta(days=start_date.weekday())
        next_month = (today.month % 12) + 1
        next_month_year = today.year + (today.month // 12)
        end_date = date(next_month_year, next_month, 1) - timedelta(days=1)
        if end_date.weekday() != 6:
            end_date += timedelta(days=(6 - end_date.weekday()))
        week_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

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
        week_days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

    elif view_mode == 'div':
        monday = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        start_date = monday
        end_date = monday + timedelta(days=20)
        week_days = [start_date + timedelta(days=i) for i in range(21)]

    else:
        start_date = today
        end_date = today + timedelta(days=6)
        week_days = [start_date + timedelta(days=i) for i in range(7)]




    print("カレンダー表示範囲:", start_date, "〜", end_date)

    # 📅 共通の週・日付リスト
    days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    weeks = [days[i:i+7] for i in range(0, len(days), 7)]

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




def add_event_view(request):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    start_date = week_start - timedelta(weeks=1)
    calendar_days = [start_date + timedelta(days=i) for i in range(35)]

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
                    day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
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
                day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
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
    calendar_days = [start_date + datetime.timedelta(days=i) for i in range(35)]  # 先週〜来週

    
    
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
            return redirect('lesson_wizard_step1')
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

@login_required
def delete_lesson_template(request, template_id):
    template = get_object_or_404(LessonTemplate, id=template_id, user=request.user)
    template.delete()
    return redirect('add_lesson_template')




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

def home_view(request):
    if request.user.is_authenticated:
        return redirect('weekly_view')  # ログインしてたらカレンダーへ
    else:
        return redirect('login')  # 未ログインならログインページへ



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



def delete_event_template_view(request, template_id):
    template = get_object_or_404(EventTemplate, id=template_id, user=request.user)
    template.delete()
    return redirect('add_event_template')



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



@login_required
def delete_course(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    course.delete()
    return redirect('course_template_list')


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





def homework_wizard_step1(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        print('subject:', subject)  # 科目IDを確認

        if subject:
            # セッションに科目IDを保存
            request.session["subject"] = subject
            print("subjectを受け取りました",subject)
                # 次のステップに進む
            print(f"Redirecting to {reverse('homework_wizard_step2')}")  # リダイレクト先URLの確認
            return redirect('homework_wizard_step2')

            # 次のステップに進む
            return redirect('homework_wizard_step2')
        else:
            # subject がない場合のエラーメッセージ
            print("subject is not provided")
            return render(request, 'homework/wizard_step1.html', {
                'error': '科目を選択してください。',
                'homework_subject_templates': HomeworkSubjectTemplate.objects.all(),
            })

    return render(request, 'homework/wizard_step1.html', {
        'homework_subject_templates': HomeworkSubjectTemplate.objects.all(),
    })



def homework_wizard_step2(request):
    # セッションに科目がなければ、step1に戻る
    if 'subject' not in request.session:
        return redirect('homework_wizard_step1')


########
    # セッションからsubjectを取得
    subject_id = request.session['subject']
    print("subject_id",subject_id)
    try:
        selected_subject = HomeworkSubjectTemplate.objects.get(id=subject_id)
        print("selected_subject",selected_subject)
        
    except HomeworkSubjectTemplate.DoesNotExist:
        selected_subject = None
        print("selected_subject779",selected_subject)
########

    if request.method == 'POST':
        # コースをPOSTで受け取る
        selected_course_id = request.POST.get('course')
        print("POSTで受け取ったcourse:", selected_course_id)

        if selected_course_id and HomeworkCourse.objects.filter(id=selected_course_id).exists():
            # courseをセッションに保存
            request.session['course'] = selected_course_id
            print(f"courseをセッションに保存しました: {selected_course_id}")

            # 次のステップに進む
            return redirect('homework_wizard_step3')
        else:
            print("courseが選ばれていないか、存在しません")
    
    courses = HomeworkCourse.objects.all()
    return render(request, 'homework/wizard_step2.html', {
        'courses': courses,
        'selected_subject': selected_subject,  # ← ここを追加
    })
    
    
def homework_wizard_step3(request):
    if 'course' not in request.session:
        return redirect('homework_wizard_step2')


########
    # セッションからsubjectを取得
    subject_id = request.session['subject']
    course_id = request.session['course']
    
    print("subject_id",subject_id)
    print("course_id",course_id)
    
    try:
        selected_subject = HomeworkSubjectTemplate.objects.get(id=subject_id)
    except HomeworkSubjectTemplate.DoesNotExist:
        selected_subject = None

    try:
        selected_course = HomeworkCourse.objects.get(id=course_id)
    except HomeworkCourse.DoesNotExist:
        selected_course = None
        
    print("selected_subject779",selected_subject)
    print("selected_course779",selected_course)
########


    # DBから科目とコースを取得（存在しなければNone）

    if request.method == 'POST':
        selected_type = request.POST.get('problem_type')
        print("POSTで受け取ったtype:", selected_type)
        
        if selected_type:
            request.session['problem_type'] = selected_type
            return redirect('homework_wizard_step4')

    problem_types = HomeworkProblemType.objects.all()


    return render(request, 'homework/wizard_step3.html', {
        'problem_types': problem_types,
        'selected_subject': selected_subject,
        'selected_course': selected_course,
    })


def homework_wizard_step4(request):
    if 'problem_type' not in request.session:
        return redirect('homework_wizard_step3')  # 問題タイプ未選択なら戻す

########
    # セッションからsubjectを取得
    subject_id = request.session['subject']
    course_id = request.session['course']
    problem_type_id = request.session['problem_type']
    
    print("subject_id",subject_id)
    print("course_id",course_id)
    print("problem_type_id",problem_type_id)
    
    try:
        selected_subject = HomeworkSubjectTemplate.objects.get(id=subject_id)
    except HomeworkSubjectTemplate.DoesNotExist:
        selected_subject = None

    try:
        selected_course = HomeworkCourse.objects.get(id=course_id)
    except HomeworkCourse.DoesNotExist:
        selected_course = None
        
    try:
        selected_problem_type = HomeworkProblemType.objects.get(id=problem_type_id)
    except HomeworkProblemType.DoesNotExist:
        selected_problem_type = None
        
    print("selected_subject779",selected_subject)
    print("selected_course779",selected_course)
########

    if request.method == 'POST':
        selected_count = request.POST.get('problem_count')
        print("POSTで受け取ったcount:", selected_count)
        if selected_count:
            request.session['problem_count'] = selected_count
            return redirect('homework_wizard_step5')

    # 最大問題数の設定（例：DBから取得、またはデフォルト30）
    from .models import HomeworkProblemCountSetting
    setting = HomeworkProblemCountSetting.objects.last()
    max_count = setting.max_count if setting else 30


    return render(request, 'homework/wizard_step4.html', {
            'range_1_max': range(1, max_count + 1),
            'selected_problem_type': selected_problem_type,
            'selected_subject': selected_subject,
            'selected_course': selected_course,
        })




def homework_wizard_step5(request):
    if 'problem_count' not in request.session:  # ✅ キー名を正しく
        return redirect('homework_wizard_step4')

#######
    # セッションからsubjectを取得
    subject_id = request.session['subject']
    course_id = request.session['course']
    problem_type_id = request.session['problem_type']
    problem_count_id = request.session['problem_count'] 
    
    print("subject_id",subject_id)
    print("course_id",course_id)
    print("problem_type_id",problem_type_id)
    print("problem_count_id",problem_count_id)
    
    try:
        selected_subject = HomeworkSubjectTemplate.objects.get(id=subject_id)
    except HomeworkSubjectTemplate.DoesNotExist:
        selected_subject = None

    try:
        selected_course = HomeworkCourse.objects.get(id=course_id)
    except HomeworkCourse.DoesNotExist:
        selected_course = None
        
    try:
        selected_problem_type = HomeworkProblemType.objects.get(id=problem_type_id)
    except HomeworkProblemType.DoesNotExist:
        selected_problem_type = None
        
   
    selected_count = request.session.get('problem_count')


        
    print("selected_count946",selected_count)
    print("selected_course779",selected_course)
########


    if request.method == 'POST':
        selected_cycles = request.POST.get('cycles')
        print("POSTで受け取ったcycles:", selected_cycles)
        if selected_cycles:
            request.session['cycles'] = selected_cycles
            return redirect('homework_wizard_step6')



    return render(request, 'homework/wizard_step5.html', {
            'selected_problem_type': selected_problem_type,
            'selected_subject': selected_subject,
            'selected_course': selected_course,
            'selected_count': selected_count,
        })


# Step6: 日付選択
def homework_wizard_step6(request):
    #######
    # セッションからsubjectを取得
    subject_id = request.session['subject']
    course_id = request.session['course']
    problem_type_id = request.session['problem_type']
    problem_count_id = request.session['problem_count'] 
    cycle_id = request.session['cycles'] 
    
    print("subject_id",subject_id)
    print("course_id",course_id)
    print("problem_type_id",problem_type_id)
    print("problem_count_id",problem_count_id)
    print("cycle_id",cycle_id)
    
    try:
        selected_subject = HomeworkSubjectTemplate.objects.get(id=subject_id)
    except HomeworkSubjectTemplate.DoesNotExist:
        selected_subject = None

    try:
        selected_course = HomeworkCourse.objects.get(id=course_id)
    except HomeworkCourse.DoesNotExist:
        selected_course = None
        
    try:
        selected_problem_type = HomeworkProblemType.objects.get(id=problem_type_id)
    except HomeworkProblemType.DoesNotExist:
        selected_problem_type = None
        
   
    selected_count = request.session.get('problem_count')
    selected_cycle = request.session.get('cycles')
    



        
    print("selected_count946",selected_count)
    print("selected_course779",selected_course)
########
    if request.method == 'POST':
        request.session['subject'] = request.POST.get('subject')
        request.session['course'] = request.POST.get('course')
        request.session['problem_type'] = request.POST.get('problem_type')
        request.session['problem_count'] = request.POST.get('problem_count')
        print("kokoha?",request.session['problem_count'] )
        request.session['cycles'] = request.POST.get('cycles')
        selected_dates = request.POST.get('selected_dates')
        if selected_dates:
            request.session['selected_dates'] = selected_dates.split(',')
            return redirect('homework_wizard_step7')

    # 📅 カレンダー表示：当週の月曜から35日分
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    calendar_days = [monday + timedelta(days=i) for i in range(35)]

    # 🔽 授業・宿題・イベントを日付ごとにまとめる
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
                    day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    context = {
        'calendar_days': calendar_days,
        'today': today,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'subject': request.session.get('subject'),
        'course': request.session.get('course'),
        'problem_type': request.session.get('problem_type'),
        'problem_count': request.session.get('problem_count'),
        'cycles': request.session.get('cycles'),
        'selected_problem_type': selected_problem_type,
        'selected_subject': selected_subject,
        'selected_course': selected_course,
        'selected_count': selected_count,
    }
    return render(request, 'homework/wizard_step6.html', context)

def homework_wizard_step7(request):
    # セッションから必要なデータを取得
    subject_id = request.session.get('subject')
    course_id = request.session.get('course')
    problem_type_id = request.session.get('problem_type')
    problem_count = int(request.session.get('problem_count', 0))
    cycles = int(request.session.get('cycles', 0))
    selected_dates = request.session.get('selected_dates', [])
    
    
    # セッションデータの整合性チェック
    if not all([subject_id, course_id, problem_type_id, problem_count, cycles, selected_dates]):
        return redirect('homework_wizard_step1')


    # ID → 名前に変換（ここが追加ポイント！）
    try:
        subject_obj = HomeworkSubjectTemplate.objects.get(id=subject_id)
        course_obj = HomeworkCourse.objects.get(id=course_id)
        problem_type_obj = HomeworkProblemType.objects.get(id=problem_type_id)
    except (HomeworkSubjectTemplate.DoesNotExist, HomeworkCourse.DoesNotExist, HomeworkProblemType.DoesNotExist):
        return redirect('homework_wizard_step1')
  

    subject_name = subject_obj.name
    course_name = course_obj.name
    problem_type_name = problem_type_obj.name    
    
        # 🔥 ここから POST処理を追加！
    if request.method == 'POST':
        # 宿題本体を保存
        homework = Homework.objects.create(subject=subject_name)

        # 詳細を保存
        detail = HomeworkDetail.objects.create(
            homework=homework,
            course=course_name,
            problem_type=problem_type_name,
            problem_count=problem_count,
        )

        # タスクを文字列にして保存
        raw_tasks = distribute_homework(problem_count, selected_dates, cycles)
        scheduled_summary = "\n".join([f"{date}: {task}" for date, task in raw_tasks])
        detail.scheduled_task = scheduled_summary
        detail.save()

        # セッションクリア（オプション）
        for key in ['subject', 'course', 'problem_type', 'problem_count', 'cycles', 'selected_dates']:
            request.session.pop(key, None)

        # カレンダーへリダイレクト
        return redirect('weekly_view')

    # カレンダー表示のための日付設定
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    calendar_days = [monday + timedelta(days=i) for i in range(35)]

    # 授業、宿題、イベントのデータ
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
                    day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    # タスクを生成（元のデータ構造：[(date, task内容)]）
    raw_tasks = distribute_homework(problem_count, selected_dates, cycles)

    # 科目・コース情報を追加した辞書形式に整形
    scheduled_tasks = [
        {
            'date': date,
            'task': task,
            'subject': subject_name,
            'course': course_name,
            'problem_type': problem_type_name,  # ← 追加！！
        }
        for date, task in raw_tasks
    ]



    
    # タスクを日付ごとにまとめる（変更後のdict形式に対応）
    tasks_by_date = defaultdict(list)
    for task in scheduled_tasks:
        tasks_by_date[task['date']].append(task)
            

    # コンテキストに名前を渡す
    context = {
        'subject': subject_name,
        'course': course_name,
        'problem_type': problem_type_name,
        'problem_count': problem_count,
        'cycles': cycles,
        'selected_dates': selected_dates,
        'calendar_days': calendar_days,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'scheduled_tasks': scheduled_tasks,
        'today': today,
    }

    return render(request, 'homework/wizard_step7.html', context)




def add_event_step1(request):
    templates = EventTemplate.objects.filter(user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            request.session['event_name'] = name
            return redirect('add_event_step2')

    return render(request, 'homework/add_event_step1.html', {
        'templates': templates,
    })

def add_event_step2(request):
    event_name = request.session.get('event_name')
    
    if 'event_name' not in request.session:
        return redirect('add_event_step1')

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    start_date = week_start - timedelta(weeks=1)
    calendar_days = [start_date + timedelta(days=i) for i in range(35)]

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
                    day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    if request.method == 'POST':
        selected_date = request.POST.get('selected_date')
        if selected_date:
            request.session['event_date'] = selected_date
            return redirect('add_event_step3')

    return render(request, 'homework/add_event_step2.html', {
        'calendar_days': calendar_days,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
        'today': today,
        'event_name': event_name,  # ← 追加
    })
    
    
def add_event_step3(request):
    event_name = request.session.get('event_name')
    event_date = request.session.get('event_date')

    if not event_name or not event_date:
        return redirect('add_event_step1')

    if request.method == 'POST':
        Event.objects.create(
            user=request.user,
            name=event_name,
            date=event_date
        )
        # セッションから削除（後始末）
        for key in ['event_name', 'event_date']:
            request.session.pop(key, None)

        return redirect('weekly_view')

    return render(request, 'homework/add_event_step3.html', {
        'event_name': event_name,
        'event_date': event_date,
    })

from django.shortcuts import render, redirect
from .models import LessonTemplate

def lesson_wizard_step1(request):
    templates = LessonTemplate.objects.filter(user=request.user)

    if request.method == 'POST':
        subject = request.POST.get('subject')
        course = request.POST.get('course')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if subject and course and start_time and end_time:
            request.session['lesson_subject'] = subject
            request.session['lesson_course'] = course
            request.session['lesson_start_time'] = start_time
            request.session['lesson_end_time'] = end_time
            return redirect('lesson_wizard_step2')

    return render(request, 'homework/lesson_wizard_step1.html', {
        'templates': templates,
    })

from datetime import timedelta, datetime
from django.utils import timezone
from collections import defaultdict
from .models import Lesson, Event, HomeworkDetail

def lesson_wizard_step2(request):
    # セッションから取得
    subject_id = request.session.get('lesson_subject')
    course_id = request.session.get('lesson_course')
    start_time = request.session.get('lesson_start_time')
    end_time = request.session.get('lesson_end_time')
    # ✅ Step1のデータがなければ戻す
    if not all(k in request.session for k in ['lesson_subject', 'lesson_course', 'lesson_start_time', 'lesson_end_time']):
        return redirect('lesson_wizard_step1')
    
    # 名前に変換
    try:
        subject = Subject.objects.get(id=subject_id)
        course = Course.objects.get(id=course_id)
    except (Subject.DoesNotExist, Course.DoesNotExist):
        return redirect('lesson_wizard_step1')



    if request.method == 'POST':
        raw_dates = request.POST.get('selected_dates')
        if raw_dates:
            selected_dates = [date.strip() for date in raw_dates.split(',') if date.strip()]
            request.session['lesson_selected_dates'] = selected_dates
            return redirect('lesson_wizard_step3')

    # カレンダー表示：今週の月曜から35日分
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    calendar_days = [monday + timedelta(days=i) for i in range(35)]

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
                    day = datetime.strptime(day_str.strip(), "%Y-%m-%d").date()
                    if calendar_days[0] <= day <= calendar_days[-1]:
                        homeworks_by_day[day].append({'detail': detail, 'task': task})

    context = {
        'subject': subject,
        'course': course,
        'start_time': start_time,
        'end_time': end_time,
        'calendar_days': calendar_days,
        'today': today,
        'events_by_day': events_by_day,
        'lessons_by_day': lessons_by_day,
        'homeworks_by_day': homeworks_by_day,
    }
    return render(request, 'homework/lesson_wizard_step2.html', context)

from .models import Subject, Course, Lesson

def lesson_wizard_step3(request):
    # セッションから取得
    subject_id = request.session.get('lesson_subject')
    course_id = request.session.get('lesson_course')
    start_time = request.session.get('lesson_start_time')
    end_time = request.session.get('lesson_end_time')
    selected_dates = request.session.get('lesson_selected_dates', [])

    if not all([subject_id, course_id, start_time, end_time, selected_dates]):
        return redirect('lesson_wizard_step1')

    # 名前に変換
    try:
        subject = Subject.objects.get(id=subject_id)
        course = Course.objects.get(id=course_id)
    except (Subject.DoesNotExist, Course.DoesNotExist):
        return redirect('lesson_wizard_step1')

    if request.method == 'POST':
        for date_str in selected_dates:
            lesson = Lesson(
                subject=subject,
                course=course,
                start_time=start_time,
                end_time=end_time,
                date=date_str
            )
            lesson.save()

        # セッションクリア（任意）
        for key in ['lesson_subject', 'lesson_course', 'lesson_start_time', 'lesson_end_time', 'lesson_selected_dates']:
            request.session.pop(key, None)

        return redirect('weekly_view')  # カレンダー画面に戻る

    return render(request, 'homework/lesson_wizard_step3.html', {
        'subject': subject,
        'course': course,
        'start_time': start_time,
        'end_time': end_time,
        'selected_dates': selected_dates,
    })
