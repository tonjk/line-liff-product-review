import os
import requests
from flask import Flask, request, abort, jsonify
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage # ImageMessage, FlexMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent #, ImageMessageContent
from dotenv import load_dotenv
load_dotenv()
from src.Chatbot import chat


# Initialize the Flask app
app = Flask(__name__)

# LINE Channel Access Token and Channel Secret
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("CHANNEL_SECRET")

# Initialize LINE API and Webhook handler
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
def get_display_name(user_id, channel_token=LINE_CHANNEL_ACCESS_TOKEN):
    url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {'Authorization': f'Bearer {channel_token}'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
        display_name = data.get('displayName', '')
    except requests.exceptions.RequestException as error:
        print(error)
        display_name = ''
    
    return display_name
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text
    user_name = get_display_name(user_id)
    response = chat(session_id=user_id, user_name=user_name, user_input=user_input)
    # print(response, user_id, flush=True)
    
    text_message = TextMessage(text=response)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(ReplyMessageRequest(reply_token=event.reply_token, messages=[text_message]))

      
@app.route('/health', methods=['GET'])
def index():
    return jsonify({'response': 'OK najaeiei'})

if __name__ == "__main__":
    # Run the Flask app
    app.run(port=int(os.environ.get("PORT", 10000)))
