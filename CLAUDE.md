# Gavi — Sistema de Inteligencia Pessoal

Bot Telegram que captura pensamento (voz, texto, links) e salva no Notion.
Deploy: Railway. Linguagem: Portugues (BR).

## Arquitetura

Duas camadas:
1. **Railway Bot (24/7)** — Captura: Telegram → classificacao por regras → Notion
2. **Claude Code Sessions** — Inteligencia: processa inbox, classifica com AI, gera insights

## Projeto

- Package: `gavi/` — rodar com `python -m gavi`
- Deploy: `Procfile` → `worker: python -m gavi`
- Deps: `python-telegram-bot>=21.0`, `trafilatura>=1.8`, `groq>=0.4`

## Notion IDs

| Recurso | Database ID |
|---------|-------------|
| Inbox "Ideias" | `311ceb428e888094bcf5dfdf00bea7e7` |
| Gosto | `a19df95ad9ff47b889b464e9217461d3` |
| Pensamento | `197bf8183c484f529445e250cea73321` |
| Fontes | `ff9f997f81f74d2e839b760dbb54fc58` |

### Paginas Notion

| Pagina | ID |
|--------|-----|
| Gavi main | `311ceb42-8e88-8116-856f-dd4ab73e9e4a` |
| Gosto page | `311ceb42-8e88-8154-84e2-ff0589997ec5` |
| Pensamento page | `311ceb42-8e88-812e-8a19-f7cfa44dee2f` |
| Fontes page | `311ceb42-8e88-8127-ae97-c69204137984` |
| Perfil Marcus | `311ceb42-8e88-8162-ab69-fd2878652d4f` |

## Env Vars (Railway)

```
CREW_BOT_TOKEN=<telegram bot token>
NOTION_TOKEN=<notion integration token>
NOTION_INBOX_ID=311ceb428e888094bcf5dfdf00bea7e7
NOTION_GOSTO_ID=a19df95ad9ff47b889b464e9217461d3
NOTION_PENSAMENTO_ID=197bf8183c484f529445e250cea73321
NOTION_FONTES_ID=ff9f997f81f74d2e839b760dbb54fc58
GROQ_API_KEY=<groq api key>
```

## Comandos Telegram

### Captura rapida
- Texto livre → auto-classifica (Tipo + Pilar) e salva
- Audio → Groq Whisper transcreve → classifica → salva
- Link → trafilatura extrai artigo → salva em Fontes

### Pilares
- `/gosto [reacao] [comentario]` — reacoes: bonito, irritante, genuino, tendencia, surpreendente
- `/pensar [reflexao]` — tipos: Filosofia, Provocacao, Observacao, Conexao
- `/fonte [url] [comentario]` — extrai artigo automaticamente
- `/corpo [registro]` — placeholder (salva no Inbox)

### CREW
- `/ideia`, `/tarefa`, `/urgente`, `/ref` — captura direta no Inbox
- `/agente [nome] [msg]` — delega para agente CREW
- `/desafio`, `/segunda`, `/review`, `/status`, `/ajuda`

## Workflow Cowork (Claude Code Sessions)

### "Processa o inbox"
1. Ler database Ideias via Notion MCP (Status="Novo")
2. Para cada entry: classificar Tipo, Pilar, Tags
3. Criar entry na database correta (Gosto/Pensamento/Fontes)
4. Marcar original como Status="Processado" no Inbox

### "Briefing sobre [tema]"
1. Buscar em Pensamento + Fontes + Gosto via Notion search
2. Ler Perfil Marcus para tom e perspectiva
3. Compilar brief estruturado

### "Analisa meu Gosto/Pensamento"
1. Ler todas entradas do database
2. Identificar padroes e clusters
3. Atualizar Perfil Marcus com insights

## 3 Pilares

### Gosto (Sensibilidade Estetica)
Reacoes: Bonito, Irritante, Genuino, Tendencia, Surpreendente
Categorias: Tipografia, Paleta, Layout, Narrativa, Marca

### Pensamento (Journal)
Tipos: Filosofia, Provocacao, Observacao, Conexao

### Corpo (futuro)
Treinos, sono, energia vs output criativo

## Agentes CREW
- SONDA — Pesquisador
- LEME — Estrategista
- TINTA — Redator
- FORMA — Designer
- PULSO — Produtor
- LUPA — Critico
