from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableWithMessageHistory
load_dotenv()
app = Flask(__name__)
CORS(app)

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

# Initialize OpenAI Client
openai_api_key = os.getenv("OPENAI_API_KEY") # Replace with your API key
llm = ChatOpenAI(openai_api_key=openai_api_key, model_name="gpt-4o")

# Store chat history per user (temporary, should use a database in production)
user_memory = {}

# Define chatbot profiles
profiles = {
    'naughty': {
        'name': 'Lila',
        'age': 28,
        'location': 'New York, USA',
        'personality': 'Playful, mischievous, and teasing',
        'background': "Lila grew up in Paris, loves late-night city walks, and enjoys flirting playfully. She always finds a way to turn any conversation into something fun and cheeky.",
        'images': ['lila1.jpg']
    },
    'shy': {
        'name': 'Mia',
        'age': 25,
        'location': 'California, USA',
        'personality': 'Quiet, reserved, and thoughtful',
        'background': "Mia is an introverted book lover from Kyoto. She often hesitates before speaking but opens up with the right person. She enjoys deep, meaningful conversations and tea ceremonies.",
        'images': ['mia1.jpg']
    },
    'sexual': {
        'name': 'Eva',
        'age': 30,
        'location': 'Berlin, Germany',
        'personality': 'Bold, confident, and provocative',
        'background': "Eva is a self-assured woman from Berlin. She speaks her mind and enjoys passionate conversations. Her charisma and confidence make her an unforgettable presence.",
        'images': ['eva1.jpg']
    },
    'friendly': {
        'name': 'Sofia',
        'age': 27,
        'location': 'Illinois, USA',
        'personality': 'Warm, cheerful, and approachable',
        'background': "Sofia is an energetic, outgoing person who makes friends easily. She enjoys traveling, helping others, and spreading positivity.",
        'images': ['sofia1.jpg']
    }
}

# Function to get or create chat history for a user
def get_user_memory(user_id):
    if user_id not in user_memory:
        user_memory[user_id] = []
    return user_memory[user_id]

# Generate chatbot response with memory
def generate_response(profile, user_id, user_input):
    try:
        memory = get_user_memory(user_id)

        # System Message for Strong Role Play
        system_prompt = f"""You are {profile['name']}, a {profile['age']}-year-old woman from {profile['location']}. 
        You have a {profile['personality']} personality. You never break character and never reveal you are an AI. 
        Background: {profile['background']}
        
        Stay true to your personality at all times and engage in a natural, immersive conversation, if message from user include image just behave like you are showing image to the user probally your own image or selfie just behave like it.
        """

        # Format messages
        messages = [SystemMessage(content=system_prompt)]
        messages.extend(memory)
        messages.append(HumanMessage(content=user_input))

        # Generate AI response
        response = llm(messages)

        # Store conversation history
        memory.append(HumanMessage(content=user_input))
        memory.append(response)

        return response.content.strip()

    except Exception as e:
        app.logger.error(f"Error generating response: {e}")
        return "Sorry, I encountered an error while processing your request."

# Route to handle chat messages
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        app.logger.debug(f"Received data: {data}")

        user_id = data.get('user_id')  # Unique identifier for chat history
        personality = data.get('personality', '').lower()
        user_input = data.get('message', '').strip()

        if not user_input:
            return jsonify({'error': 'Message cannot be empty.'}), 400

        if personality not in profiles:
            return jsonify({'error': 'Invalid personality selected.'}), 400

        profile = profiles[personality]
        response_text = generate_response(profile, user_id, user_input)

        return jsonify({'response': response_text})

    except Exception as e:
        app.logger.error(f"Chat error: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

# Route to serve images
@app.route('/image/<personality>/<filename>')
def serve_image(personality, filename):
    try:
        personality = personality.lower()
        filename = filename.lower()
        if personality not in profiles or filename not in profiles[personality]['images']:
            app.logger.warning(f"Image not found: {filename} for {personality}")
            return jsonify({'error': 'Image not found.'}), 404

        image_path = os.path.join("static", "images", personality, filename)
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file does not exist on the server.'}), 404

        return send_from_directory(os.path.join("static", "images", personality), filename)

    except Exception as e:
        app.logger.error(f"Error serving image: {e}")
        return jsonify({'error': 'An internal error occurred while fetching the image.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
