import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor


class PostgresQueries:
    """Conexão PostgreSQL; credenciais em passphrase, como no exemplo do professor."""

    TABLES = {"cliente", "locadora", "categoria", "veiculo", "funcionario", "aluguel", "pagamento"}

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = os.getenv("PGDATABASE", "locacao")
        auth_file = Path(__file__).resolve().parent / "passphrase" / "authentication.postgres"
        file_user, file_password = [part.strip() for part in auth_file.read_text(encoding="utf-8").strip().split(",", 1)]
        self.user = os.getenv("POSTGRES_USER", file_user)
        self.password = os.getenv("POSTGRES_PASSWORD", file_password)
        self.connection = None

    def connect(self):
        if self.user == "USUARIO_POSTGRES" or self.password == "SENHA_POSTGRES":
            raise ValueError("Preencha conexion/passphrase/authentication.postgres com usuario,senha ou configure POSTGRES_USER e POSTGRES_PASSWORD.")
        self.connection = psycopg2.connect(
            host=self.host, port=self.port, dbname=self.database,
            user=self.user, password=self.password,
        )
        return self.connection

    def fetch_all(self, table_name):
        if self.connection is None:
            raise RuntimeError("Conecte ao PostgreSQL antes de consultar.")
        if table_name not in self.TABLES:
            raise ValueError(f"Tabela não permitida: {table_name}")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
