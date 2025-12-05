import os
import asyncio
import ffmpeg
from telethon import TelegramClient, events
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG
# =========================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_NAME = os.getenv("SESSION_NAME", "audio_bot")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
call_py = PyTgCalls(client)

current_chat_id = None
is_in_call = False

# =========================
# START
# =========================
@client.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    await event.reply(
        "🎵 **Audio Bot Ready!**\n\n"
        "/join - Join voice chat\n"
        "/play <file> <start> <end>\n"
        "/stop - Stop audio\n"
        "/leave - Leave voice chat\n"
        "/list - List audio files\n\n"
        "✅ You can also SEND an audio file to auto-play it."
    )

# =========================
# JOIN CALL
# =========================
@client.on(events.NewMessage(pattern="/join"))
async def join_handler(event):
    global current_chat_id, is_in_call

    try:
        chat = await event.get_chat()
        current_chat_id = chat.id

        await call_py.join_group_call(
            chat.id,
            AudioPiped("audio_files/silence.mp3"),
        )

        is_in_call = True
        await event.reply("✅ Joined the voice call!")

    except Exception as e:
        await event.reply(f"❌ Error joining call: {e}")

# =========================
# PLAY WITH TIME RANGE
# =========================
@client.on(events.NewMessage(pattern=r"/play (.+)"))
async def play_handler(event):
    global is_in_call

    if not is_in_call:
        await event.reply("❌ Use /join first.")
        return

    parts = event.text.split()

    if len(parts) < 2:
        await event.reply("❌ Usage: /play filename [start] [end]")
        return

    filename = parts[1]
    start_time = int(parts[2]) if len(parts) >= 3 else 0
    end_time = int(parts[3]) if len(parts) >= 4 else None

    input_path = f"audio_files/{filename}"
    output_path = f"audio_files/trimmed_{filename}"

    if not os.path.exists(input_path):
        await event.reply("❌ File not found. Use /list.")
        return

    try:
        stream = ffmpeg.input(input_path, ss=start_time)

        if end_time:
            stream = ffmpeg.output(
                stream,
                output_path,
                t=end_time - start_time,
                acodec="libmp3lame",
            )
        else:
            stream = ffmpeg.output(stream, output_path)

        ffmpeg.run(stream, overwrite_output=True)

        await call_py.change_stream(
            current_chat_id,
            AudioPiped(output_path),
        )

        if end_time:
            await event.reply(
                f"🎵 Playing **{filename}** from {start_time}s to {end_time}s"
            )
        else:
            await event.reply(
                f"🎵 Playing **{filename}** from {start_time}s onward"
            )

    except Exception as e:
        await event.reply(f"❌ Playback error: {e}")

# =========================
# STOP
# =========================
@client.on(events.NewMessage(pattern="/stop"))
async def stop_handler(event):
    global is_in_call

    if not is_in_call:
        await event.reply("❌ Not in a call.")
        return

    try:
        await call_py.change_stream(
            current_chat_id,
            AudioPiped("audio_files/silence.mp3"),
        )
        await event.reply("⏹️ Stopped.")
    except Exception as e:
        await event.reply(f"❌ Stop error: {e}")

# =========================
# LEAVE
# =========================
@client.on(events.NewMessage(pattern="/leave"))
async def leave_handler(event):
    global is_in_call

    if not is_in_call:
        await event.reply("❌ Not in a call.")
        return

    try:
        await call_py.leave_group_call(current_chat_id)
        is_in_call = False
        await event.reply("👋 Left the call.")
    except Exception as e:
        await event.reply(f"❌ Leave error: {e}")

# =========================
# LIST FILES
# =========================
@client.on(events.NewMessage(pattern="/list"))
async def list_handler(event):
    files = os.listdir("audio_files")
    audio_files = [f for f in files if f.endswith((".mp3", ".wav", ".ogg", ".m4a"))]

    if not audio_files:
        await event.reply("📂 No audio files found.")
        return

    text = "\n".join(f"• {f}" for f in audio_files)
    await event.reply(f"📂 Available files:\n\n{text}")

# =========================
# AUDIO UPLOAD AUTO-PLAY
# =========================
@client.on(events.NewMessage)
async def audio_upload_handler(event):
    global is_in_call

    if not event.audio and not event.voice:
        return

    if not is_in_call:
        await event.reply("❌ Join the call first with /join.")
        return

    os.makedirs("audio_files", exist_ok=True)

    file_path = await event.download_media(file="audio_files/")
    filename = os.path.basename(file_path)

    try:
        await call_py.change_stream(
            current_chat_id,
            AudioPiped(file_path),
        )
        await event.reply(f"🎵 Uploaded & now playing: {filename}")

    except Exception as e:
        await event.reply(f"❌ Playback error: {e}")

# =========================
# MAIN
# =========================
async def main():
    os.makedirs("audio_files", exist_ok=True)

    print("✅ Starting bot...")
    await client.start(bot_token=BOT_TOKEN)
    await call_py.start()
    print("✅ Bot is running!")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())