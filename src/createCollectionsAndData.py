"""

Migração LocacaoVeiculos: PostgreSQL -> MongoDB.

Instalação:

    pip install -r requirements.txt

Execução:

    python createCollectionsAndData.py

Configure antes as variáveis de ambiente descritas no README.md.

O script não apaga documentos existentes.

"""

from datetime import date, datetime, time, timezone

from decimal import Decimal

from bson.decimal128 import Decimal128

from pymongo import ASCENDING, ReplaceOne

from conexion.mongo_queries import MongoQueries

from conexion.postgres_queries import PostgresQueries

TABLES = [

    "cliente",

    "locadora",

    "categoria",

    "veiculo",

    "funcionario",

    "aluguel",

    "pagamento",

]

# Não altere para True sem confirmar que pode apagar os dados das coleções.

LIMPAR_COLECOES_ANTES_DA_MIGRACAO = False

# Os nomes e campos seguem o modelo SQL informado para o projeto.

VALIDATORS = {

    "cliente": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": ["id_cliente", "nome", "cpf", "telefone", "email"],

            "properties": {

                "id_cliente": {"bsonType": ["int", "long"]},

                "nome": {"bsonType": "string"},

                "cpf": {"bsonType": "string"},

                "telefone": {"bsonType": "string"},

                "email": {"bsonType": "string"},

            },

        }

    },

    "locadora": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": ["id_locadora", "nome", "cnpj", "telefone", "email"],

            "properties": {

                "id_locadora": {"bsonType": ["int", "long"]},

                "nome": {"bsonType": "string"},

                "cnpj": {"bsonType": "string"},

                "telefone": {"bsonType": "string"},

                "email": {"bsonType": "string"},

            },

        }

    },

    "categoria": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": ["id_categoria", "nome", "descricao"],

            "properties": {

                "id_categoria": {"bsonType": ["int", "long"]},

                "nome": {"bsonType": "string"},

                "descricao": {"bsonType": "string"},

            },

        }

    },

    "veiculo": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": [

                "id_veiculo", "placa", "marca", "modelo",

                "ano", "valor_diaria", "id_categoria",

            ],

            "properties": {

                "id_veiculo": {"bsonType": ["int", "long"]},

                "placa": {"bsonType": "string"},

                "marca": {"bsonType": "string"},

                "modelo": {"bsonType": "string"},

                "ano": {

                    "bsonType": ["int", "long"],

                    "minimum": 1950,

                    "maximum": 2100,

                },

                "valor_diaria": {

                    "bsonType": "decimal",

                    "minimum": 0.01,

                },

                "id_categoria": {"bsonType": ["int", "long"]},

            },

        }

    },

    "funcionario": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": [

                "id_funcionario", "email", "senha", "nome",

                "cpf", "telefone", "cargo",

            ],

            "properties": {

                "id_funcionario": {"bsonType": ["int", "long"]},

                "email": {"bsonType": "string"},

                "senha": {"bsonType": "string"},

                "nome": {"bsonType": "string"},

                "cpf": {"bsonType": "string"},

                "telefone": {"bsonType": "string"},

                "cargo": {"bsonType": "string"},

            },

        }

    },

    "aluguel": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": [

                "id_aluguel", "data_retirada", "data_devolucao_prevista",

                "valor_total", "status", "id_cliente", "id_locadora",

                "id_veiculo", "id_funcionario",

            ],

            "properties": {

                "id_aluguel": {"bsonType": ["int", "long"]},

                "data_retirada": {"bsonType": "date"},

                "data_devolucao_prevista": {"bsonType": "date"},

                "data_devolucao_real": {"bsonType": ["date", "null"]},

                "valor_total": {

                    "bsonType": "decimal",

                    "minimum": 0,

                },

                "status": {

                    "bsonType": "string",

                    "enum": ["ATIVO", "FINALIZADO", "CANCELADO"],

                },

                "id_cliente": {"bsonType": ["int", "long"]},

                "id_locadora": {"bsonType": ["int", "long"]},

                "id_veiculo": {"bsonType": ["int", "long"]},

                "id_funcionario": {"bsonType": ["int", "long"]},

            },

        }

    },

    "pagamento": {

        "$jsonSchema": {

            "bsonType": "object",

            "required": [

                "id_pagamento", "valor", "data_pagamento",

                "metodo", "status", "id_aluguel",

            ],

            "properties": {

                "id_pagamento": {"bsonType": ["int", "long"]},

                "valor": {

                    "bsonType": "decimal",

                    "minimum": 0.01,

                },

                "data_pagamento": {"bsonType": "date"},

                "metodo": {

                    "bsonType": "string",

                    "enum": [

                        "DINHEIRO", "PIX",

                        "CARTAO_CREDITO", "CARTAO_DEBITO",

                    ],

                },

                "status": {

                    "bsonType": "string",

                    "enum": ["PENDENTE", "PAGO", "CANCELADO"],

                },

                "id_aluguel": {"bsonType": ["int", "long"]},

            },

        }

    },

}

# Índices únicos: PKs e restrições UNIQUE do modelo SQL.

