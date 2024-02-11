import logging
import os
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import regex
from regex import time_re_pattern

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

            msg = trigger_message
            for original_time, utc_time in time_to_utc_dic.items():
                receiver_tz = ZoneInfo(get_user_timezone(user_id))
                t = utc_time.astimezone(receiver_tz)
                msg = msg.replace(original_time, f"*`{t.strftime('%I:%M %p, %Y-%m-%d')}`*[{receiver_tz}]")

            # send "only visible to you" message for each user in the channel
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"{msg} {suffix}"
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def get_user_timezone(user_id):
    try:
        result = client.users_info(user=user_id)
        user = result['user']
        tz_label = user['tz']
        return tz_label
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def postprocess_time(time):
    # "10:30 PM" -> "10:30PM"
    return time.strip().replace(" ", "")


def extract_utc_from_time(time_list, sender_tz):
    time_to_utc_dic = {}

    # python logic that extract utc from time like "10:30 PM" with sender's timezone("Asia/Seoul")
    sender_tz = "America/Los_Angeles" # TODO for testing
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

def relative_date_to_timedelta(today, rel_date: str):
    timedelta_dic = {
        "today": 0,
        "td": 0,
        "tomorrow": 1,
        "tmr": 1,
        "yesterday": -1,
        "yd": -1,
        # TODO next, last
    }
    return timedelta(days=timedelta_dic[rel_date])


@bolt.message(time_re_pattern)
def timezone_convert(message, context):
    sender_id = message['user']
    sender_tz = get_user_timezone(sender_id)
    msg = message['text']

    original_times = [time for time in context['matches']]
    time_to_utc_dic = extract_utc_from_time(original_times, sender_tz)

    rel_date = regex.date_re_pattern.search(msg)[0].strip()  # use only the first match
    timedelta = relative_date_to_timedelta(datetime.now(ZoneInfo(sender_tz)), rel_date)
    time_to_utc_dic = {k: v + timedelta for k, v in time_to_utc_dic.items()}

    sender_tz = "America/Los_Angeles" # TODO for testing
    suffix = f"\n--FROM user[{sender_id}] timezone *{sender_tz}*\n>{msg}"
    send_ephemeral_message_to_channel_members(sender_id, message['channel'], msg, time_to_utc_dic, suffix)


if __name__ == "__main__":
    SocketModeHandler(bolt, os.environ.get("SLACK_APP_TOKEN")).start()