"""
InvestIA — agente de consultoria de investimentos (DIO Lab "BIA do Futuro").

Etapa 4: aplicação funcional. Streamlit (interface) + Ollama (LLM local)
+ dados de data/*.json no system prompt + validação anti-alucinação.
Como rodar: src/README.md
"""

import json
import re
from pathlib import Path

import requests
import streamlit as st

# ============ CONFIGURAÇÃO ============

# Endpoint /api/chat (e não /api/generate): aceita a conversa inteira,
# então o agente tem memória entre as mensagens.
OLLAMA_URL = "http://localhost:11434/api/chat"
MODELO = "llama3.1:8b"  # troque pelo seu (confira com `ollama list`)
PASTA_DADOS = Path(__file__).parent.parent / "data"

# Mensagens exibidas quando a validação reprova a resposta do LLM.
MENSAGENS_LIMITACAO = {
    "fora_da_base": (
        "Hmm, prefiro não te passar essa resposta: ela citava algo fora da "
        "minha base de conhecimento, e eu não arrisco palpite. Posso te "
        "ajudar com os produtos do catálogo e com as suas metas."
    ),
    "risco": (
        "Quase te enviei uma sugestão que não combina com o seu perfil de "
        "risco, então preferi segurar. Quer ver as opções de risco baixo do "
        "catálogo?"
    ),
}

# ============ REGRAS DE VALIDAÇÃO (anti-alucinação) ============

# Produtos que NÃO existem no catálogo: se o LLM citar, extrapolou a base.
# Regex com borda de palavra (\b) evita falso positivo: "câmbio" não pode
# casar "intercâmbio", nem "cripto" casar "criptografia".
TERMOS_PROIBIDOS = {
    "poupança": r"\bpoupan[çc]as?\b",
    "cripto/bitcoin": r"\bcripto(moedas?|ativos?)?\b|\bbitcoins?\b",
    "outros títulos do Tesouro": r"\btesouro\s+(ipca|prefixado)\b",
    "previdência (PGBL/VGBL)": r"\b[pv]gbl\b|\bprevid[êe]ncia\s+privada\b",
    "day trade": r"\bday\s*trade\b",
    "dólar/câmbio": r"\bd[óo]lar(es)?\b|\bc[âa]mbio\b",
    "COE": r"\bcoe\b",
}
REGEX_PROIBIDOS = {
    rotulo: re.compile(padrao, re.IGNORECASE)
    for rotulo, padrao in TERMOS_PROIBIDOS.items()
}

# Palavras que mostram que o agente está DESACONSELHANDO um produto.
# "risco alto"/"risco médio" NÃO entram: são descrição factual do catálogo
# e aparecem até em recomendações ("é risco alto, mas rende muito!").
MARCADORES_DE_ALERTA = [
    "não recomendo", "nao recomendo", "não sugiro", "nao sugiro",
    "não indico", "nao indico", "não é indicado", "nao é indicado",
    "não combina", "nao combina", "cuidado", "alerta", "evite",
    "desaconselh", "incompatível", "incompativel",
]

# Como os produtos de risco médio/alto aparecem no texto (nome, apelido,
# plural) — o LLM escreve "o Multimercado", "fundos de ações"...
APELIDOS_PRODUTO = {
    "Fundo Multimercado": re.compile(r"\bmultimercados?\b", re.IGNORECASE),
    "Fundo de Ações": re.compile(
        r"\bfundos?\s+de\s+a[çc][õo]es\b|\ba[çc][õo]es\b", re.IGNORECASE
    ),
}

# Se o cliente disser isso, liberou sugestões de risco (exceção da regra 4).
REGEX_CONSENTIMENTO = re.compile(
    r"aceito\s+(correr\s+)?risco|aceito\s+arriscar|quero\s+arriscar|"
    r"pode\s+arriscar|topo\s+(o\s+)?risco|prefiro\s+arriscar",
    re.IGNORECASE,
)

# ============ FORMATADORES (padrão brasileiro) ============

MESES = {
    "01": "janeiro", "02": "fevereiro", "03": "março", "04": "abril",
    "05": "maio", "06": "junho", "07": "julho", "08": "agosto",
    "09": "setembro", "10": "outubro", "11": "novembro", "12": "dezembro",
}
CATEGORIAS = {"renda_fixa": "renda fixa", "fundo": "fundo"}
RISCOS = {"baixo": "baixo", "medio": "médio", "alto": "alto"}


