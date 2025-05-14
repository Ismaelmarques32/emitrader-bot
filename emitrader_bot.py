import os
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

CHANNEL_ID = '@testesinaisemi'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🚀 Iniciar Sessão", callback_data='inicia_sessao'),
            InlineKeyboardButton("🛑 Encerrar Sessão", callback_data='sessao_encerrada')
        ],
        [
            InlineKeyboardButton("📈 Enviar Sinal CALL", callback_data='call'),
            InlineKeyboardButton("📉 Enviar Sinal PUT", callback_data='put')
        ],
        [
            InlineKeyboardButton("📊 Gerar Relatório", callback_data='menu_relatorio'),
            InlineKeyboardButton("👶 Novatos", callback_data='novatos')
        ],
        [
            InlineKeyboardButton("📋 Enquete - Experiência", callback_data='enquete'),
            InlineKeyboardButton("💸 Enquete - Lucro", callback_data='enquete_lucro')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    start_message = (
        "👋 Bem-vindo ao EMI TRADER Bot! \n\n"
        "Comece suas sessões, envie sinais e gere relatórios com facilidade. Escolha uma opção no menu e vamos lá! 👇"
    )
    await update.message.reply_text(start_message, reply_markup=reply_markup, parse_mode="Markdown")
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global operation_type, relatorio, current_operation, relatorio_total, waiting_for_gale_time, gale_stage
    query = update.callback_query
    await query.answer()

    if query.data == 'inicia_sessao':
        session_message = (
            "⏰ *EMI-TRADER – O show dos sinais começa às 21h! 🚀*\n\n"
            "📡 *Live ao vivo no YouTube + Sinais no Telegram*\n\n"
            "🎯 Está pronto para transformar oportunidades em resultados?\n"
            "💻 Deixe sua corretora preparada e seu mindset afiado para agir no momento certo!\n\n"
            "💡 *Dica esperta:*\n"
            "Foco total! Grandes movimentos começam com pequenas decisões — fique atento aos nossos sinais!\n\n"
            "👉 Abra sua corretora agora: [Clique aqui](https://broker-qx.pro/sign-up/?lid=949113)"
        )
        await query.edit_message_text(text=session_message, parse_mode="Markdown")
        await context.bot.send_message(chat_id=CHANNEL_ID, text=session_message, parse_mode="Markdown")

    elif query.data == 'sessao_encerrada':
        await encerrar_sessao(update, context)

    elif query.data == 'call':
        operation_type = 'CALL'
        await query.edit_message_text(
            text=(
                "📊 *Digite o Par, Preço (opcional) e a Hora no formato:*\n\n"
                "USD/JPY, 145.250, 16:20\n"
                "ou\n"
                "USD/JPY, 16:20 (para usar o preço 'Atual')"
            ),
            parse_mode="Markdown"
        )

    elif query.data == 'put':
        operation_type = 'PUT'
        await query.edit_message_text(
            text=(
                "📊 *Digite o Par, Preço (opcional) e a Hora no formato:*\n\n"
                "USD/JPY, 145.250, 16:20\n"
                "ou\n"
                "USD/JPY, 16:20 (para usar o preço 'Atual')"
            ),
            parse_mode="Markdown"
        )
async def handle_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global operation_type, current_operation, waiting_for_gale_time, gale_stage

    if update.message is None:
        await update.callback_query.answer(text="Nenhuma mensagem de texto detectada.")
        return

    if waiting_for_gale_time:
        try:
            text = update.message.text.split(',')
            hora = text[-1].strip()
            preco = "Atual"
            if len(text) == 2:
                preco = text[0].strip()
            datetime.datetime.strptime(hora, "%H:%M")
            gale_message = f"📊 Entrada confirmada para o Gale às {hora}, preço: {preco}."
            await context.bot.send_message(chat_id=CHANNEL_ID, text=gale_message)
            waiting_for_gale_time = False
            keyboard = [
                [InlineKeyboardButton("WIN ✅", callback_data='win')],
                [InlineKeyboardButton("LOSS ❌", callback_data='loss')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Escolha a próxima ação:", reply_markup=reply_markup)
            return
        except ValueError:
            await update.message.reply_text("Formato incorreto. Use: Preço (opcional), Hora (xx:xx).")
            return

    if operation_type in ['CALL', 'PUT']:
        try:
            text = update.message.text.split(',')
            if len(text) < 2:
                await update.message.reply_text("Use o formato: Par, Preço (opcional), Hora")
                return
            par = text[0].strip()
            hora = text[-1].strip()
            preco = "Atual"
            if len(text) == 3:
                preco = text[1].strip()
            datetime.datetime.strptime(hora, "%H:%M")
            current_operation = {
                "par": par,
                "preco": preco,
                "hora": hora,
                "tipo": operation_type,
                "resultado": None
            }
            keyboard = [
                [InlineKeyboardButton("1º Gale", callback_data='gale_1')],
                [InlineKeyboardButton("Cancelar entrada", callback_data='cancelar_entrada')],
                [InlineKeyboardButton("WIN ✅", callback_data='win')],
                [InlineKeyboardButton("LOSS ❌", callback_data='loss')],
                [InlineKeyboardButton("Preço Não Alcançado 📉", callback_data='preco_nao_alcancado')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            icon = "🔴" if operation_type == 'PUT' else "🟢"
            message_text = (
                f"🚀 *Hora de Lucrar!*\n"
                f"🎯 *5 Minutos de Expiração*\n\n"
                f"Par: {par}\n"
                f"💵 Preço: {preco}\n"
                f"⏰ Hora: {hora}\n"
                f"📉 Operação: {operation_type} {icon}\n\n"
                f"⚠️ 1 Gale permitido\n"
                f"Aguarde o sinal de confirmação!\n\n"
                f"📲 [Clique aqui](https://broker-qx.pro/sign-up/?lid=949113) para abrir a corretora!"
            )
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text, parse_mode="Markdown")
            await update.message.reply_text(
                f"Resultado da operação {par} {preco} às {hora} ({operation_type}):",
                reply_markup=reply_markup
            )
        except ValueError:
            await update.message.reply_text("Formato de hora inválido. Use HH:MM.")
async def show_win_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Win Direto: Explodimos no alvo! BOOM! 💥", callback_data='win_direto_boom')],
        [InlineKeyboardButton("✅ Win Direto: Foguete não tem ré, lucro confirmado! 🚀", callback_data='win_direto_foguete')],
        [InlineKeyboardButton("🎯 Win Direto: Sniper no mercado: acerto perfeito! 🔫", callback_data='win_direto_sniper')],
        [InlineKeyboardButton("🌟 Win Direto: Na precisão cirúrgica, é WIN! 🩺", callback_data='win_direto_cirurgica')],
        [InlineKeyboardButton("⏱️ Win no Gale: Fizemos história nos últimos segundos! 🕒", callback_data='win_gale_historia')],
        [InlineKeyboardButton("⏳ Win no Gale: No limite do tempo, lucro garantido! 💰", callback_data='win_gale_limite')],
        [InlineKeyboardButton("🚨 Win no Gale: Chegamos no limite, mas garantimos o lucro com força total! ⚡", callback_data='win_gale_forca_total')]
    ]
    await update.callback_query.edit_message_text(text="Escolha uma opção:", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_win_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    global current_operation, relatorio
    mensagens = {
        'win_direto_boom': "🔥 Win Direto: Explodimos no alvo! BOOM! 💥",
        'win_direto_foguete': "✅ Win Direto: Foguete não tem ré, lucro confirmado! 🚀",
        'win_direto_sniper': "🎯 Win Direto: Sniper no mercado: acerto perfeito! 🔫",
        'win_direto_cirurgica': "🌟 Win Direto: Na precisão cirúrgica, é WIN! 🩺",
        'win_gale_historia': "⏱️ Win no Gale: Fizemos história nos últimos segundos! 🕒",
        'win_gale_limite': "⏳ Win no Gale: No limite do tempo, lucro garantido! 💰",
        'win_gale_forca_total': "🚨 Win no Gale: Chegamos no limite, mas garantimos o lucro com força total! ⚡"
    }
    texto = mensagens.get(choice, "✅ Win confirmado!")
    current_operation['resultado'] = 'GAIN'
    relatorio.append(current_operation)
    current_operation = {}
    await update.callback_query.edit_message_text(text=texto)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto)
    await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_WIN)
async def show_loss_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Visão no alvo: O mercado segue, e nossa estratégia evolui junto!", callback_data='loss_visao_alvo')],
        [InlineKeyboardButton("🔥 Fortes como o mercado: O jogo virou? Calma, estamos prontos para dominar!", callback_data='loss_fortes_mercado')],
        [InlineKeyboardButton("👁️ Foco absoluto: Cada detalhe importa, e estamos na captura do próximo WIN!", callback_data='loss_foco_absoluto')],
        [InlineKeyboardButton("💡 Pensamento estratégico: Hoje aprendemos, amanhã conquistamos!", callback_data='loss_pensamento_estrategico')],
        [InlineKeyboardButton("🔍 Caminho certo: Tropeços não nos param; eles nos fortalecem!", callback_data='loss_caminho_certo')]
    ]
    await update.callback_query.edit_message_text(text="Escolha uma opção:", reply_markup=InlineKeyboardMarkup(keyboard))

async def process_loss_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    global current_operation, relatorio
    mensagens = {
        'loss_visao_alvo': "🚀 Visão no alvo: O mercado segue, e nossa estratégia evolui junto!",
        'loss_fortes_mercado': "🔥 Fortes como o mercado: O jogo virou? Calma, estamos prontos para dominar!",
        'loss_foco_absoluto': "👁️ Foco absoluto: Cada detalhe importa, e estamos na captura do próximo WIN!",
        'loss_pensamento_estrategico': "💡 Pensamento estratégico: Hoje aprendemos, amanhã conquistamos!",
        'loss_caminho_certo': "🔍 Caminho certo: Tropeços não nos param; eles nos fortalecem!"
    }
    texto = mensagens.get(choice, "❌ Loss registrado.")
    current_operation['resultado'] = 'LOSS'
    relatorio.append(current_operation)
    current_operation = {}
    await update.callback_query.edit_message_text(text=texto)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto)
    await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_LOSS)
