import os
import asyncio
from telethon import TelegramClient, events
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, Update
from pytgcalls.types.stream import StreamAudioEnded

# Configuration from environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
SESSION_NAME = os.getenv('SESSION_NAME', 'audio_bot')

# Initialize clients
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
call_py = PyTgCalls(client)

# Track current state
current_chat_id = None
is_in_call = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Welcome message"""
    await event.reply(
        "🎵 **Audio Bot Ready!**\n\n"
        "Commands:\n"
        "/join - Join the voice call\n"
        "/play <filename> - Play an audio file\n"
        "/stop - Stop playback\n"
        "/leave - Leave the voice call\n"
        "/list - List available audio files"
    )

@client.on(events.NewMessage(pattern='/join'))
async def join_handler(event):
    """Join the group voice call"""
    global current_chat_id, is_in_call
    
    try:
        chat = await event.get_chat()
        current_chat_id = chat.id
        
        # Join with silence (no audio initially)
        await call_py.join_group_call(
            chat.id,
            AudioPiped('audio_files/silence.mp3'),
            stream_type='audio'
        )
        
        is_in_call = True
        await event.reply("✅ Joined the voice call! Use /play to stream audio.")
    except Exception as e:
        await event.reply(f"❌ Error joining call: {str(e)}")

@client.on(events.NewMessage(pattern='/play (.+)'))
async def play_handler(event):
    """Play an audio file in the call"""
    global is_in_call
    
    if not is_in_call:
        await event.reply("❌ Not in a call! Use /join first.")
        return
    
    filename = event.pattern_match.group(1).strip()
    filepath = f"audio_files/{filename}"
    
    if not os.path.exists(filepath):
        await event.reply(f"❌ File '{filename}' not found. Use /list to see available files.")
        return
    
    try:
        await call_py.change_stream(
            current_chat_id,
            AudioPiped(filepath)
        )
        await event.reply(f"🎵 Now playing: **{filename}**")
    except Exception as e:
        await event.reply(f"❌ Error playing file: {str(e)}")

@client.on(events.NewMessage(pattern='/stop'))
async def stop_handler(event):
    """Stop current playback"""
    global is_in_call
    
    if not is_in_call:
        await event.reply("❌ Not in a call!")
        return
    
    try:
        await call_py.change_stream(
            current_chat_id,
            AudioPiped('audio_files/silence.mp3')
        )
        await event.reply("⏹️ Playback stopped.")
    except Exception as e:
        await event.reply(f"❌ Error stopping: {str(e)}")

@client.on(events.NewMessage(pattern='/leave'))
async def leave_handler(event):
    """Leave the voice call"""
    global is_in_call
    
    if not is_in_call:
        await event.reply("❌ Not in a call!")
        return
    
    try:
        await call_py.leave_group_call(current_chat_id)
        is_in_call = False
        await event.reply("👋 Left the voice call.")
    except Exception as e:
        await event.reply(f"❌ Error leaving: {str(e)}")

@client.on(events.NewMessage(pattern='/list'))
async def list_handler(event):
    """List available audio files"""
    audio_dir = 'audio_files'
    
    if not os.path.exists(audio_dir):
        await event.reply("❌ No audio files directory found.")
        return
    
    files = [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
    
    if not files:
        await event.reply("📂 No audio files available. Upload files to the audio_files directory.")
        return
    
    file_list = "\n".join([f"• {f}" for f in files])
    await event.reply(f"📂 **Available Audio Files:**\n\n{file_list}")

@call_py.on_stream_end()
async def on_stream_end(client, update: Update):
    """Handle when audio stream ends"""
    print(f"Stream ended in chat {update.chat_id}")
    # Optionally switch back to silence
    try:
        await call_py.change_stream(
            update.chat_id,
            AudioPiped('audio_files/silence.mp3')
        )
    except:
        pass

async def main():
    """Start the bot"""
    print("Starting Audio Bot...")
    
    # Create audio_files directory if it doesn't exist
    os.makedirs('audio_files', exist_ok=True)
    
    # Create a silence file if it doesn't exist (1 second of silence)
    silence_path = 'audio_files/silence.mp3'
    if not os.path.exists(silence_path):
        print("Creating silence file...")
        # You'll need to create this manually or use ffmpeg
    
    await client.start(bot_token=BOT_TOKEN)
    await call_py.start()
    
    print("✅ Bot is running!")
    print(f"Bot username: {(await client.get_me()).username}")
    
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())