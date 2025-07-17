import sqlite3

def criar_tabelas():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Tabela de clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT
        )
    ''')

    # Tabela de contratos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            valor_mensal REAL NOT NULL,
            data_inicio TEXT NOT NULL,
            meses_contrato INTEGER NOT NULL,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )
    ''')

    # Tabela de pagamentos mensais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contrato_id INTEGER,
            referencia TEXT,               -- Ex: 07/2025
            data_vencimento TEXT,
            valor REAL,
            status TEXT DEFAULT 'Em Dia',  -- 'Em Dia', 'Pago', 'Vencido'
            data_pagamento TEXT,
            FOREIGN KEY(contrato_id) REFERENCES contratos(id)
        )
    ''')

    conn.commit()
    conn.close()
