from decimal import Decimal
from bson.decimal128 import Decimal128
from pymongo import ASCENDING, DESCENDING
from model.veiculo import Veiculo
from model.categoria import Categoria
from conexion.mongo_queries import MongoQueries


class Controller_Veiculo:
    """Controlador CRUD de Veiculo migrado para MongoDB."""

    @staticmethod
    def _to_float(valor) -> float:
        if isinstance(valor, Decimal128):
            return float(valor.to_decimal())
        return float(valor)

    @staticmethod
    def _to_decimal128(valor: float) -> Decimal128:
        return Decimal128(Decimal(f"{valor:.2f}"))

    @staticmethod
    def _exibir_categorias(mongo: MongoQueries):
        categorias = list(mongo.db["categoria"].find().sort("id_categoria", ASCENDING))
        print("\nCategorias disponíveis:")
        for cat in categorias:
            print(f"  [{cat['id_categoria']}] {cat['nome']} - {cat.get('descricao', '')}")

    @staticmethod
    def _listar_veiculos(mongo: MongoQueries) -> bool:
        veiculos = list(
            mongo.db["veiculo"].find().sort("id_veiculo", ASCENDING)
        )

        if not veiculos:
            print("\nNenhum veículo cadastrado.")
            return False

        print("\n========== VEÍCULOS CADASTRADOS ==========")

        for doc in veiculos:
            print(
                f"ID: {doc['id_veiculo']} | "
                f"Placa: {doc['placa']} | "
                f"Marca: {doc['marca']} | "
                f"Modelo: {doc['modelo']} | "
                f"Ano: {doc['ano']} | "
                f"Valor diária: R$ {Controller_Veiculo._to_float(doc['valor_diaria']):.2f} | "
                f"Categoria: {doc['id_categoria']}"
            )

        print("==========================================")
        return True

    def _from_doc(self, mongo: MongoQueries, doc: dict):
        if doc is None:
            return None

        cat_doc = mongo.db["categoria"].find_one({"id_categoria": doc["id_categoria"]})
        if cat_doc:
            categoria = Categoria(
                cat_doc["id_categoria"],
                cat_doc["nome"],
                cat_doc["descricao"],
            )
        else:
            categoria = Categoria(doc["id_categoria"], "Desconhecida", "")

        return Veiculo(
            doc["id_veiculo"],
            categoria,
            doc["placa"],
            doc["marca"],
            doc["modelo"],
            doc["ano"],
            self._to_float(doc["valor_diaria"]),
        )

    def _proximo_id(self, mongo: MongoQueries) -> int:
        ultimo = mongo.db["veiculo"].find_one(sort=[("id_veiculo", DESCENDING)])
        return (ultimo["id_veiculo"] + 1) if ultimo and "id_veiculo" in ultimo else 1

    def verifica_existencia_veiculo(self, mongo: MongoQueries, id_veiculo: int) -> bool:
        return mongo.db["veiculo"].find_one({"id_veiculo": id_veiculo}) is not None

    def verifica_existencia_categoria(self, mongo: MongoQueries, id_categoria: int) -> bool:
        return mongo.db["categoria"].find_one({"id_categoria": id_categoria}) is not None

    def consultar_veiculo(self, id_veiculo: int):
        mongo = MongoQueries()
        try:
            mongo.connect()
            doc = mongo.db["veiculo"].find_one({"id_veiculo": id_veiculo})
            return self._from_doc(mongo, doc)
        finally:
            mongo.close()

    def listar_veiculos(self):
        mongo = MongoQueries()
        try:
            mongo.connect()
            docs = mongo.db["veiculo"].find().sort("id_veiculo", ASCENDING)
            return [self._from_doc(mongo, doc) for doc in docs]
        finally:
            mongo.close()

    def inserir_veiculo(self) -> Veiculo:
        placa = input("Placa: ").strip().upper()
        marca = input("Marca: ").strip()
        modelo = input("Modelo: ").strip()
        try:
            ano = int(input("Ano: ").strip())
            valor_diaria = float(input("Valor da diária: R$ ").strip().replace(",", "."))
        except ValueError:
            print("Ano e valor da diária devem ser numéricos.")
            return None

        if not all((placa, marca, modelo)):
            print("Placa, marca e modelo são obrigatórios.")
            return None
        if not 1950 <= ano <= 2100:
            print("O ano deve estar entre 1950 e 2100.")
            return None
        if valor_diaria <= 0:
            print("O valor da diária deve ser maior que zero.")
            return None

        mongo = MongoQueries()
        try:
            mongo.connect()

            self._exibir_categorias(mongo)

            try:
                id_categoria = int(input("\nID da categoria: ").strip())
            except ValueError:
                print("O ID da categoria deve ser numérico.")
                return None

            if mongo.db["veiculo"].find_one({"placa": placa}):
                print(f"A placa {placa} já está cadastrada.")
                return None
            if not self.verifica_existencia_categoria(mongo, id_categoria):
                print(f"A categoria {id_categoria} não existe.")
                return None

            novo_id = self._proximo_id(mongo)
            novo_doc = {
                "id_veiculo": novo_id,
                "id_categoria": id_categoria,
                "placa": placa,
                "marca": marca,
                "modelo": modelo,
                "ano": ano,
                "valor_diaria": self._to_decimal128(valor_diaria),
            }

            mongo.db["veiculo"].insert_one(novo_doc)
            veiculo = self._from_doc(mongo, novo_doc)
            print("Veículo cadastrado com sucesso!")
            print(veiculo.to_string())
            return veiculo
        finally:
            mongo.close()

    def atualizar_veiculo(self) -> Veiculo:
        mongo = MongoQueries()

        try:
            mongo.connect()

            if mongo.db["veiculo"].count_documents({}) == 0:
                print("Nenhum veículo cadastrado.")
                return None

            try:
                id_veiculo = int(
                    input("\nID do veículo que deseja atualizar: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["veiculo"].find_one(
                {"id_veiculo": id_veiculo}
            )

            if doc is None:
                print(f"O veículo {id_veiculo} não existe.")
                return None

            placa = input("Nova placa: ").strip().upper()
            marca = input("Nova marca: ").strip()
            modelo = input("Novo modelo: ").strip()

            try:
                ano = int(input("Novo ano: ").strip())
                valor_diaria = float(
                    input("Novo valor da diária: R$ ")
                    .strip()
                    .replace(",", ".")
                )
            except ValueError:
                print("Ano e valor da diária devem ser numéricos.")
                return None

            if not all((placa, marca, modelo)):
                print("Placa, marca e modelo são obrigatórios.")
                return None

            if not 1950 <= ano <= 2100:
                print("O ano deve estar entre 1950 e 2100.")
                return None

            if valor_diaria <= 0:
                print("O valor da diária deve ser maior que zero.")
                return None

            self._exibir_categorias(mongo)

            try:
                id_categoria = int(
                    input("\nNovo ID da categoria: ").strip()
                )
            except ValueError:
                print("O ID da categoria deve ser numérico.")
                return None

            if mongo.db["veiculo"].find_one(
                {"placa": placa, "id_veiculo": {"$ne": id_veiculo}}
            ):
                print(f"A placa {placa} já pertence a outro veículo.")
                return None

            if not self.verifica_existencia_categoria(mongo, id_categoria):
                print(f"A categoria {id_categoria} não existe.")
                return None

            mongo.db["veiculo"].update_one(
                {"id_veiculo": id_veiculo},
                {
                    "$set": {
                        "id_categoria": id_categoria,
                        "placa": placa,
                        "marca": marca,
                        "modelo": modelo,
                        "ano": ano,
                        "valor_diaria": self._to_decimal128(valor_diaria),
                    }
                },
            )

            doc_atualizado = mongo.db["veiculo"].find_one(
                {"id_veiculo": id_veiculo}
            )

            veiculo = self._from_doc(mongo, doc_atualizado)

            print("Veículo atualizado com sucesso!")
            print(veiculo.to_string())

            return veiculo

        finally:
            mongo.close()

    def excluir_veiculo(self):
        mongo = MongoQueries()

        try:
            mongo.connect()

            if mongo.db["veiculo"].count_documents({}) == 0:
                print("Nenhum veículo cadastrado.")
                return None

            try:
                id_veiculo = int(
                    input("\nID do veículo que deseja excluir: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["veiculo"].find_one(
                {"id_veiculo": id_veiculo}
            )

            if doc is None:
                print(f"O veículo {id_veiculo} não existe.")
                return None

            veiculo = self._from_doc(mongo, doc)

            print("\nVeículo selecionado:")
            print(veiculo.to_string())

            confirmacao = input(
                "Tem certeza de que deseja excluir este veículo? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Exclusão cancelada.")
                return None

            if mongo.db["aluguel"].find_one(
                {"id_veiculo": id_veiculo}
            ):
                print(
                    "Não é possível excluir este veículo, "
                    "pois existem aluguéis vinculados a ele."
                )
                return None

            resultado = mongo.db["veiculo"].delete_one(
                {"id_veiculo": id_veiculo}
            )

            if resultado.deleted_count == 1:
                print("Veículo excluído com sucesso!")
                return veiculo

            print("Não foi possível excluir o veículo.")
            return None

        except Exception as erro:
            print(f"Não foi possível excluir o veículo: {erro}")
            return None

        finally:
            mongo.close()