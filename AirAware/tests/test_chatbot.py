import sys
import os
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_chatbot():
    print("--------------------------------------------------")
    print("Testing Chatbot Model")
    print("--------------------------------------------------")

    try:
        # Load model and vectorizer
        with open('chatbot/model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('chatbot/vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
        
        with open('chatbot/intents.json', 'r') as f:
            intents = json.load(f)

        print("Models loaded successfully.")
    except Exception as e:
        print(f"Error loading models: {e}")
        return

    test_messages = [
        "Hello",
        "What is AQI?",
        "Tell me about PM2.5",
        "Is pollution bad for health?",
        "Wear a mask",
        "Bye",
        "What are the main pollutants?",
        "Compare cities",
        "Who created this?",
        "Check AQI in Delhi"
    ]

    for msg in test_messages:
        # Preprocess
        vec = vectorizer.transform([msg])
        # Predict
        tag = model.predict(vec)[0]
        
        # Get response (simplified, just checking tag)
        print(f"Message: '{msg}' -> Predicted Tag: '{tag}'")

    print("--------------------------------------------------")

if __name__ == "__main__":
    test_chatbot()
