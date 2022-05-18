import datetime


def seconds_to_hours(seconds):
    return str(int(seconds)//3600)+ ' hours '+str( (int(seconds)%3600)//60 )+' minutes'

def get_six_months():
    year = int(datetime.date.today().strftime("%Y"))
    months = []
    for i in range(1, int(datetime.date.today().strftime("%m")) + 1):
        month = str(i)
        if i < 10:
            month = '0' + month
        months.append([month, str(year)])
    if len(months) < 6:
        for i in range((12 - 6 - len(months)), 13):
            month = str(i)
            if i < 10:
                month = '0' + month
            months.insert(0, [month, str(year - 1)])
    return months