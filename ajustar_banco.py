import sqlite3

# Conecta ao banco
conn = sqlite3.connect('clientes.db')
cursor = conn.cursor()

# Adiciona a coluna telefone, se ainda não existir
try:
    cursor.execute("ALTER TABLE clientes ADD COLUMN telefone TEXT")
    print("Coluna 'telefone' adicionada com sucesso.")
except sqlite3.OperationalError:
    print("A coluna 'telefone' já existe.")

conn.commit()
conn.close()
