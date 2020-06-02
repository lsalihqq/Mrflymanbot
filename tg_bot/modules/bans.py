import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyelerini kısıtlamak / kısıtlamak için yeterli hak yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan tekme atması için kullanıcının davetli olması gerekir",
    "Chat_admin_required",
    "Yalnızca temel bir grubun yaratıcısı grup yöneticilerini tekmeleyebilir",
    "Channel_private",
    "Sohbette değil"
}

RUNBAN_ERRORS = {
    "Kullanıcı sohbetin yöneticisidir",
    "Sohbet bulunamadı",
    "Sohbet üyelerini kısıtlamak / kısıtlamak için yeterli hak yok",
    "User_not_participant",
    "Peer_id_invalid",
    "Grup sohbeti devre dışı bırakıldı",
    "Basit bir gruptan tekme atması için kullanıcının davetli olması gerekir",
    "Chat_admin_required",
    "Yalnızca temel bir grubun yaratıcısı grup yöneticilerini tekmeleyebilir",
    "Channel_private",
    "Sohbette değil"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Keşke yöneticileri yasaklayabilseydim ...")
        return ""

    if user_id == bot.id:
        message.reply_text("kendimi niye banlıyim aq?")
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} siktim öldü!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('siktim öldü!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Kahretsin, bu kullanıcıyı yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Keşke yöneticileri yasaklayabilseydim ...")
        return ""

    if user_id == bot.id:
        message.reply_text("kendimimi sikiyim neyin peşindesin?")
        return ""

    if not reason:
        message.reply_text("Bu kullanıcıyı yasaklamak için bir zaman belirtmediniz!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("siktim! sikme sebebim {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("siktim! sikme sebebim {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Lanet olsun, bu kullanıcıyı yasaklayamam.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("Keşke yöneticileri tekmeleyebilseydim ... ")
        return ""

    if user_id == bot.id:
        message.reply_text("Evet bunu yapmayacağım")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("götüne tekmeyi vurdum!")
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text("Kahretsin, o kullanıcıyı tekmeleyemem.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("Keşke yapabilseydim ... ama sen bir yöneticisin.")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("no problem.")
    else:
        update.effective_message.reply_text("yapmam")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("Eğer burada olmasaydım kendimi nasıl kaldırabilirim ki ...? ")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("Neden zaten sohbette olan birinin yasağını kaldırmaya çalışıyorsun?")
        return ""

    chat.unban_member(user_id)
    message.reply_text("evet gruba gelebilir!")

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbete / kullanıcıya atıfta bulunmuyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden ve bu sohbetin bir parçası olduğumdan emin olun.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("özel sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Oradaki insanları kısıtlayamıyorum! Yönetici olduğumdan ve kullanıcıları yasaklayabildiğimden emin olun.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı bulamıyorum")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("Gerçekten yöneticileri yasaklayabilseydim...")
        return

    if user_id == bot.id:
        message.reply_text("Kendimi BAN yapmayacağım, deli misin?")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("siktim öldü!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('siktim öldü!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Kahretsin, bu kullanıcıyı yasaklayamam.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("Bir sohbete / kullanıcıya atıfta bulunmuyorsunuz.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("Bir kullanıcıya atıfta bulunmuyorsunuz.")
        return
    elif not chat_id:
        message.reply_text("Bir sohbete atıfta bulunmuyorsunuz.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("Sohbet bulunamadı! Geçerli bir sohbet kimliği girdiğinizden ve bu sohbetin bir parçası olduğumdan emin olun.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("özel sohbet!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("Oradaki insanları sınırlayamam! Yönetici olduğumdan ve kullanıcıların yasağını kaldırabildiğimden emin olun.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("Bu kullanıcıyı orada bulamıyorum")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("Neden o sohbette olan birinin uzaktan yasağını kaldırmaya çalışıyorsunuz??")
        return

    if user_id == bot.id:
        message.reply_text("Kendimi UNBAN yapmayacağım, orada bir yöneticiyim!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("Evet, bu kullanıcı sohbete katılabilir!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('çıkarttım gelsin!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Kahretsin, bu kullanıcının yasağını kaldıramıyorum.")


__help__ = """
 - /kickme: grubtan çıkmak için

*sadece yönetici:*
 - /ban <sebebi>: banlar mesajı yanıtlayarak
 - /tban <sebebi> (dakika/saat/gün): süreli ban
 - /unban <kullanıcıadı>: banı kaldır
 - /kick <kullanıcı adı>: grubtan atar 
"""

__mod_name__ = "Ban"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
