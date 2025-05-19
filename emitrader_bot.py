import os
import json
import asyncio
import datetime
import pytz
import nest_asyncio
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Variáveis globais
operation_type = None
relatorio = []
relatorio_total = []
current_operation = {}
waiting_for_gale_time = False
gale_stage = 0  # Variável para controlar qual Gale está sendo confirmado

# Substitua pelos file_ids reais dos stickers
STICKER_WIN = 'CAACAgEAAxkBAAPhZsnoOnV7QkVn-3CbCRKC2e3XmuoAAjIEAAI6q-BF_bQwkyhGNVw1BA'
STICKER_LOSS = 'CAACAgEAAxkBAAPdZsnoL2B38wOunaWwLwkOaTNaoR8AAiEEAAI019hFwqt42sFtXOM1BA'
STICKER_SESSAO_INICIADA = 'CAACAgEAAxkBAAPfZsnoNZDjN_edHpedotkV6ZkfkWoAAgcGAALttuBF8IaPc-uNIoA1BA'

# ID do canal substituído pelo username do canal público
CHANNEL_ID = '@emitrader' #'@testesinaisemi'

# Função para o comando de início
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

# Função para lidar com as opções do menu
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global operation_type, relatorio, current_operation, relatorio_total, waiting_for_gale_time, gale_stage
    query = update.callback_query
    await query.answer()

    if query.data == 'inicia_sessao':
        session_message = (
            "⏰ *EMI-TRADER – O show dos sinais começa às 20h! 🚀*\n\n"
            "📡 *Live ao vivo no YouTube às 21h + Sinais no Telegram*\n\n"
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

    elif query.data == 'novatos':
        await enviar_novatos(update, context)

    elif query.data == 'enquete':
        await enviar_enquete_experiencia(update, context)

    elif query.data == 'enquete_lucro':
        await enviar_enquete_lucro(update, context)

    elif query.data.startswith('gale'):
        gale_num = int(query.data.split('_')[1])
        gale_stage = gale_num
        waiting_for_gale_time = True
        await query.edit_message_text(
            text=(
                f"📊 *Digite o Preço (opcional) e o horário no formato:*\n\n"
                f"145.250, 09:50\n"
                f"ou\n"
                f"09:50 (para usar o preço 'Atual')\n\n"
                f"Confirmando o {gale_num}º Gale."
            ),
            parse_mode="Markdown"
        )


    elif query.data == 'cancelar_entrada':
        await cancelar_entrada(update, context)

    elif query.data == 'win':
        await show_win_options(update, context)

    elif query.data == 'loss':
        await show_loss_options(update, context)

    elif query.data.startswith('win_'):
        await process_win_choice(update, context, query.data)

    elif query.data.startswith('loss_'):
        await process_loss_choice(update, context, query.data)

    elif query.data == 'preco_nao_alcancado':
        await preco_nao_alcancado(update, context)


    elif query.data == 'menu_relatorio':
        keyboard = [
            [InlineKeyboardButton("📊 Relatório Parcial", callback_data='relatorio_parcial')],
            [InlineKeyboardButton("📊 Relatório Total", callback_data='relatorio_total')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Escolha o tipo de relatório:", reply_markup=reply_markup)

    elif query.data == 'relatorio_parcial':
        await gerar_relatorio(update, context, relatorio, "parcial")

    elif query.data == 'relatorio_total':
        relatorio_total.extend(relatorio)
        await gerar_relatorio(update, context, relatorio_total, "total")

# Função para confirmar Gale com tempo fornecido manualmente
async def handle_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global operation_type, current_operation, waiting_for_gale_time, gale_stage

    if update.message is None:
        await update.callback_query.answer(text="Nenhuma mensagem de texto detectada.")
        return

    if waiting_for_gale_time:  # Confirmação do Gale
        try:
            # Dividindo o texto enviado pelo usuário
            text = update.message.text.split(',')
            hora = text[-1].strip()  # Último item será sempre o horário
            preco = "Atual"  # Valor padrão caso o preço não seja fornecido

            # Verifica se o preço foi fornecido
            if len(text) == 2:
                preco = text[0].strip()

            # Valida o formato do horário
            datetime.datetime.strptime(hora, "%H:%M")

            # Construindo a mensagem de confirmação
            gale_message = f"📊 Entrada confirmada para o Gale às {hora}, preço: {preco}."

            # Envia a mensagem para o canal
            await context.bot.send_message(chat_id=CHANNEL_ID, text=gale_message)
            waiting_for_gale_time = False  # Reseta o estado de espera do Gale

            # Menu pós-Gale
            keyboard = [
                [InlineKeyboardButton("WIN ✅", callback_data='win')],
                [InlineKeyboardButton("LOSS ❌", callback_data='loss')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Escolha a próxima ação:", reply_markup=reply_markup)
            return

        except ValueError:
            await update.message.reply_text(
                "Formato incorreto. Por favor, use o formato: Preço (opcional), Hora (xx:xx)."
            )
            return

    if operation_type in ['CALL', 'PUT']:  # Entrada principal (CALL/PUT)
        try:
            # Dividindo o texto enviado pelo usuário
            text = update.message.text.split(',')
            if len(text) < 2:
                await update.message.reply_text("Formato incorreto. Por favor, use o formato: Par, Preço (opcional), Hora")
                return

            # Extraindo os dados
            par = text[0].strip()
            hora = text[-1].strip()  # Último elemento sempre será a hora
            preco = "Atual"  # Valor padrão caso o preço não seja fornecido

            # Verificando se o preço foi fornecido
            if len(text) == 3:
                preco = text[1].strip()

            # Validando o formato da hora
            datetime.datetime.strptime(hora, "%H:%M")

            # Atualizando a operação atual
            current_operation = {
                "par": par,
                "preco": preco,
                "hora": hora,
                "tipo": operation_type,
                "resultado": None
            }

            # Criando o teclado
            keyboard = [
                [InlineKeyboardButton("1º Gale", callback_data='gale_1')],
                [InlineKeyboardButton("Cancelar entrada", callback_data='cancelar_entrada')],
                [InlineKeyboardButton("WIN ✅", callback_data='win')],
                [InlineKeyboardButton("LOSS ❌", callback_data='loss')],
                [InlineKeyboardButton("Preço Não Alcançado 📉", callback_data='preco_nao_alcancado')]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Mensagem de operação
            operation_icon = "🔴" if operation_type == 'PUT' else "🟢"
            message_text = (
                f"🚀 *Hora de Lucrar!*\n"
                f"🎯 *5 Minutos de Expiração*\n\n"
                f"Par: {par}\n"
                f"💵 Preço: {preco}\n"
                f"⏰ Hora: {hora}\n"
                f"📉 Operação: {operation_type} {operation_icon}\n\n"
                f"⚠️ 1 Gale permitido\n"
                f"Aguarde o sinal de confirmação!\n\n"
                f"📲 [Clique aqui](https://broker-qx.pro/sign-up/?lid=949113) para abrir a corretora!"
            )

            # Enviando mensagem para o canal
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text, parse_mode="Markdown")
            await update.message.reply_text(
                f"Resultado da operação {par} {preco} às {hora} ({operation_type}):",
                reply_markup=reply_markup
            )

        except ValueError:
            await update.message.reply_text("Formato de hora inválido. Use o formato HH:MM.")

# Função para gerar relatório
async def gerar_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE, operacoes, tipo):
    message = update.message if update.message else update.callback_query.message

    if not operacoes:
        await message.reply_text(f"Nenhuma operação registrada para gerar o relatório {tipo}.")
        return

    # Configurando a data do relatório
    tz_brasilia = pytz.timezone('America/Sao_Paulo')
    data = datetime.datetime.now(tz_brasilia).strftime("%d/%m")

    # Inicializando contadores
    wins = 0
    losses = 0
    cancelados = 0

    # Construindo o texto do relatório
    relatorio_text = f"📊 *Relatório de Operações - {data}*\n\n"

    for operacao in operacoes:
        par = operacao.get("par", "N/A")
        hora = operacao.get("hora", "N/A")
        tipo_operacao = operacao.get("tipo", "N/A")
        resultado = operacao.get("resultado", "N/A")

        # Mapeamento do status
        if resultado == "GAIN":
            status = "✅"
            wins += 1
        elif resultado == "LOSS":
            status = "❌"
            losses += 1
        elif resultado == "CANCELADA":
            status = "🔕"
            cancelados += 1
        else:
            status = "N/A"

        relatorio_text += f"{par} 🕒 {hora} - {tipo_operacao} -> {status}\n"

    # Adicionando os totais
    relatorio_text += (
        f"\n🏆 *Resultado {tipo.capitalize()}*\n"
        f"🎯 {wins} WIN{'s' if wins > 1 else ''}\n"
        f"❌ {losses} LOSS\n"
        f"🚫 {cancelados} Cancelado{'s' if cancelados > 1 else ''}"
    )

    # Enviando o relatório
    await message.edit_text(text=relatorio_text, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=relatorio_text, parse_mode="Markdown")

async def preco_nao_alcancado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mensagem quando o preço não é alcançado
    preco_nao_alcancado_message = (
        "📉 *Preço não alcançado:*\n"
        "⏳ *Aguarde o próximo sinal!*"
    )

    # Enviando a mensagem para o canal e respondendo ao usuário
    await update.callback_query.edit_message_text(text=preco_nao_alcancado_message, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=preco_nao_alcancado_message, parse_mode="Markdown")

# Função "Novatos"
async def enviar_novatos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    novatos_message = (
        "🚨 *ATENÇÃO, NOVATOS!* 🚨\n\n"
        "🌟 *Comece a lucrar com a EMI TRADER ainda hoje!* 🌟\n\n"
        "✅ *1º Passo*: Garanta sua conta com $50.000 de crédito demo para treinar sem risco!\n"
        "👉 [Crie sua conta agora](https://broker-qx.pro/sign-up/?lid=949113)\n\n"
        "✅ *2º Passo*: Aprenda a operar de forma segura e estratégica!\n"
        "🎥 Assista ao vídeo explicativo: [Clique aqui](https://youtu.be/R1mKfJ0wRmw)\n\n"
        "🔥 *Está pronto para sua jornada rumo ao sucesso? A ação começa agora!* 🚀"
    )
    await update.callback_query.edit_message_text(text=novatos_message, parse_mode="Markdown", disable_web_page_preview=True)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=novatos_message, parse_mode="Markdown", disable_web_page_preview=True)

# Função "Enquete - Experiência"
async def enviar_enquete_experiencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = "👤 *Qual é o seu nível de experiência com trading?*"
    options = ["Iniciante", "Intermediário", "Avançado"]
    await context.bot.send_poll(chat_id=CHANNEL_ID, question=question, options=options, is_anonymous=True)

# Função "Enquete - Lucro"
async def enviar_enquete_lucro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = "💚EMI TRADER fechou a manhã com uma SEQUÊNCIA IMBATÍVEL! ✅\n\nE aí, quem garantiu o lucro comigo? 👇🏼"
    options = [
        "Sim, lucro garantido! ✅",
        "Meta atingida, como sempre! 🏆",
        "Ah, perdi a hora...😅"
    ]
    await context.bot.send_poll(chat_id=CHANNEL_ID, question=question, options=options, is_anonymous=True)

async def show_win_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Win Direto: Explodimos no alvo! BOOM! 💥", callback_data='win_direto_boom')],
        [InlineKeyboardButton("✅ Win Direto: Lucro épico, vitória de mestre! 🎉", callback_data='win_direto_foguete')],
        [InlineKeyboardButton("🎯 Win Direto: Sniper no mercado: acerto perfeito! 🔫", callback_data='win_direto_sniper')],
        [InlineKeyboardButton("🌟 Win Direto: Na precisão cirúrgica, é WIN! 🩺", callback_data='win_direto_cirurgica')],
        [InlineKeyboardButton("⏱️ Win no Gale: Fizemos história nos últimos segundos! 🕒", callback_data='win_gale_historia')],
        [InlineKeyboardButton("⏳ Win no Gale: No limite do tempo, lucro garantido! 💰", callback_data='win_gale_limite')],
        [InlineKeyboardButton("🚨 Win no Gale: Chegamos no limite, mas garantimos o lucro com força total! ⚡", callback_data='win_gale_forca_total')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text="Escolha uma opção:", reply_markup=reply_markup)

async def show_loss_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Visão no alvo: O mercado segue, e nossa estratégia evolui junto!", callback_data='loss_visao_alvo')],
        [InlineKeyboardButton("🔥 Fortes como o mercado: O jogo virou? Calma, estamos prontos para dominar!", callback_data='loss_fortes_mercado')],
        [InlineKeyboardButton("👁️ Foco absoluto: Cada detalhe importa, e estamos na captura do próximo WIN!", callback_data='loss_foco_absoluto')],
        [InlineKeyboardButton("💡 Pensamento estratégico: Hoje aprendemos, amanhã conquistamos!", callback_data='loss_pensamento_estrategico')],
        [InlineKeyboardButton("🔍 Caminho certo: Tropeços não nos param; eles nos fortalecem!", callback_data='loss_caminho_certo')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text="Escolha uma opção:", reply_markup=reply_markup)

async def process_win_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    global current_operation, relatorio
    win_messages = {
        'win_direto_boom': "🔥 Win Direto: Explodimos no alvo! BOOM! 💥",
        'win_direto_foguete': "✅ Win Direto: Lucro épico, vitória de mestre! 🎉",
        'win_direto_sniper': "🎯 Win Direto: Sniper no mercado: acerto perfeito! 🔫",
        'win_direto_cirurgica': "🌟 Win Direto: Na precisão cirúrgica, é WIN! 🩺",
        'win_gale_historia': "⏱️ Win no Gale: Fizemos história nos últimos segundos! 🕒",
        'win_gale_limite': "⏳ Win no Gale: No limite do tempo, lucro garantido! 💰",
        'win_gale_forca_total': "🚨 Win no Gale: Chegamos no limite, mas garantimos o lucro com força total! ⚡"
    }
    message_text = win_messages.get(choice, "Win registrado!")
    current_operation['resultado'] = 'GAIN'
    relatorio.append(current_operation)
    current_operation = {}
    await update.callback_query.edit_message_text(text=message_text)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text)
    await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_WIN)

async def process_loss_choice(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str):
    global current_operation, relatorio
    loss_messages = {
        'loss_visao_alvo': "🚀 Visão no alvo: O mercado segue, e nossa estratégia evolui junto!",
        'loss_fortes_mercado': "🔥 Fortes como o mercado: O jogo virou? Calma, estamos prontos para dominar!",
        'loss_foco_absoluto': "👁️ Foco absoluto: Cada detalhe importa, e estamos na captura do próximo WIN!",
        'loss_pensamento_estrategico': "💡 Pensamento estratégico: Hoje aprendemos, amanhã conquistamos!",
        'loss_caminho_certo': "🔍 Caminho certo: Tropeços não nos param; eles nos fortalecem!"
    }
    message_text = loss_messages.get(choice, "Loss registrado!")
    current_operation['resultado'] = 'LOSS'
    relatorio.append(current_operation)
    current_operation = {}
    await update.callback_query.edit_message_text(text=message_text)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message_text)
    await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_LOSS)

