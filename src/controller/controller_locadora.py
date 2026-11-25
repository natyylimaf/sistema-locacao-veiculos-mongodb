import re
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from model.locadora import Locadora
from conexion.mongo_queries import MongoQueries


class Controller_Locadora:

    @staticmethod
    def _from_doc(doc: dict):
        """Converte um documento MongoDB em um objeto Locadora."""
        if doc is None:
            return None

        return Locadora(
            doc["id_locadora"],
            doc["nome"],
            doc["cnpj"],
            doc["telefone"],
            doc["email"]
        )

    @staticmethod
    def _somente_digitos(valor: str) -> str:
        """Remove caracteres que não sejam números do CNPJ."""
        return re.sub(r"\D", "", valor or "")

    @staticmethod
    def _proximo_id(mongo: MongoQueries) -> int:
        """Gera o próximo id_locadora inteiro sequencial."""
        ultimo = mongo.db["locadora"].find_one(
            {"id_locadora": {"$type": "number"}},
            sort=[("id_locadora", DESCENDING)]
        )

        return (
            int(ultimo["id_locadora"]) + 1
            if ultimo and "id_locadora" in ultimo
            else 1
        )

    def verifica_existencia_locadora(
        self, mongo: MongoQueries, id_locadora: int
    ) -> bool:
        """Verifica se a locadora existe."""
        return (
            mongo.db["locadora"].find_one(
                {"id_locadora": id_locadora}
            ) is not None
        )

    def consultar_locadora(self, id_locadora: int):
        """Consulta uma locadora pelo seu ID."""
        mongo = MongoQueries()

        try:
            mongo.connect()

            doc = mongo.db["locadora"].find_one({
                "id_locadora": id_locadora
            })

            return self._from_doc(doc)

        finally:
            mongo.close()

    def _listar_locadoras(self, mongo: MongoQueries):
        """Lista as locadoras cadastradas no MongoDB."""

        locadoras = mongo.db["locadora"].find(
            {},
            {
                "_id": 0,
                "id_locadora": 1,
                "nome": 1,
                "cnpj": 1
            }
        ).sort("id_locadora", 1)

        print("\n========== LOCADORAS CADASTRADAS ==========")

        encontrou = False

        for locadora in locadoras:
            encontrou = True
            print(
                f"ID: {locadora['id_locadora']} | "
                f"Nome: {locadora['nome']} | "
                f"CNPJ: {locadora['cnpj']}"
            )

        if not encontrou:
            print("Nenhuma locadora cadastrada.")

        print("============================================\n")

        return encontrou

    def inserir_locadora(self) -> Locadora:
        """Cadastra uma nova locadora."""

        nome = input("Nome da locadora: ").strip()
        cnpj = input("CNPJ: ").strip()
        telefone = input("Telefone: ").strip()
        email = input("E-mail: ").strip()

        if not all((nome, cnpj, telefone, email)):
            print("Todos os campos são obrigatórios.")
            return None

        cnpj_limpo = self._somente_digitos(cnpj)

        if len(cnpj_limpo) != 14:
            print("O CNPJ deve possuir 14 números.")
            return None

        mongo = MongoQueries()

        try:
            mongo.connect()

            collection = mongo.db["locadora"]

            # Verifica se o CNPJ já está cadastrado.
            existente = collection.find_one({
                "cnpj": cnpj_limpo
            })

            if existente is not None:
                print(f"O CNPJ {cnpj} já está cadastrado.")
                return None

            novo_id = self._proximo_id(mongo)

            novo_doc = {
                "id_locadora": novo_id,
                "nome": nome,
                "cnpj": cnpj_limpo,
                "telefone": telefone,
                "email": email
            }

            collection.insert_one(novo_doc)

            locadora = self._from_doc(novo_doc)

            print("Locadora cadastrada com sucesso!")
            print(locadora.to_string())

            return locadora

        except DuplicateKeyError:
            print("Já existe uma locadora cadastrada com esse CNPJ.")
            return None

        finally:
            mongo.close()

    def atualizar_locadora(self) -> Locadora:
        """Atualiza os dados de uma locadora existente."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if mongo.db["locadora"].count_documents({}) == 0:
                print("Nenhuma locadora cadastrada.")
                return None

            try:
                id_locadora = int(
                    input("ID da locadora que deseja atualizar: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            collection = mongo.db["locadora"]

            if not self.verifica_existencia_locadora(mongo, id_locadora):
                print(f"A locadora {id_locadora} não existe.")
                return None

            nome = input("Novo nome: ").strip()
            cnpj = input("Novo CNPJ: ").strip()
            telefone = input("Novo telefone: ").strip()
            email = input("Novo e-mail: ").strip()

            if not all((nome, cnpj, telefone, email)):
                print("Todos os campos são obrigatórios.")
                return None

            cnpj_limpo = self._somente_digitos(cnpj)

            if len(cnpj_limpo) != 14:
                print("O CNPJ deve possuir 14 números.")
                return None

            cnpj_em_uso = collection.find_one({
                "cnpj": cnpj_limpo,
                "id_locadora": {"$ne": id_locadora}
            })

            if cnpj_em_uso is not None:
                print(f"O CNPJ {cnpj} já pertence a outra locadora.")
                return None

            collection.update_one(
                {"id_locadora": id_locadora},
                {
                    "$set": {
                        "nome": nome,
                        "cnpj": cnpj_limpo,
                        "telefone": telefone,
                        "email": email
                    }
                }
            )

            doc_atualizado = collection.find_one({
                "id_locadora": id_locadora
            })

            locadora = self._from_doc(doc_atualizado)

            print("Locadora atualizada com sucesso!")
            print(locadora.to_string())

            return locadora

        except DuplicateKeyError:
            print("Já existe outra locadora cadastrada com esse CNPJ.")
            return None

        finally:
            mongo.close()

    def excluir_locadora(self):
        """Exclui uma locadora, desde que não possua aluguéis vinculados."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if mongo.db["locadora"].count_documents({}) == 0:
                print("Nenhuma locadora cadastrada.")
                return None

            try:
                id_locadora = int(
                    input("ID da locadora que deseja excluir: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["locadora"].find_one({
                "id_locadora": id_locadora
            })

            if doc is None:
                print(f"A locadora {id_locadora} não existe.")
                return None

            locadora = self._from_doc(doc)

            print("\nLocadora selecionada:")
            print(locadora.to_string())

            confirmacao = input(
                "Tem certeza de que deseja excluir esta locadora? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Exclusão cancelada.")
                return None

            aluguel_existente = mongo.db["aluguel"].find_one({
                "id_locadora": id_locadora
            })

            if aluguel_existente is not None:
                print(
                    "Não é possível excluir esta locadora, "
                    "pois existem aluguéis vinculados a ela."
                )
                return None

            resultado = mongo.db["locadora"].delete_one({
                "id_locadora": id_locadora
            })

            if resultado.deleted_count == 0:
                print("Não foi possível encontrar a locadora para exclusão.")
                return None

            print("Locadora excluída com sucesso!")

            return locadora

        except Exception as erro:
            print(f"Não foi possível excluir a locadora: {erro}")
            return None

        finally:
            mongo.close()