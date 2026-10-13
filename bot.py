# -*- coding: utf-8 -*-
"""
PUBG نۇپۇز سىستېمىسى: تېلېگرامما بوتى (Telegram Bot)
Inline Buttons ئارقىلىق نۇپۇزنى دەلىللەش (Approve / Reject) مەنتىقىسى.
Supabase بىلەن باغلانغان.
"""

import sys
import json
import re
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from supabase import create_client, Client

# -------------------------------------------------------------
# 1. سەپلىمە ئۇچۇرلىرىنى ئوقۇش
# -------------------------------------------------------------
# ئەگەر config.js دىن ئاپتوماتىك ئوقۇغىلى بولسا ئوقۇيدۇ، ياكى مۇشۇ يەردىن بىۋاسىتە ئۆزگەرتسىڭىزمۇ بولىدۇ
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key"
TELEGRAM_BOT_TOKEN = "your-bot-token"

# config.js دىن ئاپتوماتىك ئوقۇشقا ئۇرۇنۇش
try:
    with open("config.js", "r", encoding="utf-8") as f:
        content = f.read()
        url_match = re.search(r'SUPABASE_URL:\s*["\']([^"\']+)["\']', content)
        key_match = re.search(r'SUPABASE_ANON_KEY:\s*["\']([^"\']+)["\']', content)
        token_match = re.search(r'TELEGRAM_BOT_TOKEN:\s*["\']([^"\']+)["\']', content)
        if url_match and "your-project" not in url_match.group(1):
            SUPABASE_URL = url_match.group(1)
        if key_match and "your-anon-key" not in key_match.group(1):
            SUPABASE_ANON_KEY = key_match.group(1)
        if token_match and "your-bot-token" not in token_match.group(1):
            TELEGRAM_BOT_TOKEN = token_match.group(1)
except Exception as e:
    pass

# ئەگەر تېخى تەڭشەلمىگەن بولسا ئەسكەرتىش
if "your-bot-token" in TELEGRAM_BOT_TOKEN:
    print("=" * 60)
    print("⚠️ ئەسكەرتىش: config.js ياكى bot.py دا TELEGRAM_BOT_TOKEN ۋە SUPABASE تەڭشەكلىرىنى توغرىلاڭ!")
    print("=" * 60)

# Bot ۋە Supabase ئوبيېكتىنى قۇرۇش
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='HTML')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# -------------------------------------------------------------
# 2. كۇنۇپكا بېسىلغاندا بىر تەرەپ قىلىش (Callback Query Handler)
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data
    # كۇنۇپكا سانلىق مەلۇماتى فورماتى: approve_123 ياكى reject_123
    if not (data.startswith("approve_") or data.startswith("reject_")):
        bot.answer_callback_query(call.id, text="نامەلۇم مەشغۇلات!")
        return

    action, submission_id = data.split("_", 1)
    new_status = "approved" if action == "approve" else "rejected"
    status_text = "✅ تەستىقلاندى" if action == "approve" else "❌ رەت قىلىندى"
    operator_name = call.from_user.first_name or "باشقۇرغۇچى"

    try:
        # 1) Supabase دىكى مەۋجۇت ئۇچۇرنى تەكشۈرۈش
        res = supabase.table("popularity_submissions").select("*").eq("id", submission_id).execute()
        if not res.data or len(res.data) == 0:
            bot.answer_callback_query(call.id, text="⚠️ خاتالىق: بۇ خاتىرە تېپىلمىدى!", show_alert=True)
            return

        current_record = res.data[0]

        # 2) ئەگەر بۇرۇن بىر تەرەپ قىلىنغان بولسا ئەسكەرتىش
        if current_record.get("status") in ["approved", "rejected"]:
            prev_status = "تەستىقلانغان" if current_record.get("status") == "approved" else "رەت قىلىنغان"
            bot.answer_callback_query(
                call.id, 
                text=f"⚠️ بۇ ئۇچۇر بۇرۇنلا «{prev_status}» بولغان، قايتا بېسىشقا بولمايدۇ!", 
                show_alert=True
            )
            return

        # 3) Supabase سانداندىكى ھالەتنى يېڭىلاش
        now_iso = datetime.utcnow().isoformat()
        supabase.table("popularity_submissions").update({
            "status": new_status,
            "updated_at": now_iso
        }).eq("id", submission_id).execute()

        # 4) ئەسلى ئۇچۇر تېكىستىنى ئېلىش ۋە يېڭىلاش
        original_caption = call.message.caption or call.message.text or ""
        updated_caption = (
            f"{original_caption}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>ھالىتى:</b> {status_text}\n"
            f"👤 <b>بىر تەرەپ قىلغۇچى:</b> {operator_name}\n"
            f"⏰ <b>ۋاقتى:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 5) ئۇچۇرنى تەھرىرلەش (كۇنۇپكىنى يوقىتىش ۋە ھالەت قوشۇش)
        if call.message.caption is not None:
            # سۈرەتلىك ئۇچۇر بولسا caption نى يېڭىلاش
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=updated_caption,
                parse_mode="HTML",
                reply_markup=None  # كۇنۇپكىلارنى بىكار قىلىپ قايتا بېسىشنى چەكلەش
            )
        else:
            # تېكىستلىك ئۇچۇر بولسا text نى يېڭىلاش
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=updated_caption,
                parse_mode="HTML",
                reply_markup=None
            )

        # تەستىق مۇۋەپپەقىيەتلىك بولغانلىق ئەسكەرتمىسى (Toast)
        bot.answer_callback_query(call.id, text=f"مۇۋەپپەقىيەتلىك: {status_text}!")

    except Exception as e:
        print(f"خاتالىق كۆرۈلدى: {e}", file=sys.stderr)
        bot.answer_callback_query(call.id, text=f"خاتالىق كۆرۈلدى: {str(e)}", show_alert=True)


