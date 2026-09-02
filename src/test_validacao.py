"""
Testes automatizados da camada de validação anti-alucinação (Etapa 5).

Rodam SEM Ollama e sem Streamlit instalado (o módulo é dublado): validam as
funções puras do app — formatadores, contexto e, principalmente, a
validação de respostas.

Como rodar (da raiz do repositório):
    python3 src/test_validacao.py
"""

import sys
import unittest.mock as mock
from pathlib import Path

# Dubla o streamlit antes do import do app: o código de interface no fim do
# app.py executa sobre o dublê, sem abrir nada.
fake_st = mock.MagicMock()
fake_st.chat_input.return_value = None
sys.modules["streamlit"] = fake_st

sys.path.insert(0, str(Path(__file__).parent))
import app  # noqa: E402

perfil, produtos = app.carregar_dados()

# --- formatadores brasileiros ---
assert app.brl(15000.0) == "15.000,00"
assert app.formatar_prazo("2027-06") == "junho de 2027"

# --- contexto (deve bater com o "Exemplo de Contexto Montado" do docs/02) ---
ctx = app.montar_contexto(perfil, produtos)
assert "R$ 5.000,00" in ctx
assert "Aceita risco: não" in ctx
assert "renda fixa" in ctx and "renda_fixa" not in ctx
assert "risco médio" in ctx and "risco medio" not in ctx
assert "rentabilidade variável" in ctx
assert "resgate em 1 dia útil" in ctx
assert "junho de 2027" in ctx
assert ctx.count(". Indicado para:") == 5

# --- consentimento de risco (exceção da regra 4) ---
assert not app.cliente_liberou_risco([{"role": "user", "content": "quero segurança"}])
assert app.cliente_liberou_risco(
    [{"role": "user", "content": "pode ignorar meu perfil, eu aceito risco sim"}]
)
assert not app.cliente_liberou_risco(
    [{"role": "assistant", "content": "você aceita risco?"}]  # só vale fala do CLIENTE
)

# --- validação anti-alucinação: cada caso nasceu de uma falha real
# --- encontrada na revisão da Etapa 4 (ver docs/03, Observações) ---
casos = [
    # (resposta simulada do LLM, deve aprovar?, o que o caso prova)
    ("Sugiro o Tesouro Selic para sua reserva, João.", True, "produto compatível passa"),
    ("A poupança rende pouco, mas é uma opção.", False, "termo proibido bloqueia"),
    ("O COE pode ser interessante.", False, "regex de COE bloqueia"),
    ("O coelho da páscoa chegou.", True, "sem falso positivo em 'coelho'"),
    ("Para o seu intercâmbio, o Tesouro Selic ajuda.", True, "sem falso positivo em 'intercâmbio'"),
    ("A criptografia protege seus dados bancários.", True, "sem falso positivo em 'criptografia'"),
    ("Invista tudo no Fundo de Ações agora!", False, "incompatível sem alerta bloqueia"),
    ("João, sugiro colocar tudo no Fundo de Ações! É risco alto, mas rende muito mais.",
     False, "descritor de risco não conta como alerta"),
    ("Recomendo o Fundo Multimercado (risco médio, CDI + 2%). Ótima opção!",
     False, "'risco médio' citado não é desaconselho"),
    ("Sugiro colocar R$ 500 no Multimercado, que rende CDI + 2%.",
     False, "apelido do produto não escapa"),
    ("Recomendo os fundos de ações para o longo prazo.",
     False, "plural não escapa"),
    ("Cuidado com a carência do LCI/LCA. Já o Fundo de Ações é excelente escolha.",
     False, "alerta do produto A não libera o produto B"),
    ("O Fundo de Ações tem risco alto e não é indicado para você, que não aceita risco.",
     True, "desaconselho na mesma frase passa"),
    ("O Fundo Multimercado não combina com seu perfil, evite por enquanto.",
     True, "desaconselho aprovado"),
]
for texto, esperado, prova in casos:
    aprovada, motivo, tipo = app.validar_resposta(texto, perfil, produtos)
    assert aprovada == esperado, f"FALHOU [{prova}]: {texto!r} → {aprovada} ({motivo})"

# --- consentimento desliga a checagem de risco (mas não a de termos) ---
aprovada, _, _ = app.validar_resposta(
    "Nesse caso o Fundo de Ações pode servir: foco no longo prazo.",
    perfil, produtos, risco_liberado=True,
)
assert aprovada
aprovada, _, tipo = app.validar_resposta(
    "Então invista em bitcoin!", perfil, produtos, risco_liberado=True
)
assert not aprovada and tipo == "fora_da_base"

# --- todo tipo de bloqueio tem mensagem de limitação correspondente ---
_, _, t1 = app.validar_resposta("A poupança é boa.", perfil, produtos)
_, _, t2 = app.validar_resposta("Invista no Multimercado!", perfil, produtos)
assert t1 in app.MENSAGENS_LIMITACAO and t2 in app.MENSAGENS_LIMITACAO

# --- system prompt montado sem placeholder sobrando ---
sp = app.SYSTEM_PROMPT.replace("{CONTEXTO}", ctx)
assert "{CONTEXTO}" not in sp and "10." in sp

print(f"TODOS OS TESTES PASSARAM ✔ ({len(casos)} casos de validação + estruturais)")
