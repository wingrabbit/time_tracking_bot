def seconds_to_hours(seconds):
    return str(int(seconds)//3600)+ ' hours '+str( (int(seconds)%3600)//60 )+' minutes'