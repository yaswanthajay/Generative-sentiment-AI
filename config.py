import datetime

settings = {
    "username": "Yaswanth",
    "input_method": "voice",
    "time_of_day": "morning" if datetime.datetime.now().hour < 12 else "evening"
}
