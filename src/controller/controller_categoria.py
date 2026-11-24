from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from model.categoria import Categoria
from conexion.mongo_queries import MongoQueries


class Controller_Categoria:

    @staticmethod
    def _from_doc(doc: dict):
        """Converte um documento MongoDB em um objeto Categoria."""
        if doc is None:
            return None

        return Categoria(
            doc["id_categoria"],
            doc["nome"],
            doc["descricao"]
        )

    @staticmethod
    def _proximo_id(mongo: MongoQueries) -> int:
        """Gera o próximo id_categoria inteiro sequencial."""
        ultimo = mongo.db["categoria"].find_one(
            {"id_categoria": {"$type": "number"}},
            sort=[("id_categoria", DESCENDING)]
        )

        return (
            int(ultimo["id_categoria"]) + 1
            if ultimo and "id_categoria" in ultimo
            else 1
        )

    def verifica_existencia_categoria(
        self, mongo: MongoQueries, id_categoria: int
    ) -> bool:
        """Verifica se a categoria existe."""
        return (
            mongo.db["categoria"].find_one(
                {"id_categoria": id_categoria}
            ) is not None
        )

    def consultar_categoria(self, id_categoria: int):
        """Consulta uma categoria pelo seu ID."""
        mongo = MongoQueries()

        try:
            mongo.connect()

            doc = mongo.db["categoria"].find_one({
                "id_categoria": id_categoria
            })

            return self._from_doc(doc)

        finally:
            mongo.close()

    def _listar_categorias(self, mongo: MongoQueries):
        """Lista as categorias cadastradas no MongoDB."""

        categorias = mongo.db["categoria"].find(
            {},
            {
                "_id": 0,
                "id_categoria": 1,
                "nome": 1,
                "descricao": 1
            }
        ).sort("id_categoria", 1)

        print("\n========== CATEGORIAS CADASTRADAS ==========")

        encontrou = False

        for categoria in categorias:
            encontrou = True
            print(
                f"ID: {categoria['id_categoria']} | "
                f"Nome: {categoria['nome']} | "
                f"Descrição: {categoria['descricao']}"
            )

        if not encontrou:
            print("Nenhuma categoria cadastrada.")

        print("=============================================\n")

        return encontrou

    def inserir_categoria(self) -> Categoria:
        """Cadastra uma nova categoria."""

        nome = input("Nome da categoria: ").strip()
        descricao = input("Descrição: ").strip()

        if not nome or not descricao:
            print("Nome e descrição são obrigatórios.")
            return None

        mongo = MongoQueries()

        try:
            mongo.connect()

            collection = mongo.db["categoria"]

            # Verifica se o nome da categoria já está cadastrado.
            existente = collection.find_one({
                "nome": nome
            })

            if existente is not None:
                print(f"A categoria '{nome}' já existe.")
                return None

            novo_id = self._proximo_id(mongo)

            novo_doc = {
                "id_categoria": novo_id,
                "nome": nome,
                "descricao": descricao
            }

            collection.insert_one(novo_doc)

            categoria = self._from_doc(novo_doc)

            print("Categoria cadastrada com sucesso!")
            print(categoria.to_string())

            return categoria

        except DuplicateKeyError:
            print(f"A categoria '{nome}' já está cadastrada.")
            return None

        finally:
            mongo.close()

    def atualizar_categoria(self) -> Categoria:
        """Atualiza os dados de uma categoria existente."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if not self._listar_categorias(mongo):
                return None

            try:
                id_categoria = int(
                    input("ID da categoria que deseja atualizar: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            collection = mongo.db["categoria"]

            if not self.verifica_existencia_categoria(
                mongo, id_categoria
            ):
                print(f"A categoria {id_categoria} não existe.")
                return None

            nome = input("Novo nome: ").strip()
            descricao = input("Nova descrição: ").strip()

            if not nome or not descricao:
                print("Nome e descrição são obrigatórios.")
                return None

            duplicada = collection.find_one({
                "nome": nome,
                "id_categoria": {"$ne": id_categoria}
            })

            if duplicada is not None:
                print(f"A categoria '{nome}' já existe.")
                return None

            collection.update_one(
                {"id_categoria": id_categoria},
                {
                    "$set": {
                        "nome": nome,
                        "descricao": descricao
                    }
                }
            )

            doc_atualizado = collection.find_one({
                "id_categoria": id_categoria
            })

            categoria = self._from_doc(doc_atualizado)

            print("Categoria atualizada com sucesso!")
            print(categoria.to_string())

            return categoria

        except DuplicateKeyError:
            print("Já existe outra categoria com esse nome.")
            return None

        finally:
            mongo.close()

    def excluir_categoria(self):
        """Exclui uma categoria, desde que não possua veículos vinculados."""

        mongo = MongoQueries()

        try:
            mongo.connect()

            if not self._listar_categorias(mongo):
                return None

            try:
                id_categoria = int(
                    input("ID da categoria que deseja excluir: ").strip()
                )
            except ValueError:
                print("O ID deve ser um número inteiro.")
                return None

            doc = mongo.db["categoria"].find_one({
                "id_categoria": id_categoria
            })

            if doc is None:
                print(f"A categoria {id_categoria} não existe.")
                return None

            categoria = self._from_doc(doc)

            print("\nCategoria selecionada:")
            print(categoria.to_string())

            confirmacao = input(
                "Tem certeza de que deseja excluir esta categoria? (S/N): "
            ).strip().upper()

            if confirmacao != "S":
                print("Exclusão cancelada.")
                return None

            veiculo_existente = mongo.db["veiculo"].find_one({
                "id_categoria": id_categoria
            })

            if veiculo_existente is not None:
                print(
                    "Não é possível excluir esta categoria, "
                    "pois existem veículos vinculados a ela."
                )
                return None

            resultado = mongo.db["categoria"].delete_one({
                "id_categoria": id_categoria
            })

            if resultado.deleted_count == 0:
                print("Não foi possível encontrar a categoria para exclusão.")
                return None

            print("Categoria excluída com sucesso!")

            return categoria

        except Exception as erro:
            print(f"Não foi possível excluir a categoria: {erro}")
            return None

        finally:
            mongo.close()