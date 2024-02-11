import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import regex
from regex import time_re_pattern

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dateutil.relativedelta import relativedelta, FR, MO, TU, WE, TH, SA, SU

NAME = "slack-tz-helper"
logger = logging.getLogger(NAME)

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
bolt = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def send_ephemeral_message_to_channel_members(sender_id, channel_id, trigger_message, time_to_utc_dic, suffix):
    try:
        result = client.conversations_members(channel=channel_id)
        members = result['members']

        for user_id in members:
            # don't send a message to the bot itself
            # if user_id in {bolt.client.auth_test()["user_id"], sender_id}:
            if user_id in {bolt.client.auth_test()["user_id"]}:
                continue

            receiver_tz = ZoneInfo(get_user_timezone(get_user_info(user_id)))

            msg = trigger_message
            for original_time, utc_time in time_to_utc_dic.items():
                t = utc_time.astimezone(receiver_tz)
                msg = msg.replace(original_time, f"*{t.strftime('%I:%M %p, %a, %Y-%m-%d')}*")

            # send "only visible to you" message for each user in the channel
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"{msg} {suffix} to `{receiver_tz}`"
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def get_user_info(user_id):
    try:
        result = client.users_info(user=user_id)
        user = result['user']
        return user
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e

def get_user_timezone(user_info):
    return user_info.get('tz')

def get_user_name(user_info):
    return user_info.get('name')

def postprocess_time(time):
    # "10PM" -> "10:00PM"
    if ':' not in time:
        time = f"{time[:-2]}:00{time[-2:]}"
    # "10:30 PM" -> "10:30PM"
    time = time.strip().replace(" ", "")
    return time




def extract_utc_from_time(time_list, sender_tz):
    time_to_utc_dic = {}

    # python logic that extract utc from time like "10:30 PM" with sender's timezone("Asia/Seoul")
    input_format = '%I:%M%p'
    for time in time_list:
        processed_time = postprocess_time(time)
        t = datetime.strptime(processed_time, input_format)
        # date가 안들어왔다는 가정 하에
        date_now = datetime.now(ZoneInfo(sender_tz))
        local_time_with_tz = t.replace(
            year=date_now.year,
            month=date_now.month,
            day=date_now.day,
            tzinfo=ZoneInfo(sender_tz)
        )
        utc_time = local_time_with_tz.astimezone(ZoneInfo("UTC"))
        time_to_utc_dic[time] = utc_time

    return time_to_utc_dic

def relative_date_to_timedelta(rel_date: str, weekday: str = None):
    day_timedelta_dic = {
        "today": 0,
        "td": 0,
        "tonight": 0,
        "tomorrow": 1,
        "tmr": 1,
        "yesterday": -1,
        "yd": -1,
        # TODO next, last, this
    }

    week_timedelta_dic = {
        "this": 0,
        "next": 1,
        "last": -1,
    }

    weekday_dic = {
        "monday": MO,
        "tuesday": TU,
        "wednesday": WE,
        "thursday": TH,
        "friday": FR,
        "saturday": SA,
        "sunday": SU,
    }

    if rel_date.lower() in day_timedelta_dic:
        return timedelta(days=day_timedelta_dic[rel_date])

    if rel_date.lower() in week_timedelta_dic and weekday is not None:
        rel_weekday = weekday_dic[weekday.lower()](week_timedelta_dic[rel_date.lower()])
        return relativedelta(weekday=rel_weekday)



@bolt.message(time_re_pattern)
def timezone_convert(message, context):
    start_time = datetime.now()

    sender_id = message['user']
    sender_info = get_user_info(sender_id)
    sender_name = get_user_name(sender_info)
    sender_tz = get_user_timezone(sender_info)
    sender_tz = "Asia/Shanghai"  # TODO for testing
    original_msg = message['text']
    converted_msg = original_msg

    time_1 = datetime.now()
    print(f"Getting user info: {time_1 - start_time}")

    original_times = [time for time in context['matches']]
    time_to_utc_dic = extract_utc_from_time(original_times, sender_tz)

    time_2 = datetime.now()
    print(f"extract utc from info: {time_2 - time_1}")

    rel_date_match = regex.date_re_pattern.search(original_msg)
    rel_date = rel_date_match[0].strip() if rel_date_match and rel_date_match[0] else None # use only the first match
    weekday_match = regex.weekday_re_pattern.search(original_msg)
    weekday = weekday_match[0].strip() if weekday_match and weekday_match[0] else None  # use only the first match
    if rel_date:
        timedelta = relative_date_to_timedelta(rel_date, weekday)
        time_to_utc_dic = {k: v + timedelta for k, v in time_to_utc_dic.items()}
        converted_msg = converted_msg.replace(rel_date, f"~{rel_date}~")
        if weekday:
            converted_msg = converted_msg.replace(weekday, f"~{weekday}~")

    time_3 = datetime.now()
    print(f"relative date to timedelta: {time_3 - time_2}")

    suffix = f"\n>{sender_name} : _{original_msg}_\nconverted from `{sender_tz}`"
    send_ephemeral_message_to_channel_members(sender_id, message['channel'], converted_msg, time_to_utc_dic, suffix)

    time_4 = datetime.now()
    print(f"send ephemeral message: {time_4 - time_3}")
    print(f"total time: {time_4 - start_time}")


if __name__ == "__main__":
    SocketModeHandler(bolt, os.environ.get("SLACK_APP_TOKEN")).start()