def brl(valor):
    """15000.0 → '15.000,00' (o Python nativo faria '15,000.00')."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_prazo(prazo):
    """'2027-06' → 'junho de 2027'."""
    ano, mes = prazo.split("-")
    return f"{MESES[mes]} de {ano}"


# ============ CARREGAR DADOS ============
# Só os dois JSONs; os CSVs ficam fora do protótipo (docs/02).


def carregar_dados():
    with open(PASTA_DADOS / "perfil_investidor.json", encoding="utf-8") as f:
        perfil = json.load(f)
    with open(PASTA_DADOS / "produtos_financeiros.json", encoding="utf-8") as f:
        produtos = json.load(f)
    return perfil, produtos


# ============ MONTAR CONTEXTO ============
# Os JSONs viram o texto do "Exemplo de Contexto Montado" do docs/02.


def montar_contexto(perfil, produtos):
    metas = "\n".join(
        f"  {i}. {m['meta']} — R$ {brl(m['valor_necessario'])} até {formatar_prazo(m['prazo'])}"
        for i, m in enumerate(perfil["metas"], start=1)
    )
    linhas = "\n".join(
        f"{i}. {p['nome']} — {CATEGORIAS[p['categoria']]}, risco {RISCOS[p['risco']]}, "
        f"{'rentabilidade variável' if p['rentabilidade'].lower() == 'variável' else p['rentabilidade']}, "
        f"aporte mínimo R$ {brl(p['aporte_minimo'])}, {p['liquidez']}. "
        f"Indicado para: {p['indicado_para']}."
        for i, p in enumerate(produtos, start=1)
    )
    return f"""PERFIL DO CLIENTE
- Nome: {perfil['nome']}, {perfil['idade']} anos, {perfil['profissao']}
- Renda mensal: R$ {brl(perfil['renda_mensal'])}
- Perfil de investidor: {perfil['perfil_investidor']}
- Aceita risco: {"sim" if perfil['aceita_risco'] else "não"}
- Objetivo principal: {perfil['objetivo_principal']}
- Patrimônio total: R$ {brl(perfil['patrimonio_total'])}
- Reserva de emergência atual: R$ {brl(perfil['reserva_emergencia_atual'])}
- Metas:
{metas}

CATÁLOGO DE PRODUTOS (única fonte permitida para sugestões)
{linhas}"""


# ============ SYSTEM PROMPT ============
# As 10 regras do docs/03; o {CONTEXTO} recebe o texto acima.

SYSTEM_PROMPT = """Você é o InvestIA, um consultor virtual de investimentos para pessoas iniciantes.
Seu objetivo é ajudar o cliente a escolher, entre os produtos do catálogo abaixo,
os mais adequados ao perfil e às metas dele — sempre explicando o porquê.

PERSONALIDADE E TOM:
- Consultivo-educativo, informal-profissional, português claro e frases curtas.
- Chame o cliente pelo nome. Não pressione a decidir.
- Se usar um termo técnico (CDI, liquidez, IR), explique em uma frase.

DADOS (sua única fonte de verdade):
{CONTEXTO}

REGRAS:
1. Baseie TODAS as respostas exclusivamente nos DADOS acima.
2. Nunca invente números, taxas, produtos ou condições. Se a informação não
   está nos DADOS (ex: taxa Selic atual), diga que não sabe — pode indicar
   canais oficiais para o cliente consultar, mas nunca arrisque um valor.
3. Só recomende produtos do catálogo. Nunca sugira produtos externos
   (poupança, COE, criptomoedas, ações individuais etc.).
4. Respeite o risco: como o cliente não aceita risco, só sugira produtos de
   risco baixo — a menos que ele diga explicitamente o contrário na conversa.
5. O perfil do cliente tem uma contradição (perfil "moderado", mas aceita
   risco: não). Antes da primeira recomendação, aponte isso e pergunte o que
   prevalece.
