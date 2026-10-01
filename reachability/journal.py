"""SQLite command journal for one local authority, with POSIX process locking.

Integrity hashes detect accidental corruption. The database remains inside the
trusted service boundary; these hashes are not cryptographic issuer attestation.
"""
from dataclasses import dataclass
import fcntl
from hashlib import sha256
from pathlib import Path
import sqlite3

from .codec import dumps, loads

SCHEMA = "admission-journal/v1"


class StoreInUse(RuntimeError):
    pass


class RecoveryError(RuntimeError):
    pass


def digest(text: str) -> str:
    return sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class JournalEntry:
    sequence: int
    command: str
    key: str
    payload: str
    result_digest: str
    previous_digest: str
    entry_digest: str

    def computed_digest(self) -> str:
        return digest(dumps((self.sequence, self.command, self.key, self.payload,
                             self.result_digest, self.previous_digest)))


class SQLiteJournal:
    def __init__(self, path: str | Path, initial: dict):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_file = open(str(self.path) + ".lock", "a+b")
        self._connection = None
        try:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            self._lock_file.close()
            raise StoreInUse("another authority already owns this journal") from error
        try:
            self._connection = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=FULL")
            self._connection.execute("BEGIN IMMEDIATE")
            self._connection.execute("CREATE TABLE IF NOT EXISTS metadata "
                                     "(id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)")
            self._connection.execute("CREATE TABLE IF NOT EXISTS events ("
                                     "sequence INTEGER PRIMARY KEY, command TEXT NOT NULL, "
                                     "key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, "
                                     "result_digest TEXT NOT NULL, previous_digest TEXT NOT NULL, "
                                     "entry_digest TEXT NOT NULL)")
            row = self._connection.execute("SELECT value FROM metadata WHERE id=1").fetchone()
            if row is None:
                if self._connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]:
                    raise RecoveryError("journal metadata is missing")
                value = dumps({"schema": SCHEMA, "initial": initial})
                self._connection.execute("INSERT INTO metadata VALUES (1, ?)", (value,))
            else:
                value = row[0]
            metadata = loads(value)
            if metadata["schema"] != SCHEMA:
                raise RecoveryError("unsupported journal schema")
            self.initial = metadata["initial"]
            self._genesis = digest(value)
            self._connection.execute("COMMIT")
        except BaseException:
            self.close()
            raise

    def entries(self) -> tuple[JournalEntry, ...]:
        rows = self._connection.execute(
            "SELECT sequence, command, key, payload, result_digest, previous_digest, entry_digest "
            "FROM events ORDER BY sequence").fetchall()
        entries = tuple(JournalEntry(*row) for row in rows)
        previous = self._genesis
        for sequence, entry in enumerate(entries, 1):
            if (entry.sequence != sequence or entry.previous_digest != previous
                    or entry.entry_digest != entry.computed_digest()):
                raise RecoveryError("journal sequence or integrity check failed")
            previous = entry.entry_digest
        return entries

    def append(self, command: str, key: str, payload: str, result_digest: str,
               expected_sequence: int) -> int:
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT sequence, entry_digest FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
            sequence, previous = row if row is not None else (0, self._genesis)
            if sequence != expected_sequence:
                raise RecoveryError("journal changed outside its commit authority")
            entry = JournalEntry(sequence + 1, command, key, payload, result_digest, previous, "")
            connection.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", (
                entry.sequence, command, key, payload, result_digest, previous, entry.computed_digest()))
            connection.execute("COMMIT")
            return entry.sequence
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if not self._lock_file.closed:
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            self._lock_file.close()