async def cancelar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_operation, relatorio
    msg = "🔕 Gale cancelado:\nA estratégia manda, seguimos firmes!\n\n⏳ Aguarde o próximo sinal."
    if 'par' in current_operation:
        current_operation['resultado'] = 'CANCELADA'
        relatorio.append(current_operation)
        current_operation = {}
    else:
        msg = "Nenhuma operação ativa para cancelar."
    await update.callback_query.edit_message_text(text=msg, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)

async def preco_nao_alcancado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "📉 *Preço não alcançado:*\n⏳ *Aguarde o próximo sinal!*"
    await update.callback_query.edit_message_text(text=msg, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")

async def encerrar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global relatorio, relatorio_total
    msg = (
        "🛑 Sessão Encerrada!\n\n"
        "✨ Gratidão por estar conosco na EMI-TRADER!\n"
        "💼 Amanhã é um novo dia para conquistar o mercado.\n\n"
        "📈 Lembre-se: consistência é a chave, e os gráficos sempre estarão a seu favor! 🚀"
    )
    await update.callback_query.edit_message_text(text=msg, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg, parse_mode="Markdown")
    relatorio_total.extend(relatorio)
    relatorio = []

async def gerar_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE, ops, tipo):
    msg = update.message if update.message else update.callback_query.message
    if not ops:
        await msg.reply_text(f"Nenhuma operação registrada para gerar o relatório {tipo}.")
        return
    tz = pytz.timezone('America/Sao_Paulo')
    data = datetime.datetime.now(tz).strftime("%d/%m")
    wins, losses, cancelados = 0, 0, 0
    texto = f"📊 *Relatório de Operações - {data}*\n\n"
    for o in ops:
        par = o.get("par", "N/A")
        hora = o.get("hora", "N/A")
        tipo_op = o.get("tipo", "N/A")
        r = o.get("resultado", "N/A")
        if r == "GAIN": wins += 1; s = "✅"
        elif r == "LOSS": losses += 1; s = "❌"
        elif r == "CANCELADA": cancelados += 1; s = "🔕"
        else: s = "N/A"
        texto += f"{par} 🕒 {hora} - {tipo_op} -> {s}\n"
    texto += f"\n🏆 *Resultado {tipo.capitalize()}*\n🎯 {wins} WIN{'s' if wins > 1 else ''}\n❌ {losses} LOSS\n🚫 {cancelados} Cancelado{'s' if cancelados > 1 else ''}"
    await msg.edit_text(text=texto, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode="Markdown")

