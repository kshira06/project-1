from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Attendance
from datetime import datetime, time, timedelta
from django.utils.timezone import now as timezone_now
from calendar import month_name


@login_required
def attendance_main(request):
    user = request.user
    today = datetime.today().date()
    attendance, _ = Attendance.objects.get_or_create(user=user, date=today)

    if request.method == 'POST':
        action = request.POST.get('action')
        now = datetime.now().time()

        if action == 'clock':
            if not attendance.clock_in:
                attendance.clock_in = now
            elif not attendance.clock_out:
                attendance.clock_out = now
                work_duration = datetime.combine(today, attendance.clock_out) - datetime.combine(today, attendance.clock_in)
                if work_duration.total_seconds() > 9 * 3600:
                    attendance.is_overtime = True

        elif action == 'start_break' and not attendance.clock_out:
            if not attendance.break_start:
                attendance.break_start = now

        elif action == 'end_break' and not attendance.clock_out:
            if attendance.break_start and not attendance.break_end:
                attendance.break_end = now
                b_start = datetime.combine(today, attendance.break_start)
                b_end = datetime.combine(today, attendance.break_end)
                if (b_end - b_start) > timedelta(hours=1):
                    attendance.break_violation = True

        attendance.save()
        return redirect('attendance_main')

    return render(request, 'core/attendance_main.html', {
        'today_attendance': attendance,
        'days_range': range(1, 32)  # for calendar if needed
    })


@login_required
def attendance_history(request):
    user = request.user
    current_date = timezone_now()

    selected_date_str = request.GET.get('date')  # From calendar
    selected_month = request.GET.get('month')    # From month navigation

    attendance_entries = []
    selected_date = None

    # 1. If specific date is selected via calendar
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            records = Attendance.objects.filter(user=user, date=selected_date)
        except ValueError:
            records = Attendance.objects.filter(user=user, date__month=current_date.month, date__year=current_date.year)
    else:
        # 2. Fallback to month view
        if selected_month:
            try:
                selected_month = int(selected_month)
                selected_month = max(1, min(12, selected_month))
            except ValueError:
                selected_month = current_date.month
        else:
            selected_month = current_date.month

        selected_year = current_date.year
        records = Attendance.objects.filter(
            user=user,
            date__month=selected_month,
            date__year=selected_year
        ).order_by('-date')

    for entry in records:
        status = ""
        break_duration = "--"

        if entry.clock_in:
            if entry.clock_in < time(9, 0):
                status = "green"
            elif entry.clock_in <= time(9, 15):
                status = "orange"
            else:
                status = "red"

        if entry.clock_in and entry.clock_out:
            duration = datetime.combine(entry.date, entry.clock_out) - datetime.combine(entry.date, entry.clock_in)
            break_minutes = 0

            if entry.break_start and entry.break_end:
                b_duration = datetime.combine(entry.date, entry.break_end) - datetime.combine(entry.date, entry.break_start)
                break_minutes = b_duration.total_seconds() / 60

            total_minutes = duration.total_seconds() / 60 - break_minutes
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            break_duration = f"{hours:02d} : {minutes:02d} Hr"

        attendance_entries.append({
            'date': entry.date,
            'clock_in': entry.clock_in,
            'clock_out': entry.clock_out,
            'break_start': entry.break_start,
            'break_end': entry.break_end,
            'break_taken': break_duration,
            'status': status,
        })

    selected_month_final = selected_date.month if selected_date else selected_month
    selected_year_final = selected_date.year if selected_date else current_date.year

    context = {
        'attendance_entries': attendance_entries,
        'current_month_name': month_name[selected_month_final],
        'current_year': selected_year_final,
        'previous_month': selected_month_final - 1 if selected_month_final > 1 else 1,
        'next_month': selected_month_final + 1 if selected_month_final < 12 else 12,
        'selected_date': selected_date_str,
        'days_range': range(1, 32),  # ⬅️ for calendar looping if needed in HTML
    }

    return render(request, 'core/attendance_history.html', context)


@login_required
def gps_live_view(request):
    return render(request, 'core/gps_live.html')
