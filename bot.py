import os
from datetime import datetime, timedelta
from dateutil import parser
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from ai_parser import extract_transaction
from sheets_store import save_transaction


BOT_TOKEN = os.getenv("BOT_TOKEN")
VALID_SHEETS = ["JCI", "SRPL", "JLM", "MJM", "JJM"]

# Track ongoing conversations
pending_transactions = {}


# -------- DATE NORMALIZER --------
def normalize_date(text):

    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    text = text.lower()

    if text == "today":
        return now.strftime("%Y-%m-%d")

    if text == "yesterday":
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    if text in ["day before", "day before yesterday"]:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")

    if text == "tomorrow":
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        parsed = parser.parse(text, fuzzy=True)
        return parsed.strftime("%Y-%m-%d")
    except:
        return None


# -------- GROUP DETECTOR --------
def detect_group(text):

    text = text.upper()

    for group in VALID_SHEETS:
        if group in text:
            return group

    return None


# -------- TELEGRAM HANDLER --------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    print("USER MESSAGE:", user_text)

    # If answering follow-up
    if user_id in pending_transactions:

        state = pending_transactions[user_id]
        field = state["next_field"]

        # DATE FOLLOW-UP
        if field == "date":

            parsed_date = normalize_date(user_text)

            if not parsed_date:
                await update.message.reply_text(
                    "Couldn't understand the date.\nTry: today, yesterday, 14 Jan, Tuesday"
                )
                return

            state["data"]["date"] = parsed_date

            if not state["data"]["amount"]:
                state["next_field"] = "amount"
                await update.message.reply_text("How much was the payment?")
                return

        # AMOUNT FOLLOW-UP
        if field == "amount":

            try:
                state["data"]["amount"] = float(user_text)
            except:
                await update.message.reply_text("Please enter a valid number.")
                return

            state["next_field"] = "category"
            await update.message.reply_text("What was this for?")
            return

        # CATEGORY FOLLOW-UP
        if field == "category":

            state["data"]["category"] = user_text
            state["next_field"] = "payment_mode"
            await update.message.reply_text("How did you pay?")
            return

        # PAYMENT MODE FOLLOW-UP
        if field == "payment_mode":

            state["data"]["payment_mode"] = user_text
            state["next_field"] = "group"

            await update.message.reply_text(
                "Which group?\nJCI / SRPL / JLM / MJM / JJM"
            )
            return

        # GROUP SELECTION
        if field == "group":

            sheet = user_text.upper()

            if sheet not in VALID_SHEETS:
                await update.message.reply_text(
                    "Please choose one:\nJCI / SRPL / JLM / MJM / JJM"
                )
                return

            save_transaction(
                state["data"],
                state["raw"],
                sheet
            )

            del pending_transactions[user_id]

            await update.message.reply_text("Transaction saved ✅")

            return

    # -------- NEW TRANSACTION --------
    try:

        sheet = detect_group(user_text)

        data = extract_transaction(user_text)

        print("AI PARSED DATA:", data)

        pending_transactions[user_id] = {
            "data": data,
            "raw": user_text,
            "next_field": None
        }

        # DATE CHECK
        if not data["date"]:
            pending_transactions[user_id]["next_field"] = "date"
            await update.message.reply_text("When was the payment made?")
            return
        else:
            data["date"] = normalize_date(data["date"])

        # AMOUNT CHECK
        if not data["amount"]:
            pending_transactions[user_id]["next_field"] = "amount"
            await update.message.reply_text("How much was the payment?")
            return

        # CATEGORY CHECK
        if not data["category"]:
            pending_transactions[user_id]["next_field"] = "category"
            await update.message.reply_text("What was this for?")
            return

        # PAYMENT MODE CHECK
        if not data["payment_mode"]:
            pending_transactions[user_id]["next_field"] = "payment_mode"
            await update.message.reply_text("How did you pay?")
            return

        # AUTO GROUP SAVE
        if sheet:

            save_transaction(
                data,
                user_text,
                sheet
            )

            del pending_transactions[user_id]

            await update.message.reply_text("Transaction saved ✅")

            return

        # ASK GROUP
        pending_transactions[user_id]["next_field"] = "group"

        await update.message.reply_text(
            "Which group?\nJCI / SRPL / JLM / MJM / JJM"
        )

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "Sorry, I couldn't understand that transaction."
        )


# -------- MAIN --------
def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()