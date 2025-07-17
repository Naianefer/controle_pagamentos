from flask import Flask, render_template, request, redirect, url_for
from models import criar_tabelas
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import sqlite3
import os

app = Flask(__name__)
criar_tabelas()

def conectar():
    return sqlite3.connect('banco.db')

def atualizar_status_vencidos():
    hoje = datetime.today().strftime('%Y-%m-%d')
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(''' 
        UPDATE pagamentos 
        SET status = 'Atrasado'
        WHERE data_vencimento < ? AND status = 'Em Dia'
    ''', (hoje,))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clientes')
    clientes = cursor.fetchall()
    conn.close()
    return render_template('home.html', clientes=clientes)

@app.route('/cliente/novo', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO clientes (nome, email) VALUES (?, ?)', (nome, email))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    return render_template('add_client.html')

@app.route('/cliente/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']

        cursor.execute('''
            UPDATE clientes
            SET nome = ?, email = ?
            WHERE id = ?
        ''', (nome, email, cliente_id))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    cursor.execute('SELECT nome, email FROM clientes WHERE id = ?', (cliente_id,))
    cliente = cursor.fetchone()
    conn.close()

    return render_template('editar_cliente.html', cliente=cliente, cliente_id=cliente_id)

@app.route('/cliente/excluir/<int:cliente_id>', methods=['GET', 'POST'])
def excluir_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('home'))

@app.route('/contrato/novo/<int:cliente_id>', methods=['GET', 'POST'])
def novo_contrato(cliente_id):
    if request.method == 'POST':
        valor = float(request.form['valor'])  
        inicio = request.form['inicio']
        fim = request.form['fim']

        data_inicio = datetime.strptime(inicio, '%Y-%m-%d')
        data_fim = datetime.strptime(fim, '%Y-%m-%d')
        meses = (data_fim.year - data_inicio.year) * 12 + (data_fim.month - data_inicio.month) + 1

        if meses <= 0:
            return "Erro: a data final deve ser posterior à data inicial"

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(''' 
            INSERT INTO contratos (cliente_id, valor_mensal, data_inicio, meses_contrato)
            VALUES (?, ?, ?, ?)
        ''', (cliente_id, valor, inicio, meses))
        contrato_id = cursor.lastrowid

        for i in range(meses):
            vencimento = data_inicio + relativedelta(months=i)
            ref = vencimento.strftime('%m/%Y')
            ultimo_dia = calendar.monthrange(vencimento.year, vencimento.month)[1]
            vencimento = vencimento.replace(day=ultimo_dia)
            status = 'Atrasado' if vencimento.date() < datetime.today().date() else 'Em Dia'

            cursor.execute(''' 
                INSERT INTO pagamentos (contrato_id, referencia, data_vencimento, valor, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (contrato_id, ref, vencimento.strftime('%Y-%m-%d'), valor, status))

        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    return render_template('add_contract.html', cliente_id=cliente_id)

@app.route('/cliente/<int:cliente_id>/pagamentos')
def listar_pagamentos(cliente_id):
    atualizar_status_vencidos()

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(''' 
        SELECT p.id, p.referencia, p.data_vencimento, p.valor, p.status, p.data_pagamento 
        FROM pagamentos p
        JOIN contratos c ON p.contrato_id = c.id
        WHERE c.cliente_id = ?
        ORDER BY p.data_vencimento
    ''', (cliente_id,))
    pagamentos = cursor.fetchall()

    cursor.execute('SELECT nome FROM clientes WHERE id = ?', (cliente_id,))
    nome_cliente = cursor.fetchone()[0]
    conn.close()

    # Formatando as datas para o padrão pt-br (dd/mm/yyyy)
    for i in range(len(pagamentos)):
        pagamentos[i] = list(pagamentos[i])  # Para poder modificar os elementos
        pagamentos[i][2] = datetime.strptime(pagamentos[i][2], '%Y-%m-%d').strftime('%d/%m/%Y')  # Formata data_vencimento
        if pagamentos[i][5]:
            pagamentos[i][5] = datetime.strptime(pagamentos[i][5], '%Y-%m-%d').strftime('%d/%m/%Y')  # Formata data_pagamento
        if pagamentos[i][4] == 'Vencido':  # Substitui 'Vencido' por 'Atrasado'
            pagamentos[i][4] = 'Atrasado'

    return render_template('pagamentos.html', pagamentos=pagamentos, nome_cliente=nome_cliente, cliente_id=cliente_id)

@app.route('/pagamento/<int:pagamento_id>/pagar')
def pagar_parcela(pagamento_id):
    hoje = datetime.today().strftime('%Y-%m-%d')
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(''' 
        UPDATE pagamentos
        SET status = 'Pago', data_pagamento = ? 
        WHERE id = ? 
    ''', (hoje, pagamento_id))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route('/pagamento/<int:pagamento_id>/ticket')
def gerar_ticket(pagamento_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(''' 
        SELECT c.nome, p.referencia, p.valor, p.data_vencimento 
        FROM pagamentos p
        JOIN contratos ct ON p.contrato_id = ct.id
        JOIN clientes c ON ct.cliente_id = c.id
        WHERE p.id = ? 
    ''', (pagamento_id,))
    dados = cursor.fetchone()
    conn.close()

    nome, ref, valor, venc = dados
    conteudo = f'''TICKET DE COBRANÇA
Cliente: {nome}
Referência: {ref}
Vencimento: {venc}
Valor: R$ {valor:.2f}
'''

    nome_arquivo = f'ticket_{nome}_{ref.replace("/", "_")}.txt'
    with open(nome_arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    return f'Ticket gerado com sucesso: {nome_arquivo}'

if __name__ == '__main__':
    app.run(debug=True)
