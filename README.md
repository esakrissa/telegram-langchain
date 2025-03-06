# Travel Agency Telegram Bot

A Telegram bot that helps users plan their vacations by providing information about destinations, accommodations, flights, and activities. The bot uses LangChain with OpenAI's GPT-4o-mini model to generate responses.

## Features

- Interactive conversation flow with inline buttons
- Destination recommendations based on user preferences
- Resort selection and information
- Flight options and pricing
- Activity suggestions for families
- Budget planning assistance

## Prerequisites

- Python 3.8+
- Telegram Bot Token (from BotFather)
- OpenAI API Key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/telegram-langchain.git
cd telegram-langchain
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

1. Start the bot:
```bash
python bot.py
```

2. Open Telegram and search for your bot by username.

3. Start a conversation with the bot by sending the `/start` command.

4. Follow the conversation flow to plan your vacation.

## Conversation Flow

The bot follows a structured conversation flow:

1. **Initial Contact**: User expresses interest in planning a vacation
2. **Preference Gathering**: Bot asks about dates, party size, preferences, and budget
3. **Destination Recommendations**: Bot suggests suitable destinations
4. **Destination Details**: User can ask for more information about specific destinations
5. **Resort Selection**: Bot provides resort options based on the selected destination
6. **Flight Options**: Bot provides flight information
7. **Activity Suggestions**: Bot suggests activities at the destination
8. **Booking Support**: Bot assists with the booking process

## Example Conversation

```
User: Hi, I'm looking to plan a beach vacation next month
Bot: Hello! I'd be happy to help you plan your beach vacation. To get started:
* When exactly are you planning to travel next month?
* How many people will be traveling?
* Do you have any specific beach destinations in mind?
* What's your approximate budget range for this trip?

User: We're thinking June 15-22, 2 adults and 1 child. Somewhere warm with clear water. Budget around $3000 total.
Bot: Thanks for sharing those details! Based on your dates (June 15-22), party size (2 adults, 1 child), and $3000 budget, here are some warm destinations with clear waters that would work well:
1. Cancun, Mexico - Family-friendly resorts, beautiful Caribbean beaches
2. Punta Cana, Dominican Republic - All-inclusive options within your budget
3. Gulf Coast, Florida - Domestic option with less travel time
Would you like more information about any of these destinations? Or do you have other preferences I should consider?
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 