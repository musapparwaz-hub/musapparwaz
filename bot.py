# -*- coding: utf-8 -*-
"""
PUBG نۇپۇز سىستېمىسى: تېلېگرامما بوتى (Telegram Bot)
- Inline Buttons ئارقىلىق تەستىقلاش / رەت قىلىش
- دەلىللەش نەتىجىسىنى باشقۇرغۇچى ۋە خېرىدارغا دەرھال يەتكۈزۈش
- پەقەت باشقۇرغۇچىغىلا ئېچىۋېتىلگەن «بارلىق ئابونتلارغا ئۇچۇر تارقىتىش (Broadcast)» مەركىزى
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
SUPABASE_URL = "https://soqeaukdppqcxvdhonac.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_5Bqn-ZdZ_bmvBZTLYDsVXA_ZGkijOlC"
TELEGRAM_BOT_TOKEN = "8672194185:AAG3cor9idBuCOz8Qm84JUkwe1hLfRRpEYY"
ADMIN_CHAT_ID = "6613680953"

# config.js دىن ئوقۇپ قوشۇمچە يېڭىلاش
try:
    with open("config.js", "r", encoding="utf-8") as f:
        content = f.read()
        url_match = re.search(r'SUPABASE_URL:\s*["\']([^"\']+)["\']', content)
        key_match = re.search(r'SUPABASE_ANON_KEY:\s*["\']([^"\']+)["\']', content)
        token_match = re.search(r'TELEGRAM_BOT_TOKEN:\s*["\']([^"\']+)["\']', content)
        chat_match = re.search(r'TELEGRAM_CHAT_ID:\s*["\']([^"\']+)["\']', content)
        if url_match and "your-project" not in url_match.group(1):
            SUPABASE_URL = url_match.group(1)
        if key_match and "your-anon-key" not in key_match.group(1):
            SUPABASE_ANON_KEY = key_match.group(1)
        if token_match and "your-bot-token" not in token_match.group(1):
            TELEGRAM_BOT_TOKEN = token_match.group(1)
        if chat_match and "your-chat-id" not in chat_match.group(1):
            ADMIN_CHAT_ID = str(chat_match.group(1)).strip()
except Exception:
    pass

# Bot ۋە Supabase ئوبيېكتىنى قۇرۇش
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='HTML')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# باشقۇرغۇچىنىڭ نۆۋەتتىكى ھالىتى (State tracking)
admin_states = {}


# -------------------------------------------------------------
# 2. ئابونتلارنى ساندانغا قوشۇش (Auto register bot user)
# -------------------------------------------------------------
def register_user(from_user):
    try:
        supabase.table("bot_users").upsert({
            "user_id": from_user.id,
            "first_name": from_user.first_name or "",
            "username": from_user.username or ""
        }).execute()
    except Exception:
        pass


# -------------------------------------------------------------
# 3. كۇنۇپكا بېسىلغاندا بىر تەرەپ قىلىش (Approve / Reject)
# -------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    data = call.data
    operator_id = str(call.from_user.id)

    # 1) باشقۇرغۇچى ئۇچۇر يوللاش كۇنۇپكىسىنى باسقاندا
    if data == "admin_start_broadcast":
        if operator_id != str(ADMIN_CHAT_ID):
            bot.answer_callback_query(call.id, text="بۇ بۆلەك پەقەت باشقۇرغۇچىغىلا ئوچۇق!", show_alert=True)
            return
        admin_states[operator_id] = "waiting_for_broadcast_msg"
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id=call.message.chat.id,
            text=(
                "✍️ <b>بارلىق ئابونتلارغا ئەۋەتىدىغان ئۇچۇر تېكىستىنى مۇشۇ يەرگە يېزىپ يوللاڭ:</b>\n\n"
                "<i>(ئەسكەرتىش: يازغان خېتىڭىز بوتقا ئەزا بولغان ھەممە ئادەمگە دەرھال بېرىدۇ. بىكار قىلىش ئۈچۈن /cancel نى بېسىڭ)</i>"
            ),
            parse_mode="HTML"
        )
        return

    # 2) تەستىقلاش ۋە رەت قىلىش
    if not (data.startswith("approve_") or data.startswith("reject_")):
        bot.answer_callback_query(call.id, text="نامەلۇم مەشغۇلات!")
        return

    action, submission_id = data.split("_", 1)
    new_status = "approved" if action == "approve" else "rejected"
    status_text = "✅ تەستىقلاندى" if action == "approve" else "❌ رەت قىلىندى"
    operator_name = call.from_user.first_name or "باشقۇرغۇچى"

    try:
        # Supabase دىكى ئۇچۇرنى ئېلىش
        res = supabase.table("popularity_submissions").select("*").eq("id", submission_id).execute()
        if not res.data or len(res.data) == 0:
            bot.answer_callback_query(call.id, text="⚠️ خاتالىق: بۇ خاتىرە تېپىلمىدى!", show_alert=True)
            return

        current_record = res.data[0]

        # ئەگەر ئىلگىرى بىر تەرەپ قىلىنغان بولسا ئەسكەرتىش
        if current_record.get("status") in ["approved", "rejected"]:
            prev_status = "تەستىقلانغان" if current_record.get("status") == "approved" else "رەت قىلىنغان"
            bot.answer_callback_query(
                call.id, 
                text=f"⚠️ بۇ ئۇچۇر بۇرۇنلا «{prev_status}» بولغان!", 
                show_alert=True
            )
            return

        # Supabase نى يېڭىلاش
        now_iso = datetime.utcnow().isoformat()
        supabase.table("popularity_submissions").update({
            "status": new_status,
            "updated_at": now_iso
        }).eq("id", submission_id).execute()

        # باشقۇرغۇچىنىڭ تېلېگرامما ئېكرانىدىكى ئۇچۇرنى يېڭىلاش
        original_caption = call.message.caption or call.message.text or ""
        updated_caption = (
            f"{original_caption}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📌 <b>ھالىتى:</b> {status_text}\n"
            f"👤 <b>تەستىقلىغۇچى:</b> {operator_name}\n"
            f"⏰ <b>ۋاقتى:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if call.message.caption is not None:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=updated_caption,
                parse_mode="HTML",
                reply_markup=None
            )
        else:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=updated_caption,
                parse_mode="HTML",
                reply_markup=None
            )

        bot.answer_callback_query(call.id, text=f"مۇۋەپپەقىيەتلىك: {status_text}!")

        # 3) ئابونىتقا (خېرىدارغا) تېلېگرامما ئارقىلىق دەرھال يەتكۈزۈش
        contact_raw = current_record.get("contact_info")
        pubg_id_val = current_record.get("pubg_id")
        amount_val = current_record.get("amount")

        if contact_raw:
            clean_chat_id = "".join(filter(str.isdigit, str(contact_raw)))
            if clean_chat_id and len(clean_chat_id) >= 6:
                try:
                    if new_status == "approved":
                        user_notice = (
                            f"🎉 <b>ھۆرمەتلىك ئابونت، نۇپۇز زاكازىڭىز تەستىقلاندى!</b>\n\n"
                            f"🎮 <b>PUBG ID:</b> <code>{pubg_id_val}</code>\n"
                            f"💎 <b>نۇپۇز سانى:</b> <b>+{int(amount_val):,}</b>\n"
                            f"📌 <b>ھالىتى:</b> ✅ تەستىقلاندى\n"
                            f"⏰ <b>ۋاقتى:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                            f"رەھمەت، نۇپۇز ئويۇن ھېساباتىڭىزغا كۈچكە ئىگە بولدى! ✨"
                        )
                    else:
                        user_notice = (
                            f"⚠️ <b>ھۆرمەتلىك ئابونت، نۇپۇز زاكازىڭىز رەت قىلىندى!</b>\n\n"
                            f"🎮 <b>PUBG ID:</b> <code>{pubg_id_val}</code>\n"
                            f"💎 <b>نۇپۇز سانى:</b> {int(amount_val):,}\n"
                            f"📌 <b>ھالىتى:</b> ❌ رەت قىلىندى\n\n"
                            f"مەسىلە كۆرۈلسە مەسئۇل خادىم بىلەن ئالاقىلىشىڭ: @SELilo7"
                        )
                    bot.send_message(chat_id=clean_chat_id, text=user_notice, parse_mode="HTML")
                except Exception as notify_err:
                    print(f"خېرىدارغا ئۇقتۇرۇش ئەۋەتىشتە خاتالىق: {notify_err}", file=sys.stderr)

    except Exception as e:
        print(f"خاتالىق كۆرۈلدى: {e}", file=sys.stderr)
        bot.answer_callback_query(call.id, text=f"خاتالىق: {str(e)}", show_alert=True)


# -------------------------------------------------------------
# 4. بارلىق كىرگەن ئۇچۇرلارنى بىر تەرەپ قىلىش
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    from_id = str(message.chat.id)
    register_user(message.from_user)

    # 1) باشقۇرغۇچى ئۇچۇر تارقىتىشنى بىكار قىلسا
    if message.text and message.text.strip() == "/cancel":
        if from_id in admin_states:
            del admin_states[from_id]
            bot.reply_to(message, "❌ مەشغۇلات بىكار قىلىندى.")
            return

    # 2) باشقۇرغۇچى ئابونتلارغا ئۇچۇر تارقىتىۋاتقان بولسا
    if from_id == str(ADMIN_CHAT_ID) and admin_states.get(from_id) == "waiting_for_broadcast_msg":
        broadcast_text = message.text or ""
        del admin_states[from_id]

        status_msg = bot.reply_to(message, "⏳ ئۇچۇر بارلىق ئابونتلارغا ئەۋەتىلىۋاتىدۇ...")
        
        try:
            # بارلىق ئابونتلارنى ئوقۇش
            users_res = supabase.table("bot_users").select("user_id").execute()
            users_list = users_res.data or []
            
            success_count = 0
            fail_count = 0

            for u in users_list:
                uid = u.get("user_id")
                if str(uid) == str(ADMIN_CHAT_ID):
                    continue
                try:
                    bot.send_message(
                        chat_id=uid,
                        text=f"📢 <b>باشقۇرغۇچىدىن يېڭى ئۇقتۇرۇش:</b>\n\n{broadcast_text}",
                        parse_mode="HTML"
                    )
                    success_count += 1
                except Exception:
                    fail_count += 1

            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"✅ <b>ئۇچۇر تارقىتىش تاماملاندى!</b>\n\n👥 مۇۋەپپەقىيەتلىك يەتكۈزۈلدى: {success_count}\n❌ مەغلۇپ بولدى: {fail_count}"
            )
        except Exception as err:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=status_msg.message_id,
                text=f"ئۇچۇر ئەۋەتىشتە خاتالىق كۆرۈلدى: {err}"
            )
        return

    # 3) باشقۇرغۇچى مەخسۇس باشقۇرۇش كۆرۈنمە يۈزى (پەقەت ADMIN كۆرەلەيدۇ)
    if from_id == str(ADMIN_CHAT_ID):
        admin_panel_markup = InlineKeyboardMarkup(row_width=1)
        btn_broadcast = InlineKeyboardButton(text="📢 ئابونتلارغا ئومۇمىي ئۇچۇر تارقىتىش", callback_data="admin_start_broadcast")
        btn_website = InlineKeyboardButton(text="🌐 نۇپۇز تاپشۇرۇش بېتى", url="https://musapparwaz-hub.github.io/musapparwaz/")
        btn_admin_web = InlineKeyboardButton(text="🔐 تور باشقۇرۇش مەركىزى", url="https://musapparwaz-hub.github.io/musapparwaz/admin.html")
        admin_panel_markup.add(btn_broadcast, btn_website, btn_admin_web)

        admin_welcome = (
            f"👑 <b>ھۆرمەتلىك باشقۇرغۇچى، سىستېمىغا مەرھابا!</b>\n\n"
            "بۇ سىزنىڭ مەخسۇس باشقۇرۇش كۆزنىكىڭىز. بۇ يەردىن كەلگەن نۇپۇزلارنى تەستىقلىيالايسىز ياكى بارلىق ئابونتلارغا بىۋاسىتە ئۇقتۇرۇش تارقىتالايسىز.\n\n"
            "👇 <b>تۆۋەندىكى تۈگمىدىن مەشغۇلاتنى تاللاڭ:</b>"
        )
        bot.reply_to(message, admin_welcome, parse_mode="HTML", reply_markup=admin_panel_markup)
        return

    # 4) ئادەتتىكى خېرىدارلار ئۈچۈن قارشى ئېلىش ئۇچۇرى (باشقۇرۇش بۆلىكى قەتئىي كۆرۈنمەيدۇ)
    user_name = message.from_user.first_name or "دوستۇم"
    client_welcome = (
        f"👋 <b>ئەسسالامۇ ئەلەيكۇم، {user_name}!</b>\n\n"
        "🎮 <b>PUBG نۇپۇز (Popularity) رەسمىي دەلىللەش مەركىزىگە خۇش كەپسىز!</b>\n\n"
        "⚡ <b>سىز بۇ يەردە:</b>\n"
        "• ئويۇن كىملىكىڭىزگە تېز سۈرئەتتە نۇپۇز قاچىلىيالايسىز.\n"
        "• زاكاز تاپشۇرغاندىن كېيىن، تەستىق نەتىجىسى مۇشۇ يەرگە دەرھال كېلىدۇ.\n\n"
        "👇 <b>تۆۋەندىكى تۈگمىنى بېسىپ نۇپۇز تاپشۇرۇش بېتىنى ئېچىڭ:</b>"
    )

    client_markup = InlineKeyboardMarkup(row_width=1)
    btn_website = InlineKeyboardButton(text="🚀 نۇپۇز تاپشۇرۇش بېتىنى ئېچىش", url="https://musapparwaz-hub.github.io/musapparwaz/")
    btn_contact = InlineKeyboardButton(text="💬 مەسئۇل بىلەن ئالاقىلىشىش", url="https://t.me/SELilo7")
    client_markup.add(btn_website, btn_contact)

    bot.reply_to(message, client_welcome, parse_mode="HTML", reply_markup=client_markup)


# -------------------------------------------------------------
# 5. بوتنى توختىماي قوزغىتىش
# -------------------------------------------------------------
if __name__ == "__main__":
    print(f"🚀 PUBG نۇپۇز بوتى مۇۋەپپەقىيەتلىك قوزغالدى! Admin ID: {ADMIN_CHAT_ID}")
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as err:
        print(f"بوت خىزمىتىدە ئۈزۈلۈش: {err}")