# -------------------------------------------------------------
# 3. باشلىنىش بۇيرۇقى (/start ۋە /help)
# -------------------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name or "دوستۇم"
    
    welcome_text = (
        f"👋 <b>ئەسسالامۇ ئەلەيكۇم، {user_name}!</b>\n\n"
        "🎮 <b>PUBG نۇپۇز (Popularity) رەسمىي دەلىللەش بوتىغا خۇش كەپسىز!</b>\n\n"
        "⚡ <b>سىستېما ئىقتىدارلىرى:</b>\n"
        "• تور بەتتىن كەلگەن نۇپۇز زاكازلىرىنى سۈرەت بىلەن دەل ۋاقتىدا قوبۇل قىلىش\n"
        "• بىرلا چەككەندە <b>[ ✅ تەستىقلاش ]</b> ياكى <b>[ ❌ رەت قىلىش ]</b>\n"
        "• ساندان ۋە كۆرۈنمە يۈزنى ئاپتوماتىك يېڭىلاش\n\n"
        f"🆔 <b>سىزنىڭ تېلېگرامما ID ڭىز:</b> <code>{message.chat.id}</code>\n\n"
        "👇 <b>تۆۋەندىكى تۈگمىلەرنى بېسىپ بىۋاسىتە تور بېكەتنى ئاچالايسىز:</b>"
    )

    # كۇنۇپكىلار (خېرىدار بېتى ۋە ئالاقىلىشىش)
    markup = InlineKeyboardMarkup(row_width=1)
    btn_website = InlineKeyboardButton(
        text="🌐 نۇپۇز تاپشۇرۇش بېتىنى ئېچىش", 
        url="https://musapparwaz-hub.github.io/musapparwaz/"
    )
    btn_contact = InlineKeyboardButton(
        text="💬 مەسئۇل بىلەن ئالاقىلىشىش", 
        url="https://t.me/SELilo7"
    )
    markup.add(btn_website, btn_contact)

    bot.reply_to(message, welcome_text, parse_mode="HTML", reply_markup=markup)


# ستاتىستىكا كۆرۈش بۇيرۇقى (/stats)
@bot.message_handler(commands=['stats'])
def send_stats(message):
    try:
        res = supabase.table("popularity_submissions").select("status").execute()
        data = res.data or []
        total = len(data)
        pending = sum(1 for x in data if x.get("status") == "pending")
        approved = sum(1 for x in data if x.get("status") == "approved")
        rejected = sum(1 for x in data if x.get("status") == "rejected")

        stats_text = (
            "📊 <b>نۇپۇز زاكازلىرى ستاتىستىكىسى:</b>\n\n"
            f"📦 <b>ئومۇمىي زاكاز:</b> {total}\n"
            f"⏳ <b>كۈتۈلمەكتە:</b> {pending}\n"
            f"✅ <b>تەستىقلانغان:</b> {approved}\n"
            f"❌ <b>رەت قىلىنغان:</b> {rejected}\n"
        )
        bot.reply_to(message, stats_text, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"ستاتىستىكىنى ئېلىشتا خاتالىق: {e}")


# -------------------------------------------------------------
# 4. بوتنى قوزغىتىش (Polling)
# -------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 PUBG نۇپۇز تېلېگرامما بوتى مۇۋەپپەقىيەتلىك قوزغالدى...")
    print("يېڭى نۇپۇز تاپشۇرۇش ئۇچۇرلىرى ۋە دەلىللەش كۇنۇپكىلىرى كۈتۈلمەكتە...")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as err:
        print(f"بوت خىزمىتىدە ئۈزۈلۈش كۆرۈلدى: {err}")
