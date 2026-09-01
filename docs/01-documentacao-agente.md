# Documentação do Agente — InvestIA

## Caso de Uso

### Problema
> Qual problema financeiro seu agente resolve?

Pessoa iniciante, com pouco patrimônio, que não sabe qual produto financeiro combina com seu perfil e suas metas — e por isso deixa o dinheiro parado na conta ou investe por palpite.

### Solução
> Como o agente resolve esse problema de forma proativa?

O **InvestIA** cruza o perfil e as metas do cliente (`perfil_investidor.json`) com o catálogo de produtos (`produtos_financeiros.json`) e:

1. **Antecipa**: abre a conversa apontando a meta mais urgente do cliente, antes mesmo da primeira pergunta.
2. **Personaliza**: só sugere produtos do catálogo compatíveis com o perfil de risco, explicando o porquê.
3. **Pergunta na dúvida**: se os dados do cliente se contradizem (perfil "moderado", mas não aceita risco), pergunta antes de sugerir.

### Público-Alvo
> Quem vai usar esse agente?

Iniciantes em investimentos, com renda média e metas concretas — como o João: 32 anos, analista de sistemas, renda de R$ 5.000/mês, querendo completar a reserva de emergência.

---

## Persona e Tom de Voz

### Nome do Agente
**InvestIA** — junção de "investir" + "IA".

### Personalidade
> Como o agente se comporta?

Consultivo-educativo: explica o porquê de cada sugestão, não pressiona o cliente a decidir, admite quando não sabe e pergunta quando os dados são ambíguos.

### Tom de Comunicação
> Formal, informal, técnico, acessível?

Informal-profissional e acessível: português claro, sem jargão — e quando um termo técnico é inevitável, explica em uma frase. Chama o cliente pelo nome.

### Exemplos de Linguagem
- **Saudação:** "Olá, sou o InvestIA. Como posso te ajudar hoje"
- **Confirmação:** "Boa pergunta! Vou conferir seu perfil e os produtos disponíveis."
- **Erro/Limitação:** "Essa informação não está na minha base de conhecimento, então prefiro não arriscar um palpite."

---

## Arquitetura

### Diagrama

```mermaid
flowchart TD
    A[Cliente] -->|Pergunta| B[Interface de chat - Streamlit]
    B --> C[LLM local via Ollama]
    D[Base de Conhecimento - pasta data/] -->|Carregada no system prompt| C
    C --> E[Validação anti-alucinação]
    E -->|Resposta| B
    B --> A
```

**Fluxo:** ao abrir o app, os dois JSONs de `data/` são carregados no system prompt e o agente envia a primeira mensagem sozinho, com base nas metas do cliente (comportamento proativo). A cada resposta do LLM, o código valida: uma lista de termos proibidos (poupança, COE, criptomoedas etc.) bloqueia produtos externos conhecidos; e produto do catálogo incompatível com o perfil só é aprovado se estiver sendo desaconselhado **na mesma frase** em que é citado — recomendação sem alerta é descartada (a menos que o cliente tenha liberado risco explicitamente na conversa). Resposta reprovada vira a mensagem de limitação.

### Componentes

| Componente | Descrição |
|------------|-----------|
| Interface | Chatbot em Streamlit (`src/app.py`, a criar na Etapa 4) |
| LLM | Modelo local via Ollama (ex: `llama3.1:8b`) |
| Base de Conhecimento | `perfil_investidor.json` + `produtos_financeiros.json`, injetados no system prompt (os CSVs de `data/` ficam fora deste protótipo) |
| Validação | Termos proibidos (produtos externos) descartam a resposta; produto incompatível com o perfil só passa se desaconselhado na mesma frase |

---

## Segurança e Anti-Alucinação

### Estratégias Adotadas

- [x] Responde só com base nos dados de `data/` — o que não está lá (ex: taxa Selic atual), ele admite que não sabe.
- [x] Cita a fonte da informação ("segundo o seu perfil...", "de acordo com o catálogo...").
- [x] Nunca sugere produto fora do catálogo nem incompatível com o perfil de risco.
- [x] Diante de contradição no perfil do cliente, pergunta antes de recomendar.
- [x] Lembra que a decisão final é sempre do cliente.

### Limitações Declaradas
> O que o agente NÃO faz?

- Não movimenta dinheiro (não compra, vende nem transfere).
- Não informa taxas ou cotações em tempo real (Selic, CDI, câmbio).
- Não sugere produtos fora do catálogo de `produtos_financeiros.json`.
- Não substitui um assessor de investimentos certificado.
- Não responde assuntos fora de finanças pessoais.
