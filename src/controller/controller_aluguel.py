from datetime import date, datetime, time, timezone
from decimal import Decimal
from bson.decimal128 import Decimal128

from conexion.mongo_queries import MongoQueries
from model.aluguel import Aluguel
from model.cliente import Cliente
from model.locadora import Locadora
from model.veiculo import Veiculo
from model.categoria import Categoria
from model.funcionario import Funcionario


class Controller_Aluguel:

    @staticmethod
    def _to_datetime(valor):
        """Converte date/datetime para datetime UTC exigido pelo validador BSON."""
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
        """Converte datetime vindo do MongoDB de volta para date."""
        if valor is None:
            return None
        if isinstance(valor, datetime):
            return valor.date()
        return valor

    @staticmethod
    def _to_decimal128(valor) -> Decimal128:
        """Converte número para Decimal128 exigido pelo validador BSON."""
        return Decimal128(Decimal(str(valor)))

    @staticmethod
    def _to_float(valor) -> float:
        """Converte Decimal128 ou numérico para float Python."""
        if valor is None:
            return None
        if isinstance(valor, Decimal128):
            return float(valor.to_decimal())
        return float(valor)

    @staticmethod
    def _proximo_id(mongo: MongoQueries) -> int:
        """Gera o próximo id_aluguel inteiro sequencial."""
        ultimo = mongo.db["aluguel"].find_one(sort=[("id_aluguel", -1)])
        return (int(ultimo["id_aluguel"]) + 1) if ultimo else 1

    def _montar_aluguel(self, mongo: MongoQueries, doc: dict):
        """Reconstrói o objeto Aluguel completo buscando os documentos relacionados."""
        if doc is None:
            return None

        cliente_doc = mongo.db["cliente"].find_one({"id_cliente": doc["id_cliente"]})
        locadora_doc = mongo.db["locadora"].find_one({"id_locadora": doc["id_locadora"]})
        veiculo_doc = mongo.db["veiculo"].find_one({"id_veiculo": doc["id_veiculo"]})
        funcionario_doc = mongo.db["funcionario"].find_one({"id_funcionario": doc["id_funcionario"]})

        cliente = None
        if cliente_doc:
            cliente = Cliente(
                cliente_doc["id_cliente"],
                cliente_doc["nome"],
                cliente_doc["cpf"],
                cliente_doc["telefone"],
                cliente_doc["email"],
            )

        locadora = None
        if locadora_doc:
            locadora = Locadora(
                locadora_doc["id_locadora"],
                locadora_doc["nome"],
                locadora_doc["cnpj"],
                locadora_doc["telefone"],
                locadora_doc["email"],
            )

        veiculo = None
        if veiculo_doc:
            categoria_doc = mongo.db["categoria"].find_one(
                {"id_categoria": veiculo_doc["id_categoria"]}
            )
            categoria = None
            if categoria_doc:
                categoria = Categoria(
                    categoria_doc["id_categoria"],
                    categoria_doc["nome"],
                    categoria_doc["descricao"],
                )
            veiculo = Veiculo(
                veiculo_doc["id_veiculo"],
                categoria,
                veiculo_doc["placa"],
                veiculo_doc["marca"],
                veiculo_doc["modelo"],
                veiculo_doc["ano"],
                self._to_float(veiculo_doc["valor_diaria"]),
            )

        funcionario = None
        if funcionario_doc:
            funcionario = Funcionario(
                funcionario_doc["id_funcionario"],
                funcionario_doc["email"],
                None,
                funcionario_doc["nome"],
                funcionario_doc["cpf"],
                funcionario_doc["telefone"],
                funcionario_doc["cargo"],
            )

        return Aluguel(
            doc["id_aluguel"],
            cliente,
            locadora,
            veiculo,
            funcionario,
            self._to_date(doc["data_retirada"]),
            self._to_date(doc["data_devolucao_prevista"]),
            self._to_date(doc.get("data_devolucao_real")),
            self._to_float(doc["valor_total"]),
            doc["status"],
        )

    def verifica_existencia_aluguel(self, mongo: MongoQueries, id_aluguel: int) -> bool:
        return mongo.db["aluguel"].count_documents({"id_aluguel": id_aluguel}, limit=1) > 0

    def consultar_aluguel(self, id_aluguel: int):
        mongo = MongoQueries()
        try:
            mongo.connect()
            doc = mongo.db["aluguel"].find_one({"id_aluguel": id_aluguel})
            return self._montar_aluguel(mongo, doc)
        finally:
            mongo.close()

    def listar_alugueis(self):
        mongo = MongoQueries()
        try:
            mongo.connect()
            docs = list(mongo.db["aluguel"].find().sort("id_aluguel", 1))
            return [self._montar_aluguel(mongo, doc) for doc in docs]
        finally:
            mongo.close()

    def inserir_aluguel(self, aluguel: Aluguel):
        """Insere um aluguel no MongoDB a partir do objeto Aluguel já preenchido."""
        if aluguel is None or any((
            aluguel.get_cliente() is None,
            aluguel.get_locadora() is None,
            aluguel.get_veiculo() is None,
            aluguel.get_funcionario() is None,
            aluguel.get_data_retirada() is None,
            aluguel.get_data_devolucao_prevista() is None,
            aluguel.get_valor_total() is None,
            not aluguel.get_status(),
        )):
            raise ValueError("Preencha cliente, locadora, veículo, funcionário, datas, valor e status.")

        if aluguel.get_data_devolucao_prevista() < aluguel.get_data_retirada():
            raise ValueError("A devolução prevista não pode ser anterior à retirada.")

        if float(aluguel.get_valor_total()) < 0:
            raise ValueError("O valor total não pode ser negativo.")

        status = aluguel.get_status().strip().upper()
        if status not in {"ATIVO", "FINALIZADO", "CANCELADO"}:
            raise ValueError("Status inválido. Use ATIVO, FINALIZADO ou CANCELADO.")

        id_cliente = aluguel.get_cliente().get_id_cliente()
        id_locadora = aluguel.get_locadora().get_id_locadora()
        id_veiculo = aluguel.get_veiculo().get_id_veiculo()
        id_funcionario = aluguel.get_funcionario().get_id_funcionario()

        mongo = MongoQueries()
        try:
            mongo.connect()

            # Valida os 4 relacionamentos antes de inserir (integridade referencial)
            checks = (
                ("cliente", "id_cliente", id_cliente),
                ("locadora", "id_locadora", id_locadora),
                ("veiculo", "id_veiculo", id_veiculo),
                ("funcionario", "id_funcionario", id_funcionario),
            )
            for colecao, campo, valor in checks:
                if mongo.db[colecao].count_documents({campo: valor}, limit=1) == 0:
                    raise ValueError(f"Não existe registro em {colecao} com {campo}={valor}.")

            novo_id = self._proximo_id(mongo)
            documento = {
                "id_aluguel": novo_id,
                "id_cliente": id_cliente,
                "id_locadora": id_locadora,
                "id_veiculo": id_veiculo,
                "id_funcionario": id_funcionario,
                "data_retirada": self._to_datetime(aluguel.get_data_retirada()),
                "data_devolucao_prevista": self._to_datetime(aluguel.get_data_devolucao_prevista()),
                "data_devolucao_real": self._to_datetime(aluguel.get_data_devolucao_real()),
                "valor_total": self._to_decimal128(aluguel.get_valor_total()),
                "status": status,
            }

            mongo.db["aluguel"].insert_one(documento)
            return self._montar_aluguel(mongo, documento)
        finally:
            mongo.close()

    def atualizar_status_aluguel(
        self,
        id_aluguel: int,
        status: str,
        data_devolucao_real: date = None
    ):
        """Atualiza o status e a data real de devolução do aluguel."""
        if not status or status.strip().upper() not in {"ATIVO", "FINALIZADO", "CANCELADO"}:
            raise ValueError("Status inválido. Use ATIVO, FINALIZADO ou CANCELADO.")

        status = status.strip().upper()

        mongo = MongoQueries()
        try:
            mongo.connect()

            doc = mongo.db["aluguel"].find_one({"id_aluguel": id_aluguel})
            if doc is None:
                raise ValueError(f"O aluguel {id_aluguel} não existe.")

            if status == "FINALIZADO" and data_devolucao_real is None:
                raise ValueError("Informe a data real de devolução para finalizar o aluguel.")

            data_retirada = self._to_date(doc["data_retirada"])
            if data_devolucao_real is not None and self._to_date(data_devolucao_real) < data_retirada:
                raise ValueError("A data real de devolução não pode ser anterior à retirada.")

            mongo.db["aluguel"].update_one(
                {"id_aluguel": id_aluguel},
                {
                    "$set": {
                        "status": status,
                        "data_devolucao_real": self._to_datetime(data_devolucao_real),
                    }
                },
            )

            doc_atualizado = mongo.db["aluguel"].find_one({"id_aluguel": id_aluguel})
            return self._montar_aluguel(mongo, doc_atualizado)
        finally:
            mongo.close()

    def excluir_aluguel(self, id_aluguel: int):
        mongo = MongoQueries()
        try:
            mongo.connect()

            if not self.verifica_existencia_aluguel(mongo, id_aluguel):
                raise ValueError(f"O aluguel {id_aluguel} não existe.")

            # Preserva a regra de negócio: bloqueia exclusão se houver pagamento vinculado
            if mongo.db["pagamento"].count_documents({"id_aluguel": id_aluguel}, limit=1) > 0:
                raise ValueError(
                    "Não é possível excluir este aluguel, "
                    "pois existem pagamentos vinculados a ele."
                )

            mongo.db["aluguel"].delete_one({"id_aluguel": id_aluguel})
        finally:
            mongo.close()

        return True
