class ContaBancaria:
    def __init__(self, saldo_inicial=0):
        self.saldo = saldo_inicial

    def depositar(self, valor):
        self.saldo += valor
        print("Depósito realizado com sucesso.")

    def sacar(self, valor):
        if self.saldo >= valor:
            self.saldo -= valor
            print("Saque realizado com sucesso.")
        else:
            print("Saldo insuficiente.")

    def extrato(self):
        print(f"Saldo atual: R$ {self.saldo:.2f}")


# Função para exibir o menu
def exibir_menu():
    print("====================================")
    print("======== BANCO VOLTE SEMPRE ========")
    print("====================================")
    print("1. Depositar")
    print("2. Sacar")
    print("3. Extrato")
    print("4. Sair")
    print("====================================")


# Exemplo de uso
conta = ContaBancaria(1000)  # Cria uma conta com saldo inicial de 1000

while True:
    exibir_menu()
    opcao = input("Escolha uma opção (1-4): ")

    if opcao == "1":
        valor = float(input("Digite o valor para depósito: "))
        conta.depositar(valor)
    elif opcao == "2":
        valor = float(input("Digite o valor para saque: "))
        conta.sacar(valor)
    elif opcao == "3":
        conta.extrato()
    elif opcao == "4":
        print("Obrigado por usar nosso banco! VOLTE SEMPRE!!!")
        break
    else:
        print("Opção inválida. Tente novamente.")
