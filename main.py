# main.py — Permanent Telegram Reporting Userbot
import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ReportRequest
from telethon.errors import FloodWaitError

# ==== YOUR CREDENTIALS (from Render Environment Variables) ====
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ==== USER-CONFIGURABLE SETTINGS (you control via commands) ====
report_reason = "pornography"   # Default = NSFW
reason_map = {
    "1": "spam", "2": "violence", "3": "pornography", "4": "child_abuse",
    "5": "copyright", "6": "geo_irrelevant", "7": "illegal_drugs",
    "8": "personal_details", "9": "other"
}

# ==== COMMANDS YOU WILL USE ====
# /start → shows help
# /setreason 3 → changes reason (3 = pornography)
/report @channel 50 → reports last 50 posts
# /report @channel 12345 12400 → reports range

@client.on(events.NewMessage(outgoing=True, pattern=r"/start"))
async def start(event):
    await event.reply(
        "Reporting Userbot Active!\n\n"
        "Commands:\n"
        "/report @channel <count> → report last X posts\n"
        "/report @channel <from_id> <to_id> → report range\n"
        "/setreason <number> → change reason\n\n"
        f"Current reason: {report_reason.upper()} ({[k for k,v in reason_map.items() if v==report_reason][0]})"
    )

@client.on(events.NewMessage(outgoing=True, pattern=r"/setreason (\d+)"))
async def set_reason(event):
    global report_reason
    num = event.pattern_match.group(1)
    if num in reason_map:
        report_reason = reason_map[num]
        await event.reply(f"Reason updated → {report_reason.upper()}")
    else:
        await event.reply("Invalid reason. Use 1–9")

@client.on(events.NewMessage(outgoing=True, pattern=r"/report (@\w+|\d+) ?(\d+)? ?(\d+)?"))
async def report_command(event):
    await event.reply("Starting report job…")

    channel = event.pattern_match.group(1)
    arg2 = event.pattern_match.group(2)
    arg3 = event.pattern_match.group(3)

    try:
        entity = await client.get_entity(channel)
    except Exception as e:
        await event.reply(f"Cannot find channel {channel}\n{e}")
        return

    # Determine message IDs
    if arg2 and arg3:
        # Range mode
        start_id = int(arg2)
        end_id = int(arg3)
        message_ids = list(range(start_id, end_id + 1))
        mode_text = f"range {start_id}–{end_id}"
    elif arg2:
        # Count mode
        count = int(arg2)
        messages = await client.get_messages(entity, limit=count)
        message_ids = [m.id for m in messages]
        mode_text = f"last {count} posts"
    else:
        await event.reply("Usage: /report @channel <count> or <from> <to>")
        return

    success = 0
    failed = 0
    for msg_id in message_ids:
        try:
            await client(ReportRequest(
                peer=entity,
                id=[msg_id],
                reason=report_reason,
                message="NSFW / inappropriate content"
            ))
            success += 1
            await asyncio.sleep(2.5)  # Safe delay
        except FloodWaitError as e:
            await event.reply(f"FloodWait: {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            failed += 1
            print(f"Failed {msg_id}: {e}")

    result = f"Finished reporting {channel}\n" \
             f"Mode: {mode_text}\n" \
             f"Reason: {report_reason.upper()}\n" \
             f"Success: {success} | Failed: {failed}"
    await event.reply(result)

# ==== Start the userbot ====
async def main():
    print("Userbot starting...")
    await client.start()
    print("Userbot is ONLINE! Send /start in your Saved Messages to test.")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
