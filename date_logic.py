import holidays
import datetime
import dateparser
from dateutil.relativedelta import relativedelta

# UK Holidays (England)
uk_holidays = holidays.UK(years=[2024, 2025, 2026, 2027], subdiv='England')

def is_working_day(date_obj):
    """Check if a date is a working day (Mon-Fri) and not a bank holiday."""
    if date_obj.weekday() >= 5: # 5=Sat, 6=Sun
        return False
    if date_obj in uk_holidays:
        return False
    return True

def add_working_days(start_date, days):
    """Add N working days to a date, skipping weekends and holidays."""
    current_date = start_date
    added = 0
    while added < days:
        current_date += datetime.timedelta(days=1)
        if is_working_day(current_date):
            added += 1
    return current_date

def calculate_opt_out_dates(enrollment_text):
    """
    Parses natural language date (e.g. '3rd Jan 2026') 
    and calculates Start/End dates for Opt Out.
    Rule: Start = Enrollment + 3 Working Days
          End   = Start + 1 Calendar Month
    """
    # 1. Parse Date from Text
    # We use dateparser with specific settings to prefer DMY
    date_obj = dateparser.parse(enrollment_text, settings={'DATE_ORDER': 'DMY', 'PREFER_DATES_FROM': 'future'})
    
    if not date_obj:
        return None

    enrollment_date = date_obj.date()

    # 2. Calculate Start Date (Enrollment + 3 Working Days)
    opt_out_start = add_working_days(enrollment_date, 3)

    # 3. Calculate End Date (Start + 1 Month)
    # Using relativedelta correctly handles "Jan 31 + 1 month = Feb 28/29"
    opt_out_end = opt_out_start + relativedelta(months=1)

    return {
        "enrollment_date": enrollment_date,
        "start_date": opt_out_start,
        "end_date": opt_out_end,
        "summary": (
            f"Based on an enrollment date of {enrollment_date.strftime('%d %B %Y')}:\n"
            f"- Your Opt-out Period STARTS on: {opt_out_start.strftime('%A, %d %B %Y')} (3 working days later)\n"
            f"- Your Opt-out Period ENDS on: {opt_out_end.strftime('%A, %d %B %Y')} (1 month later)"
        )
    }

if __name__ == "__main__":
    # Test
    print(calculate_opt_out_dates("3rd Jan 2026")['summary'])
