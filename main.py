# main.py — Works perfectly on Render Web Service (Free Tier)
import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ReportRequest
from telethon.errors import FloodWaitError
import threading
import uvicorn
from fastapi import FastAPI

# ==== YOUR CREDENTIALS ====
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# ==== SETTINGS ====
report_reason = "pornography"  # Default = NSFW
reason_map = {
    "1": "spam", "2": "violence", "3": "pornography", "4": "child_abuse",
    "5": "copyright", "6": "geo_irrelevant", "7": "illegal_drugs",
    "8": "personal_details", "9": "other"
}

# ==== COMMANDS (send to Saved Messages) ====
@client.on(events.NewMessage(outgoing=True, pattern="/start"))
async def start(event):
    await event.reply(
        "NSFW Reporter Bot is ONLINE!\n\n"
        "Commands:\n"
        "/report @channel 50 → report last 50 posts\n"
        "/report @channel 12345 12400 → report range\n"
        "/setreason 3 → set reason (3 = pornography)\n\n"
        f"Current reason: {report_reason.upper()}"
    )

@client.on(events.NewMessage(outgoing=True, pattern=r"/setreason (\d+)"))
async def set_reason(event):
    global report_reason
    num = event.pattern_match.group(1)
    if num in reason_map:
        report_reason = reason_map[num]
        await event.reply(f"Reason changed → {report_reason.upper()}")
    else:
        await event.reply("Invalid number. Use 1–9")

@client.on(events.NewMessage(outgoing=True, pattern=r"/report (@[\w]+|\d+) ?(\d+)? ?(\d+)?"))
async def report(event):
    await event.reply("Starting report job...")
    channel = event.pattern_match.group(1)
    arg2 = event.pattern_match.group(2)
    arg3 = event.pattern_match.group(3)

    try:
        entity = await client.get_entity(channel)
    except Exception as e:
        await event.reply(f"Channel not found: {e}")
        return

    if arg2 and arg3:
        start, end = int(arg2), int(arg3)
        ids = list(range(start, end + 1))
        mode = f"range {start}–{end}"
    elif arg2:
        count = int(arg2)
        msgs = await client.get_messages(entity, limit=count)
        ids = [m.id for m in msgs]
        mode = f"last {count} posts"
    else:
        await event.reply("Usage: /report @channel <count> or <from> <to>")
        return

    success = 0
    for msg_id in ids:
        try:
            await client(ReportRequest(
                peer=entity,
                id=[msg_id],
                reason=report_reason,
                message="NSFW content"
            ))
            success += 1
            print(f"Reported {msg_id}")
            await asyncio.sleep(2.5)
        except FloodWaitError as e:
            await event.reply(f"FloodWait {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"Failed {msg_id}: {e}")

    await event.reply(f"DONE!\n{channel}\n{mode}\nReported: {success}\nReason: {report_reason.upper()}")

# ==== FastAPI dummy web server (keeps Render happy) ====
app = FastAPI(title="NSFW Reporter")

@app.get("/")
async def home():
    return {"status": "Userbot is running!", "tip": "Send /start in Telegram Saved Messages"}

# ==== Run both bot + web server correctly ====
async def run_telegram_bot():
    await client.start()
    print("Telegram Userbot is now ONLINE and ready!")
    await client.run_until_disconnected()

async def start_server():
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    print("Starting NSFW Reporter Userbot + Web Server...")
    await asyncio.gather(
        run_telegram_bot(),
        start_server()
    )

# === CORRECT WAY: Run only ONCE ===
if __name__ == "__main__":
    asyncio.run(main())
