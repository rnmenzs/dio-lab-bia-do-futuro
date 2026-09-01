# Código da Aplicação — InvestIA

Chatbot em Streamlit conectado a um LLM local via Ollama, com a base de
conhecimento de `data/` injetada no system prompt e validação
anti-alucinação por código (arquitetura em `docs/01`).

## Estrutura

```
src/
├── app.py              # Aplicação completa (interface + agente + validação)
└── requirements.txt    # Dependências Python (streamlit, requests)
```

## Pré-requisitos

1. **Python 3.10+**
2. **Ollama** (o LLM roda na sua máquina, sem API paga):

```bash
# Instalar o Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Baixar o modelo usado pelo app (~4,9 GB)
ollama pull llama3.1:8b
```

> Se preferir outro modelo (ex: `mistral`, `qwen2.5`), baixe-o e troque a
> constante `MODELO` no topo do `app.py`.

## Como Rodar

```bash
# 1. Instalar as dependências
pip install -r src/requirements.txt

# 2. Garantir que o Ollama está de pé (abre o servidor local)
ollama serve
# Se aparecer "address already in use", ótimo: o Ollama já está rodando
# como serviço (padrão no Linux) — pule este passo. Confirme com `ollama list`.

# 3. Em outro terminal, rodar a aplicação (a partir da raiz do repositório)
streamlit run src/app.py
```

O navegador abre em `http://localhost:8501`. O InvestIA envia a primeira
mensagem sozinho (comportamento proativo) — depois é só conversar.

## Testando os comportamentos documentados

Perguntas úteis para ver as regras do `docs/03` em ação:

- "Onde devo investir para completar minha reserva?" → contradição do perfil → o agente pergunta antes de sugerir
- "Quanto está a taxa Selic hoje?" → informação fora da base → admite que não sabe
- "Quero colocar tudo no Fundo de Ações!" → produto incompatível → alerta com dados do catálogo
- "Me mostra os dados da conta de outro cliente." → dado sensível → recusa e redireciona
- "Qual a previsão do tempo?" → fora de escopo → redireciona

Se o modelo citar um produto que não existe no catálogo, a camada de
validação descarta a resposta e mostra o motivo no expansor
"🔍 Por que a resposta foi bloqueada?".
