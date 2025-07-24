from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Attendance
from datetime import datetime, time, timedelta, date
from django.utils.timezone import now as timezone_now
from calendar import month_name, monthrange


@login_required
def attendance_main(request):
    user = request.user
    today = datetime.today().date()
    attendance, _ = Attendance.objects.get_or_create(user=user, date=today)

    # Process Clock IN/OUT and Breaks
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

    # --- Total Working Hours & Total Breaks for current month ---
    current_month = today.month
    current_year = today.year
    records = Attendance.objects.filter(user=user, date__month=current_month, date__year=current_year)

    total_working_minutes = 0
    total_break_minutes = 0

    for record in records:
        if record.clock_in and record.clock_out:
            start = datetime.combine(record.date, record.clock_in)
            end = datetime.combine(record.date, record.clock_out)
            total_minutes = (end - start).total_seconds() / 60

            # Minus break if exists
            if record.break_start and record.break_end:
                b_start = datetime.combine(record.date, record.break_start)
                b_end = datetime.combine(record.date, record.break_end)
                break_duration = (b_end - b_start).total_seconds() / 60
                total_minutes -= break_duration
                total_break_minutes += break_duration

            total_working_minutes += total_minutes

    # Convert mins ➜ Hr:Min format
    working_hours = int(total_working_minutes // 60)
    working_minutes = int(total_working_minutes % 60)
    total_working_hours_str = f"{working_hours:02d}:{working_minutes:02d} Hrs"

    break_hours = int(total_break_minutes // 60)
    break_minutes = int(total_break_minutes % 60)
    total_break_taken_str = f"{break_hours:02d}:{break_minutes:02d} Hrs"

    # ✅ ADDITION: Calculate total_time_balance and total_leaves
    working_days = records.exclude(clock_in=None).count()
    expected_minutes = working_days * 9 * 60
    time_balance_minutes = total_working_minutes - expected_minutes

    balance_hours = int(abs(time_balance_minutes) // 60)
    balance_minutes = int(abs(time_balance_minutes) % 60)
    sign = "-" if time_balance_minutes < 0 else "+"
    total_time_balance = f"{sign} {balance_hours:02d}:{balance_minutes:02d} Hrs"

    # ✅ FIXED: Total Leaves excluding Sundays
    total_days = monthrange(current_year, current_month)[1]
    total_leaves = 0

    for day in range(1, today.day + 1):  # Loop only till today
        current_date = date(current_year, current_month, day)
        if current_date.weekday() == 6:  # Sunday = 6
            continue
        if not Attendance.objects.filter(user=user, date=current_date, clock_in__isnull=False, clock_out__isnull=False).exists():
            total_leaves += 1

    return render(request, 'core/attendance_main.html', {
        'today_attendance': attendance,
        'days_range': range(1, 32),
        'total_working_hours': total_working_hours_str,
        'total_break_taken': total_break_taken_str,
        'total_time_balance': total_time_balance,
        'total_leaves': total_leaves,
    })

@login_required
def attendance_history(request):
    user = request.user
    current_date = timezone_now()

    selected_date_str = request.GET.get('date')
    selected_month = request.GET.get('month')

    attendance_entries = []
    selected_date = None

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            records = Attendance.objects.filter(user=user, date=selected_date)
        except ValueError:
            records = Attendance.objects.filter(user=user, date__month=current_date.month, date__year=current_date.year)
    else:
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
            break_duration = f"{hours:02d}:{minutes:02d} Hr"

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
        'days_range': range(1, 32),
    }

    return render(request, 'core/attendance_history.html', context)


@login_required
def gps_live_view(request):
    return render(request, 'core/gps_live.html')
