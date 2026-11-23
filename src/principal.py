"""Ponto de entrada do Sistema de Locação de Veículos."""

from datetime import date

from pymongo import MongoClient

from controller.controller_aluguel import Controller_Aluguel
from controller.controller_categoria import Controller_Categoria
from controller.controller_cliente import Controller_Cliente
from controller.controller_funcionario import Controller_Funcionario
from controller.controller_locadora import Controller_Locadora
from controller.controller_pagamento import Controller_Pagamento
from controller.controller_veiculo import Controller_Veiculo
from model.aluguel import Aluguel
from model.pagamento import Pagamento
from reports.relatorios import Relatorio
from utils import config
from utils.splash_screen import SplashScreen


tela_inicial = SplashScreen()
relatorio = Relatorio()
ctrl_aluguel = Controller_Aluguel()
ctrl_categoria = Controller_Categoria()
ctrl_cliente = Controller_Cliente()
ctrl_funcionario = Controller_Funcionario()
ctrl_locadora = Controller_Locadora()
ctrl_pagamento = Controller_Pagamento()
ctrl_veiculo = Controller_Veiculo()


def _conectar_mongo():
    uri = getattr(config, "MONGO_URI", "mongodb://localhost:27017/")
    db_name = getattr(config, "MONGO_DB_NAME", "locacao_veiculos")
    client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    return client, client[db_name]


def _ler_inteiro(mensagem: str) -> int:
    """Lê um número inteiro e exibe uma mensagem clara em caso de erro."""
    try:
        return int(input(mensagem).strip())
    except ValueError as erro:
        raise ValueError("Digite um número inteiro válido.") from erro


def _ler_data(mensagem: str, permitir_vazio: bool = False):
    """Lê datas no formato AAAA-MM-DD, usado pelos modelos."""
    texto = input(mensagem).strip()
    if permitir_vazio and not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError as erro:
        raise ValueError(
            "Data inválida. Use o formato AAAA-MM-DD (ex.: 2026-10-28)."
        ) from erro


def _ler_valor(mensagem: str) -> float:
    """Aceita valor decimal com ponto ou vírgula."""
    try:
        return float(
            input(mensagem)
            .strip()
            .replace("R$", "")
            .replace(" ", "")
            .replace(",", ".")
        )
    except ValueError as erro:
        raise ValueError(
            "Digite um valor numérico válido, por exemplo 120,50."
        ) from erro


def _listar_opcoes(
    chave_colecao: str, titulo: str, campos: list[str] | None = None
) -> None:
    """Lista documentos de uma coleção do MongoDB para ajudar no preenchimento."""
    colecoes = getattr(config, "COLECOES", {})
    nome_colecao = colecoes.get(chave_colecao, chave_colecao)
    client = None
    try:
        client, db = _conectar_mongo()
        projecao = {"_id": 0}
        if campos:
            for campo in campos:
                projecao[campo] = 1
        registros = list(db[nome_colecao].find({}, projecao))
        print(f"\n--- {titulo} ---")
        if not registros:
            print("Nenhum registro cadastrado.")
            return
        for registro in registros:
            print(" | ".join(f"{chave}: {valor}" for chave, valor in registro.items()))
    finally:
        if client is not None:
            client.close()


def _executar_com_tratamento(acao) -> None:
    """Evita que um erro de entrada ou do banco encerre o programa inteiro."""
    try:
        acao()
    except KeyboardInterrupt:
        print("\nOperação interrompida.")
    except Exception as erro:
        print(f"\nNão foi possível concluir a operação: {erro}")
    input("\nPressione Enter para continuar...")


def _exibir_lista_entidade(opcao: int) -> None:
    """Exibe os registros cadastrados usando os relatórios antes de solicitar o ID."""
    opcoes_relatorio = {
        1: relatorio.get_relatorio_clientes,
        2: relatorio.get_relatorio_locadoras,
        3: relatorio.get_relatorio_categorias,
        4: relatorio.get_relatorio_veiculos,
        5: relatorio.get_relatorio_funcionarios,
        6: relatorio.get_relatorio_alugueis,
        7: relatorio.get_relatorio_pagamentos,
    }
    acao = opcoes_relatorio.get(opcao)
    if acao:
        print("\n" + "=" * 80)
        print(" REGISTROS CADASTRADOS ".center(80, "="))
        print("=" * 80)
        acao()
        print("=" * 80 + "\n")


