"""Relatórios do Sistema de Locação de Veículos (MongoDB)."""

from pymongo import MongoClient
from utils import config


class Relatorio:
    def __init__(self, uri: str = None, db_name: str = None):
        self.uri = uri or config.MONGO_URI
        self.db_name = db_name or config.MONGO_DB_NAME

    def _conectar(self):
        client = MongoClient(self.uri, serverSelectionTimeoutMS=3000)
        return client, client[self.db_name]

    @staticmethod
    def _exibir_documentos(titulo: str, registros: list, pausar: bool = True) -> None:
        print(f"\n--- {titulo} ---")
        if not registros:
            print("Nenhum registro encontrado.")
        else:
            for idx, doc in enumerate(registros, start=1):
                limpo = {k: v for k, v in doc.items() if k != "_id"}
                linha = " | ".join(f"{chave}: {valor}" for chave, valor in limpo.items())
                print(f"{idx}. {linha}")
        if pausar:
            input(f"\nPressione Enter para sair do relatório de {titulo.lower()}...")

    def _listar_colecao(
        self,
        chave_colecao: str,
        titulo: str,
        pausar: bool = True
    ) -> None:
        nome_colecao = config.COLECOES[chave_colecao]

        # Define o campo de identificação de cada coleção.
        campos_id = {
            "clientes": "id_cliente",
            "locadoras": "id_locadora",
            "categorias": "id_categoria",
            "veiculos": "id_veiculo",
            "funcionarios": "id_funcionario",
            "pagamentos": "id_pagamento",
        }

        campo_id = campos_id[chave_colecao]

        # Não permite que a senha dos funcionários apareça no relatório.
        projecao = {"senha": 0} if chave_colecao == "funcionarios" else None

        client = None
        try:
            client, db = self._conectar()

            registros = list(
                db[nome_colecao]
                .find({}, projecao)
                .sort(campo_id, 1)
            )

            self._exibir_documentos(titulo, registros, pausar=pausar)

        finally:
            if client is not None:
                client.close()

    def get_relatorio_clientes(self):
        self._listar_colecao("clientes", "Clientes")

    def get_relatorio_locadoras(self):
        self._listar_colecao("locadoras", "Locadoras")

    def get_relatorio_veiculos(self):
        self._listar_colecao("veiculos", "Veículos")

    def get_relatorio_funcionarios(self):
        self._listar_colecao("funcionarios", "Funcionários")

    def get_relatorio_categorias(self, pausar: bool = True):
        self._listar_colecao("categorias", "Categorias", pausar=pausar)

    def get_relatorio_pagamentos(self):
        self._listar_colecao("pagamentos", "Pagamentos")

    def get_relatorio_alugueis(self):
        """Relatório de aluguéis utilizando $lookup para relacionar as coleções."""
        client = None
        try:
            client, db = self._conectar()
            col_alugueis = config.COLECOES["alugueis"]
            col_clientes = config.COLECOES["clientes"]
            col_locadoras = config.COLECOES["locadoras"]
            col_veiculos = config.COLECOES["veiculos"]
            col_funcionarios = config.COLECOES["funcionarios"]

            pipeline = [
                {
                    "$lookup": {
                        "from": col_clientes,
                        "localField": "id_cliente",
                        "foreignField": "id_cliente",
                        "as": "cliente_doc",
                    }
                },
                {"$unwind": {"path": "$cliente_doc", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": col_locadoras,
                        "localField": "id_locadora",
                        "foreignField": "id_locadora",
                        "as": "locadora_doc",
                    }
                },
                {"$unwind": {"path": "$locadora_doc", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": col_veiculos,
                        "localField": "id_veiculo",
                        "foreignField": "id_veiculo",
                        "as": "veiculo_doc",
                    }
                },
                {"$unwind": {"path": "$veiculo_doc", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": col_funcionarios,
                        "localField": "id_funcionario",
                        "foreignField": "id_funcionario",
                        "as": "funcionario_doc",
                    }
                },
                {"$unwind": {"path": "$funcionario_doc", "preserveNullAndEmptyArrays": True}},
                {
                    "$project": {
                        "_id": 0,
                        "id_aluguel": 1,
                        "nome_cliente": "$cliente_doc.nome",
                        "nome_locadora": "$locadora_doc.nome",
                        "marca": "$veiculo_doc.marca",
                        "modelo": "$veiculo_doc.modelo",
                        "nome_funcionario": "$funcionario_doc.nome",
                        "data_retirada": 1,
                        "data_devolucao_prevista": 1,
                        "data_devolucao_real": {
                            "$ifNull": ["$data_devolucao_real", "Não devolvido"]
                        },
                        "valor_total": 1,
                        "status": 1,
                    }
                },
                {"$sort": {"id_aluguel": 1}},
            ]

            resultados = list(db[col_alugueis].aggregate(pipeline))
            self._exibir_documentos("Aluguéis", resultados)
        finally:
            if client is not None:
                client.close()

    def get_relatorio_faturamento(self):
        """Faturamento por categoria utilizando agregação com $group e$sum."""
        client = None
        try:
            client, db = self._conectar()
            col_alugueis = config.COLECOES["alugueis"]
            col_veiculos = config.COLECOES["veiculos"]
            col_categorias = config.COLECOES["categorias"]

            pipeline = [
                {"$match": {"status": {"$ne": "CANCELADO"}}},
                {
                    "$lookup": {
                        "from": col_veiculos,
                        "localField": "id_veiculo",
                        "foreignField": "id_veiculo",
                        "as": "veiculo_doc",
                    }
                },
                {"$unwind": "$veiculo_doc"},
                {
                    "$lookup": {
                        "from": col_categorias,
                        "localField": "veiculo_doc.id_categoria",
                        "foreignField": "id_categoria",
                        "as": "categoria_doc",
                    }
                },
                {"$unwind": "$categoria_doc"},
                {
                    "$group": {
                        "_id": "$categoria_doc.nome",
                        "total_alugueis": {"$sum": 1},
                        "faturamento": {"$sum": "$valor_total"},
                        "ticket_medio": {"$avg": "$valor_total"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "categoria": "$_id",
                        "total_alugueis": 1,
                        "faturamento": {"$round": ["$faturamento", 2]},
                        "ticket_medio": {"$round": ["$ticket_medio", 2]},
                    }
                },
                {"$sort": {"faturamento": -1}},
            ]

            resultados = list(db[col_alugueis].aggregate(pipeline))
            self._exibir_documentos("Faturamento por categoria", resultados)
        finally:
            if client is not None:
                client.close()