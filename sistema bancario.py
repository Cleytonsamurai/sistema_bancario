class ContaBancaria:
  def __init__(self, saldo_inicial=0):
      self.saldo = saldo_inicial
      self.titular = None

  def depositar(self, valor):
      self.saldo += valor
      print("Depósito realizado com sucesso.")

  def sacar(self, *, saldo, valor, extrato, limite, numero_saques):
      if saldo - valor >= limite and numero_saques > 0:
          saldo -= valor
          numero_saques -= 1
          print("Saque realizado com sucesso.")
      elif saldo - valor < limite:
          print("Saque não permitido: ultrapassaria o limite.")
      else:
          print("Saque não permitido: número máximo de saques atingido.")
      return saldo, extrato

  def extrato(self, *, extrato, saldo):
      print(f"{extrato}: R$ {saldo:.2f}")


class Usuario:
  def __init__(self, nome, data_nascimento, cpf, endereco):
      self.nome = nome
      self.data_nascimento = data_nascimento
      self.cpf = cpf
      self.endereco = endereco
      self.conta_corrente = None


def validar_cpf(cpf):
  if len(cpf) == 11 and cpf.isdigit():
      return True
  return False


def criar_usuario(usuarios):
  print("========== Cadastro de Usuário ==========")
  nome = input("Digite o nome do usuário: ")
  data_nascimento = input("Digite a data de nascimento (DD/MM/AAAA): ")

  # Solicitar o CPF até que seja válido
  while True:
      cpf = input("Digite o CPF do usuário (11 dígitos): ")
      if validar_cpf(cpf):
          break
      else:
          print("CPF inválido. Por favor, insira os 11 dígitos.")

  endereco = input("Digite o endereço completo (logradouro, número - bairro - cidade/estado): ")

  # Verifica se o CPF já está cadastrado
  for usuario in usuarios:
      if usuario.cpf == cpf:
          print("Erro: CPF já cadastrado.")
          return None

  return Usuario(nome, data_nascimento, cpf, endereco)


def criar_conta_corrente(usuarios):
  if usuarios:
      cpf = input("Digite o CPF do usuário: ")
      usuario_encontrado = None

      for usuario in usuarios:
          if usuario.cpf == cpf:
              usuario_encontrado = usuario
              break

      if usuario_encontrado:
          saldo_inicial = float(input("Digite o saldo inicial da conta: "))
          conta = ContaBancaria(saldo_inicial)
          conta.titular = usuario_encontrado
          usuario_encontrado.conta_corrente = conta
          print("Conta corrente criada com sucesso.")
          return conta
      else:
          print("Usuário não encontrado.")
          return None
  else:
      print("Não há usuários cadastrados.")
      return None


def listar_contas(contas):
  print("========== Lista de Contas ==========")
  for i, conta in enumerate(contas, 1):
      if conta.titular:
          print(f"{i}. Titular: {conta.titular.nome}, Saldo: R$ {conta.saldo:.2f}")
      else:
          print(f"{i}. Sem titular associado, Saldo: R$ {conta.saldo:.2f}")


def exibir_menu():
  print("====================================")
  print("======== Banco Pixaqui =========")
  print("====================================")
  print("1. Criar Usuário")
  print("2. Criar Conta Corrente")
  print("3. Depositar")
  print("4. Sacar")
  print("5. Extrato")
  print("6. Listar Contas")
  print("7. Sair")
  print("====================================")


def realizar_deposito(*, saldo, valor, extrato):
  saldo += valor
  print("Depósito realizado com sucesso.")
  return saldo, extrato


def realizar_saque(*, saldo, valor, extrato, limite, numero_saques):
  if saldo - valor >= limite and numero_saques > 0:
      saldo -= valor
      numero_saques -= 1
      print("Saque realizado com sucesso.")
  elif saldo - valor < limite:
      print("Saque não permitido: ultrapassaria o limite.")
  else:
      print("Saque não permitido: número máximo de saques atingido.")
  return saldo, extrato


def exibir_extrato(conta):
  conta.extrato(extrato="Saldo atual", saldo=conta.saldo)


def main():
  print("Bem-vindo ao Banco Pixaqui!")
  usuarios = []
  contas = []

  while True:
      exibir_menu()
      opcao = input("Escolha uma opção (1-7): ")

      if opcao == "1":
          usuario = criar_usuario(usuarios)
          if usuario:
              usuarios.append(usuario)
              print("Usuário criado com sucesso.")
      elif opcao == "2":
          conta = criar_conta_corrente(usuarios)
          if conta:
              contas.append(conta)
      elif opcao == "3":
          if contas:
              valor = float(input("Digite o valor para depósito: "))
              saldo, _ = realizar_deposito(
                  saldo=contas[int(input("Digite o número da conta: ")) - 1].saldo,
                  valor=valor,
                  extrato="Saldo atual"
              )
              contas[int(input("Digite o número da conta: ")) - 1].saldo = saldo
          else:
              print("Não há contas correntes cadastradas.")
      elif opcao == "4":
          if contas:
              valor = float(input("Digite o valor para saque: "))
              saldo, _ = realizar_saque(
                  saldo=contas[int(input("Digite o número da conta: ")) - 1].saldo,
                  valor=valor,
                  extrato="Saldo atual",
                  limite=-1000,  # Defina o limite aqui
                  numero_saques=2  # Defina o número máximo de saques aqui
              )
              contas[int(input("Digite o número da conta: ")) - 1].saldo = saldo
          else:
              print("Não há contas correntes cadastradas.")
      elif opcao == "5":
          if contas:
              exibir_extrato(contas[int(input("Digite o número da conta: ")) - 1])
          else:
              print("Não há contas correntes cadastradas.")
      elif opcao == "6":
          if contas:
              listar_contas(contas)
          else:
              print("Não há contas correntes cadastradas.")
      elif opcao == "7":
          print("Obrigado por usar o Banco Pixaqui! Volte sempre!")
          break
      else:
          print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
  main()
