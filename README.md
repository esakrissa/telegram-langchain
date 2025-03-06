# Travel Agency Telegram Bot

A Telegram bot that helps users plan their vacations by providing information about destinations, accommodations, flights, and activities in Bali. The bot uses LangChain with OpenAI's GPT-4o-mini model to generate responses.

## Features

- Interactive conversation flow with inline buttons
- Destination recommendations based on user preferences
- Resort selection and information
- Flight options and pricing
- Activity suggestions for families
- Budget planning assistance

## Prerequisites

- Python 3.10+
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

## Core Features (Future Implementation)

### 1. Initial Contact and Preference Gathering
The bot initiates the conversation by asking about travel dates, party size, destination preferences, and budget. Based on this information, it recommends suitable destinations in Bali such as Ubud (cultural heart), Seminyak/Kuta (beach resorts), and Uluwatu (clifftop luxury).

### 2. Dynamic Knowledge Retrieval
When users ask about specific destinations, the bot provides detailed information about:
- Safety considerations for families
- Family-friendly activities (e.g., Sacred Monkey Forest in Ubud, Waterbom Park in Kuta)
- Weather conditions during the travel period
- Travel requirements (passports, visas, etc.)

### 3. Multi-Turn Conversation with Memory
The bot remembers previous interactions, allowing for natural conversation flow. For example, if a user asks about safety in Ubud and then requests resort recommendations, the bot recalls the context and provides relevant family-friendly resort options with pricing details.

### 4. Integration with External Tools
The bot can simulate checking flight options from the user's location to Bali, providing:
- Flight options with airlines, prices, and schedules
- Total cost calculations combining flights and accommodation
- Budget comparison and alternatives if the total exceeds the user's budget

### 5. Advanced Planning and Problem Solving
If the initial options exceed the user's budget, the bot can suggest:
- Alternative accommodations at different price points
- Different travel dates for better pricing
- Budget-friendly activities and transportation options

### 6. Detailed Itinerary and Booking Support
The bot provides comprehensive information about activities near the chosen resort:
- Walking-distance attractions
- Short-drive excursions (e.g., Tegallalang Rice Terraces from Ubud)
- Worth-the-drive destinations (e.g., Bali Safari Park)
- Transportation options with approximate costs

## License

This project is licensed under the MIT License - see the LICENSE file for details. 