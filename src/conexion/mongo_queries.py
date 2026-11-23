import os
from pymongo import MongoClient

class MongoQueries:

    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.database_name = os.getenv(
            "MONGO_DATABASE",
            "LocacaoVeiculos"
        )

        if not self.mongo_uri:
            raise ValueError("A variável MONGO_URI não foi configurada.")

    def connect(self):
        self.client = MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS=10000
        )

        self.db = self.client[self.database_name]

        self.client.admin.command("ping")

        print("MongoDB Atlas conectado com sucesso!")

    def close(self):
        if hasattr(self, "client"):
            self.client.close()
