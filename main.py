import os
from gtts import gTTS
import streamlit as st
from llama_cpp import Llama
import tempfile
import time
import speech_recognition as sr
import pydub

# Initialize LLaMA model (adjust path accordingly)
llm = Llama(model_path="path_to_your_model.gguf")

# Convert text to speech using gTTS
def speak_output(text):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        audio_path = fp.name
    st.audio(audio_path, format="audio/mp3")
    return audio_path

# Recognize speech input
def listen_input():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening...")
        audio = r.listen(source)
        try:
            query = r.recognize_google(audio)
            return query
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Speech service is unavailable."

# LLaMA generate response
def generate_response(prompt):
    output = llm(prompt, max_tokens=100)
    return output["choices"][0]["text"].strip()

# Streamlit UI
st.title("🦙 Voice-Enabled LLaMA Chatbot")
st.write("Speak something and LLaMA will respond with voice.")

if st.button("🎙️ Start Talking"):
    user_input = listen_input()
    st.success(f"You said: {user_input}")
    response = generate_response(user_input)
    st.success(f"LLaMA says: {response}")
    speak_output(response)
