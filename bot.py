import os
from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

from ai_parser import extract_transaction
from sheets_store import save_transaction


BOT_TOKEN = os.getenv("BOT_TOKEN")
VALID_SHEETS = ["JCI", "SRPL", "JLM", "MJM", "JJM"]

# Track ongoing conversations
pending_transactions = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    print("USER MESSAGE:", user_text)

    # If user is answering a follow-up question
    if user_id in pending_transactions:

        state = pending_transactions[user_id]
        field = state["next_field"]

        # Amount follow-up
        if field == "amount":

            try:
                state["data"]["amount"] = float(user_text)
            except:
                await update.message.reply_text("Please enter a valid number.")
                return

            state["next_field"] = "category"
            await update.message.reply_text("What was this for?")
            return

        # Category follow-up
        if field == "category":

            state["data"]["category"] = user_text
            state["next_field"] = "payment_mode"
            await update.message.reply_text("How did you pay?")
            return

        # Payment mode follow-up
        if field == "payment_mode":

            state["data"]["payment_mode"] = user_text
            state["next_field"] = "group"

            await update.message.reply_text(
                "Which group?\nJCI / SRPL / JLM / MJM / JJM"
            )
            return

        # Group selection
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

    # Otherwise this is a new transaction
    try:

        data = extract_transaction(user_text)

        print("AI PARSED DATA:", data)

        pending_transactions[user_id] = {
            "data": data,
            "raw": user_text,
            "next_field": None
        }

        # Follow-up order

        if not data["amount"]:
            pending_transactions[user_id]["next_field"] = "amount"
            await update.message.reply_text("How much was the payment?")
            return

        if not data["category"]:
            pending_transactions[user_id]["next_field"] = "category"
            await update.message.reply_text("What was this for?")
            return

        if not data["payment_mode"]:
            pending_transactions[user_id]["next_field"] = "payment_mode"
            await update.message.reply_text("How did you pay?")
            return

        pending_transactions[user_id]["next_field"] = "group"

        await update.message.reply_text(
            "Which group?\nJCI / SRPL / JLM / MJM / JJM"
        )

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            "Sorry, I couldn't understand that transaction."
        )


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()