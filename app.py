
from flask import Flask, render_template, request, jsonify
import random
import math
import os
import time

app = Flask(__name__)

PRODUTOS = {
    "Peça Simples": {
        "valor_venda": 40, "custo_material": 15, "tempo": 5
    },
    "Componente": {
        "valor_venda": 85, "custo_material": 35, "tempo": 8
    },
    "Equipamento": {
        "valor_venda": 180, "custo_material": 80, "tempo": 12
    },
}

MODELOS = {
    "prensa": {
        "nome": "Prensa", "capacidade": 2,
        "custo": 400, "produto": "Peça Simples"
    },
    "montagem": {
        "nome": "Montagem", "capacidade": 4,
        "custo": 800, "produto": "Componente"
    },
    "forno": {
        "nome": "Forno", "capacidade": 6,
        "custo": 1200, "produto": "Equipamento"
    },
}

CORES = [
    "#3498db", "#e74c3c", "#2ecc71",
    "#9b59b6", "#f39c12", "#1abc9c"
]


def novo_jogo(nomes=None):
    if not isinstance(nomes, list) or len(nomes) < 2:
        nomes = ["Funcionário 1", "Funcionário 2"]

    jogo = {
        "dinheiro": 1000.0,
        "dia": 1,
        "tempo_dia": 0,
        "rodando": True,
        "funcionarios": [],
        "maquinas": [],
        "estoque": {p: 0 for p in PRODUTOS},
        "producao_total": 0,
        "vendas_total": 0,
        "mensagem": "Bem-vindo à sua fábrica!",
        "ultimo_tick": time.time(),
    }

    for nome in nomes[:2]:
        jogo["funcionarios"].append({
            "nome": str(nome)[:30],
            "motivacao": random.randint(75, 100),
            "salario": 50,
            "presente": True,
            "cor": random.choice(CORES),
            "x": random.randint(100, 800),
            "y": random.randint(220, 480),
            "maquina": None,
            "estado": "andando",
        })

    for tipo, x in [("prensa", 260), ("montagem", 520)]:
        modelo = MODELOS[tipo]
        jogo["maquinas"].append({
            "nome": f'{modelo["nome"]} {len(jogo["maquinas"]) + 1}',
            "tipo": tipo,
            "x": x,
            "y": 300,
            "capacidade": modelo["capacidade"],
            "custo": modelo["custo"],
            "produto": modelo["produto"],
            "durabilidade": 100,
            "funcionando": True,
            "produzindo": False,
            "tempo_producao": 0,
            "quantidade_producao": 0,
            "producao_total": 0,
            "funcionario": None,
        })

    return jogo


def numero(valor, padrao=0):
    try:
        resultado = float(valor)
        return resultado if math.isfinite(resultado) else padrao
    except (TypeError, ValueError):
        return padrao


def atualizar(jogo, delta):
    if not jogo["rodando"]:
        return

    delta = max(0, min(numero(delta), 5))
    jogo["tempo_dia"] += delta

    for maquina in jogo["maquinas"]:
        if not maquina["funcionando"] or not maquina["produzindo"]:
            continue

        maquina["tempo_producao"] -= delta

        if maquina["tempo_producao"] <= 0:
            maquina["tempo_producao"] = 0
            maquina["produzindo"] = False

            qtd = maquina["quantidade_producao"]
            produto = maquina["produto"]

            jogo["estoque"][produto] += qtd
            jogo["producao_total"] += qtd
            maquina["producao_total"] += qtd

            indice = maquina["funcionario"]

            if indice is not None and indice < len(jogo["funcionarios"]):
                funcionario = jogo["funcionarios"][indice]
                funcionario["estado"] = "andando"
                funcionario["maquina"] = None

            maquina["funcionario"] = None
            maquina["quantidade_producao"] = 0
            jogo["mensagem"] = (
                f'{maquina["nome"]} produziu {qtd}x {produto}.'
            )

    for funcionario in jogo["funcionarios"]:
        if not funcionario["presente"]:
            continue

        if funcionario["estado"] == "produzindo":
            continue

        if random.random() < 0.025:
            funcionario["x"] = random.randint(80, 830)
            funcionario["y"] = random.randint(180, 500)

    while jogo["tempo_dia"] >= 1800:
        jogo["tempo_dia"] -= 1800
        passar_dia(jogo)


