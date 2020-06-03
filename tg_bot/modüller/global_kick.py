
import html
from telegram import Message, Update, Bot, User, Chat, ParseMode
from typing import List, Optional
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GKICK_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyesini kısıtlamak/kısıtlamamak için yeterli hak yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Temel bir gruptan tekmelemek için bir kullanıcının davetlisi olması gerekir",
    "Chat_admin_required",
    "Sadece temel bir grubun yaratıcısı grup yöneticilerini tekmeleyebilir",
    "Channel_private",
    "Sohbette yok",
    "Yöntem sadece süper grup ve kanal sohbetleri için kullanılabilir", 
}

@run_async
def gkick(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    user_id = extract_user(message, args)
    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in GKICK_ERRORS:
            pass
        else:
            message.reply_text("Kullanıcı Genel olarak tekmelenemez, çünkü: {}".format(excp.message))
            return
    except TelegramError:
            pass

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyor gibi görünüyorsunuz")
        Return
    if int(user_id) in SUDO_USERS or int(user_id) in SUPPORT_USERS:
        message.reply_text("OHHH! Birisi bir sudo / destek kullanıcı gkick çalışıyor! *patlamış mısır hazırla*")
        return
    if int(user_id) == OWNER_ID:
        message.reply_text("Wow! Birisi o kadar noob ki sahibimi tekmelemek istiyor! *Patates Cipsi hazırla*")
        Dönüş
    if int(user_id) == bot.id:
        message.reply_text("OHH... Kendimi tekmeleyeyim... Olmaz... ")
        return
    chats = get_all_chats()
    message.reply_text("Küresel tekme kullanıcı @{}".format(user_chat.username))
    for chat in chats:
        try:
             bot.unban_chat_member(chat.chat_id, user_id)  # Unban_member = kick (and not ban)
        except BadRequest as excp:
            if excp.message in GKICK_ERRORS:
                pass
            else:
                message.reply_text("Kullanıcı Genel olarak tekmelenemez, çünkü: {}".format(excp.message))
                return
        except TelegramError:
            pass

GKICK_HANDLER = CommandHandler("gkick", gkick, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
dispatcher.add_handler(GKICK_HANDLER)                              
