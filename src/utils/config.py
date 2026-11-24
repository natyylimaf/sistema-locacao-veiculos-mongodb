import os
from time import sleep

# Configuração de conexão MongoDB Atlas
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DATABASE", "LocacaoVeiculos")

# Nomes das coleções no MongoDB Atlas
COLECOES = {
    "clientes": "cliente",
    "locadoras": "locadora",
    "categorias": "categoria",
    "veiculos": "veiculo",
    "funcionarios": "funcionario",
    "alugueis": "aluguel",
    "pagamentos": "pagamento",
}

MENU_PRINCIPAL = """
========== SISTEMA DE LOCAÇÃO DE VEÍCULOS ==========
1 - Relatórios
2 - Inserir registros
3 - Atualizar registros
4 - Remover registros
5 - Sair
"""

MENU_RELATORIOS = """
==================== RELATÓRIOS ====================
1 - Clientes
2 - Locadoras
3 - Categorias
4 - Veículos
5 - Funcionários
6 - Aluguéis
7 - Pagamentos
8 - Faturamento por categoria
0 - Voltar ao menu principal
"""

MENU_ENTIDADES = """
==================== ENTIDADES =====================
1 - Clientes
2 - Locadoras
3 - Categorias
4 - Veículos
5 - Funcionários
6 - Aluguéis (cadastro/status/devolução)
7 - Pagamentos
0 - Voltar ao menu principal
"""


def clear_console(wait_time: float = 0.0) -> None:
    """Limpa o terminal, funcionando tanto no Windows quanto no Linux/macOS."""
    if wait_time > 0:
        sleep(wait_time)
    os.system("cls" if os.name == "nt" else "clear")