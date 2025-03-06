# Bali Travel Planner Bot 🌴

> An AI-powered Telegram bot that helps plan the perfect Bali vacation using LangChain and GPT-4. Get personalized recommendations for destinations, accommodations, and activities while staying within your budget.

[![Deploy to Cloud Run](https://github.com/esakrissa/telegram-langchain/actions/workflows/deploy.yml/badge.svg)](https://github.com/esakrissa/telegram-langchain/actions/workflows/deploy.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🤖 **Smart Conversations**: Multi-turn dialogue with memory for natural interactions
- 🏨 **Real-time Data**: Live integration with flight, hotel, and weather APIs
- 🌍 **Language Support**: Automatic translation and cultural context
- 💰 **Budget Planning**: Smart cost analysis and alternative suggestions
- 📍 **Local Insights**: Curated recommendations for Bali's best experiences

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Telegram Bot Token
- OpenAI API Key

### Setup
```bash
# Clone and install
git clone https://github.com/yourusername/telegram-langchain.git
cd telegram-langchain
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python bot.py
```

## 🏗 Architecture

```mermaid
graph TD
    A[Telegram User] -->|Messages| B[Bot Service]
    B -->|Queries| C[LangChain + GPT-4]
    C -->|Cached Responses| D[Redis]
    C -->|Persistent Data| E[Supabase]
    B -->|External Data| F[Travel APIs]
```

### Tech Stack
- 🔄 **Runtime**: Python 3.10+, Docker
- 🧠 **AI/ML**: LangChain, OpenAI GPT-4
- 💾 **Storage**: Redis (Cache), Supabase (Database)
- ☁️ **Cloud**: GCP (e2-micro, Cloud Run)
- 🔄 **CI/CD**: GitHub Actions

## 🛠 Development

### Local Setup
```bash
docker-compose up -d
```

### Production Deployment
Automatically deployed to Google Cloud Run via GitHub Actions on main branch push.

## 📝 License

MIT © [Your Name]

---
Made with ❤️ for travelers 