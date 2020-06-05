
from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

from requests import get

@run_async
def ud(bot: Bot, update: Update):
  message = update.effective_message
  text = message.text[len('/ud '):]
  results = get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
  reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
  message.reply_text(reply_text)

__help__ = """
 - /ud:{kelime} Aramak istediğiniz sözcüğü veya ifadeyi yazın. /ud telegram Word: Telegram Definition: Bir zamanlar popüler olan telekomünikasyon sistemi, gönderenin telgraf servisiyle iletişimkuracağı ve [telefon] üzerinden [mesajlarını] konuşacağı bir sistemdir. İletiyi alan kişi daha sonra teletip makinesi aracılığıyla alıcının [adresi] yakınındaki bir telgraf ofisine gönderir. İleti daha sonra adrese elden teslim edilir. 1851'den 2006'da hizmeti kesilene kadar, Western Union"
"""

__mod_name__ = "ud"
  
ud_handle = DisableAbleCommandHandler("ud", ud)

dispatcher.add_handler(ud_handle)
