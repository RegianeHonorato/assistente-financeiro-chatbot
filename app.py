from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timedelta
import re
import sqlite3

# Importar todas as funções necessárias de db.py
try:
    from db import (
        add_gasto, add_receita, create_tables,
        get_ultimos_gastos, get_gastos_por_data,
        get_gastos_mes_atual, get_gastos_por_categoria_periodo,
        resumo_por_categoria, resumo_por_forma_pagamento, resumo_por_conta # Adicionando resumos
    )
    create_tables()
except ImportError as imp_err:
    print(f"ERRO CRÍTICO: Falha ao importar de db.py: {imp_err}")
    # Definir funções dummy para evitar que o app quebre totalmente na inicialização
    def _mock_db_function(*args, **kwargs): print(f"MOCK DB: Função do DB não encontrada devido a erro de importação.")
    add_gasto = add_receita = create_tables = get_ultimos_gastos = get_gastos_por_data = \
    get_gastos_mes_atual = get_gastos_por_categoria_periodo = resumo_por_categoria = \
    resumo_por_forma_pagamento = resumo_por_conta = _mock_db_function
except Exception as e_db_init:
    print(f"ERRO CRÍTICO ao inicializar DB (ex: create_tables): {e_db_init}")

app = Flask(__name__)

def processar_mensagem(mensagem_usuario):
    mensagem = mensagem_usuario.lower().strip()
    data_hoje_str = datetime.now().strftime("%Y-%m-%d")
    data_compra_dt = datetime.now()

    # Regex para Gasto
    gasto_match = re.search(
        r'gastei\s*([\d,\.]+)'                                  # 1: VALOR (obrigatório)
        r'(?:.*?(?:\s*no\s*(?:cart[aã]o\s+)?([\wçãõáéíóú]+)))'    # 2: CARTAO/CONTA (obrigatório para este padrão)
        r'(?:.*?(?:categoria\s+([\wçãõáéíóú]+)))?'              # 3: CATEGORIA (opcional)
        r'(?:.*?(?:loja\s+([\w\sçãõáéíóú]+?)))?'                 # 4: LOJA (opcional)
        r'(?:.*?(?:parcelado\s*(?:em)?\s*(\d+)x?))?',           # 5: PARCELAS (opcional)
        # A ideia é que cada (?:.*?...)? tenta encontrar seu padrão específico
        # em qualquer lugar após o anterior.
        mensagem
    )

    # Regex para Receita
    receita_match = re.search(
        r'recebi\s*([\d,\.]+)'
        r'(?:.*?categoria\s+([\wçãõáéíóú]+))?',
        mensagem
    )

    # --- Lógica de Registro de Gasto ---
    if gasto_match:
        try:
            valor_str = gasto_match.group(1).replace(',', '.')
            valor = float(valor_str)
            conta = gasto_match.group(2) # Regex agora torna a conta obrigatória
            categoria = gasto_match.group(3) if gasto_match.group(3) else "outros_gastos"
            loja_raw = gasto_match.group(4)
            loja = loja_raw.strip() if loja_raw else "nao_especificada"
            parcelas_str = gasto_match.group(5)
            parcelas_total = int(parcelas_str) if parcelas_str else 1
            e_parcelado = parcelas_total > 1

            for i in range(parcelas_total):
                data_parcela_dt = data_compra_dt + timedelta(days=30 * i)
                data_parcela_str = data_parcela_dt.strftime("%Y-%m-%d")
                valor_da_parcela = round(valor / parcelas_total, 2)
                if i == parcelas_total - 1:
                    valor_da_parcela = round(valor - (round(valor / parcelas_total, 2) * (parcelas_total - 1)), 2)
                desc_base = f"{categoria.capitalize()} - {loja.capitalize()}"
                descricao_final = f"{desc_base} (Parc. {i+1}/{parcelas_total})" if e_parcelado else desc_base
                add_gasto(descricao_final, valor_da_parcela, categoria, "crédito", conta, data_parcela_str, e_parcelado, parcelas_total)

            return (f"✅ Gasto de R${valor:.2f} em {parcelas_total}x (R${valor/parcelas_total:.2f}/mês) registrado!\n"
                    f"Categoria: {categoria}, Cartão: {conta}, Loja: {loja}.") if e_parcelado else \
                   (f"✅ Gasto de R${valor:.2f} registrado!\n"
                    f"Categoria: {categoria}, Cartão: {conta}, Loja: {loja}.")
        except ValueError: return "😕 Valor ou número de parcelas inválido."
        except sqlite3.Error as db_err:
            print(f"APP: Erro DB (gasto): {db_err}")
            return "⚠️ Ops! Problema com o banco de dados ao salvar gasto."
        except Exception as e:
            print(f"APP: Erro inesperado (gasto): {e}")
            return "⚠️ Ops! Algo muito estranho deu errado ao processar seu gasto."

    # --- Lógica de Registro de Receita ---
    elif receita_match:
        try:
            valor_str = receita_match.group(1).replace(',', '.')
            valor = float(valor_str)
            categoria = receita_match.group(2) if receita_match.group(2) else "outras_receitas"
            descricao = f"Receita - {categoria.capitalize()}"
            add_receita(descricao, valor, data_hoje_str)
            return f"✅ Receita de R${valor:.2f} registrada na categoria {categoria}!"
        except ValueError: return "😕 Valor inválido para receita."
        except sqlite3.Error as db_err:
            print(f"APP: Erro DB (receita): {db_err}")
            return "⚠️ Ops! Problema com o banco de dados ao salvar receita."
        except Exception as e:
            print(f"APP: Erro inesperado (receita): {e}")
            return "⚠️ Ops! Algo muito estranho deu errado ao processar sua receita."

    # --- Comandos de Consulta e Resumo ---
    elif mensagem == 'ultimos gastos':
        try:
            gastos = get_ultimos_gastos(5)
            if not gastos: return "👍 Nenhum gasto recente."
            reply = "Últimos gastos:\n" + "\n".join([f"🗓️ {d} - {desc}: R${v:.2f}" for d, desc, v in gastos])
            return reply
        except Exception as e: print(f"APP: Erro (ultimos gastos): {e}"); return "⚠️ Erro ao buscar últimos gastos."

    elif mensagem == 'gastos hoje':
        try:
            gastos = get_gastos_por_data(data_hoje_str)
            if not gastos: return f"👍 Nenhum gasto hoje ({data_hoje_str})."
            total_hoje = sum(g[1] for g in gastos)
            reply = f"Gastos de hoje ({data_hoje_str}):\n" + \
                    "\n".join([f"- {desc} ({cat}): R${v:.2f}" for desc, v, cat in gastos]) + \
                    f"\n\nTotal hoje: R${total_hoje:.2f}"
            return reply
        except Exception as e: print(f"APP: Erro (gastos hoje): {e}"); return "⚠️ Erro ao buscar gastos de hoje."

    elif mensagem == 'gastos mes' or mensagem == 'gastos este mes':
        try:
            gastos = get_gastos_mes_atual()
            if not gastos: return "👍 Nenhum gasto este mês."
            total_mes = sum(g[2] for g in gastos)
            reply = "Gastos deste mês:\n" + \
                    "\n".join([f"🗓️ {d} - {desc} ({cat}): R${v:.2f}" for d, desc, v, cat in gastos]) + \
                    f"\n\nTotal este mês: R${total_mes:.2f}"
            return reply
        except Exception as e: print(f"APP: Erro (gastos mes): {e}"); return "⚠️ Erro ao buscar gastos do mês."

    match_gastos_cat_mes = re.match(r'gastos\s+([\wçãõáéíóú]+)\s+este mes', mensagem) # use 'mensagem' aqui
    if match_gastos_cat_mes: # Deve ser um elif para não conflitar com 'gastos mes'
        categoria_busca = match_gastos_cat_mes.group(1)
        try:
            hoje = datetime.now()
            primeiro_dia_mes = hoje.replace(day=1).strftime("%Y-%m-%d")
            proximo_mes_primeiro_dia = (hoje.replace(day=28) + timedelta(days=4)).replace(day=1)
            ultimo_dia_mes_atual = (proximo_mes_primeiro_dia - timedelta(days=1)).strftime("%Y-%m-%d")
            
            gastos = get_gastos_por_categoria_periodo(categoria_busca, primeiro_dia_mes, ultimo_dia_mes_atual)
            if not gastos: return f"👍 Nenhum gasto para '{categoria_busca}' este mês."
            total_cat_mes = sum(g[2] for g in gastos)
            reply = f"Gastos de '{categoria_busca.capitalize()}' este mês:\n" + \
                    "\n".join([f"🗓️ {d} - {desc}: R${v:.2f}" for d, desc, v in gastos]) + \
                    f"\n\nTotal '{categoria_busca.capitalize()}': R${total_cat_mes:.2f}"
            return reply
        except Exception as e: print(f"APP: Erro (gastos {categoria_busca} mes): {e}"); return f"⚠️ Erro ao buscar gastos de '{categoria_busca}'."

    # Comandos de Resumo (adicionados)
    elif mensagem == 'resumo categoria':
        try:
            items = resumo_por_categoria()
            if not items: return "Ainda não há gastos para resumir por categoria."
            reply = "Resumo por Categoria:\n" + "\n".join([f"- {cat}: R${total:.2f}" for cat, total in items])
            return reply
        except Exception as e: print(f"APP: Erro (resumo categoria): {e}"); return "⚠️ Erro ao gerar resumo por categoria."
    
    elif mensagem == 'resumo forma de pagamento' or mensagem == 'resumo formapagamento':
        try:
            items = resumo_por_forma_pagamento()
            if not items: return "Ainda não há gastos para resumir por forma de pagamento."
            reply = "Resumo por Forma de Pagamento:\n" + "\n".join([f"- {fp}: R${total:.2f}" for fp, total in items])
            return reply
        except Exception as e: print(f"APP: Erro (resumo forma pgto): {e}"); return "⚠️ Erro ao gerar resumo por forma de pagamento."

    elif mensagem == 'resumo conta':
        try:
            items = resumo_por_conta()
            if not items: return "Ainda não há gastos para resumir por conta."
            reply = "Resumo por Conta:\n" + "\n".join([f"- {c}: R${total:.2f}" for c, total in items])
            return reply
        except Exception as e: print(f"APP: Erro (resumo conta): {e}"); return "⚠️ Erro ao gerar resumo por conta."


    # --- Comando de Ajuda ---
    elif mensagem == 'ajuda' or mensagem == 'comandos':
         return ("Comandos disponíveis:\n"
                "➡️ `Gastei <v> no <cartao> [cat <c>] [loja <l>] [parc <N>x]`\n"
                "   Ex: Gastei 50 no nubank cat comida loja mercado parc 3x\n"
                "➡️ `Recebi <valor> [cat <categoria>]`\n"
                "➡️ `ultimos gastos`\n"
                "➡️ `gastos hoje`\n"
                "➡️ `gastos mes` (ou `gastos este mes`)\n"
                "➡️ `gastos <categoria> este mes` (Ex: gastos comida este mes)\n"
                "➡️ `resumo categoria` / `resumo formapagamento` / `resumo conta`\n"
                "➡️ `ajuda` ou `comandos`.")

    # --- Resposta Padrão ---
    return ("Sinto muito, não entendi sua mensagem. 🤔\n"
            "Use `ajuda` para ver os comandos disponíveis.")

@app.route('/', methods=['POST'])
def webhook():
    mensagem_recebida = request.form.get('Body', '').strip()
    resposta_texto = "Desculpe, ocorreu um problema e não pude processar sua mensagem."

    if not mensagem_recebida:
        print("Webhook: Mensagem vazia recebida.")
        resposta_texto = "Não recebi nenhuma mensagem para processar."
    else:
        print(f"Webhook: Mensagem recebida: '{mensagem_recebida}'")
        try:
            resposta_texto = processar_mensagem(mensagem_recebida)
        except Exception as proc_err:
            print(f"Webhook: Erro crítico não capturado em processar_mensagem: {proc_err}")
            resposta_texto = "⚠️ Ocorreu um erro grave no processamento. A equipe foi notificada."
        print(f"Webhook: Resposta processada: '{resposta_texto}'")

    twiml_response = MessagingResponse()
    twiml_response.message(resposta_texto)
    return str(twiml_response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)