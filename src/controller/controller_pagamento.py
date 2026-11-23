from datetime import date, datetime, time, timezone
from decimal import Decimal
from bson.decimal128 import Decimal128

from conexion.mongo_queries import MongoQueries
from model.pagamento import Pagamento
from model.aluguel import Aluguel


class Controller_Pagamento:
    """Controlador de Pagamento adaptado para MongoDB."""

    @staticmethod
    def _to_datetime(valor):
        if valor is None:
            return None
        if isinstance(valor, datetime):
            if valor.tzinfo is None:
                return valor.replace(tzinfo=timezone.utc)
            return valor.astimezone(timezone.utc)
        if isinstance(valor, date):
            return datetime.combine(valor, time.min, tzinfo=timezone.utc)
        return valor

    @staticmethod
    def _to_date(valor):
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor.date()
        return valor

    @staticmethod
    def _to_decimal128(valor) -> Decimal128:
        return Decimal128(Decimal(str(valor)))

    @staticmethod
    def _to_float(valor) -> float:
        if valor is None:
            return None
        if isinstance(valor, Decimal128):
            return float(valor.to_decimal())
        return float(valor)

    @staticmethod
    def _proximo_id(mongo: MongoQueries) -> int:
        ultimo = mongo.db["pagamento"].find_one(sort=[("id_pagamento", -1)])
        return (int(ultimo["id_pagamento"]) + 1) if ultimo else 1

    def _pagamento_from_doc(self, doc: dict):
        if doc is None:
            return None
        aluguel = Aluguel(id_aluguel=doc["id_aluguel"])
        return Pagamento(
            doc["id_pagamento"],
            aluguel,
            self._to_float(doc["valor"]),
            self._to_date(doc["data_pagamento"]),
            doc["metodo"],
            doc["status"],
        )

    def verifica_existencia_pagamento(
        self,
        mongo: MongoQueries,
        id_pagamento: int,
        id_aluguel: int = None,
    ) -> bool:
        filtro = {"id_pagamento": id_pagamento}
        if id_aluguel is not None:
            filtro["id_aluguel"] = id_aluguel
        return mongo.db["pagamento"].count_documents(filtro, limit=1) > 0

    def consultar_pagamento(self, id_pagamento: int, id_aluguel: int = None):
        mongo = MongoQueries()
        try:
            mongo.connect()
            filtro = {"id_pagamento": id_pagamento}
            if id_aluguel is not None:
                filtro["id_aluguel"] = id_aluguel
            doc = mongo.db["pagamento"].find_one(filtro)
            return self._pagamento_from_doc(doc)
        finally:
            mongo.close()

    def listar_pagamentos(self, id_aluguel: int = None):
        mongo = MongoQueries()
        try:
            mongo.connect()
            filtro = {"id_aluguel": id_aluguel} if id_aluguel is not None else {}
            docs = list(
                mongo.db["pagamento"].find(filtro).sort([("id_aluguel", 1), ("id_pagamento", 1)])
            )
            return [self._pagamento_from_doc(doc) for doc in docs]
        finally:
            mongo.close()

    def inserir_pagamento(self, pagamento: Pagamento):
        if pagamento is None or pagamento.get_aluguel() is None:
            raise ValueError("É necessário informar o aluguel do pagamento.")

        if pagamento.get_valor() is None or float(pagamento.get_valor()) <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")

        data_pagamento = pagamento.get_data_pagamento()
        metodo = pagamento.get_metodo()
        status = pagamento.get_status()

        if data_pagamento is None:
            raise ValueError("A data do pagamento é obrigatória.")

        if not isinstance(metodo, str) or not metodo.strip():
            raise ValueError("O método do pagamento é obrigatório.")

        if not isinstance(status, str) or not status.strip():
            raise ValueError("O status do pagamento é obrigatório.")

        metodo = metodo.strip().upper()
        status = status.strip().upper()

        metodos_validos = {"DINHEIRO", "PIX", "CARTAO_CREDITO", "CARTAO_DEBITO"}
        status_validos = {"PENDENTE", "PAGO", "CANCELADO"}

        if metodo not in metodos_validos:
            raise ValueError(
                "Método inválido. Use DINHEIRO, PIX, CARTAO_CREDITO ou CARTAO_DEBITO."
            )

        if status not in status_validos:
            raise ValueError("Status inválido. Use PENDENTE, PAGO ou CANCELADO.")

        id_aluguel = pagamento.get_aluguel().get_id_aluguel()

        mongo = MongoQueries()
        try:
            mongo.connect()

            # Valida o relacionamento: o aluguel precisa existir antes de criar o pagamento
            if mongo.db["aluguel"].count_documents({"id_aluguel": id_aluguel}, limit=1) == 0:
                raise ValueError(f"O aluguel {id_aluguel} não existe.")

            novo_id = self._proximo_id(mongo)
            documento = {
                "id_pagamento": novo_id,
                "id_aluguel": id_aluguel,
                "valor": self._to_decimal128(pagamento.get_valor()),
                "data_pagamento": self._to_datetime(data_pagamento),
                "metodo": metodo,
                "status": status,
            }

            mongo.db["pagamento"].insert_one(documento)
            return self._pagamento_from_doc(documento)
        finally:
            mongo.close()

    def atualizar_pagamento(
        self,
        id_pagamento: int,
        id_aluguel: int,
        valor: float,
        data_pagamento,
        metodo: str,
        status: str,
    ):
        if valor is None or float(valor) <= 0:
            raise ValueError("O valor do pagamento deve ser maior que zero.")

        if data_pagamento is None:
            raise ValueError("A data do pagamento é obrigatória.")

        if not isinstance(metodo, str) or not metodo.strip():
            raise ValueError("O método do pagamento é obrigatório.")

        if not isinstance(status, str) or not status.strip():
            raise ValueError("O status do pagamento é obrigatório.")

        metodo = metodo.strip().upper()
        status = status.strip().upper()

        metodos_validos = {"DINHEIRO", "PIX", "CARTAO_CREDITO", "CARTAO_DEBITO"}
        status_validos = {"PENDENTE", "PAGO", "CANCELADO"}

        if metodo not in metodos_validos:
            raise ValueError(
                "Método inválido. Use DINHEIRO, PIX, CARTAO_CREDITO ou CARTAO_DEBITO."
            )

        if status not in status_validos:
            raise ValueError("Status inválido. Use PENDENTE, PAGO ou CANCELADO.")

        mongo = MongoQueries()
        try:
            mongo.connect()

            if not self.verifica_existencia_pagamento(mongo, id_pagamento, id_aluguel):
                raise ValueError("O pagamento informado não existe.")

            mongo.db["pagamento"].update_one(
                {"id_pagamento": id_pagamento, "id_aluguel": id_aluguel},
                {
                    "$set": {
                        "valor": self._to_decimal128(valor),
                        "data_pagamento": self._to_datetime(data_pagamento),
                        "metodo": metodo,
                        "status": status,
                    }
                },
            )

            doc_atualizado = mongo.db["pagamento"].find_one(
                {"id_pagamento": id_pagamento, "id_aluguel": id_aluguel}
            )
            return self._pagamento_from_doc(doc_atualizado)
        finally:
            mongo.close()

    def excluir_pagamento(self, id_pagamento: int, id_aluguel: int):
        mongo = MongoQueries()
        try:
            mongo.connect()

            if not self.verifica_existencia_pagamento(mongo, id_pagamento, id_aluguel):
                raise ValueError("O pagamento informado não existe.")

            mongo.db["pagamento"].delete_one(
                {"id_pagamento": id_pagamento, "id_aluguel": id_aluguel}
            )
        finally:
            mongo.close()

        return True
