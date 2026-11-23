from pymongo import MongoClient
from utils import config


class SplashScreen:
    # (rótulo_exibicao, chave_em_config_COLECOES)
    COLECOES_EXIBICAO = (
        ("clientes", "clientes"),
        ("locadoras", "locadoras"),
        ("categorias", "categorias"),
        ("veículos", "veiculos"),
        ("funcionários", "funcionarios"),
        ("aluguéis", "alugueis"),
        ("pagamentos", "pagamentos"),
    )

    def __init__(self, uri: str = None, db_name: str = None):
        self.uri = uri or config.MONGO_URI
        self.db_name = db_name or config.MONGO_DB_NAME
        self.created_by = (
            "Walisson Pastori, Nathália Lima, Davi Pitangui, "
            "Gabriel Modesto e Bryan Nascimento"
        )
        self.professor = "Howard Roatti"
        self.disciplina = "Banco de Dados"
        self.semestre = "2026/2"

    def _conectar(self):
        client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
        return client, client[self.db_name]

    def _contar_colecao(self, chave_colecao: str):
        nome_colecao = config.COLECOES[chave_colecao]
        client = None
        try:
            client, db = self._conectar()
            return db[nome_colecao].count_documents({})
        except Exception:
            return None
        finally:
            if client is not None:
                client.close()

    def get_totais(self) -> dict:
        """Consulta a quantidade de documentos de cada coleção no MongoDB."""
        totais = {}
        for rotulo, chave in self.COLECOES_EXIBICAO:
            totais[rotulo] = self._contar_colecao(chave)
        return totais

    # Métodos mantidos para compatibilidade com o projeto
    def get_total_clientes(self):
        return self._contar_colecao("clientes")

    def get_total_locadoras(self):
        return self._contar_colecao("locadoras")

    def get_total_categorias(self):
        return self._contar_colecao("categorias")

    def get_total_veiculos(self):
        return self._contar_colecao("veiculos")

    def get_total_funcionarios(self):
        return self._contar_colecao("funcionarios")

    def get_total_alugueis(self):
        return self._contar_colecao("alugueis")

    def get_total_pagamentos(self):
        return self._contar_colecao("pagamentos")

    def get_updated_screen(self) -> str:
        totais = self.get_totais()

        def formatar(nome: str) -> str:
            valor = totais.get(nome)
            return "N/D" if valor is None else str(valor)

        largura = 62
        borda = "#" * (largura + 2)

        def linha(texto=""):
            return f"#{texto:<{largura}}#"

        return "\n".join([
            borda,
            linha("SISTEMA DE LOCAÇÃO DE VEÍCULOS".center(largura)),
            linha(),
            linha("  TOTAL DE DOCUMENTOS EXISTENTES"),
            linha(f"    Clientes:      {formatar('clientes'):>6}"),
            linha(f"    Locadoras:     {formatar('locadoras'):>6}"),
            linha(f"    Categorias:    {formatar('categorias'):>6}"),
            linha(f"    Veículos:      {formatar('veículos'):>6}"),
            linha(f"    Funcionários:  {formatar('funcionários'):>6}"),
            linha(f"    Aluguéis:      {formatar('aluguéis'):>6}"),
            linha(f"    Pagamentos:    {formatar('pagamentos'):>6}"),
            linha(),
            linha("  CRIADO POR:"),
            linha("  Bryan Monteiro, Davi Pitangui,"),
            linha("  Gabryel Modesto, Nathália Lima e"),
            linha("  Walisson Pastori"),
            linha(),
            linha(f"  Disciplina: {self.disciplina}"),
            linha(f"              {self.semestre}"),
            linha(f"  Professor:  {self.professor}"),
            borda,
        ])