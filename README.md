AI-powered Telegram Finance Bot that converts text and cheque images into structured transactions, auto-validates entries, and logs them into Google Sheets with intelligent parsing, OCR, and conversational workflows.

⸻

💸 Finance Bot — AI-Powered Transaction Logger

An intelligent Telegram bot that converts natural language messages and cheque images into structured financial records and logs them directly into Google Sheets.

Built for real-world usage, the bot combines:

* 🤖 AI-based transaction parsing
* 🧾 Cheque OCR + validation
* 💬 Conversational data completion
* 📊 Automated Google Sheets logging

⸻

✨ Features

🧠 Smart Text Parsing

* Understands messages like:
    * JLM paid 200 to Priya
    * Received 15000 from Arun via bank transfer
* Detects:
    * amount
    * type (income/expense)
    * category
    * payment mode
    * group
    * TDS

⸻

💬 Conversational Flow

* Automatically asks for missing fields:
    * date
    * amount
    * category
    * payment mode
    * TDS (always asked)
    * group
* Maintains context across messages

⸻

🧾 Cheque OCR (Next-Level Feature)

* Upload a cheque image → bot extracts:
    * amount
    * payee
    * date
* Then:
    * asks for TDS
    * asks for narration
    * confirms with user:
        “Let me confirm — are these details correct?”

⸻

🔍 Hybrid AI + Rule Engine

* Uses LLM (Perplexity/OpenAI-compatible)
* Falls back to regex + heuristics for reliability
* Handles edge cases like:
    * “JLM paid…” vs “Priya paid…”
    * narration-based inference
    * messy real-world inputs

⸻

📊 Google Sheets Integration

Logs transactions into structured columns:

date | amount | type | category | description | payment_mode | tds_percent | raw_message

Supports multiple sheets:

* JCI
* SRPL
* JLM
* MJM
* JJM

⸻

🧪 Safe Test Environment

* .env.test vs .env.production
* DRY_RUN=true mode (no real writes)
* Separate test bot + test sheet

⸻

🏗️ Architecture

Telegram → Bot → AI Parser → Validation Layer → Sheets Store
                          ↘ OCR (for cheques)

⸻

📂 Project Structure

finance_bot/
├── bot.py                # Main Telegram bot logic
├── ai_parser.py          # AI + rule-based transaction extraction
├── cheque_ocr.py        # OCR + cheque parsing logic
├── sheets_store.py      # Google Sheets integration
├── config.py            # Environment handling (optional)
├── requirements.txt
├── .env.test
├── .env.production
├── test_parser.py
├── test_cheque_ocr.py

⸻

⚙️ Setup

1. Clone repo

git clone https://github.com/yourusername/finance_bot.git
cd finance_bot

⸻

2. Create virtual environment

python3 -m venv .venv
source .venv/bin/activate

⸻

3. Install dependencies

pip install -r requirements.txt

⸻

4. Setup environment variables

Create .env.test:

BOT_TOKEN=your_test_telegram_bot_token
OPENAI_API_KEY=your_api_key
GOOGLE_SHEET_ID=your_test_sheet_id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
ENVIRONMENT=test
DRY_RUN=true

⸻

5. Run bot locally

python bot.py

⸻

🧪 Testing

Test parser only

python test_parser.py

⸻

Test cheque OCR

python test_cheque_ocr.py

⸻

Test full bot

* Message your test Telegram bot
* Try:

JLM paid 200 to Priya
Received 15000 from Arun
Lunch 300

⸻

🔐 Safety & Best Practices

* ❌ Never commit credentials.json
* ❌ Never expose API keys
* ✅ Use .env.test for development
* ✅ Use separate test Google Sheet
* ✅ Use DRY_RUN=true before real writes

⸻

🧠 Future Roadmap

* Handwriting training loop for cheque OCR
* Confidence scoring + auto-correction
* Dashboard for analytics
* Multi-user authentication
* WhatsApp integration

⸻

👨‍💻 Author

Samarth Madhivanan
AI + Healthcare + Systems Builder

⸻

⭐ Why this project stands out

This isn’t just a bot — it’s a mini financial assistant system combining:

* LLM reasoning
* OCR pipelines
* conversational UX
* real-world accounting workflows

⸻