def _executar_com_repeticao(acao, mensagem: str, opcao_entidade: int = 0) -> None:
    """Executa uma ação em loop, exibindo a lista da entidade (se aplicável) a cada iteração."""
    while True:
        if opcao_entidade != 0:
            _exibir_lista_entidade(opcao_entidade)

        _executar_com_tratamento(acao)

        resposta = input(f"\n{mensagem} (S/N): ").strip().upper()

        if resposta != "S":
            break


# --------------------------------------------------------------- RELATÓRIOS


def reports(opcao_relatorio: int = 0) -> None:
    opcoes = {
        1: relatorio.get_relatorio_clientes,
        2: relatorio.get_relatorio_locadoras,
        3: relatorio.get_relatorio_categorias,
        4: relatorio.get_relatorio_veiculos,
        5: relatorio.get_relatorio_funcionarios,
        6: relatorio.get_relatorio_alugueis,
        7: relatorio.get_relatorio_pagamentos,
        8: relatorio.get_relatorio_faturamento,
    }
    acao = opcoes.get(opcao_relatorio)
    if acao:
        acao()
    elif opcao_relatorio != 0:
        print("Opção de relatório inválida.")


# --------------------------------------------------------------- ALUGUÉIS


def _novo_aluguel() -> Aluguel:
    _listar_opcoes("clientes", "Clientes", ["id_cliente", "nome", "cpf"])
    id_cliente = _ler_inteiro("ID do cliente: ")

    _listar_opcoes("locadoras", "Locadoras", ["id_locadora", "nome", "cnpj"])
    id_locadora = _ler_inteiro("ID da locadora: ")

    _listar_opcoes(
        "veiculos",
        "Veículos",
        ["id_veiculo", "placa", "marca", "modelo", "valor_diaria"],
    )
    id_veiculo = _ler_inteiro("ID do veículo: ")

    _listar_opcoes(
        "funcionarios",
        "Funcionários",
        ["id_funcionario", "nome", "cargo"],
    )
    id_funcionario = _ler_inteiro("ID do funcionário responsável: ")

    cliente = ctrl_cliente.consultar_cliente(id_cliente)
    locadora = ctrl_locadora.consultar_locadora(id_locadora)
    veiculo = ctrl_veiculo.consultar_veiculo(id_veiculo)
    funcionario = ctrl_funcionario.consultar_funcionario(id_funcionario)
    if any(item is None for item in (cliente, locadora, veiculo, funcionario)):
        raise ValueError(
            "Um dos IDs informados não existe. Confira as listas e tente novamente."
        )

    data_retirada = _ler_data("Data da retirada (AAAA-MM-DD): ")
    data_prevista = _ler_data("Data prevista para devolução (AAAA-MM-DD): ")
    valor_total = _ler_valor("Valor total do aluguel (R$): ")
    status = (
        input("Status [ATIVO/FINALIZADO/CANCELADO] (padrão ATIVO): ")
        .strip()
        .upper()
        or "ATIVO"
    )

    return Aluguel(
        cliente=cliente,
        locadora=locadora,
        veiculo=veiculo,
        funcionario=funcionario,
        data_retirada=data_retirada,
        data_devolucao_prevista=data_prevista,
        data_devolucao_real=None,
        valor_total=valor_total,
        status=status,
    )


def _inserir_aluguel() -> None:
    aluguel = ctrl_aluguel.inserir_aluguel(_novo_aluguel())
    print("Aluguel cadastrado com sucesso!")
    print(aluguel.to_string())


