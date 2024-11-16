import os
from groq import Groq
from gtts import gTTS
import telebot

# Initialize Groq client with your API key
groq_client = Groq(api_key="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")

# Replace this with your Telegram bot token
BOT_TOKEN = "1913742955:AAEF9aJk7ukWc841KJ9-7JPrshAmlERNiq8"

# Initialize the bot
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Send me a voice message, and I'll transcribe it, get a response from Gemma, and send it back as voice!")

@bot.message_handler(content_types=["voice"])
def handle_voice(message):
    try:
        # Step 1: Download the voice file
        file_info = bot.get_file(message.voice.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("audio.ogg", "wb") as f:
            f.write(downloaded_file)

        # Step 2: Convert OGG to M4A for Whisper compatibility
        m4a_path = "audio.m4a"
        os.system("ffmpeg -i audio.ogg -ac 1 -ar 16000 audio.m4a -y")

        # Step 3: Transcribe the audio using Groq Whisper
        with open(m4a_path, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.m4a", audio_file.read()),
                model="whisper-large-v3",
                language="en",
                response_format="verbose_json",
            )
        transcribed_text = transcription["text"]

        # Step 4: Send the transcribed text to Gemma for a response
        gemma_response = groq_client.chat.completions.create(
            model="gemma-7b-it",
            messages=[{"role": "user", "content": transcribed_text}],
            temperature=1,
            max_tokens=100,  # Short response
            top_p=1,
        )
        response_text = "".join(chunk["choices"][0]["delta"].get("content", "") for chunk in gemma_response)

        # Step 5: Convert the response to a voice message using gTTS
        tts = gTTS(response_text)
        tts_file_path = "response.mp3"
        tts.save(tts_file_path)

        # Step 6: Send the generated voice message back to the user
        with open(tts_file_path, "rb") as voice:
            bot.send_voice(chat_id=message.chat.id, voice=voice)

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists("audio.ogg"):
            os.remove("audio.ogg")
        if os.path.exists("audio.m4a"):
            os.remove("audio.m4a")
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")

# Start the bot
print("Bot is running...")
bot.polling(non_stop=True)
