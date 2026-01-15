"""Time expression calculations."""

def get_finnish_hour(hour):
    """Get Finnish word for hour number in nominative case."""
    finnish_hours = {1: "yksi", 2: "kaksi", 3: "kolme", 4: "nelja", 5: "viisi", 6: "kuusi", 7: "seitseman", 8: "kahdeksan", 9: "yhdeksan", 10: "kymmenen",
                     11: "yksitoista", 12: "kaksitoista"}
    return finnish_hours.get(hour, str(hour))


def get_time_expression(now, language):
    """Generate a natural language time expression for the given time."""
    hours = now.hour
    minutes = now.minute

    # Convert 24-hour format to 12-hour format for expressions
    display_hour = hours % 12
    if display_hour == 0:
        display_hour = 12

    next_hour = (hours + 1) % 12
    if next_hour == 0:
        next_hour = 12

    finnish_current_hour = get_finnish_hour(display_hour)
    finnish_next_hour = get_finnish_hour(next_hour)

    if minutes <= 7:
        if language == 'fi':
            return f"noin {finnish_current_hour}"
        else:
            return f"about {display_hour} o'clock"
    elif minutes <= 22:
        if language == 'fi':
            return f"noin varttia yli {finnish_current_hour}"
        else:
            return f"about quarter past {display_hour}"
    elif minutes <= 37:
        if language == 'fi':
            return f"noin puoli {finnish_next_hour}"
        else:
            return f"about half past {display_hour}"
    elif minutes <= 52:
        if language == 'fi':
            return f"noin varttia vaille {finnish_next_hour}"
        else:
            return f"about quarter to {next_hour}"
    else:
        if language == 'fi':
            return f"noin {finnish_next_hour}"
        else:
            return f"about {next_hour} o'clock"


def get_time_of_day(hour, translations):
    """Get the time of day category."""
    time_of_day_translations = translations['time_expressions']['time_of_day']

    if 4 <= hour < 6:
        return time_of_day_translations['early_morning']
    elif 6 <= hour < 10:
        return time_of_day_translations['morning']
    elif 10 <= hour < 12:
        return time_of_day_translations['forenoon']
    elif 12 <= hour < 14:
        return time_of_day_translations['noon']
    elif 14 <= hour < 18:
        return time_of_day_translations['afternoon']
    elif 18 <= hour < 20:
        return time_of_day_translations['early_evening']
    elif 20 <= hour < 24:
        return time_of_day_translations['late_evening']
    else:  # 0-4
        return time_of_day_translations['night']
