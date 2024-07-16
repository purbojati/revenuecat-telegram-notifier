import json
import os
import requests
from datetime import datetime, timedelta
import pytz

TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHANNEL_ID = os.environ['TELEGRAM_CHANNEL_ID']

# Global variables to store daily summary
daily_summary = {
    'date': datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d'),
    'initial_purchases': 0,
    'renewals': 0,
    'cancellations': 0,
    'product_changes': 0,
    'total_revenue': 0
}

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHANNEL_ID, 'text': message}
    response = requests.post(url, json=data)
    if response.status_code != 200:
        print(f'Error sending Telegram message: {response.text}')

def update_daily_summary(event_type, price):
    global daily_summary
    
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(jakarta_tz)
    
    # If it's a new day, reset the summary
    if daily_summary['date'] != current_time.strftime('%Y-%m-%d'):
        daily_summary = {
            'date': current_time.strftime('%Y-%m-%d'),
            'initial_purchases': 0,
            'renewals': 0,
            'cancellations': 0,
            'product_changes': 0,
            'total_revenue': 0
        }
    
    if event_type == 'INITIAL_PURCHASE':
        daily_summary['initial_purchases'] += 1
        daily_summary['total_revenue'] += int(float(price))
    elif event_type == 'RENEWAL':
        daily_summary['renewals'] += 1
        daily_summary['total_revenue'] += int(float(price))
    elif event_type == 'CANCELLATION':
        daily_summary['cancellations'] += 1
    elif event_type == 'PRODUCT_CHANGE':
        daily_summary['product_changes'] += 1

    print(f"Event: {event_type}, Price: {price}, New Total Revenue: {daily_summary['total_revenue']}")

def generate_daily_summary():
    global daily_summary
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(jakarta_tz)
    yesterday = (current_time - timedelta(days=1)).strftime('%Y-%m-%d')
    
    message = (
        f"📊 Daily Summary for {yesterday} (Jakarta Time)\n\n"
        f"🎉 New Purchases: {daily_summary['initial_purchases']}\n"
        f"♻️ Renewals: {daily_summary['renewals']}\n"
        f"❌ Cancellations: {daily_summary['cancellations']}\n"
        f"🔁 Product Changes: {daily_summary['product_changes']}\n"
        f"💰 Total Revenue: Rp{daily_summary['total_revenue']}\n"
        f"\nGenerated at: {current_time.strftime('%Y-%m-%d %H:%M:%S')} WIB"
    )
    return message

def lambda_handler(event, context):
    try:
        # Check if this is a scheduled event for daily summary
        if event.get('detail-type') == 'Scheduled Event':
            summary_message = generate_daily_summary()
            send_telegram_message(summary_message)
            # Reset the summary for the new day
            global daily_summary
            daily_summary = {
                'date': datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d'),
                'initial_purchases': 0,
                'renewals': 0,
                'cancellations': 0,
                'product_changes': 0,
                'total_revenue': 0
            }
            return {
                'statusCode': 200,
                'body': 'Daily summary sent to Telegram successfully!'
            }

        # Log the incoming event for debugging
        print(f'Event: {event}')

        # Check if the event structure is as expected
        if 'event' not in event:
            raise ValueError("No event data in the received event")

        event_data = event['event']
        
        product_id = event_data.get('product_id')
        event_type = event_data.get('type')
        price = event_data.get('price_in_purchased_currency')
        user_id = event_data.get('app_user_id')
        new_product_id = event_data.get('new_product_id')

        if product_id is None or event_type is None or price is None:
            raise ValueError("Missing required fields in event data")

        # Update daily summary
        update_daily_summary(event_type, price)

        # Determine message based on event type
        if event_type == 'INITIAL_PURCHASE':
            message = (
                f"🎉 NEW PURCHASE\n"
                f"{product_id}\n"
                f"Rp{int(float(price))}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'RENEWAL':
            message = (
                f"♻️ R️ENEWAL\n"
                f"{product_id}\n"
                f"Rp{int(float(price))}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'CANCELLATION':
            message = (
                f"❌ CANCELLATION\n"
                f"{product_id}\n"
                f"Rp{int(float(price))}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        elif event_type == 'PRODUCT_CHANGE':
            message = (
                f"🔁 PRODUCT CHANGE\n"
                f"{product_id} → {new_product_id}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}\n"
            )
        else:
            message = (
                f"📢 OTHER EVENT\n"
                f"{product_id}\n"
                f"{event_type}\n"
                f"Rp{int(float(price))}\n"
                f"https://app.revenuecat.com/customers/ec85b090/{user_id}"
            )

        send_telegram_message(message)

        return {
            'statusCode': 200,
            'body': 'Message sent to Telegram successfully!'
        }
    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': 500,
            'body': f'Error processing request: {e}'
        }