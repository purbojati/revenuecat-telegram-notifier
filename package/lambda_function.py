# NEW CODE
import json
import os
import requests
from datetime import datetime
import pytz
import boto3
from boto3.dynamodb.conditions import Key
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHANNEL_ID = os.environ['TELEGRAM_CHANNEL_ID']
DYNAMODB_TABLE_NAME = 'DailySummary'

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def get_daily_summary(date):
    try:
        response = table.get_item(Key={'date': date})
        default_summary = {
            'date': date,
            'initial_purchases_android': 0,
            'initial_purchases_ios': 0,
            'renewals_android': 0,
            'renewals_ios': 0,
            'cancellations_android': 0,
            'cancellations_ios': 0,
            'product_changes_android': 0,
            'product_changes_ios': 0,
            'total_revenue_android': 0,
            'total_revenue_ios': 0
        }
        
        if 'Item' in response:
            logger.info(f"Retrieved summary for date: {date}")
            # Merge existing data with default values to ensure all fields exist
            return {**default_summary, **response['Item']}
        else:
            logger.info(f"No existing summary found for date: {date}. Creating new summary.")
            return default_summary
            
    except Exception as e:
        logger.error(f"Error retrieving summary from DynamoDB: {str(e)}")
        raise

def update_daily_summary(event_type, price, platform):
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_date = datetime.now(jakarta_tz).strftime('%Y-%m-%d')
    
    summary = get_daily_summary(current_date)
    platform = platform.lower()
    
    if event_type == 'INITIAL_PURCHASE':
        summary[f'initial_purchases_{platform}'] += 1
        summary[f'total_revenue_{platform}'] += int(float(price))
    elif event_type == 'RENEWAL':
        summary[f'renewals_{platform}'] += 1
        summary[f'total_revenue_{platform}'] += int(float(price))
    elif event_type == 'CANCELLATION':
        summary[f'cancellations_{platform}'] += 1
    elif event_type == 'PRODUCT_CHANGE':
        summary[f'product_changes_{platform}'] += 1

    try:
        table.put_item(Item=summary)
        logger.info(f"Updated summary for date: {current_date}")
    except Exception as e:
        logger.error(f"Error updating summary in DynamoDB: {str(e)}")
        raise

def generate_daily_summary():
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_date = datetime.now(jakarta_tz).strftime('%Y-%m-%d')
    summary = get_daily_summary(current_date)
    
    total_purchases = summary['initial_purchases_android'] + summary['initial_purchases_ios']
    total_renewals = summary['renewals_android'] + summary['renewals_ios']
    total_cancellations = summary['cancellations_android'] + summary['cancellations_ios']
    total_changes = summary['product_changes_android'] + summary['product_changes_ios']
    total_revenue = summary['total_revenue_android'] + summary['total_revenue_ios']
    
    message = (
        f"╔═══════════════════════════\n"
        f"║ 📊 DAILY SUMMARY • {current_date}\n"
        f"╠═══════════════════════════\n"
        f"║ 📱 TOTAL\n"
        f"╟───────────────────────────\n"
        f"║ 🎉 New Purchases    : {total_purchases}\n"
        f"║ ♻️ Renewals         : {total_renewals}\n"
        f"║ ❌ Cancellations    : {total_cancellations}\n"
        f"║ 🔁 Product Changes  : {total_changes}\n"
        f"║ 💰 Revenue         : Rp{int(total_revenue):,}\n"
        f"╠═══════════════════════════\n"
        f"║ 🤖 ANDROID\n"
        f"╟───────────────────────────\n"
        f"║ 🎉 New Purchases    : {summary['initial_purchases_android']}\n"
        f"║ ♻️ Renewals         : {summary['renewals_android']}\n"
        f"║ ❌ Cancellations    : {summary['cancellations_android']}\n"
        f"║ 🔁 Product Changes  : {summary['product_changes_android']}\n"
        f"║ 💰 Revenue         : Rp{int(summary['total_revenue_android']):,}\n"
        f"╠═══════════════════════════\n"
        f"║ 🍎 iOS\n"
        f"╟───────────────────────────\n"
        f"║ 🎉 New Purchases    : {summary['initial_purchases_ios']}\n"
        f"║ ♻️ Renewals         : {summary['renewals_ios']}\n"
        f"║ ❌ Cancellations    : {summary['cancellations_ios']}\n"
        f"║ 🔁 Product Changes  : {summary['product_changes_ios']}\n"
        f"║ 💰 Revenue         : Rp{int(summary['total_revenue_ios']):,}\n"
        f"╚═══════════════════════════\n\n"
        f"Generated: {datetime.now(jakarta_tz).strftime('%Y-%m-%d %H:%M:%S')} WIB"
    )
    return message

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHANNEL_ID, 'text': message}
    response = requests.post(url, json=data)
    if response.status_code != 200:
        logger.error(f'Error sending Telegram message: {response.text}')

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        if event.get('detail-type') == 'Scheduled Event':
            summary_message = generate_daily_summary()
            send_telegram_message(summary_message)
            return {
                'statusCode': 200,
                'body': json.dumps('Daily summary sent to Telegram successfully!')
            }

        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        if 'event' not in body:
            raise ValueError("No event data in the received webhook")

        event_info = body['event']
        
        product_id = event_info.get('product_id', 'Unknown Product')
        event_type = event_info.get('type', 'Unknown Event')
        price = event_info.get('price_in_purchased_currency') or event_info.get('price', 0)
        user_id = event_info.get('app_user_id', 'Unknown User')
        new_product_id = event_info.get('new_product_id', 'N/A')
        
        platform = event_info.get('store', 'Unknown Platform').upper()
        if platform == 'APP_STORE':
            platform = 'IOS'
        elif platform == 'PLAY_STORE':
            platform = 'ANDROID'

        if event_type == 'INITIAL_PURCHASE':
            message = (
                f"🎉 NEW PURCHASE ({platform})\n"
                f"{product_id}\n"
                f"Rp{int(float(price)):,}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'RENEWAL':
            message = (
                f"♻️ R️ENEWAL ({platform})\n"
                f"{product_id}\n"
                f"Rp{int(float(price)):,}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'CANCELLATION':
            message = (
                f"❌ CANCELLATION ({platform})\n"
                f"{product_id}\n"
                f"Rp{int(float(price)):,}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'PRODUCT_CHANGE':
            message = (
                f"🔁 PRODUCT CHANGE ({platform})\n"
                f"{product_id} → {new_product_id}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        else:
            message = (
                f"📢 NDAK TAU ({platform})\n"
                f"{product_id}\n"
                f"{event_type}\n"
                f"Rp{int(float(price)):,}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}"
            )

        update_daily_summary(event_type, price, platform)
        send_telegram_message(message)

        return {
            'statusCode': 200,
            'body': json.dumps('Message sent to Telegram successfully!')
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing request: {str(e)}')
        }