def passar_dia(jogo):
    jogo["dia"] += 1
    salarios = sum(f["salario"] for f in jogo["funcionarios"])
    jogo["dinheiro"] -= salarios

    for funcionario in jogo["funcionarios"]:
        chance_falta = max(2, 25 - funcionario["motivacao"] // 5)
        funcionario["presente"] = random.randint(1, 100) > chance_falta

        if funcionario["presente"]:
            funcionario["motivacao"] = max(
                0, funcionario["motivacao"] - random.randint(2, 5)
            )
        else:
            funcionario["motivacao"] = min(
                100, funcionario["motivacao"] + 10
            )

        funcionario["estado"] = "andando"
        funcionario["maquina"] = None

    for maquina in jogo["maquinas"]:
        if maquina["produzindo"] and maquina["funcionario"] is not None:
            indice = maquina["funcionario"]

            if indice < len(jogo["funcionarios"]):
                funcionario = jogo["funcionarios"][indice]
                funcionario["estado"] = "andando"
                funcionario["maquina"] = None

        maquina["produzindo"] = False
        maquina["tempo_producao"] = 0
        maquina["quantidade_producao"] = 0
        maquina["funcionario"] = None

        if maquina["funcionando"]:
            maquina["durabilidade"] = max(
                0, maquina["durabilidade"] - random.randint(3, 8)
            )

            if maquina["durabilidade"] == 0:
                maquina["funcionando"] = False

    jogo["mensagem"] = (
        f"Dia {jogo['dia']} iniciado. Salários: ${salarios:.2f}"
    )


def executar_acao(jogo, dados):
    acao = dados.get("acao", "")
    indice = dados.get("indice", -1)

    if acao == "pausar":
        jogo["rodando"] = not jogo["rodando"]
        jogo["mensagem"] = (
            "Jogo pausado." if not jogo["rodando"] else "Jogo retomado."
        )

    elif acao == "produzir":
        if not jogo["rodando"]:
            jogo["mensagem"] = "Retome o jogo antes de produzir."
            return

        ocupados = {
            maquina["funcionario"]
            for maquina in jogo["maquinas"]
            if maquina["produzindo"]
            and maquina["funcionario"] is not None
        }

        feitos = 0

        for i, maquina in enumerate(jogo["maquinas"]):
            if not maquina["funcionando"] or maquina["produzindo"]:
                continue

            funcionario_encontrado = next((
                (j, f)
                for j, f in enumerate(jogo["funcionarios"])
                if f["presente"]
                and j not in ocupados
                and f["estado"] != "produzindo"
            ), None)

            if funcionario_encontrado is None:
                break

            j, funcionario = funcionario_encontrado
            produto = PRODUTOS[maquina["produto"]]
            qtd = max(
                1,
                int(maquina["capacidade"] * funcionario["motivacao"] / 100)
            )
            custo = produto["custo_material"] * qtd

            if jogo["dinheiro"] < custo:
                continue

            jogo["dinheiro"] -= custo
            maquina["produzindo"] = True
            maquina["tempo_producao"] = produto["tempo"]
            maquina["quantidade_producao"] = qtd
            maquina["funcionario"] = j
            funcionario["estado"] = "produzindo"
            funcionario["maquina"] = i

            ocupados.add(j)
            feitos += 1

        jogo["mensagem"] = (
            f"{feitos} produção(ões) iniciada(s)."
            if feitos
            else "Sem funcionários, máquinas ou dinheiro para produzir."
        )

    elif acao == "contratar":
        nome = str(dados.get("nome", "")).strip()[:30]

        if not nome:
            jogo["mensagem"] = "Digite um nome."
        elif jogo["dinheiro"] < 150:
            jogo["mensagem"] = "Dinheiro insuficiente."
        elif len(jogo["funcionarios"]) >= 30:
            jogo["mensagem"] = "Limite de funcionários atingido."
        else:
            jogo["dinheiro"] -= 150
            jogo["funcionarios"].append({
                "nome": nome,
                "motivacao": random.randint(75, 100),
                "salario": 50,
                "presente": True,
                "cor": random.choice(CORES),
                "x": random.randint(100, 800),
                "y": random.randint(220, 480),
                "maquina": None,
                "estado": "andando",
            })
            jogo["mensagem"] = f"{nome} foi contratado."

    elif acao == "comprar_maquina":
        tipo = dados.get("tipo")
        modelo = MODELOS.get(tipo)
        x = numero(dados.get("x"), 450)
        y = numero(dados.get("y"), 400)

        if modelo is None:
            jogo["mensagem"] = "Tipo de máquina inválido."
        elif jogo["dinheiro"] < modelo["custo"]:
            jogo["mensagem"] = "Dinheiro insuficiente."
        elif len(jogo["maquinas"]) >= 20:
            jogo["mensagem"] = "Limite de máquinas atingido."
        elif any(
            math.hypot(x - m["x"], y - m["y"]) < 145
            for m in jogo["maquinas"]
        ):
            jogo["mensagem"] = "Local muito próximo de outra máquina."
        else:
            x = max(100, min(800, x))
            y = max(220, min(480, y))
            jogo["dinheiro"] -= modelo["custo"]

            jogo["maquinas"].append({
                "nome": f'{modelo["nome"]} {len(jogo["maquinas"]) + 1}',
                "tipo": tipo,
                "x": x,
                "y": y,
                "capacidade": modelo["capacidade"],
                "custo": modelo["custo"],
                "produto": modelo["produto"],
                "durabilidade": 100,
                "funcionando": True,
                "produzindo": False,
                "tempo_producao": 0,
                "quantidade_producao": 0,
                "producao_total": 0,
                "funcionario": None,
            })

            jogo["mensagem"] = "Máquina comprada."

    elif acao == "vender_produto":
        produto = dados.get("produto")

        if produto not in PRODUTOS:
            jogo["mensagem"] = "Produto inválido."
        else:
            qtd = jogo["estoque"][produto]

            if qtd <= 0:
                jogo["mensagem"] = "Produto indisponível no estoque."
            else:
                valor = qtd * PRODUTOS[produto]["valor_venda"]
                jogo["estoque"][produto] = 0
                jogo["dinheiro"] += valor
                jogo["vendas_total"] += qtd
                jogo["mensagem"] = (
                    f"{qtd} unidades vendidas por ${valor:.2f}."
                )

    elif acao in ("reparar", "vender_maquina"):
        if (
            not isinstance(indice, int)
            or isinstance(indice, bool)
            or not 0 <= indice < len(jogo["maquinas"])
        ):
            jogo["mensagem"] = "Máquina inválida."
            return

        maquina = jogo["maquinas"][indice]

        if acao == "reparar":
            custo = maquina["custo"] * 0.20

            if maquina["produzindo"]:
                jogo["mensagem"] = "A máquina está produzindo."
            elif jogo["dinheiro"] < custo:
                jogo["mensagem"] = "Dinheiro insuficiente."
            else:
                jogo["dinheiro"] -= custo
                maquina["durabilidade"] = 100
                maquina["funcionando"] = True
                jogo["mensagem"] = f'{maquina["nome"]} reparada.'

        else:
            if maquina["produzindo"]:
                jogo["mensagem"] = (
                    "Não é possível vender durante a produção."
                )
            else:
                valor = (
                    maquina["custo"]
                    * max(0.20, maquina["durabilidade"] / 100)
                    * 0.60
                )

                jogo["dinheiro"] += valor
                jogo["maquinas"].pop(indice)

                for funcionario in jogo["funcionarios"]:
                    if funcionario["maquina"] == indice:
                        funcionario["maquina"] = None
                        funcionario["estado"] = "andando"
                    elif (
                        funcionario["maquina"] is not None
                        and funcionario["maquina"] > indice
                    ):
                        funcionario["maquina"] -= 1

                for outra in jogo["maquinas"]:
                    if (
                        outra["funcionario"] is not None
                        and outra["funcionario"] < len(jogo["funcionarios"])
                        and jogo["funcionarios"][outra["funcionario"]]["maquina"]
                        is not None
                    ):
                        pass

                jogo["mensagem"] = f'Máquina vendida por ${valor:.2f}.'

    elif acao == "motivar":
        if jogo["dinheiro"] < 100:
            jogo["mensagem"] = "Dinheiro insuficiente."
        else:
            jogo["dinheiro"] -= 100

            for funcionario in jogo["funcionarios"]:
                funcionario["motivacao"] = min(
                    100, funcionario["motivacao"] + 20
                )

            jogo["mensagem"] = "Equipe motivada!"

    elif acao == "dia_seguinte":
        passar_dia(jogo)

    else:
        jogo["mensagem"] = "Ação desconhecida."


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/diagnostico")
def api_diagnostico():
    return jsonify({
        "ok": True,
        "mensagem": "Servidor funcionando"
    })


@app.post("/api/novo")
def api_novo():
    dados = request.get_json(silent=True) or {}
    nomes = dados.get("nomes")

    if (
        not isinstance(nomes, list)
        or len(nomes) < 2
        or not all(isinstance(nome, str) for nome in nomes[:2])
    ):
        nomes = ["Funcionário 1", "Funcionário 2"]

    return jsonify(novo_jogo(nomes))


@app.post("/api/acao")
def api_acao():
    dados = request.get_json(silent=True) or {}
    jogo = dados.get("jogo")

    if not isinstance(jogo, dict):
        return jsonify({"erro": "Estado do jogo inválido."}), 400

    try:
        executar_acao(jogo, dados)
        return jsonify(jogo)
    except (KeyError, TypeError, ValueError, IndexError) as erro:
        app.logger.warning("Erro ao executar ação: %s", erro)
        return jsonify({
            "erro": "Não foi possível executar essa ação."
        }), 400


@app.post("/api/tick")
def api_tick():
    dados = request.get_json(silent=True) or {}
    jogo = dados.get("jogo")

    if not isinstance(jogo, dict):
        return jsonify({"erro": "Estado do jogo inválido."}), 400

    try:
        atualizar(jogo, dados.get("delta", 1))
        return jsonify(jogo)
    except (KeyError, TypeError, ValueError, IndexError) as erro:
        app.logger.warning("Erro ao atualizar jogo: %s", erro)
        return jsonify({
            "erro": "Não foi possível atualizar o jogo."
        }), 400


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    app.run(debug=debug)

