import os
from datetime import datetime, timedelta
from dateutil import parser
import pytz

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from ai_parser import extract_transaction
from sheets_store import save_transaction

# -------- SIMPLE FALLBACK PARSER --------
def simple_parse(text):

    words = text.lower().split()

    data = {
        "amount": None,
        "category": None,
        "payment_mode": None,
        "date": None,
        "type": None
    }

    # detect transaction type
    income_words = {"received", "got", "credited", "deposit", "refund", "incoming", "receivedfrom"}
    expense_words = {"paid", "gave", "sent", "spent", "bought"}

    for w in words:
        if w in income_words:
            data["type"] = "income"
            break
        if w in expense_words:
            data["type"] = "expense"
            break

    # detect amount
    for w in words:
        try:
            value = float(w)
            data["amount"] = value
            break
        except:
            pass

    # payment mode keywords
    if "gpay" in words or "upi" in words:
        data["payment_mode"] = "gpay"

    if "cash" in words:
        data["payment_mode"] = "cash"

    if "card" in words:
        data["payment_mode"] = "card"

    # detect date words
    for w in words:
        if w in ["today", "yesterday", "tomorrow"]:
            data["date"] = w

    # guess category (last word that isn't number/payment/date)
    blacklist = {
        "gpay", "upi", "cash", "card",
        "today", "yesterday", "tomorrow",
        "paid", "gave", "sent", "spent",
        "received", "got", "credited", "refund"
    }
    for w in reversed(words):
        if w not in blacklist:
            try:
                float(w)
                continue
            except:
                data["category"] = w
                break

    return data


BOT_TOKEN = os.getenv("BOT_TOKEN")
VALID_SHEETS = ["JCI", "SRPL", "JLM", "MJM", "JJM"]

pending_transactions = {}


# -------- DATE NORMALIZER --------
def normalize_date(text):

    india = pytz.timezone("Asia/Kolkata")
    now = datetime.now(india)

    text = text.lower().strip()

    # flexible phrases
    if "today" in text:
        return now.strftime("%Y-%m-%d")

    if "yesterday" in text:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")

    if "day before" in text:
        return (now - timedelta(days=2)).strftime("%Y-%m-%d")

    if "tomorrow" in text:
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        parsed = parser.parse(text, fuzzy=True)
        return parsed.strftime("%Y-%m-%d")
    except:
        return None


# -------- GROUP DETECTOR --------
def detect_group(text):

    text = text.upper()

    for g in VALID_SHEETS:
        if g in text:
            return g

    return None


# -------- FIELD CHECK PIPELINE --------
async def continue_pipeline(update, user_id):

    state = pending_transactions[user_id]
    data = state["data"]

    if not data.get("amount"):
        state["next_field"] = "amount"
        await update.message.reply_text("How much was the payment?")
        return

    if not data.get("category"):
        state["next_field"] = "category"
        await update.message.reply_text("What was this for?")
        return

    if not data.get("payment_mode"):
        state["next_field"] = "payment_mode"
        await update.message.reply_text("How did you pay?")
        return

    if not data.get("date"):
        state["next_field"] = "date"
        await update.message.reply_text("When was the payment made?")
        return

    # if group already detected, save directly
    if data.get("group"):
        save_transaction(data, state["raw"], data["group"])
        del pending_transactions[user_id]
        await update.message.reply_text("Transaction saved ✅")
        return

    state["next_field"] = "group"

    await update.message.reply_text(
        "Which group?\nJCI / SRPL / JLM / MJM / JJM"
    )


# -------- TELEGRAM HANDLER --------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    print("USER MESSAGE:", user_text)

    # -------- FOLLOW-UP FLOW --------
    if user_id in pending_transactions:

        state = pending_transactions[user_id]
        field = state["next_field"]
        data = state["data"]

        if field == "date":

            parsed = normalize_date(user_text)

            if not parsed:
                await update.message.reply_text(
                    "Couldn't understand the date.\nTry: today, yesterday, 14 Jan, Tuesday"
                )
                return

            data["date"] = parsed
            await continue_pipeline(update, user_id)
            return

        if field == "amount":

            try:
                data["amount"] = float(user_text)
            except:
                await update.message.reply_text("Please enter a valid number.")
                return

            await continue_pipeline(update, user_id)
            return

        if field == "category":

            data["category"] = user_text
            await continue_pipeline(update, user_id)
            return

        if field == "payment_mode":

            data["payment_mode"] = user_text
            await continue_pipeline(update, user_id)
            return

        if field == "group":

            sheet = user_text.upper()

            if sheet not in VALID_SHEETS:
                await update.message.reply_text(
                    "Please choose one:\nJCI / SRPL / JLM / MJM / JJM"
                )
                return

            data["group"] = sheet

            save_transaction(data, state["raw"], data["group"])

            del pending_transactions[user_id]

            await update.message.reply_text("Transaction saved ✅")

            return

    # -------- NEW TRANSACTION --------
    try:

        data = extract_transaction(user_text)

        # fallback parser if AI misses fields
        fallback = simple_parse(user_text)

        for k, v in fallback.items():
            if not data.get(k) and v:
                data[k] = v

        print("AI PARSED DATA:", data)

        # detect group from message
        sheet = detect_group(user_text)
        if sheet:
            data["group"] = sheet

        # normalize parsed date
        if data.get("date"):
            data["date"] = normalize_date(data["date"])

        pending_transactions[user_id] = {
            "data": data,
            "raw": user_text,
            "next_field": None
        }

        # FULL AUTO SAVE
        if (
            data.get("date")
            and data.get("amount")
            and data.get("category")
            and data.get("payment_mode")
            and data.get("group")
        ):

            save_transaction(data, user_text, data["group"])

            del pending_transactions[user_id]

            await update.message.reply_text("Transaction saved ✅")

            return

        # CONTINUE ASKING
        await continue_pipeline(update, user_id)

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "Sorry, I couldn't understand that transaction."
        )


# -------- MAIN --------
def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()