import sqlite3
from datetime import datetime, timedelta

# Conectar ao banco de dados
def connect_db():
    conn = sqlite3.connect('financeiro.db')
    conn.execute("PRAGMA foreign_keys = 1") # Habilitar chaves estrangeiras, se for usar no futuro
    return conn

# Criar as tabelas no banco de dados
def create_tables():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                categoria TEXT NOT NULL,
                forma_pagamento TEXT NOT NULL,
                conta TEXT NOT NULL,
                data DATE NOT NULL,
                parcelado BOOLEAN NOT NULL,
                parcelas INTEGER DEFAULT 1,
                pago BOOLEAN NOT NULL DEFAULT 0
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS receitas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                valor REAL NOT NULL,
                data DATE NOT NULL
            )
            ''')
            conn.commit()
            print("DB: Tabelas verificadas/criadas com sucesso.")
    except sqlite3.Error as e:
        print(f"DB: Erro ao criar/verificar tabelas: {e}")
        raise

# Função para adicionar um gasto
def add_gasto(descricao, valor, categoria, forma_pagamento, conta, data, parcelado, parcelas):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO gastos (descricao, valor, categoria, forma_pagamento, conta, data, parcelado, parcelas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (descricao, valor, categoria, forma_pagamento, conta, data, parcelado, parcelas))
            conn.commit()
            print(f"DB: Gasto '{descricao}' R${valor:.2f} adicionado para {data}.")
    except sqlite3.Error as e:
        print(f"DB: Erro ao adicionar gasto: {e}")
        raise

# Função para adicionar uma receita
def add_receita(descricao, valor, data):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO receitas (descricao, valor, data)
            VALUES (?, ?, ?)
            ''', (descricao, valor, data))
            conn.commit()
            print(f"DB: Receita '{descricao}' R${valor:.2f} adicionada para {data}.")
    except sqlite3.Error as e:
        print(f"DB: Erro ao adicionar receita: {e}")
        raise

# --- Funções de Consulta ---
def get_ultimos_gastos(limit=5):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data, descricao, valor FROM gastos
                ORDER BY data DESC, id DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro ao buscar últimos gastos: {e}")
        raise

def get_gastos_por_data(data_especifica): # data_especifica no formato "YYYY-MM-DD"
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT descricao, valor, categoria FROM gastos
                WHERE data = ?
                ORDER BY id DESC
            ''', (data_especifica,))
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro ao buscar gastos por data ({data_especifica}): {e}")
        raise

def get_gastos_mes_atual():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            # Usar 'localtime' é importante se o servidor DB e o app podem ter fusos horários diferentes
            # para 'now'. Para datas puras YYYY-MM-DD, strftime('%Y-%m', 'now') é geralmente ok.
            cursor.execute('''
                SELECT data, descricao, valor, categoria FROM gastos
                WHERE strftime('%Y-%m', data) = strftime('%Y-%m', 'now', 'localtime')
                ORDER BY data DESC, id DESC
            ''')
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro ao buscar gastos do mês atual: {e}")
        raise

def get_gastos_por_categoria_periodo(categoria, data_inicio, data_fim):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data, descricao, valor FROM gastos
                WHERE lower(categoria) = lower(?) AND data BETWEEN ? AND ?
                ORDER BY data DESC, id DESC
            ''', (categoria.strip(), data_inicio, data_fim)) # Adicionado strip() na categoria
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro ao buscar gastos por categoria ('{categoria}') e período: {e}")
        raise

# --- Funções de Resumo (mantidas como estavam, mas com 'with') ---
def resumo_por_categoria():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT categoria, SUM(valor) AS total FROM gastos GROUP BY categoria ORDER BY total DESC")
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro no resumo por categoria: {e}")
        raise

def resumo_por_forma_pagamento():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT forma_pagamento, SUM(valor) AS total FROM gastos GROUP BY forma_pagamento ORDER BY total DESC")
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro no resumo por forma de pagamento: {e}")
        raise

def resumo_por_conta():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT conta, SUM(valor) AS total FROM gastos GROUP BY conta ORDER BY total DESC")
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"DB: Erro no resumo por conta: {e}")
        raise

if __name__ == '__main__':
    print("Executando inicialização e testes de db.py...")
    create_tables()
    # Você pode adicionar chamadas de teste aqui se desejar
    print("Testes de db.py concluídos (se houver).")