UNIQUE_INDEXES = {

    "cliente": ["id_cliente", "cpf"],

    "locadora": ["id_locadora", "cnpj"],

    "categoria": ["id_categoria", "nome"],

    "veiculo": ["id_veiculo", "placa"],

    "funcionario": ["id_funcionario", "email", "cpf"],

    "aluguel": ["id_aluguel"],

    "pagamento": ["id_pagamento"],

}

# Índices para os campos usados nos relacionamentos.

RELATION_INDEXES = {

    "veiculo": ["id_categoria"],

    "aluguel": [

        "id_cliente", "id_locadora", "id_veiculo", "id_funcionario"

    ],

    "pagamento": ["id_aluguel"],

}

def convert_value(value):

    """Converte tipos retornados pelo PostgreSQL para tipos BSON."""

    if value is None:

        return None

    if isinstance(value, Decimal):

        return Decimal128(value)

    # datetime deve ser testado antes de date, pois herda de date.

    if isinstance(value, datetime):

        if value.tzinfo is None:

            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)

    if isinstance(value, date):

        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    if isinstance(value, list):

        return [convert_value(item) for item in value]

    if isinstance(value, dict):

        return {key: convert_value(item) for key, item in value.items()}

    return value

def convert_document(row):

    return {column: convert_value(value) for column, value in row.items()}

def create_collections(mongo):

    """Cria coleções novas ou aplica validadores às existentes."""

    existing = mongo.db.list_collection_names()

    for name in TABLES:

        if name not in existing:

            mongo.db.create_collection(

                name,

                validator=VALIDATORS[name],

                validationLevel="strict",

                validationAction="error",

            )

            print(f"Coleção criada: {name}")

        else:

            mongo.db.command(

                "collMod",

                name,

                validator=VALIDATORS[name],

                validationLevel="strict",

                validationAction="error",

            )

            print(f"Validador aplicado: {name}")

def clear_collections_if_requested(mongo):

    """Apaga documentos somente quando a constante foi explicitamente ativada."""

    if not LIMPAR_COLECOES_ANTES_DA_MIGRACAO:

        return

    confirmacao = input(

        "Isso apagará os documentos das 7 coleções. Digite APAGAR para continuar: "

    )

    if confirmacao != "APAGAR":

        raise RuntimeError("Limpeza cancelada pelo usuário.")

    for name in TABLES:

        mongo.db[name].delete_many({})

    print("Documentos antigos removidos.")

def create_indexes(mongo):

    """

    Cria índices únicos e de relacionamento.

    Os índices únicos dos IDs usam partialFilterExpression para ignorar

    documentos antigos que ainda não tenham o campo id_\*.

    """

    for collection_name, fields in UNIQUE_INDEXES.items():

        collection = mongo.db[collection_name]

        for field in fields:

            options = {

                "unique": True,

                "name": f"uq_{collection_name}_{field}",

            }

            if field.startswith("id_"):

                options["partialFilterExpression"] = {

                    field: {"$exists": True}

                }

            collection.create_index([(field, ASCENDING)], **options)

    for collection_name, fields in RELATION_INDEXES.items():

        collection = mongo.db[collection_name]

        for field in fields:

            collection.create_index(

                [(field, ASCENDING)],

                name=f"ix_{collection_name}_{field}",

            )

    print("Índices criados/verificados.")

def extract_and_insert(postgres, mongo):

    """

    Extrai as sete tabelas e sincroniza os documentos no MongoDB.

    Mantém os IDs originais nos campos id_\*; o MongoDB cria _id.

    """

    for table_name in TABLES:

        print(f"Consultando PostgreSQL: {table_name}")

        rows = postgres.fetch_all(table_name)

        if not rows:

            print(f"{table_name}: nenhum registro encontrado.")

            continue

        id_field = f"id_{table_name}"

        operations = []

        for row in rows:

            document = convert_document(row)

            if id_field not in document or document[id_field] is None:

                raise ValueError(

                    f"A tabela {table_name} não retornou a chave {id_field}."

                )

            operations.append(

                ReplaceOne(

                    {id_field: document[id_field]},

                    document,

                    upsert=True,

                )

            )

        result = mongo.db[table_name].bulk_write(operations, ordered=True)

        print(

            f"{table_name}: {len(rows)} registro(s) lido(s); "

            f"{result.upserted_count} inserido(s), "

            f"{result.modified_count} atualizado(s)."

        )

def show_counts(mongo):

    print("\nQuantidade de documentos por coleção:")

    for name in TABLES:

        print(f"{name}: {mongo.db[name].count_documents({})}")

def main():

    mongo = MongoQueries()

    postgres = PostgresQueries()

    try:

        mongo.connect()

        print("Conectado ao MongoDB.")

        postgres.connect()

        print("Conectado ao PostgreSQL.")

        create_collections(mongo)

        clear_collections_if_requested(mongo)

        create_indexes(mongo)

        extract_and_insert(postgres, mongo)

        show_counts(mongo)

        print("\nMigração concluída com sucesso.")

    finally:

        postgres.close()

        mongo.close()

if __name__ == "__main__":

    main()