async def enviar_novatos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🚨 *ATENÇÃO, NOVATOS!* 🚨\n\n"
        "🌟 *Comece a lucrar com a EMI TRADER ainda hoje!* 🌟\n\n"
        "✅ *1º Passo*: Garanta sua conta com $50.000 de crédito demo para treinar sem risco!\n"
        "👉 [Crie sua conta agora](https://broker-qx.pro/sign-up/?lid=949113)\n\n"
        "✅ *2º Passo*: Aprenda a operar de forma segura e estratégica!\n"
        "🎥 Assista ao vídeo explicativo: [Clique aqui](https://youtu.be/R1mKfJ0wRmw)\n\n"
        "🔥 *Está pronto para sua jornada rumo ao sucesso? A ação começa agora!* 🚀"
    )
    await update.callback_query.edit_message_text(text=texto, parse_mode="Markdown", disable_web_page_preview=True)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=texto, parse_mode="Markdown", disable_web_page_preview=True)

async def enviar_enquete_experiencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_poll(chat_id=CHANNEL_ID, question="👤 *Qual é o seu nível de experiência com trading?*", options=["Iniciante", "Intermediário", "Avançado"], is_anonymous=True)

async def enviar_enquete_lucro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = "💚EMI TRADER fechou a manhã com uma SEQUÊNCIA IMBATÍVEL! ✅\n\nE aí, quem garantiu o lucro comigo? 👇🏼"
    o = ["Sim, lucro garantido! ✅", "Meta atingida, como sempre! 🏆", "Ah, perdi a hora...😅"]
    await context.bot.send_poll(chat_id=CHANNEL_ID, question=q, options=o, is_anonymous=True)
async def send_sticker_at_2100(context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            now = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
            target_time = now.replace(hour=21, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += datetime.timedelta(days=1)
            await asyncio.sleep((target_time - now).total_seconds())
            await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_SESSAO_INICIADA)
        except Exception as e:
            print(f"Erro no envio automático de sticker: {e}")

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signal))

nest_asyncio.apply()
loop = asyncio.get_event_loop()
loop.create_task(send_sticker_at_2100(app))
app.run_polling()
