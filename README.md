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
The bot leverages multiple external APIs to provide real-time, accurate travel information:

#### Flight Information (Skyscanner API)
- Real-time flight searches with pricing, schedules, and airline options
- Fare alerts and price trend analysis
- Layover information and flight duration
- Baggage allowance and airline policies

#### Accommodation (Booking.com API)
- Real-time hotel availability and pricing
- Property details, amenities, and room types
- Guest reviews and ratings
- Special offers and package deals
- Real-time booking confirmation

#### Weather Services (OpenWeatherMap API)
- Current weather conditions in Bali
- 7-day weather forecast
- Seasonal weather patterns
- Natural disaster alerts and warnings

#### Currency Services (Exchange Rate API)
- Real-time currency conversion
- Historical exchange rate trends
- Local payment method information
- Price comparisons in user's preferred currency

#### Language Support (Google Cloud Translation API)
- Real-time translation of bot responses
- Common Indonesian phrases and pronunciation
- Cultural context and etiquette tips
- Menu and sign translation assistance

#### Comprehensive Cost Analysis
- Total trip cost calculation including flights, accommodation, and activities
- Budget tracking and allocation suggestions
- Price comparisons across different seasons
- Alternative options for budget optimization

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

## Technical Infrastructure

### Data Storage & Caching
#### Redis Caching System
- In-memory caching for frequently accessed data
- Caching of API responses (hotels seaerches, weather, currency rates, flight searches)
- Session management and rate limiting
- TTL-based cache invalidation for dynamic data
- Pub/Sub system for real-time updates

#### Supabase Database
- User preferences and profiles
- Conversation history and context
- Booking records and itineraries
- Analytics and usage statistics
- Audit logs and system events

### Development Environment
#### Local Development
- Docker containerization for consistent development
- Docker Compose for multi-service orchestration
- Hot-reloading for rapid development
- Environment-specific configuration management

#### Google Cloud Platform Setup
- GCP e2-micro instance for development environment
- Docker container deployment
- Cloud SQL for database management
- Cloud Storage for static assets
- Cloud Logging for centralized logging

### Production Deployment
#### Google Cloud Run
- Serverless container deployment
- Automatic scaling based on demand
- Zero-downtime deployments
- SSL/TLS certificate management
- Cloud CDN integration

#### CI/CD Pipeline (GitHub Actions)
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Google Cloud
        uses: google-github-actions/setup-gcloud@v0
        
      - name: Build and Push Docker Image
        run: |
          gcloud builds submit --tag gcr.io/$PROJECT_ID/telegram-bot
          
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy telegram-bot \
            --image gcr.io/$PROJECT_ID/telegram-bot \
            --platform managed \
            --region asia-southeast1
```

### Performance Optimization
- Redis caching for API responses
- Connection pooling for database queries
- Lazy loading of non-critical data
- Automated scaling based on load
- CDN for static asset delivery

### Monitoring and Logging
- Google Cloud Monitoring
- Prometheus metrics collection
- Grafana dashboards
- Error tracking and alerting
- Performance analytics

## License

This project is licensed under the MIT License - see the LICENSE file for details. 