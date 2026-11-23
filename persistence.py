"""Persistencia local SQLite o PostgreSQL y objetos privados de GCP."""
import io
import os
import re
import sqlite3
from pathlib import Path


class CloudCursor:
    def __init__(self, cursor, lastrowid=None):
        self.cursor, self.lastrowid = cursor, lastrowid

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def __iter__(self):
        return iter(self.cursor)


class CloudConnection:
    """Adapta los parámetros y los identificadores generados al motor PostgreSQL."""
    def __init__(self):
        import psycopg
        self.connection = psycopg.connect(
            host=os.environ['DB_HOST'], port=int(os.environ.get('DB_PORT','5432')), dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
            connect_timeout=15,
        )
        self.dictionary = False

    @property
    def row_factory(self):
        return self.dictionary

    @row_factory.setter
    def row_factory(self, _):
        self.dictionary = True

    def execute(self, sql, args=()):
        from psycopg.rows import dict_row, tuple_row
        # Existing queries use positional SQLite placeholders; literal percent
        # signs in LIKE patterns must be escaped for psycopg parameter binding.
        sql = sql.replace('%', '%%').replace('?', '%s')
        insert = bool(re.match(r'\s*INSERT\s+INTO\s', sql, re.I))
        if insert:
            sql = sql.rstrip().rstrip(';') + ' RETURNING id'
        cursor = self.connection.cursor(row_factory=dict_row if self.dictionary else tuple_row)
        cursor.execute(sql, args)
        generated = None
        if insert:
            row = cursor.fetchone()
            generated = row['id'] if self.dictionary else row[0]
        return CloudCursor(cursor, generated)

    def executescript(self, sql):
        sql = sql.replace('id INTEGER PRIMARY KEY', 'id BIGSERIAL PRIMARY KEY')
        for statement in sql.split(';'):
            if statement.strip():
                self.execute(statement)

    def reset_sequences(self):
        # Seed requests contain explicit ids; advance all serial sequences.
        for table in ('users','requests','events','documents','appointments','visits','notifications','institutional','query_log'):
            self.execute(f"SELECT setval(pg_get_serial_sequence('{table}','id'), COALESCE(MAX(id),1), COUNT(*)>0) FROM {table}")

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def connect(data, *, initialize=False):
    if os.environ.get('DB_HOST'):
        conn = CloudConnection()
        if initialize:
            # Serialize schema and demo-data initialization across revisions.
            conn.execute('SELECT pg_advisory_xact_lock(742026)')
        return conn
    conn = sqlite3.connect(Path(data) / 'portal.sqlite3', timeout=15)
    conn.execute('PRAGMA journal_mode=WAL' if initialize else 'PRAGMA foreign_keys=ON')
    return conn


def put_document(data, name, content, mime='application/pdf'):
    if os.environ.get('DOCUMENT_BUCKET'):
        from google.cloud import storage
        storage.Client().bucket(os.environ['DOCUMENT_BUCKET']).blob('documents/'+name).upload_from_string(content, content_type=mime)
    else:
        (Path(data) / 'files' / name).write_bytes(content)


def get_document(data, name):
    if os.environ.get('DOCUMENT_BUCKET'):
        from google.cloud import storage
        return io.BytesIO(storage.Client().bucket(os.environ['DOCUMENT_BUCKET']).blob('documents/'+name).download_as_bytes())
    return Path(data) / 'files' / name
