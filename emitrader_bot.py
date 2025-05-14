import asyncio
import datetime
import pytz
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

operation_type = None
relatorio = []
relatorio_total = []
current_operation = {}
waiting_for_gale_time = False
gale_stage = 0

STICKER_WIN = 'CAACAgEAAxkBAAPhZsnoOnV7QkVn-3CbCRKC2e3XmuoAAjIEAAI6q-BF_bQwkyhGNVw1BA'
STICKER_LOSS = 'CAACAgEAAxkBAAPdZsnoL2B38wOunaWwLwkOaTNaoR8AAiEEAAI019hFwqt42sFtXOM1BA'
STICKER_SESSAO_INICIADA = 'CAACAgEAAxkBAAPfZsnoNZDjN_edHpedotkV6ZkfkWoAAgcGAALttuBF8IaPc-uNIoA1BA'

CHANNEL_ID = '@emitrader'

