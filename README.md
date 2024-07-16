# Lambda Telegram Notification for RevenueCat Events

This project implements an AWS Lambda function that processes RevenueCat webhook events and sends notifications to a Telegram channel. It also provides a daily summary of events at midnight Jakarta time.

## Features

- Real-time notifications for RevenueCat events (purchases, renewals, cancellations, etc.)
- Daily summary of events sent at midnight Jakarta time
- In-memory data storage for efficient processing
- Easy setup using AWS Lambda and EventBridge

## Prerequisites

- An AWS account with access to Lambda and EventBridge
- A Telegram bot token and channel ID
- A RevenueCat account with webhook configuration

## Setup

### 1. Create a Lambda Function

1. Go to AWS Lambda console and create a new function.
2. Choose Python 3.8 or later as the runtime.
3. Copy the code from `lambda_function.py` in this repository to your Lambda function.

### 2. Configure Environment Variables

In the Lambda function configuration, add the following environment variables:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_CHANNEL_ID`: Your Telegram channel ID

### 3. Set Up EventBridge Rule

1. Go to Amazon EventBridge console and create a new rule.
2. Set the rule to run on a schedule.
3. Use the following cron expression to run at midnight Jakarta time (5pm UTC): `0 17 * * ? *`
4. Set the target as your Lambda function.

### 4. Configure RevenueCat Webhook

In your RevenueCat dashboard:
1. Go to Project Settings > Integrations.
2. Add a new webhook.
3. Set the URL to your Lambda function's invoke URL.
4. Select the events you want to receive notifications for.

## Usage

Once set up, the system will automatically:
- Send individual notifications to your Telegram channel for each RevenueCat event.
- Send a daily summary at midnight Jakarta time.

### Resetting Data

To reset the in-memory data, invoke the Lambda function with the following test event:

```json
{
  "action": "reset_data"
}
```

## Customization

You can modify the `lambda_function.py` file to customize:
- The format of individual event messages
- The content of the daily summary
- The timezone for the daily summary (currently set to Asia/Jakarta)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
