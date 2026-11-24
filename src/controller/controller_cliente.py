import re
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from model.cliente import Cliente
from conexion.mongo_queries import MongoQueries
from controller.validacao_cpf import ler_cpf


class Controller_Cliente:

    @staticmethod
    def _from_doc(doc: dict):
        """Converte um documento MongoDB em um objeto Cliente."""
        if doc is None:
            return None

        return Cliente(
            doc["id_cliente"],
            doc["nome"],
            doc["cpf"],
            doc["telefone"],
            doc["email"],
        )

    @staticmethod
    def _somente_digitos(valor: str) -> str:
        """Remove caracteres que não sejam números."""
        return re.sub(r"\D", "", valor or "")

    @staticmethod
    def _proximo_id(mongo: MongoQueries) -> int:
        """Gera o próximo id_cliente inteiro sequencial."""
        ultimo = mongo.db["cliente"].find_one(
            {"id_cliente": {"$type": "number"}},
            sort=[("id_cliente", DESCENDING)]
        )

        return (
            int(ultimo["id_cliente"]) + 1
            if ultimo and "id_cliente" in ultimo
            else 1
        )

    def verifica_existencia_cliente(
        self, mongo: MongoQueries, id_cliente: int
    ) -> bool:
        """Verifica se o cliente existe."""
        return (
            mongo.db["cliente"].find_one(
                {"id_cliente": id_cliente}
            ) is not None
        )

    def consultar_cliente(self, id_cliente: int):
        """Consulta um cliente pelo ID."""
        mongo = MongoQueries()

        try:
            mongo.connect()

            doc = mongo.db["cliente"].find_one({
                "id_cliente": id_cliente
            })

            return self._from_doc(doc)

        finally:
            mongo.close()

    def _listar_clientes(self, mongo: MongoQueries):
        """Lista os clientes cadastrados no MongoDB."""

        clientes = mongo.db["cliente"].find(
            {},
            {
                "_id": 0,
                "id_cliente": 1,
                "nome": 1,
                "cpf": 1
            }
        ).sort("id_cliente", 1)

        print("\n========== CLIENTES CADASTRADOS ==========")

        encontrou = False

        for cliente in clientes:
            encontrou = True
            print(
                f"ID: {cliente['id_cliente']} | "
                f"Nome: {cliente['nome']} | "
                f"CPF: {cliente['cpf']}"
            )

        if not encontrou:
            print("Nenhum cliente cadastrado.")

        print("==========================================\n")

        return encontrou

    def inserir_cliente(self) -> Cliente:
        """Cadastra um novo cliente."""

        nome = input("Nome: ").strip()
        cpf = ler_cpf("CPF: ")
        telefone = input("Telefone: ").strip()
        email = input("E-mail: ").strip()

        if not all((nome, cpf, telefone, email)):
            print("Todos os campos são obrigatórios.")
            return None

        cpf_limpo = self._somente_digitos(cpf)

        mongo = MongoQueries()

        try:
            mongo.connect()

            # Verifica se o CPF já está cadastrado.
            if mongo.db["cliente"].find_one({
                "cpf": {"$in": [cpf_limpo, cpf]}
            }):
                print(f"O CPF {cpf} já está cadastrado.")
                return None

            novo_id = self._proximo_id(mongo)

            novo_doc = {
                "id_cliente": novo_id,
                "nome": nome,
                "cpf": cpf_limpo,
                "telefone": telefone,
                "email": email,
            }

            mongo.db["cliente"].insert_one(novo_doc)

            cliente = self._from_doc(novo_doc)

            print("Cliente cadastrado com sucesso!")
            print(cliente.to_string())

            return cliente

        except DuplicateKeyError:
            print("Já existe um cliente cadastrado com esse CPF.")
            return None

        finally:
            mongo.close()

    def atualizar_cliente(self) -> Cliente:
        """Atualiza os dados de um cliente existente."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if not self._listar_clientes(mongo):
                return None

            try:
                id_cliente = int(
                    input("ID do cliente que deseja atualizar: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            if not self.verifica_existencia_cliente(mongo, id_cliente):
                print(f"O cliente de ID {id_cliente} não existe.")
                return None

            nome = input("Novo nome: ").strip()
            cpf = ler_cpf("Novo CPF: ")
            telefone = input("Novo telefone: ").strip()
            email = input("Novo e-mail: ").strip()

            if not all((nome, cpf, telefone, email)):
                print("Todos os campos são obrigatórios.")
                return None

            cpf_limpo = self._somente_digitos(cpf)

            # Verifica se o CPF pertence a outro cliente.
            cpf_em_uso = mongo.db["cliente"].find_one({
                "cpf": {"$in": [cpf_limpo, cpf]},
                "id_cliente": {"$ne": id_cliente}
            })

            if cpf_em_uso is not None:
                print(f"O CPF {cpf} já pertence a outro cliente.")
                return None

            mongo.db["cliente"].update_one(
                {"id_cliente": id_cliente},
                {
                    "$set": {
                        "nome": nome,
                        "cpf": cpf_limpo,
                        "telefone": telefone,
                        "email": email,
                    }
                }
            )

            doc_atualizado = mongo.db["cliente"].find_one({
                "id_cliente": id_cliente
            })

            cliente = self._from_doc(doc_atualizado)

            print("Cliente atualizado com sucesso!")
            print(cliente.to_string())

            return cliente

        except DuplicateKeyError:
            print("Já existe outro cliente cadastrado com esse CPF.")
            return None

        finally:
            mongo.close()

    def excluir_cliente(self):
        """Exclui um cliente, desde que não possua aluguéis vinculados."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if not self._listar_clientes(mongo):
                return None

            try:
                id_cliente = int(
                    input("ID do cliente que deseja excluir: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["cliente"].find_one({
                "id_cliente": id_cliente
            })

            if doc is None:
                print(f"O cliente de ID {id_cliente} não existe.")
                return None

            cliente = self._from_doc(doc)

            print("\nCliente selecionado:")
            print(cliente.to_string())

            confirmacao = input(
                "Tem certeza de que deseja excluir este cliente? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Exclusão cancelada.")
                return None

            # Verifica se existem aluguéis vinculados ao cliente.
            aluguel_existente = mongo.db["aluguel"].find_one({
                "id_cliente": id_cliente
            })

            if aluguel_existente:
                print(
                    "Não é possível excluir este cliente, "
                    "pois existem aluguéis vinculados a ele."
                )
                return None

            mongo.db["cliente"].delete_one({
                "id_cliente": id_cliente
            })

            print("Cliente removido com sucesso!")

            return cliente

        except Exception as erro:
            print(f"Não foi possível excluir o cliente: {erro}")
            return None

        finally:
            mongo.close()