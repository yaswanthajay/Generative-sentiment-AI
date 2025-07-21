import os
import time
import datetime
import threading
import signal
import sys
import re
import pyttsx3
import speech_recognition as sr
from llama_cpp import Llama

# === GLOBAL SETTINGS ===
settings = {
    "username": "User",
    "input_method": "voice",
    "time_of_day": "morning"
}

# === TIME OF DAY ===
current_hour = datetime.datetime.now().hour
if 5 <= current_hour < 12:
    settings["time_of_day"] = "morning"
elif 12 <= current_hour < 18:
    settings["time_of_day"] = "afternoon"
else:
    settings["time_of_day"] = "evening"

# === INIT TTS ENGINE ===
engine = pyttsx3.init()
engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)

# === INIT LLaMA MODEL ===
llm = Llama(model_path="model.gguf", n_ctx=2048)

# === EMOTION DETECTION ===
def detect_emotion(text):
    text = text.lower()
    if any(w in text for w in ["sad", "depressed", "cry", "unhappy"]):
        return "sad"
    elif any(w in text for w in ["angry", "mad", "frustrated"]):
        return "angry"
    elif any(w in text for w in ["happy", "great", "joy", "awesome", "love"]):
        return "happy"
    return "neutral"

# === EMOTION WRAPPER ===
def emotion_wrap(response, emotion):
    if emotion == "sad":
        return "I'm really sorry to hear that. " + response
    elif emotion == "angry":
        return "I understand how frustrating that must be. " + response
    elif emotion == "happy":
        return "Yay! That's wonderful! " + response
    return response

# === SPEAK OUTPUT (Safe) ===
speak_lock = threading.Lock()
speak_interrupted = threading.Event()

def speak_output(text):
    with speak_lock:
        speak_interrupted.clear()

        def monitor_interrupt():
            while not speak_interrupted.is_set():
                time.sleep(0.1)
            try:
                engine.stop()
            except RuntimeError:
                pass

        interrupt_thread = threading.Thread(target=monitor_interrupt)
        interrupt_thread.start()

        try:
            engine.say(text)
            engine.runAndWait()
        except RuntimeError as e:
            print("⚠️ TTS Error:", e)

# === LISTEN TO VOICE ===
def get_voice_input(timeout=8, phrase_time_limit=10):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening... (say 'stop' to exit, 'next' to skip, 'change to text')")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except sr.WaitTimeoutError:
            print("⏳ No voice detected.")
        except sr.UnknownValueError:
            print("🤷 Couldn't understand. Try again.")
        except sr.RequestError as e:
            print(f"[ERROR] Voice recognition error: {e}")
    return None

# === LLaMA RESPONSE ===
def ask_llama(prompt):
    print("🧠 Thinking...")
    output = llm.create_completion(
        prompt=f"User: {prompt}\nAI:",
        max_tokens=200,
        stop=["User:", "AI:"],
        temperature=0.7
    )
    return output["choices"][0]["text"].strip()

# === GREETING ===
def greet_user():
    greeting = f"Good {settings['time_of_day']}, {settings['username']}! How can I help you today?"
    print(greeting)
    speak_output(greeting)

# === INPUT METHOD SWITCH ===
def get_input_method():
    print("Select input method:\n1. Text\n2. Voice")
    choice = input("Enter 1 or 2: ").strip()
    settings["input_method"] = "text" if choice == "1" else "voice"

# === HANDLE EMOTION PROMPT ===
def handle_emotion_prompt(emotion):
    if emotion == "sad":
        speak_output("You sound down. I'm here for you.")
    elif emotion == "angry":
        speak_output("Let's take a breath together. Tell me more.")
    elif emotion == "happy":
        speak_output("That's awesome! Tell me what's going well.")

# === HANDLE RESPONSE ===
def run_response(user_input):
    # Split into multiple questions
    questions = [q.strip() for q in re.split(r'[.?!]', user_input) if q.strip()]
    final_response = ""

    for i, question in enumerate(questions):
        emotion = detect_emotion(question)
        print(f"\n➡️ Question {i + 1}: {question}")
        print(f"[Emotion Detected]: {emotion}")
        handle_emotion_prompt(emotion)

        response = ask_llama(question)
        wrapped_response = emotion_wrap(response, emotion)

        print(f"🤖 AI: {wrapped_response}")
        final_response += wrapped_response + " "

    # Speak all responses
    tts_thread = threading.Thread(target=speak_output, args=(final_response.strip(),))
    tts_thread.start()

    if settings["input_method"] == "text":
        print("\n[Press ENTER to stop speaking early or wait for it to finish]")
        input()
        speak_interrupted.set()
    else:
        print("[Say 'next' or 'stop' to interrupt]")

    tts_thread.join()

# === SHUTDOWN HANDLER ===
stop_event = threading.Event()

def handle_signal(sig, frame):
    print("\n[INFO] Ctrl+C pressed. Exiting.")
    stop_event.set()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)

# === MAIN LOOP ===
def main():
    greet_user()
    get_input_method()

    while not stop_event.is_set():
        user_input = None

        if settings["input_method"] == "text":
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if user_input.lower() in ["exit", "quit", "stop"]:
                speak_output("Session ended. Goodbye!")
                break
            elif "change to voice" in user_input.lower():
                settings["input_method"] = "voice"
                speak_output("Switched to voice mode.")
                continue

        else:
            user_input = get_voice_input()
            if not user_input:
                continue

            if "stop" in user_input.lower():
                speak_output("Session ended. Goodbye!")
                break
            elif "next" in user_input.lower():
                speak_interrupted.set()
                print("⏭ Skipping to next...")
                continue
            elif "change to text" in user_input.lower():
                settings["input_method"] = "text"
                speak_output("Switched to text mode.")
                continue

        if user_input:
            thread = threading.Thread(target=run_response, args=(user_input,))
            thread.start()
            thread.join()

if __name__ == "__main__":
    main()
