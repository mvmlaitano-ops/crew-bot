#!/usr/bin/env python3
"""CREW Bot (@creacrewbot) - Motor criativo da CREW no Telegram."""

import random, datetime, asyncio, os, sys
from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("CREW_BOT_TOKEN", "")
GROUP_CHAT_ID = os.environ.get("CREW_GROUP_CHAT_ID", None)

DESAFIOS = [
    {"agente": "SONDA", "titulo": "O Dado Invisivel", "briefing": "Escolha uma marca que voce admira. Encontre um dado publico sobre ela que NINGUEM esta usando como argumento de venda. Transforme esse dado num insight criativo em 3 linhas.", "prazo": "sexta 18h", "entrega": "Texto de 3 linhas + fonte do dado"},
    {"agente": "LEME", "titulo": "6 Palavras", "briefing": "Resuma o posicionamento de qualquer marca em exatamente 6 palavras. Se nao conseguir, voce nao entendeu a marca. Faca 3 versoes.", "prazo": "sexta 18h", "entrega": "3 versoes de 6 palavras + nome da marca"},
    {"agente": "TINTA", "titulo": "A Primeira Frase", "briefing": "Escreva 5 primeiras frases de posts de LinkedIn sobre o MESMO tema. Regra: nenhuma pode comecar com Eu, Hoje ou Voce sabia. Escolha a melhor.", "prazo": "sexta 18h", "entrega": "5 frases + indicacao da vencedora"},
    {"agente": "FORMA", "titulo": "Marca em 60 Minutos", "briefing": "Crie uma identidade visual minima (nome + logo + paleta + 1 aplicacao) para um negocio absurdo: uma barbearia submarina, uma padaria para gatos, um Uber de guarda-chuvas.", "prazo": "sexta 18h", "entrega": "1 imagem com logo + paleta + mockup"},
    {"agente": "PULSO", "titulo": "Conteudo Relampago", "briefing": "Crie um post completo (texto + direcao visual) em 30 minutos. Timer rodando. Tema livre. O objetivo e provar que feito bate perfeito.", "prazo": "sexta 18h", "entrega": "Post pronto (texto + visual)"},
    {"agente": "LUPA", "titulo": "Destrua Isso", "briefing": "Escolha qualquer campanha recente. Liste 3 problemas estrategicos que ninguem comentou. Depois, proponha como consertar cada um.", "prazo": "sexta 18h", "entrega": "3 problemas + 3 solucoes"},
    {"agente": "CREW COLETIVO", "titulo": "Marca do Zero", "briefing": "Criem uma marca ficticia completa entre todos. SONDA pesquisa, LEME posiciona, TINTA escreve, FORMA cria o visual, PULSO monta o plano, LUPA destroi e reconstroi.", "prazo": "domingo 23h59", "entrega": "Uma peca por agente + 1 apresentacao final"},
]

AGENTES = {
    "sonda": {"emoji": "\U0001f52c", "nome": "SONDA", "papel": "O Pesquisador", "frase": "Os dados nao mentem. Mas as vezes sussurram.", "desc": "Pesquisa, dados, contexto cultural, descoberta de tensoes humanas."},
    "leme": {"emoji": "\U0001f9ed", "nome": "LEME", "papel": "O Estrategista", "frase": "Posicionamento nao e o que voce diz. E o espaco que voce ocupa na mente de quem importa.", "desc": "Posicionamento, briefing, direcao estrategica, arquitetura de marca."},
    "tinta": {"emoji": "\u2712\ufe0f", "nome": "TINTA", "papel": "A Redatora", "frase": "A palavra certa no lugar certo muda tudo. A errada, tambem.", "desc": "Copy, headlines, narrativa, tom de voz, roteiro."},
    "forma": {"emoji": "\U0001f3a8", "nome": "FORMA", "papel": "O Designer", "frase": "Se precisa explicar, o design falhou.", "desc": "Direcao de arte, identidade visual, moodboard, layout, tipografia."},
    "pulso": {"emoji": "\u26a1", "nome": "PULSO", "papel": "O Produtor", "frase": "Ideia sem execucao e hobby. Com execucao, e negocio.", "desc": "Planejamento, execucao, calendario, canais, formato, viabilidade."},
    "lupa": {"emoji": "\U0001f50d", "nome": "LUPA", "papel": "A Critica", "frase": "Eu nao sou dificil. Eu sou honesta.", "desc": "Revisao, quality control, stress test, advocacia do diabo."},
}

def format_desafio(d):
    semana = datetime.date.today().isocalendar()[1]
    return (
        f"==================\n"
        f"*DESAFIO DA SEMANA {semana}*\n"
        f"==================\n\n"
        f"*Proposto por:* {d['agente']}\n\n"
        f"*{d['titulo']}*\n\n"
        f"{d['briefing']}\n\n"
        f"*Entrega:* {d['entrega']}\n"
        f"*Prazo:* {d['prazo']}\n\n"
        f"_Quem pega? Responde aqui com \U0001f64b_\n"
        f"=================="
    )