# Função para cancelar entrada
async def cancelar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_operation, relatorio

    # Mensagem de cancelamento
    cancel_message = (
        "🔕 Gale cancelado:\n"
        "A estratégia manda, seguimos firmes!\n\n"
        "⏳ Aguarde o próximo sinal."
    )

    # Registra a operação como cancelada no relatório
    if 'par' in current_operation:
        current_operation['resultado'] = 'CANCELADA'
        relatorio.append(current_operation)  # Adiciona ao relatório
        current_operation = {}  # Reseta a operação atual
    else:
        # No caso de não haver operação ativa, apenas envia a mensagem
        cancel_message = "Nenhuma operação ativa para cancelar."

    await update.callback_query.edit_message_text(text=cancel_message, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=cancel_message)

# Função para encerrar sessão
async def encerrar_sessao(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global relatorio, relatorio_total
    encerrar_message = (
        "🛑 Sessão Encerrada!\n\n"
        "✨ Gratidão por estar conosco na EMI-TRADER!\n"
        "💼 Amanhã é um novo dia para conquistar o mercado.\n\n"
        "📈 Lembre-se: consistência é a chave, e os gráficos sempre estarão a seu favor! 🚀"
    )
    await update.callback_query.edit_message_text(text=encerrar_message, parse_mode="Markdown")
    await context.bot.send_message(chat_id=CHANNEL_ID, text=encerrar_message, parse_mode="Markdown")

    # Transferindo o relatório parcial para o relatório total e limpando o relatório parcial
    relatorio_total.extend(relatorio)
    relatorio = []

async def send_sticker_at_830(context: ContextTypes.DEFAULT_TYPE):
    """Função para enviar o sticker de 'Sessão Iniciada' às 20:00 diariamente."""
    while True:
        try:
            now = datetime.datetime.now(pytz.timezone('America/Sao_Paulo'))
            target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)

            # Se o tempo alvo já passou no dia de hoje, ajuste para o dia seguinte
            if now > target_time:
                target_time += datetime.timedelta(days=1)

            wait_time = (target_time - now).total_seconds()
            await asyncio.sleep(wait_time)
            await context.bot.send_sticker(chat_id=CHANNEL_ID, sticker=STICKER_SESSAO_INICIADA)
        except Exception as e:
            print(f"Erro inesperado: {e}")

# Inicializando o bot
app = ApplicationBuilder().token('7372781018:AAGp67ScEVsyQFr6FQo2HezNKAS8zqjJwAU').build()

nest_asyncio.apply()

# Função webhook para lidar com requisições do Telegram
async def webhook(request):
    if request.method == "POST":
        data = await request.json()
        update = Update.de_json(data, app.bot)
        await app.process_update(update)
        return web.Response(text="OK")
    return web.Response(status=405)

# Função principal para rodar o bot via webhook
async def main():
    await app.initialize()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signal))

    asyncio.create_task(send_sticker_at_830(app))

    application = web.Application()
    application.router.add_post("/webhook", webhook)

    runner = web.AppRunner(application)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 8080)))
    await site.start()

    webhook_url = "https://emitrader-bot-production.up.railway.app/webhook"
    await app.bot.set_webhook(url=webhook_url)

    print("✅ Webhook iniciado com sucesso")

    # 👇 Isso aqui é essencial!
    await asyncio.Event().wait()
    
# Executa tudo
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
