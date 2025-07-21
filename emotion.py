# emotion.py

import random

def detect_emotion(text):
    emotions = {
        "happy": ["great", "good", "awesome", "fantastic", "love"],
        "sad": ["sad", "unhappy", "upset", "depressed"],
        "angry": ["angry", "mad", "furious", "irritated"],
        "neutral": []
    }

    text = text.lower()
    for emotion, keywords in emotions.items():
        if any(word in text for word in keywords):
            return emotion
    return "neutral"
