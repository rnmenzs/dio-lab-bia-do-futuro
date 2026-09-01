# 💰 InvestIA — Consultor Virtual de Investimentos

Agente de IA que ajuda **investidores iniciantes** a escolher, entre os produtos
de um catálogo, os mais adequados ao seu perfil e às suas metas — explicando o
porquê de cada sugestão e **sem inventar informações**.

Projeto desenvolvido para o Lab da DIO
["Construa Seu Assistente Virtual Com IA"](https://github.com/digitalinnovationone/dio-lab-bia-do-futuro)
(trilha Bradesco — Dados, Cibersegurança e GenAI).

---

## O problema

Pessoa iniciante, com pouco patrimônio, não sabe qual produto financeiro combina
com seu perfil e metas — e por isso deixa o dinheiro parado na conta ou investe
por palpite.

## A solução

O **InvestIA** cruza o perfil e as metas do cliente com o catálogo de produtos
([`data/`](./data/)) e:

1. **Antecipa** — abre a conversa apontando a meta mais urgente, antes da primeira pergunta;
2. **Personaliza** — só sugere produtos do catálogo compatíveis com o perfil de risco, explicando o porquê;
3. **Pergunta na dúvida** — detecta contradições no perfil do cliente e pergunta antes de recomendar.

**Anti-alucinação em duas camadas:** regras no system prompt **+ validação por
código** — determinística, ela descarta respostas que citem produtos fora do
catálogo ou recomendem produto incompatível com o perfil sem desaconselhá-lo.

## Como funciona

Streamlit (interface de chat) + Ollama (LLM local, sem API paga) + os JSONs de
`data/` injetados no system prompt + camada de validação. Arquitetura completa
com diagrama em [`docs/01`](./docs/01-documentacao-agente.md).

```bash
pip install -r src/requirements.txt
ollama pull llama3.1:8b
streamlit run src/app.py
```

Passo a passo completo (incluindo instalar o Ollama): [`src/README.md`](./src/README.md)

## As 6 etapas do desafio

| Etapa | Entrega | Status |
|-------|---------|--------|
| 1. Documentação do agente | [`docs/01-documentacao-agente.md`](./docs/01-documentacao-agente.md) | ✅ |
| 2. Base de conhecimento | [`docs/02-base-conhecimento.md`](./docs/02-base-conhecimento.md) | ✅ |
| 3. Prompts do agente | [`docs/03-prompts.md`](./docs/03-prompts.md) | ✅ |
| 4. Aplicação funcional | [`src/app.py`](./src/app.py) | ✅ |
| 5. Avaliação e métricas | [`docs/04-metricas.md`](./docs/04-metricas.md) | 🔜 |
| 6. Pitch | [`docs/05-pitch.md`](./docs/05-pitch.md) | 🔜 |

## Estrutura do repositório

```
├── data/       # Base de conhecimento (perfil do cliente + catálogo de produtos)
├── docs/       # Documentação das etapas do desafio
├── src/        # Aplicação (Streamlit + Ollama)
└── assets/     # Materiais de apoio
```

---

Feito por [@rnmenzs](https://github.com/rnmenzs) sobre o
[repositório base](https://github.com/digitalinnovationone/dio-lab-bia-do-futuro)
da [DIO](https://www.dio.me/).
