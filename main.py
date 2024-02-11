import logging
import os
import re

from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

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


@bolt.message("6am")
def timezone_convert(message, context):
    user = message['user']
    time = context['matches'][0]
    send_ephemeral_message_to_channel_members(message['channel'], f"timezone-related word detected, user - {user} - {time}")


if __name__ == "__main__":
    SocketModeHandler(bolt, os.environ.get("SLACK_APP_TOKEN")).start()