def _atualizar_aluguel() -> None:
    id_aluguel = _ler_inteiro("ID do aluguel: ")
    status = input("Novo status [ATIVO/FINALIZADO/CANCELADO]: ").strip().upper()
    if status == "FINALIZADO":
        data_real = _ler_data("Data real da devolução (AAAA-MM-DD): ")
    else:
        data_real = None
    aluguel = ctrl_aluguel.atualizar_status_aluguel(id_aluguel, status, data_real)
    print("Aluguel atualizado com sucesso!")
    print(aluguel.to_string())


def _excluir_aluguel() -> None:
    id_aluguel = _ler_inteiro("ID do aluguel que deseja excluir: ")

    aluguel = ctrl_aluguel.consultar_aluguel(id_aluguel)
    if aluguel is None:
        raise ValueError("O aluguel informado não existe.")

    print("\nAluguel selecionado:")
    print(aluguel.to_string())

    confirmacao = input("\nConfirma a exclusão deste aluguel? (S/N): ").strip().upper()
    if confirmacao != "S":
        print("Exclusão cancelada.")
        return

    ctrl_aluguel.excluir_aluguel(id_aluguel)
    print("Aluguel excluído com sucesso!")


# -------------------------------------------------------------- PAGAMENTOS


def _inserir_pagamento() -> None:
    print("\n--- Lista de Aluguéis para Pagamento ---")
    relatorio.get_relatorio_alugueis()

    id_aluguel = _ler_inteiro("\nID do aluguel relacionado ao pagamento: ")
    valor = _ler_valor("Valor do pagamento (R$): ")
    data_pagamento = _ler_data("Data do pagamento (AAAA-MM-DD): ")
    metodo = (
        input("Método [DINHEIRO/PIX/CARTAO_CREDITO/CARTAO_DEBITO]: ")
        .strip()
        .upper()
    )
    status = input("Status [PENDENTE/PAGO/CANCELADO]: ").strip().upper()

    pagamento = Pagamento(
        aluguel=Aluguel(id_aluguel=id_aluguel),
        valor=valor,
        data_pagamento=data_pagamento,
        metodo=metodo,
        status=status,
    )
    pagamento_criado = ctrl_pagamento.inserir_pagamento(pagamento)
    print("Pagamento cadastrado com sucesso!")
    print(pagamento_criado.to_string())


def _atualizar_pagamento() -> None:
    id_pagamento = _ler_inteiro("ID do pagamento que deseja atualizar: ")
    id_aluguel = _ler_inteiro("ID do aluguel relacionado ao pagamento: ")
    valor = _ler_valor("Novo valor (R$): ")
    data_pagamento = _ler_data("Nova data (AAAA-MM-DD): ")
    metodo = (
        input("Novo método [DINHEIRO/PIX/CARTAO_CREDITO/CARTAO_DEBITO]: ")
        .strip()
        .upper()
    )
    status = input("Novo status [PENDENTE/PAGO/CANCELADO]: ").strip().upper()

    pagamento = ctrl_pagamento.atualizar_pagamento(
        id_pagamento, id_aluguel, valor, data_pagamento, metodo, status
    )
    print("Pagamento atualizado com sucesso!")
    print(pagamento.to_string())


def _excluir_pagamento() -> None:
    id_pagamento = _ler_inteiro("ID do pagamento que deseja excluir: ")
    id_aluguel = _ler_inteiro("ID do aluguel relacionado ao pagamento: ")

    pagamento = ctrl_pagamento.consultar_pagamento(id_pagamento, id_aluguel)

    if pagamento is None:
        raise ValueError("Não foi encontrado um pagamento com os IDs informados.")

    print("\nPagamento selecionado:")
    print(pagamento.to_string())

    confirmacao = (
        input("\nConfirma a exclusão deste pagamento? (S/N): ").strip().upper()
    )

    if confirmacao != "S":
        print("Exclusão cancelada.")
        return

    ctrl_pagamento.excluir_pagamento(id_pagamento, id_aluguel)
    print("Pagamento excluído com sucesso!")


# --------------------------------------------------------------- INSERIR


