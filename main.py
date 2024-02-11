import logging
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from regex import time_re_pattern

NAME = "slack-tz-helper"
logger = logging.getLogger(NAME)

client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
bolt = App(token=os.environ.get("SLACK_BOT_TOKEN"))

def send_ephemeral_message_to_channel_members(channel_id, trigger_message):
    try:
        result = client.conversations_members(channel=channel_id)
        members = result['members']

        for user_id in members:
            # don't send a message to the bot itself
            if user_id == bolt.client.auth_test()["user_id"]:
                continue

            # send "only visible to you" message for each user in the channel
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text=f"Ephemeral message in response to a trigger: {trigger_message}"
            )
    except Exception as e:
        logger.error(f"Error: {e}")


def get_user_timezone(user_id):
    try:
        result = client.users_info(user=user_id)
        user = result['user']
        tz_label = user['tz']
        return tz_label
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def postprocess_time(time_list):
    # "10:30 PM" -> "10:30PM"
    time_list = [time.replace(" ", "") for time in time_list]
    return time_list


def extract_utc_from_time(time_list, sender_tz):
    time_to_utc_dic = {}

    # python logic that extract utc from time like "10:30 PM" with sender's timezone("Asia/Seoul")
    sender_tz = "America/Los_Angeles"
    input_format = '%H:%M%p'
    for time in time_list:
        t = datetime.strptime(time, input_format)
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


@bolt.message(time_re_pattern)
def timezone_convert(message, context):
    sender_id = message['user']
    original_times = [time for time in context['matches']]
    sender_tz = get_user_timezone(sender_id)
    original_times = postprocess_time(original_times)
    time_to_utc_dic = extract_utc_from_time(original_times, sender_tz)

    print(time_to_utc_dic)

    # 각 매칭된 시간에 대해 "original time" -> "UTC time" 딕셔너리를 만들어서 넘김.
    time = context['matches'][0]

    send_ephemeral_message_to_channel_members(message['channel'], f"{sender_id} - {time}")


if __name__ == "__main__":
    SocketModeHandler(bolt, os.environ.get("SLACK_APP_TOKEN")).start()