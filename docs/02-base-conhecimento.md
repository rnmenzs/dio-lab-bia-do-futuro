# Base de Conhecimento — InvestIA

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `perfil_investidor.json` | JSON | Personalização: perfil de risco, metas e situação da reserva entram no system prompt |
| `produtos_financeiros.json` | JSON | Catálogo: única fonte de produtos que o agente pode sugerir |
| `transacoes.csv` | CSV | Fora deste protótipo (decisão de escopo — ver `docs/01`) |
| `historico_atendimento.csv` | CSV | Fora deste protótipo (decisão de escopo — ver `docs/01`) |

---

## Adaptações nos Dados

Duas adaptações, ambas para garantir que toda resposta do agente seja rastreável aos dados:

1. **Campo `liquidez` nos 5 produtos** (`produtos_financeiros.json`): liquidez é o atributo decisivo para recomendar produto de reserva de emergência, e o catálogo original não trazia essa informação — sem ela, o agente teria que responder "não sei" a qualquer pergunta sobre resgate (ou inventar a resposta).
2. **Prazos das metas atualizados** (`perfil_investidor.json`): os prazos originais (jun/2026 e dez/2027) já estavam vencidos ou apertados em relação à data atual; foram movidos para jun/2027 e dez/2028 para o cenário da demonstração fazer sentido.

---

## Estratégia de Integração

### Como os dados são carregados?
> Descreva como seu agente acessa a base de conhecimento.

Uma única vez, na abertura do app: o código (`src/app.py`) lê os dois JSONs, formata como texto e monta o system prompt. Não há consulta à base em tempo de execução.

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

Vão inteiros no system prompt. Com 1 perfil e 5 produtos, a base cabe folgada no contexto do modelo — por isso não usamos RAG/banco vetorial, que só se justifica quando a base é grande demais para o contexto.

---

## Exemplo de Contexto Montado

> Como os dois JSONs viram texto dentro do system prompt:

```
PERFIL DO CLIENTE
- Nome: João Silva, 32 anos, analista de sistemas
- Renda mensal: R$ 5.000,00
- Perfil de investidor: moderado
- Aceita risco: não
- Patrimônio total: R$ 15.000,00
- Reserva de emergência atual: R$ 10.000,00
- Metas:
  1. Completar reserva de emergência — R$ 15.000,00 até jun/2027
  2. Entrada do apartamento — R$ 50.000,00 até dez/2028

CATÁLOGO DE PRODUTOS (única fonte permitida para sugestões)
1. Tesouro Selic — renda fixa, risco baixo, 100% da Selic, aporte mínimo R$ 30,
   resgate em 1 dia útil. Indicado para: reserva de emergência e iniciantes.
2. CDB Liquidez Diária — renda fixa, risco baixo, 102% do CDI, aporte mínimo R$ 100,
   resgate no mesmo dia. Indicado para: quem busca segurança com rendimento diário.
3. LCI/LCA — renda fixa, risco baixo, 95% do CDI, aporte mínimo R$ 1.000,
   resgate somente após carência de 90 dias. Indicado para: quem pode esperar 90 dias (isento de IR).
4. Fundo Multimercado — fundo, risco médio, CDI + 2%, aporte mínimo R$ 500,
   resgate em 5 dias úteis. Indicado para: perfil moderado que busca diversificação.
5. Fundo de Ações — fundo, risco alto, rentabilidade variável, aporte mínimo R$ 100,
   resgate em 30 dias. Indicado para: perfil arrojado com foco no longo prazo.
```
