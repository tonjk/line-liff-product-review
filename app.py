import os
# from openai import OpenAI
import requests, json
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
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
print(LINE_CHANNEL_ACCESS_TOKEN, flush=True)
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

def gen_flex_content(response_with_order: dict):
    products = response_with_order.get('order', [])
    content = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "JORAKAY RECEIPT",
                    "weight": "bold",
                    "color": "#1DB446",
                    "size": "sm"
                },
                {
                    "type": "text",
                    "text": "สรุปรายการสินค้า",
                    "weight": "bold",
                    "size": "xl",
                    "margin": "xs"
                },
                {
                    "type": "separator",
                    "margin": "xxl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "md",
                    "contents": []
                }
                        ]
                },
         "footer": {
             "layout": "vertical",
             "contents": [
                 {
                    "color": "#00833e",
                    "style": "primary",
                    "action": {
                    "type": "uri",
                    "uri": "https://jorakaystore.com/homepage",
                    "label": "ชำระเงิน"
                    },
                    "type": "button"
          }
        ],
        "type": "box"
      },
        "styles": {
            "footer": {
                "separator": True
                        }
                    }
    }

    # Reference to the contents where products will be added
    product_contents = content["body"]["contents"][3]["contents"]

    # Loop to add each product dynamically
    for product in products:
        product_contents.append({
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": product["sku"],
                    "size": "sm",
                    "color": "#555555",
                    "flex": 0
                },
                {
                    "type": "text",
                    "text": f"{product['qty']}",
                    "size": "sm",
                    "color": "#111111",
                    "align": "end"
                }
            ]
        })

    # Extract shipping
    shipping_type = response_with_order.get('shipping_type', '')
    shipping_cost = 100 if shipping_type=="1" or shipping_type=="3" else 200 if shipping_type=="2" else 100
    # Add the final separator and total price section
    total_price = sum([float(product["price"])*int(product["qty"]) for product in products]) + shipping_cost
    product_contents.extend([
        {
            "type": "separator",
            "margin": "xxl"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "ค่าขนส่ง:",
                    "size": "xxs",
                    "color": "#555555"
                },
                {
                    "type": "text",
                    "text": f"{shipping_cost:,.2f} บาท",
                    "size": "xxs",
                    "color": "#111111",
                    "align": "end"
                }
            ]
        },
        {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "text",
                    "text": "ราคารวม:",
                    "size": "md",
                    "color": "#555555"
                },
                {
                    "type": "text",
                    "text": f"{total_price:,.2f} บาท",
                    "size": "md",
                    "color": "#111111",
                    "align": "end"
                }
            ]
        }
    ])

    # Add the footer section
    content["body"]["contents"].extend([
        {
            "type": "separator",
            "margin": "md"
        },
        {
            "type": "box",
            "layout": "horizontal",
            "margin": "md",
            "contents": [
                {
                    "type": "text",
                    "text": "THANK YOU",
                    "size": "xxs",
                    "color": "#aaaaaa",
                    "flex": 0,
                    "margin": "none"
                }
            ],
            "cornerRadius": "none",
            "justifyContent": "center"
        }
    ])
    flex_message = {"type": "flex",
                "altText": "This is a Flex Message",
                "contents": content}
    return flex_message

def send_flex_message(user_id, flex_message, response_text):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("LINE_CHANNEL_ACCESS_TOKEN")}'
    }
    data = {
        "to": user_id,
        "messages": [flex_message,
                     {"type": "text", "text": response_text}]
    }

    response = requests.post('https://api.line.me/v2/bot/message/push', headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status: {response.status_code}, Response: {response.text}")

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
    response = chat(session_id=user_id,user_input=user_input)
    print(response, user_id, flush=True)
    
    text_message = TextMessage(text=response)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(ReplyMessageRequest(reply_token=event.reply_token, messages=[text_message]))

      
@app.route('/health', methods=['GET'])
def index():
    return jsonify({'response': 'OK najaeiei'})

if __name__ == "__main__":
    # Run the Flask app
    app.run(port=int(os.getenv("PORT", 5000)))
