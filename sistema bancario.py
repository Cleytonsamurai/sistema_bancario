import datetime
import textwrap
import pytz
from abc import ABC, abstractclassmethod, abstractproperty

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
            Agência:\t{conta.agencia}
            Número:\t\t{conta.numero}
            Titular:\t{conta.cliente.nome}
            Saldo:\t\tR$ {conta.saldo:.2f}
        """
        except IndexError:
            raise StopIteration
        finally:
            self._index += 1


class Cliente:
    def __init__(self, nome, data_nascimento, cpf, endereco):
        self.nome = nome
        self.data_nascimento = data_nascimento
        self.cpf = cpf
        self.endereco = endereco
        self.contas = []
        self.indice_conta = 0

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
            return

        if valor > 0:
            self._saldo += valor
            agora = datetime.datetime.now(self.fuso_horario)
            self.historico.adicionar_transacao(Deposito(valor))
            print("Depósito realizado com sucesso.")
        else:
            print("Operação falhou! O valor informado é inválido.")

    def sacar(self, valor):
        if not self.pode_fazer_transacao():
            print("Você excedeu o número de transações permitidas para hoje.")
            return

        if valor > self._saldo:
            print("Operação falhou! Você não tem saldo suficiente.")
        elif valor > 500:
            print("Operação falhou! O valor do saque excede o limite.")
        elif len([t for t in self.historico.transacoes if t["tipo"] == "Saque"]) >= 3:
            print("Operação falhou! Número máximo de saques excedido.")
        elif valor > 0:
            self._saldo -= valor
            agora = datetime.datetime.now(self.fuso_horario)
            self.historico.adicionar_transacao(Saque(valor))
            print("Saque realizado com sucesso.")
        else:
            print("Operação falhou! O valor informado é inválido.")

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


def log_transacao(func):
    def envelope(*args, **kwargs):
        resultado = func(*args, **kwargs)
        print(f"{datetime.datetime.now()}: {func.__name__.upper()}")
        return resultado

    return envelope


def exibir_menu():
    menu = """\n
    ================ BANCO PIXAQUI ================
    [d]\tDepositar
    [s]\tSacar
    [e]\tExtrato
    [nc]\tNova conta
    [lc]\tListar contas
    [lu]\tListar usuários
    [nu]\tNovo usuário
    [q]\tSair
    => """
    return input(textwrap.dedent(menu))


def filtrar_cliente(cpf, clientes):
    clientes_filtrados = [cliente for cliente in clientes if cliente.cpf == cpf]
    return clientes_filtrados[0] if clientes_filtrados else None


def recuperar_conta_cliente(cliente):
    if not cliente.contas:
        print("\n@@@ Cliente não possui conta! @@@")
        return None

    # FIXME: não permite cliente escolher a conta
    return cliente.contas[0]


@log_transacao
def depositar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do depósito: "))
    transacao = Deposito(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


@log_transacao
def sacar(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    valor = float(input("Informe o valor do saque: "))
    transacao = Saque(valor)

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    cliente.realizar_transacao(conta, transacao)


@log_transacao
def exibir_extrato(clientes):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado! @@@")
        return

    conta = recuperar_conta_cliente(cliente)
    if not conta:
        return

    print("\n================ EXTRATO ================")
    extrato = ""
    tem_transacao = False
    for transacao in conta.historico.gerar_relatorio():
        tem_transacao = True
        extrato += f'\n{transacao["tipo"]}:\n\tR$ {transacao["valor"]:.2f}'

    if not tem_transacao:
        extrato = "Não foram realizadas movimentações"

    print(extrato)
    print(f"\nSaldo:\n\tR$ {conta.saldo:.2f}")
    print("==========================================")


@log_transacao
def criar_cliente(clientes):
    cpf = input("Informe o CPF (somente número): ")
    cliente = filtrar_cliente(cpf, clientes)

    if cliente:
        print("\n@@@ Já existe cliente com esse CPF! @@@")
        return

    nome = input("Informe o nome completo: ")
    data_nascimento = input("Informe a data de nascimento (dd-mm-aaaa): ")
    endereco = input("Informe o endereço (logradouro, nro - bairro - cidade/sigla estado): ")

    cliente = Cliente(nome=nome, data_nascimento=data_nascimento, cpf=cpf, endereco=endereco)

    clientes.append(cliente)

    print("\n=== Cliente criado com sucesso! ===")


@log_transacao
def criar_conta(numero_conta, clientes, contas):
    cpf = input("Informe o CPF do cliente: ")
    cliente = filtrar_cliente(cpf, clientes)

    if not cliente:
        print("\n@@@ Cliente não encontrado, fluxo de criação de conta encerrado! @@@")
        return

    conta = ContaCorrente(numero=numero_conta, cliente=cliente, saldo_inicial=0, limite=500, limite_saques=50)
    contas.append(conta)
    cliente.adicionar_conta(conta)

    print("\n=== Conta criada com sucesso! ===")


def listar_contas(contas):
    for conta in ContasIterador(contas):
        print("=" * 100)
        print(textwrap.dedent(str(conta)))


def listar_usuarios(clientes):
    print("\n================ USUÁRIOS ================")
    for cliente in clientes:
        print(f"Nome: {cliente.nome}\tCPF: {cliente.cpf}")
    print("==========================================")


def main():
    clientes = []
    contas = []

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
            numero_conta = len(contas) + 1
            criar_conta(numero_conta, clientes, contas)

        elif opcao == "lc":
            listar_contas(contas)

        elif opcao == "lu":
            listar_usuarios(clientes)

        elif opcao == "q":
            break

        else:
            print("\n@@@ Operação inválida, por favor selecione novamente a operação desejada. @@@")


if __name__ == "__main__":
    main()
