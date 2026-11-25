import re
from pymongo import ASCENDING, DESCENDING
from model.funcionario import Funcionario
from conexion.mongo_queries import MongoQueries
from controller.validacao_cpf import ler_cpf


class Controller_Funcionario:
    """Controlador CRUD de Funcionario migrado para MongoDB."""

    @staticmethod
    def _from_doc(doc: dict):
        if doc is None:
            return None
        # A ordem dos argumentos corresponde ao construtor do model Funcionario:
        # id, email, senha, nome, cpf, telefone, cargo.
        return Funcionario(
            doc["id_funcionario"],
            doc["email"],
            doc.get("senha"),
            doc["nome"],
            doc["cpf"],
            doc["telefone"],
            doc["cargo"],
        )

    @staticmethod
    def _somente_digitos(valor: str) -> str:
        return re.sub(r"\D", "", valor or "")

    @classmethod
    def _cpf_ja_cadastrado(
        cls, mongo: MongoQueries, cpf_limpo: str, ignorar_id: int = None
    ) -> bool:
        cpf_formatado = (
            f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
            if len(cpf_limpo) == 11
            else cpf_limpo
        )
        filtro = {"cpf": {"$in": [cpf_limpo, cpf_formatado]}}
        if ignorar_id is not None:
            filtro["id_funcionario"] = {"$ne": ignorar_id}
        return mongo.db["funcionario"].find_one(filtro) is not None

    def _proximo_id(self, mongo: MongoQueries) -> int:
        ultimo = mongo.db["funcionario"].find_one(sort=[("id_funcionario", DESCENDING)])
        return (ultimo["id_funcionario"] + 1) if ultimo and "id_funcionario" in ultimo else 1

    def verifica_existencia_funcionario(
        self, mongo: MongoQueries, id_funcionario: int
    ) -> bool:
        return (
            mongo.db["funcionario"].find_one({"id_funcionario": id_funcionario})
            is not None
        )

    def consultar_funcionario(self, id_funcionario: int):
        mongo = MongoQueries()
        try:
            mongo.connect()
            doc = mongo.db["funcionario"].find_one({"id_funcionario": id_funcionario})
            return self._from_doc(doc)
        finally:
            mongo.close()

    @staticmethod
    def _listar_funcionarios(mongo: MongoQueries) -> bool:
        funcionarios = list(
            mongo.db["funcionario"].find(
                {},
                {
                    "_id": 0,
                    "id_funcionario": 1,
                    "nome": 1,
                    "cpf": 1,
                    "cargo": 1,
                    "email": 1,
                },
            ).sort("id_funcionario", ASCENDING)
        )

        if not funcionarios:
            print("\nNenhum funcionário cadastrado.")
            return False

        print("\n========== FUNCIONÁRIOS CADASTRADOS ==========")

        for funcionario in funcionarios:
            print(
                f"ID: {funcionario['id_funcionario']} | "
                f"Nome: {funcionario['nome']} | "
                f"CPF: {funcionario['cpf']} | "
                f"Cargo: {funcionario['cargo']} | "
                f"E-mail: {funcionario['email']}"
            )

        print("==============================================")
        return True

    def inserir_funcionario(self) -> Funcionario:
        nome = input("Nome: ").strip()
        cpf = ler_cpf("CPF: ")
        telefone = input("Telefone: ").strip()
        email = input("E-mail: ").strip()
        senha = input("Senha: ").strip()
        cargo = input("Cargo: ").strip()

        if not all((nome, cpf, telefone, email, senha, cargo)):
            print("Todos os campos são obrigatórios.")
            return None

        cpf_limpo = self._somente_digitos(cpf)

        mongo = MongoQueries()
        try:
            mongo.connect()

            if self._cpf_ja_cadastrado(mongo, cpf_limpo):
                print(f"O CPF {cpf} já está cadastrado.")
                return None

            if mongo.db["funcionario"].find_one({"email": email}):
                print(f"O e-mail {email} já está cadastrado.")
                return None

            novo_id = self._proximo_id(mongo)
            novo_doc = {
                "id_funcionario": novo_id,
                "email": email,
                "senha": senha,
                "nome": nome,
                "cpf": cpf_limpo,
                "telefone": telefone,
                "cargo": cargo,
            }

            mongo.db["funcionario"].insert_one(novo_doc)
            funcionario = self._from_doc(novo_doc)
            print("Funcionário cadastrado com sucesso!")
            print(funcionario.to_string())
            return funcionario
        finally:
            mongo.close()

    def atualizar_funcionario(self) -> Funcionario:
        mongo = MongoQueries()
        try:
            mongo.connect()

            if mongo.db["funcionario"].count_documents({}) == 0:
                print("Nenhum funcionário cadastrado.")
                return None

            try:
                id_funcionario = int(
                    input("\nID do funcionário que deseja atualizar: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            if not self.verifica_existencia_funcionario(mongo, id_funcionario):
                print(f"O funcionário {id_funcionario} não existe.")
                return None

            nome = input("Novo nome: ").strip()
            cpf = ler_cpf("Novo CPF: ")
            telefone = input("Novo telefone: ").strip()
            email = input("Novo e-mail: ").strip()
            senha = input(
                "Nova senha (pressione Enter para manter a atual): "
            ).strip()
            cargo = input("Novo cargo: ").strip()

            if not all((nome, cpf, telefone, email, cargo)):
                print("Nome, CPF, telefone, e-mail e cargo são obrigatórios.")
                return None

            cpf_limpo = self._somente_digitos(cpf)

            if self._cpf_ja_cadastrado(mongo, cpf_limpo, ignorar_id=id_funcionario):
                print(f"O CPF {cpf} já pertence a outro funcionário.")
                return None

            if mongo.db["funcionario"].find_one(
                {"email": email, "id_funcionario": {"$ne": id_funcionario}}
            ):
                print(f"O e-mail {email} já pertence a outro funcionário.")
                return None

            campos_atualizados = {
                "email": email,
                "nome": nome,
                "cpf": cpf_limpo,
                "telefone": telefone,
                "cargo": cargo,
            }
            if senha:
                campos_atualizados["senha"] = senha

            mongo.db["funcionario"].update_one(
                {"id_funcionario": id_funcionario},
                {"$set": campos_atualizados},
            )

            doc_atualizado = mongo.db["funcionario"].find_one(
                {"id_funcionario": id_funcionario}
            )
            funcionario = self._from_doc(doc_atualizado)
            print("Funcionário atualizado com sucesso!")
            print(funcionario.to_string())
            return funcionario
        finally:
            mongo.close()

    def excluir_funcionario(self):
        mongo = MongoQueries()
        try:
            mongo.connect()

            if mongo.db["funcionario"].count_documents({}) == 0:
                print("Nenhum funcionário cadastrado.")
                return None

            try:
                id_funcionario = int(
                    input("\nID do funcionário que deseja excluir: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["funcionario"].find_one({"id_funcionario": id_funcionario})
            if doc is None:
                print(f"O funcionário {id_funcionario} não existe.")
                return None

            funcionario = self._from_doc(doc)

            print("\nFuncionário selecionado:")
            print(funcionario.to_string())

            confirmacao = input(
                "Tem certeza de que deseja excluir este funcionário? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Exclusão cancelada.")
                return None

            if mongo.db["aluguel"].find_one({"id_funcionario": id_funcionario}):
                print(
                    "Não é possível excluir este funcionário, "
                    "pois existem aluguéis vinculados a ele."
                )
                return None

            resultado = mongo.db["funcionario"].delete_one(
                {"id_funcionario": id_funcionario}
            )

            if resultado.deleted_count == 1:
                print("Funcionário excluído com sucesso!")
                return funcionario

            print("Não foi possível excluir o funcionário.")
            return None

        except Exception as erro:
            print(f"Não foi possível excluir o funcionário: {erro}")
            return None
        finally:
            mongo.close()