import datetime
import textwrap
import pytz
from abc import ABC, abstractclassmethod, abstractproperty
import logging
import os
import sqlite3

# Configuração do Logger
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_filename = os.path.join(log_directory, "transacoes.log")
logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(asctime)s - %(message)s")

# Configuração do Banco de Dados SQLite
db_filename = os.path.join(log_directory, "banco_pix.db")

conn = sqlite3.connect(db_filename)
cursor = conn.cursor()

# Criação das tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    endereco TEXT NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS contas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL,
    agencia TEXT NOT NULL,
    saldo REAL NOT NULL,
    limite REAL NOT NULL,
    limite_saques INTEGER NOT NULL,
    cliente_id INTEGER NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    valor REAL NOT NULL,
    data TEXT NOT NULL,
    conta_id INTEGER NOT NULL,
    FOREIGN KEY (conta_id) REFERENCES contas (id)
)
''')
conn.commit()

class ContasIterador:
    def __init__(self, contas):
        self.contas = contas
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            conta = self.contas[self._index]
            return f"""\
            Agência:\t{conta['agencia']}
            Número:\t\t{conta['numero']}
            Titular:\t{conta['cliente']['nome']}
            Saldo:\t\tR$ {conta['saldo']:.2f}
        """
        except IndexError:
            raise StopIteration
        finally:
            self._index += 1


class Cliente:
    def __init__(self, nome, data_nascimento, cpf, endereco, id=None):
        self.id = id
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
        self.endereco = endereco
        self.contas = []

    def realizar_transacao(self, conta, transacao):
        if len(conta.historico.transacoes_do_dia()) >= 2:
            print("\n@@@ Você excedeu o número de transações permitidas para hoje! @@@")
            return

        transacao.registrar(conta)

    def adicionar_conta(self, conta):
        self.contas.append(conta)


class ContaBancaria(ABC):
    def __init__(self, saldo_inicial=0, fuso_horario='America/Sao_Paulo'):
        self._saldo = saldo_inicial
        self.titular = None
        self._historico = Historico()
        self.fuso_horario = pytz.timezone(fuso_horario)

    @property
    def saldo(self):
        return self._saldo

    @property
    def historico(self):
        return self._historico

    def contar_transacoes_hoje(self):
        hoje = datetime.datetime.now(self.fuso_horario).date()
        return sum(1 for data, _ in self.historico.transacoes if data.date() == hoje)

    def pode_fazer_transacao(self):
        return self.contar_transacoes_hoje() < 10

    def depositar(self, valor):
        if not self.pode_fazer_transacao():
            print("Você excedeu o número de transações permitidas para hoje.")
            return False

        if valor > 0:
            self._saldo += valor
            agora = datetime.datetime.now(self.fuso_horario)
            self.historico.adicionar_transacao(Deposito(valor))
            print("Depósito realizado com sucesso.")
            logging.info(f"Depósito: R$ {valor:.2f} - Saldo: R$ {self._saldo:.2f}")
            return True
        else:
            print("Operação falhou! O valor informado é inválido.")
            return False

    def sacar(self, valor):
        if not self.pode_fazer_transacao():
            print("Você excedeu o número de transações permitidas para hoje.")
            return False

        if valor > self._saldo:
            print("Operação falhou! Você não tem saldo suficiente.")
            return False
        elif valor > 500:
            print("Operação falhou! O valor do saque excede o limite.")
            return False
        elif len([t for t in self.historico.transacoes if t["tipo"] == "Saque"]) >= 3:
            print("Operação falhou! Número máximo de saques excedido.")
            return False
        elif valor > 0:
            self._saldo -= valor
            agora = datetime.datetime.now(self.fuso_horario)
            self.historico.adicionar_transacao(Saque(valor))
            print("Saque realizado com sucesso.")
            logging.info(f"Saque: R$ {valor:.2f} - Saldo: R$ {self._saldo:.2f}")
            return True
        else:
            print("Operação falhou! O valor informado é inválido.")
            return False

    def extrato(self):
        print("\n================ EXTRATO ================")
        if not self.historico.transacoes:
            print("Não foram realizadas movimentações.")
        for transacao in self.historico.transacoes:
            print(f"{transacao['data']} - {transacao['tipo']} de R$ {transacao['valor']:.2f}")
        print(f"\nSaldo:\t\tR$ {self._saldo:.2f}")
        print("==========================================")


class ContaCorrente(ContaBancaria):
    def __init__(self, numero, cliente, saldo_inicial=0, limite=500, limite_saques=3):
        super().__init__(saldo_inicial)
        self._numero = numero
        self._agencia = "0001"
        self._cliente = cliente
        self._limite = limite
        self._limite_saques = limite_saques

    @property
    def numero(self):
        return self._numero

    @property
    def agencia(self):
        return self._agencia

    @property
    def cliente(self):
        return self._cliente

    def __str__(self):
        return f"""\
            Agência:\t{self.agencia}
            C/C:\t\t{self.numero}
            Titular:\t{self.cliente.nome}
        """


class Historico:
    def __init__(self):
        self._transacoes = []

    @property
    def transacoes(self):
        return self._transacoes

    def adicionar_transacao(self, transacao):
        self._transacoes.append(
            {
                "tipo": transacao.__class__.__name__,
                "valor": transacao.valor,
                "data": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            }
        )

    def gerar_relatorio(self, tipo_transacao=None):
        for transacao in self._transacoes:
            if tipo_transacao is None or transacao["tipo"].lower() == tipo_transacao.lower():
                yield transacao

    def transacoes_do_dia(self):
        data_atual = datetime.datetime.utcnow().date()
        transacoes = []
        for transacao in self._transacoes:
            data_transacao = datetime.datetime.strptime(transacao["data"], "%d-%m-%Y %H:%M:%S").date()
            if data_atual == data_transacao:
                transacoes.append(transacao)
        return transacoes


class Transacao(ABC):
    @property
    @abstractproperty
    def valor(self):
        pass

    @abstractclassmethod
    def registrar(self, conta):
        pass


class Saque(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.sacar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
            cursor.execute(
                "INSERT INTO transacoes (tipo, valor, data, conta_id) VALUES (?, ?, ?, ?)",
                ("Saque", self.valor, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), conta.id)
            )
            conn.commit()


class Deposito(Transacao):
    def __init__(self, valor):
        self._valor = valor

    @property
    def valor(self):
        return self._valor

    def registrar(self, conta):
        sucesso_transacao = conta.depositar(self.valor)

        if sucesso_transacao:
            conta.historico.adicionar_transacao(self)
            cursor.execute(
                "INSERT INTO transacoes (tipo, valor, data, conta_id) VALUES (?, ?, ?, ?)",
                ("Deposito", self.valor, datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), conta.id)
            )
            conn.commit()


def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        transacao_info = f"{datetime.datetime.now()}: {func.__name__.upper()}"
        logging.info(transacao_info)
        return resultado

    return envelope


def exibir_menu():
    menu = """\n
    ================ BANCO PIX ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [lu]\tListar usuários
    [nu]\tNovo usuário
    [ec]\tExcluir cliente (admin)
    [q]\tSair
    => """
    return input(textwrap.dedent(menu))


def filtrar_cliente(cpf):
    cursor.execute("SELECT id, nome, data_nascimento, cpf, endereco FROM clientes WHERE cpf = ?", (cpf,))
    row = cursor.fetchone()
    if row:
        return Cliente(id=row[0], nome=row[1], data_nascimento=row[2], cpf=row[3], endereco=row[4])
    return None


def recuperar_conta_cliente(cliente):
    cursor.execute("SELECT id, numero, agencia, saldo, limite, limite_saques FROM contas WHERE cliente_id = ?", (cliente.id,))
    row = cursor.fetchone()
    if row:
        conta = ContaCorrente(numero=row[1], cliente=cliente, saldo_inicial=row[3], limite=row[4], limite_saques=row[5])
        conta.id = row[0]
        return conta
    print("\n@@@ Cliente não possui conta! @@@")
    return None


@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, Deposito(valor))


@log_transacao
def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, Saque(valor))


@log_transacao
def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    conta.extrato()


@log_transacao
def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente número): ")
    cliente = filtrar_cliente(cpf)

    if cliente:
        print("\n@@@ Já existe cliente com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cursor.execute(
        "INSERT INTO clientes (nome, data_nascimento, cpf, endereco) VALUES (?, ?, ?, ?)",
        (nome, data_nascimento, cpf, endereco)
    )
    conn.commit()
    print("\n=== Cliente criado com sucesso! ===")


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf)

    if not cliente:
        print("\n@@@ Cliente não encontrado, fluxo de criação de conta encerrado! @@@")
        return

    conta = ContaCorrente(numero=numero_conta, cliente=cliente, saldo_inicial=0, limite=500, limite_saques=50)
    cursor.execute(
        "INSERT INTO contas (numero, agencia, saldo, limite, limite_saques, cliente_id) VALUES (?, ?, ?, ?, ?, ?)",
        (conta.numero, conta.agencia, conta.saldo, conta._limite, conta._limite_saques, cliente.id)
    )
    conn.commit()
    print("\n=== Conta criada com sucesso! ===")


def listar_contas(contas):
    cursor.execute("SELECT contas.numero, contas.agencia, contas.saldo, clientes.nome FROM contas JOIN clientes ON contas.cliente_id = clientes.id")
    contas = cursor.fetchall()
    for conta in contas:
        print("=" * 100)
        print(f"Agência:\t{conta[1]}\nNúmero:\t\t{conta[0]}\nTitular:\t{conta[3]}\nSaldo:\t\tR$ {conta[2]:.2f}\n")


def listar_usuarios(clientes):
    cursor.execute("SELECT nome, cpf FROM clientes")
    clientes = cursor.fetchall()
    print("\n================ USUÁRIOS ================")
    for cliente in clientes:
        print(f"Nome: {cliente[0]}\tCPF: {cliente[1]}")
    print("==========================================")


@log_transacao
def excluir_cliente():
    cpf = input("Informe o CPF do cliente a ser excluído: ")
    cliente = filtrar_cliente(cpf)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    cursor.execute("DELETE FROM contas WHERE cliente_id = ?", (cliente.id,))
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente.id,))
    conn.commit()
    print("\n=== Cliente excluído com sucesso! ===")


def login():
    print("=============== LOGIN ===============")
    username = input("Usuário: ")
    password = input("Senha: ")

    if username == "admin" and password == "admin":
        return True
    else:
        print("Usuário ou senha incorretos!")
        return False


def main():
    if not login():
        return

    while True:
        opcao = exibir_menu()

        if opcao == "d":
            depositar(clientes)

        elif opcao == "s":
            sacar(clientes)

        elif opcao == "e":
            exibir_extrato(clientes)

        elif opcao == "nu":
            criar_cliente(clientes)

        elif opcao == "nc":
            cursor.execute("SELECT COUNT(*) FROM contas")
            numero_conta = cursor.fetchone()[0] + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "lu":
            listar_usuarios(clientes)

        elif opcao == "ec":
            excluir_cliente()

        elif opcao == "q":
            conn.close()
            break

        else:
            print("\n@@@ Operação inválida, por favor selecione novamente a operação desejada. @@@")


if __name__ == "__main__":
    main()