def format_planning():
    hoje = datetime.date.today().strftime("%d/%m/%Y")
    semana = datetime.date.today().isocalendar()[1]
    return (
        f"==================\n"
        f"*PLANNING - SEMANA {semana}*\n"
        f"==================\n"
        f"_{hoje}_\n\n"
        f"*1. Review rapido* (5 min)\n"
        f"O que saiu semana passada?\n\n"
        f"*2. Prioridades da semana* (10 min)\n"
        f"Maximo 3 entregas.\n\n"
        f"*3. Alocacao* (5 min)\n"
        f"Quem trabalha em que?\n\n"
        f"*4. Bloqueios* (5 min)\n\n"
        f"*5. Momento e se...* (5 min)\n"
        f"Uma ideia maluca. Sem julgamento.\n\n"
        f"_Bora, CREW. A semana comeca agora._\n"
        f"=================="
    )

def format_review():
    semana = datetime.date.today().isocalendar()[1]
    return (
        f"==================\n"
        f"*REVIEW - SEMANA {semana}*\n"
        f"==================\n\n"
        f"Cada agente responde:\n\n"
        f"*[NOME]*\n"
        f"Entregas:\n"
        f"Metrica da semana:\n"
        f"Aprendizado:\n\n"
        f"_Sexta e dia de olhar pra tras e celebrar._\n"
        f"=================="
    )

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        "==================\n"
        "*CREW Bot - Ativo*\n"
        "==================\n\n"
        "Sou o motor criativo da CREW.\n"
        "6 agentes. 1 missao. Zero ego.\n\n"
        "*Comandos:*\n"
        "/desafio - Dispara um desafio criativo\n"
        "/segunda - Planning de Segunda\n"
        "/review - Review de Sexta\n"
        "/agente [nome] - Info sobre um agente\n"
        "/status - Status da CREW\n"
        "/ajuda - Lista de comandos\n\n"
        f"_Chat ID: {chat_id}_\n"
        "==================",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_desafio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = random.choice(DESAFIOS)
    await update.message.reply_text(format_desafio(d), parse_mode=ParseMode.MARKDOWN)

async def cmd_segunda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_planning(), parse_mode=ParseMode.MARKDOWN)

async def cmd_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_review(), parse_mode=ParseMode.MARKDOWN)

async def cmd_agente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        nomes = ", ".join([k for k in AGENTES.keys()])
        await update.message.reply_text(f"Qual agente? Use: /agente [nome]\n\nAgentes: {nomes}")
        return
    nome = context.args[0].lower()
    if nome not in AGENTES:
        await update.message.reply_text(f"Agente '{nome}' nao encontrado. Tente: sonda, leme, tinta, forma, pulso, lupa")
        return
    a = AGENTES[nome]
    await update.message.reply_text(
        f"==================\n"
        f"{a['emoji']} *{a['nome']}* - {a['papel']}\n"
        f"==================\n\n"
        f"_{a['frase']}_\n\n"
        f"{a['desc']}\n"
        f"==================",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hoje = datetime.date.today()
    semana = hoje.isocalendar()[1]
    dias = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]
    dia_semana = dias[hoje.weekday()]
    await update.message.reply_text(
        f"==================\n"
        f"*STATUS DA CREW*\n"
        f"==================\n\n"
        f"{dia_semana}, {hoje.strftime('%d/%m/%Y')}\n"
        f"Semana {semana}\n\n"
        f"*Agentes ativos:* 6/6\n"
        f"SONDA | LEME | TINTA | FORMA | PULSO | LUPA\n\n"
        f"*Banco de desafios:* {len(DESAFIOS)} disponiveis\n"
        f"==================",
        parse_mode=ParseMode.MARKDOWN
    )

async def cmd_ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "==================\n"
        "*COMANDOS DA CREW*\n"
        "==================\n\n"
        "/desafio - Desafio criativo aleatorio\n"
        "/segunda - Planning de Segunda\n"
        "/review - Review de Sexta\n"
        "/agente [nome] - Info do agente\n"
        "/status - Status da CREW\n"
        "/ajuda - Este menu\n\n"
        "*Agentes:* sonda, leme, tinta, forma, pulso, lupa\n"
        "==================",
        parse_mode=ParseMode.MARKDOWN
    )

async def enviar_desafio_semanal(chat_id):
    bot = Bot(token=BOT_TOKEN)
    d = random.choice(DESAFIOS)
    await bot.send_message(chat_id=chat_id, text=format_desafio(d), parse_mode=ParseMode.MARKDOWN)

async def enviar_planning(chat_id):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=format_planning(), parse_mode=ParseMode.MARKDOWN)

async def enviar_review(chat_id):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=format_review(), parse_mode=ParseMode.MARKDOWN)

def main():
    import time
    # Limpa conexoes anteriores antes de iniciar
    async def cleanup_and_start():
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            await bot.delete_webhook(drop_pending_updates=True)
            print("Webhook deletado, aguardando 2s...")
        time.sleep(2)

    asyncio.run(cleanup_and_start())

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("desafio", cmd_desafio))
    app.add_handler(CommandHandler("segunda", cmd_segunda))
    app.add_handler(CommandHandler("review", cmd_review))
    app.add_handler(CommandHandler("agente", cmd_agente))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("ajuda", cmd_ajuda))
    print("CREW Bot iniciado com sucesso!")
    app.run_polling(drop_pending_updates=True, poll_interval=2.0, timeout=10)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        action = sys.argv[1]
        chat_id = sys.argv[2]
        if action == "send-desafio":
            asyncio.run(enviar_desafio_semanal(chat_id))
        elif action == "send-planning":
            asyncio.run(enviar_planning(chat_id))
        elif action == "send-review":
            asyncio.run(enviar_review(chat_id))
    else:
        main()

