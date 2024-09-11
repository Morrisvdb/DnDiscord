import datetime

def parse_time(time):
    """This demon parses time from a string.

    Args:
        time (str): The time

    Returns:
        datetime.time: The time object
    """
    try:
        time = time.split(":")
        hour = int(time[0])
        minute = int(time[1])
        if hour < 0 or hour > 23 or minute < 0 or minute > 59:
            return None
        time = datetime.time(hour=hour, minute=minute)
        return time
    except:
        return None
        # try:
        #     time = time.split(";")
        #     hour = int(time[0])
        #     minute = int(time[1])
        #     if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        #         return None
        #     time = datetime.time(hour=hour, minute=minute)
        #     return time
        # except:
        #     try:
        #         time = time.split("-")
        #         hour = int(time[0])
        #         minute = int(time[1])
        #         if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        #             return None
        #         time = datetime.time(hour=hour, minute=minute)
        #         return time
        #     except:
        #         try:
        #             time = time.split(" ")
        #             hour = int(time[0])
        #             minute = int(time[1])
        #             if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        #                 return None
        #             time = datetime.time(hour=hour, minute=minute)
        #             return time
        #         except:
        #             return None