def inserir(opcao_inserir: int = 0) -> None:
    opcoes = {
        1: ctrl_cliente.inserir_cliente,
        2: ctrl_locadora.inserir_locadora,
        3: ctrl_categoria.inserir_categoria,
        4: ctrl_veiculo.inserir_veiculo,
        5: ctrl_funcionario.inserir_funcionario,
        6: _inserir_aluguel,
        7: _inserir_pagamento,
    }

    acao = opcoes.get(opcao_inserir)

    if acao:
        _executar_com_repeticao(
            acao,
            "Deseja cadastrar outro registro desta entidade?",
            0,
        )
    elif opcao_inserir != 0:
        print("Opção de cadastro inválida.")


# -------------------------------------------------------------- ATUALIZAR


def atualizar(opcao_atualizar: int = 0) -> None:
    opcoes = {
        1: ctrl_cliente.atualizar_cliente,
        2: ctrl_locadora.atualizar_locadora,
        3: ctrl_categoria.atualizar_categoria,
        4: ctrl_veiculo.atualizar_veiculo,
        5: ctrl_funcionario.atualizar_funcionario,
        6: _atualizar_aluguel,
        7: _atualizar_pagamento,
    }

    acao = opcoes.get(opcao_atualizar)

    if acao:
        _executar_com_repeticao(
            acao,
            "Deseja atualizar outro registro desta entidade?",
            opcao_atualizar,
        )
    elif opcao_atualizar != 0:
        print("Opção de atualização inválida.")


# ---------------------------------------------------------------- REMOVER


def excluir(opcao_excluir: int = 0) -> None:
    opcoes = {
        1: ctrl_cliente.excluir_cliente,
        2: ctrl_locadora.excluir_locadora,
        3: ctrl_categoria.excluir_categoria,
        4: ctrl_veiculo.excluir_veiculo,
        5: ctrl_funcionario.excluir_funcionario,
        6: _excluir_aluguel,
        7: _excluir_pagamento,
    }

    acao = opcoes.get(opcao_excluir)

    if acao:
        _executar_com_repeticao(
            acao,
            "Deseja excluir outro registro desta entidade?",
            opcao_excluir,
        )
    elif opcao_excluir != 0:
        print("Opção de remoção inválida.")


def _ler_opcao(mensagem: str, minimo: int, maximo: int) -> int:
    opcao = _ler_inteiro(mensagem)
    if not minimo <= opcao <= maximo:
        raise ValueError(f"Escolha uma opção entre {minimo} e {maximo}.")
    return opcao


def run() -> None:
    print(tela_inicial.get_updated_screen())
    if any(valor is None for valor in tela_inicial.get_totais().values()):
        print("\nAviso: não foi possível ler as contagens do MongoDB.")
        print("Confira o serviço do MongoDB e as variáveis MONGO_URI / MONGO_DB_NAME.")
    input("\nPressione Enter para abrir o menu principal...")

    while True:
        config.clear_console()
        print(config.MENU_PRINCIPAL)
        try:
            opcao = _ler_opcao("Escolha uma opção [1-5]: ", 1, 5)
        except ValueError as erro:
            print(erro)
            input("\nPressione Enter para tentar novamente...")
            continue

        if opcao == 1:
            config.clear_console()
            print(config.MENU_RELATORIOS)
            try:
                opcao_relatorio = _ler_opcao("Escolha uma opção [0-8]: ", 0, 8)
                if opcao_relatorio != 0:
                    try:
                        reports(opcao_relatorio)
                    except Exception as erro:
                        print(f"\nNão foi possível gerar o relatório: {erro}")
                        input("\nPressione Enter para continuar...")
            except ValueError as erro:
                print(erro)
                input("\nPressione Enter para continuar...")

        elif opcao in (2, 3, 4):
            config.clear_console()
            print(config.MENU_ENTIDADES)
            operacao = {2: inserir, 3: atualizar, 4: excluir}[opcao]
            try:
                escolha = _ler_opcao("Escolha uma entidade [0-7]: ", 0, 7)
                if escolha != 0:
                    operacao(escolha)
            except ValueError as erro:
                print(erro)
                input("\nPressione Enter para continuar...")

        elif opcao == 5:
            print("Obrigado por utilizar o Sistema de Locação de Veículos!")
            break


if __name__ == "__main__":
    run()