6. Cite a fonte da informação ("segundo seu perfil...", "de acordo com o
   catálogo...").
7. Encerre toda recomendação lembrando que a decisão final é do cliente e que
   você não substitui um assessor de investimentos certificado.
8. Perguntas fora de finanças pessoais e investimentos: recuse com educação e
   redirecione para o seu tema.
9. Na primeira mensagem da conversa, cumprimente e mencione proativamente a
   meta mais urgente do cliente, oferecendo ajuda.
10. Você não executa nem simula operações financeiras (aplicar, comprar,
    vender, transferir). Se o cliente pedir, explique que você apenas orienta.
11. Você só conhece os dados do cliente desta conversa. Nunca compartilhe,
    procure ou invente dados de outras pessoas."""


# ============ VALIDAÇÃO ANTI-ALUCINAÇÃO ============
# Roda depois de cada resposta do LLM. Determinística: não depende de o
# modelo "se comportar". Devolve (aprovada?, motivo, tipo).


def cliente_liberou_risco(mensagens):
    """True se o CLIENTE disse na conversa que aceita risco (regra 4)."""
    return any(
        m["role"] == "user" and REGEX_CONSENTIMENTO.search(m["content"])
        for m in mensagens
    )


def validar_resposta(texto, perfil, produtos, risco_liberado=False):
    # 1) Termo fora do catálogo → o LLM extrapolou a base.
    for rotulo, regex in REGEX_PROIBIDOS.items():
        if regex.search(texto):
            return False, f"citou termo fora do catálogo: '{rotulo}'", "fora_da_base"

    # 2) Produto incompatível com o perfil só passa se estiver sendo
    #    desaconselhado NA MESMA FRASE em que é citado — um alerta sobre o
    #    produto A não pode liberar o produto B.
    if not perfil["aceita_risco"] and not risco_liberado:
        for frase in re.split(r"(?<=[.!?\n])\s+", texto.lower()):
            for p in produtos:
                if p["risco"] == "baixo":
                    continue
                regex_produto = APELIDOS_PRODUTO.get(p["nome"]) or re.compile(
                    re.escape(p["nome"].lower())
                )
                citado = regex_produto.search(frase)
                if citado and not any(m in frase for m in MARCADORES_DE_ALERTA):
                    return False, (
                        f"recomendou '{p['nome']}' (risco {RISCOS[p['risco']]}) "
                        f"sem desaconselhar, para cliente que não aceita risco"
                    ), "risco"

    return True, "ok", "ok"


# ============ CHAMAR O OLLAMA ============


def perguntar(mensagens_da_conversa, system_prompt):
    mensagens = [{"role": "system", "content": system_prompt}] + mensagens_da_conversa
    resposta = requests.post(
        OLLAMA_URL,
        json={"model": MODELO, "messages": mensagens, "stream": False},
        timeout=120,
    )
    resposta.raise_for_status()
    return resposta.json()["message"]["content"]


# ============ INTERFACE (Streamlit) ============


def exibir(role, texto):
    """Mostra a mensagem no chat escapando o '$' — sem isso o markdown do
    Streamlit trata 'R$ 10.000' como início de fórmula LaTeX e come o cifrão.
    Só afeta a exibição; o texto guardado no histórico continua intacto."""
    st.chat_message(role).write(texto.replace("$", "\\$"))


st.set_page_config(page_title="InvestIA", page_icon="💰")
st.title("💰 InvestIA")
st.caption(
    "Consultor virtual de investimentos — protótipo educativo. "
    "Não substitui um assessor de investimentos certificado."
)

# O Streamlit re-executa o script inteiro a cada mensagem; o session_state
# preserva a conversa. O chat começa vazio: o agente só fala quando o
# cliente manda a primeira mensagem (a saudação fica com o LLM, regra 9).
if "mensagens" not in st.session_state:
    perfil, produtos = carregar_dados()
    st.session_state.perfil = perfil
    st.session_state.produtos = produtos
    st.session_state.system_prompt = SYSTEM_PROMPT.replace(
        "{CONTEXTO}", montar_contexto(perfil, produtos)
    )
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    exibir(msg["role"], msg["content"])

if pergunta := st.chat_input("Pergunte sobre seus investimentos..."):
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    exibir("user", pergunta)

    with st.spinner("Consultando seu perfil e o catálogo..."):
        try:
            bruta = perguntar(
                st.session_state.mensagens, st.session_state.system_prompt
            )
        except requests.exceptions.RequestException:
            st.error(
                "Não consegui falar com o Ollama. Ele está rodando? "
                f"`ollama list` deve mostrar `{MODELO}` "
                f"(baixe com `ollama pull {MODELO}`)."
            )
            st.stop()

    aprovada, motivo, tipo = validar_resposta(
        bruta,
        st.session_state.perfil,
        st.session_state.produtos,
        risco_liberado=cliente_liberou_risco(st.session_state.mensagens),
    )
    final = bruta if aprovada else MENSAGENS_LIMITACAO[tipo]

    st.session_state.mensagens.append({"role": "assistant", "content": final})
    exibir("assistant", final)

    # Evidência para a Etapa 5: motivo e resposta descartada ficam visíveis.
    if not aprovada:
        with st.expander("🔍 Por que a resposta foi bloqueada?"):
            st.write(f"**Motivo:** {motivo}")
            st.write("**Resposta descartada:** " + bruta.replace("$", "\\$"))
