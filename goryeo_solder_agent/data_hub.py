from __future__ import annotations

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any

TABLES = (
    "work_orders", "raw_material_lots", "incoming_inspections", "melting_batches",
    "process_readings", "casting_rolling", "quality_inspections", "packages",
    "shipments", "knowledge_documents", "rules", "settings",
)


class GoryeoSolderRepository:
    """고려솔더 시제품용 읽기 전용 Data Hub. 모든 초기 레코드는 가상 데모다."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    TABLE_LABELS = {
        "work_orders":"작업지시", "raw_material_lots":"원료 LOT", "incoming_inspections":"수입검사",
        "melting_batches":"용해 배치", "process_readings":"공정 측정", "casting_rolling":"주조·압연",
        "quality_inspections":"품질검사", "packages":"포장 LOT", "shipments":"출하",
        "knowledge_documents":"지식문서", "rules":"확인 규칙", "settings":"설정",
    }

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _dicts(rows):
        return [dict(row) for row in rows]

    def _query(self, sql, params=()):
        with self._connect() as connection:
            return self._dicts(connection.execute(sql, params).fetchall())

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript("""
            CREATE TABLE IF NOT EXISTS work_orders (
              work_order TEXT PRIMARY KEY, product_code TEXT, product_name TEXT, target_qty_kg REAL,
              due_date TEXT, status TEXT, progress_pct REAL, customer_label TEXT);
            CREATE TABLE IF NOT EXISTS raw_material_lots (
              material_lot TEXT PRIMARY KEY, material_name TEXT, supplier_label TEXT,
              received_qty_kg REAL, available_qty_kg REAL, certificate_status TEXT,
              quarantine_status TEXT, received_at TEXT);
            CREATE TABLE IF NOT EXISTS incoming_inspections (
              inspection_id TEXT PRIMARY KEY, material_lot TEXT, inspected_at TEXT,
              composition_result TEXT, appearance_result TEXT, weight_result TEXT,
              final_result TEXT, inspector TEXT, note TEXT);
            CREATE TABLE IF NOT EXISTS melting_batches (
              melt_batch TEXT PRIMARY KEY, work_order TEXT, furnace_id TEXT, recipe_revision TEXT,
              planned_qty_kg REAL, actual_qty_kg REAL, started_at TEXT, ended_at TEXT,
              status TEXT, approval_status TEXT);
            CREATE TABLE IF NOT EXISTS process_readings (
              reading_id TEXT PRIMARY KEY, melt_batch TEXT, measured_at TEXT,
              temperature_c REAL, hold_time_min REAL, stir_speed_rpm REAL,
              oxygen_ppm REAL, dross_kg REAL, status TEXT);
            CREATE TABLE IF NOT EXISTS casting_rolling (
              process_id TEXT PRIMARY KEY, melt_batch TEXT, process_name TEXT, equipment_id TEXT,
              started_at TEXT, ended_at TEXT, input_qty_kg REAL, output_qty_kg REAL,
              thickness_mm REAL, width_mm REAL, result TEXT);
            CREATE TABLE IF NOT EXISTS quality_inspections (
              inspection_id TEXT PRIMARY KEY, work_order TEXT, melt_batch TEXT, inspection_type TEXT,
              inspected_at TEXT, sample_qty INTEGER, composition_result TEXT,
              dimension_result TEXT, surface_result TEXT, final_result TEXT, approver TEXT);
            CREATE TABLE IF NOT EXISTS packages (
              package_lot TEXT PRIMARY KEY, work_order TEXT, melt_batch TEXT, package_type TEXT,
              net_weight_kg REAL, label_status TEXT, packed_at TEXT, status TEXT);
            CREATE TABLE IF NOT EXISTS shipments (
              shipment_no TEXT PRIMARY KEY, work_order TEXT, package_lot TEXT,
              planned_date TEXT, actual_date TEXT, quantity_kg REAL, status TEXT,
              quality_approval TEXT);
            CREATE TABLE IF NOT EXISTS knowledge_documents (
              document_id TEXT PRIMARY KEY, filename TEXT, title TEXT, revision TEXT, owner TEXT,
              effective_date TEXT, status TEXT, keywords TEXT, body TEXT, source_label TEXT);
            CREATE TABLE IF NOT EXISTS rules (
              rule_id TEXT PRIMARY KEY, name TEXT, source_table TEXT, condition TEXT, owner TEXT,
              action TEXT, source_document TEXT, revision TEXT, status TEXT);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            """)
            if connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 0:
                self._seed(connection)
            self._seed_knowledge(connection)

    @staticmethod
    def _seed(connection):
        connection.executemany("INSERT INTO work_orders VALUES (?,?,?,?,?,?,?,?)", [
            ("WO-KS-260901", "KS-R01", "솔더 압연재 A", 3200, "2026-09-08", "압연 진행", 64, "데모 고객 A"),
            ("WO-KS-260902", "KS-W02", "솔더 와이어 B", 1800, "2026-09-10", "용해 완료", 41, "데모 고객 B"),
            ("WO-KS-260903", "KS-I03", "솔더 잉곳 C", 2500, "2026-09-12", "원료 확인", 18, "데모 고객 C"),
        ])
        connection.executemany("INSERT INTO raw_material_lots VALUES (?,?,?,?,?,?,?,?)", [
            ("RM-260827-SN", "주석계 원료", "데모 공급사 A", 5000, 2150, "확인", "사용가능", "2026-08-27 10:10"),
            ("RM-260829-AL", "알루미늄계 원료", "데모 공급사 B", 4000, 780, "확인", "사용가능", "2026-08-29 14:20"),
            ("RM-260901-ADD", "첨가 원료", "데모 공급사 C", 600, 110, "미첨부", "보류", "2026-09-01 09:20"),
        ])
        connection.executemany("INSERT INTO incoming_inspections VALUES (?,?,?,?,?,?,?,?,?)", [
            ("II-KS-001", "RM-260827-SN", "2026-08-27 11:00", "확인", "적합", "적합", "합격", "데모 검사자", "공급사 성적서 확인"),
            ("II-KS-002", "RM-260829-AL", "2026-08-29 15:00", "재확인", "적합", "적합", "조건부", "데모 검사자", "조성 기준 원문 미등록"),
            ("II-KS-003", "RM-260901-ADD", "2026-09-01 10:00", "미확인", "적합", "적합", "보류", "데모 검사자", "성적서 미첨부"),
        ])
        connection.executemany("INSERT INTO melting_batches VALUES (?,?,?,?,?,?,?,?,?,?)", [
            ("MB-260901-01", "WO-KS-260901", "FUR-01", "DEMO-R1", 1700, 1688, "2026-09-02 08:00", "2026-09-02 11:10", "완료", "데모 승인"),
            ("MB-260901-02", "WO-KS-260901", "FUR-01", "DEMO-R1", 1500, 980, "2026-09-03 08:20", None, "진행", "미승인"),
            ("MB-260902-01", "WO-KS-260902", "FUR-02", "DEMO-R2", 1800, 1782, "2026-09-02 13:00", "2026-09-02 16:30", "완료", "데모 승인"),
        ])
        connection.executemany("INSERT INTO process_readings VALUES (?,?,?,?,?,?,?,?,?)", [
            ("RD-KS-001", "MB-260901-01", "2026-09-02 09:10", 612, 35, 42, 28, 9.4, "데모 정상"),
            ("RD-KS-002", "MB-260901-02", "2026-09-03 09:30", 628, 47, 38, 41, 14.8, "데모 주의"),
            ("RD-KS-003", "MB-260902-01", "2026-09-02 14:20", 598, 32, 44, 25, 8.6, "데모 정상"),
        ])
        connection.executemany("INSERT INTO casting_rolling VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            ("PR-KS-001", "MB-260901-01", "주조", "CAST-01", "2026-09-02 11:20", "2026-09-02 12:10", 1688, 1660, None, 320, "완료"),
            ("PR-KS-002", "MB-260901-01", "압연", "ROLL-01", "2026-09-03 08:00", None, 1660, 1180, 1.2, 300, "진행"),
            ("PR-KS-003", "MB-260902-01", "주조", "CAST-02", "2026-09-02 16:40", "2026-09-02 17:25", 1782, 1751, None, 18, "완료"),
        ])
        connection.executemany("INSERT INTO quality_inspections VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            ("QI-KS-001", "WO-KS-260901", "MB-260901-01", "공정검사", "2026-09-02 11:15", 3, "데모 적합", "미측정", "적합", "조건부", "데모 품질팀"),
            ("QI-KS-002", "WO-KS-260902", "MB-260902-01", "완료검사", "2026-09-02 17:40", 5, "데모 적합", "적합", "적합", "합격", "데모 품질팀"),
        ])
        connection.executemany("INSERT INTO packages VALUES (?,?,?,?,?,?,?,?)", [
            ("PK-KS-260902-A", "WO-KS-260902", "MB-260902-01", "코일", 1742, "확인", "2026-09-03 10:20", "출하검토"),
        ])
        connection.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)", [
            ("SH-KS-001", "WO-KS-260902", "PK-KS-260902-A", "2026-09-07", None, 1742, "승인대기", "데모 품질 승인 검토"),
        ])

    @staticmethod
    def _seed_knowledge(connection):
        root = Path(__file__).resolve().parents[1] / "sample_docs" / "knowledge"
        for path in sorted(root.glob("KS-KB-*.md")):
            text = path.read_text(encoding="utf-8")
            head, body = text.split("\n---\n", 1)
            meta = json.loads(head)
            connection.execute("INSERT INTO knowledge_documents VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(document_id) DO NOTHING", (
                meta["document_id"], path.name, meta["title"], meta["revision"], meta["owner"],
                meta["effective_date"], meta["status"], meta["keywords"], body, "로컬 데모 문서"))
        rules = root / "rules.json"
        if rules.exists():
            for rule in json.loads(rules.read_text(encoding="utf-8")):
                connection.execute("INSERT INTO rules VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(rule_id) DO NOTHING", tuple(rule[k] for k in (
                    "rule_id", "name", "source_table", "condition", "owner", "action", "source_document", "revision", "status")))

    def dashboard(self):
        with self._connect() as c:
            return {
                "active_orders": c.execute("SELECT COUNT(*) FROM work_orders WHERE progress_pct<100").fetchone()[0],
                "melt_alerts": c.execute("SELECT COUNT(*) FROM process_readings WHERE status LIKE '%주의%'").fetchone()[0],
                "incoming_holds": c.execute("SELECT COUNT(*) FROM incoming_inspections WHERE final_result!='합격'").fetchone()[0],
                "quality_holds": c.execute("SELECT COUNT(*) FROM quality_inspections WHERE final_result!='합격'").fetchone()[0],
                "shipment_pending": c.execute("SELECT COUNT(*) FROM shipments WHERE status!='출하완료'").fetchone()[0],
            }

    def get_work_orders(self, work_order=None, status=None):
        sql, params = "SELECT * FROM work_orders WHERE 1=1", []
        if work_order: sql += " AND work_order=?"; params.append(work_order)
        if status: sql += " AND status LIKE ?"; params.append(f"%{status}%")
        return self._query(sql + " ORDER BY due_date", tuple(params))

    def get_material_lots(self, material_lot=None, issues_only=False):
        sql, params = "SELECT m.*,i.final_result,i.note FROM raw_material_lots m LEFT JOIN incoming_inspections i USING(material_lot) WHERE 1=1", []
        if material_lot: sql += " AND m.material_lot=?"; params.append(material_lot)
        if issues_only: sql += " AND (m.quarantine_status!='사용가능' OR i.final_result!='합격')"
        return self._query(sql + " ORDER BY m.received_at DESC", tuple(params))

    def get_melting_status(self, melt_batch=None, alerts_only=False):
        sql, params = "SELECT b.*,r.measured_at,r.temperature_c,r.hold_time_min,r.stir_speed_rpm,r.oxygen_ppm,r.dross_kg,r.status AS reading_status FROM melting_batches b LEFT JOIN process_readings r USING(melt_batch) WHERE 1=1", []
        if melt_batch: sql += " AND b.melt_batch=?"; params.append(melt_batch)
        if alerts_only: sql += " AND r.status LIKE '%주의%'"
        return self._query(sql + " ORDER BY b.started_at DESC", tuple(params))

    def get_process_trace(self, work_order):
        jobs = self.get_work_orders(work_order)
        melts = self._query("SELECT * FROM melting_batches WHERE work_order=? ORDER BY started_at", (work_order,))
        return {"work_order": jobs[0] if jobs else None, "melting": melts,
                "readings": self._query("SELECT r.* FROM process_readings r JOIN melting_batches b USING(melt_batch) WHERE b.work_order=?", (work_order,)),
                "casting_rolling": self._query("SELECT p.* FROM casting_rolling p JOIN melting_batches b USING(melt_batch) WHERE b.work_order=?", (work_order,)),
                "quality": self._query("SELECT * FROM quality_inspections WHERE work_order=?", (work_order,)),
                "packages": self._query("SELECT * FROM packages WHERE work_order=?", (work_order,)),
                "shipments": self._query("SELECT * FROM shipments WHERE work_order=?", (work_order,))}

    def get_quality_status(self, work_order=None, issues_only=False):
        sql, params = "SELECT * FROM quality_inspections WHERE 1=1", []
        if work_order: sql += " AND work_order=?"; params.append(work_order)
        if issues_only: sql += " AND final_result!='합격'"
        return self._query(sql + " ORDER BY inspected_at DESC", tuple(params))

    def get_shipment_status(self, work_order=None):
        sql, params = "SELECT s.*,p.label_status,p.net_weight_kg FROM shipments s LEFT JOIN packages p USING(package_lot) WHERE 1=1", []
        if work_order: sql += " AND s.work_order=?"; params.append(work_order)
        return self._query(sql + " ORDER BY planned_date", tuple(params))

    @staticmethod
    def _terms(text):
        words = re.findall(r"[가-힣A-Za-z0-9]+", text.lower())
        return {p for word in words for p in [word] + [word[i:i+2] for i in range(len(word)-1)] if len(p) >= 2}

    def search_knowledge(self, query, limit=5):
        tokens = self._terms(query)
        docs = self.knowledge_documents()
        ranked = []
        for doc in docs:
            score = len(tokens & self._terms(doc["title"] + " " + doc["keywords"] + " " + doc["body"]))
            if score: ranked.append({**doc, "score": score, "text": doc["body"]})
        return sorted(ranked, key=lambda d: (-d["score"], d["document_id"]))[:max(1, min(int(limit), 20))]

    def knowledge_documents(self):
        rows = self._query("SELECT * FROM knowledge_documents ORDER BY document_id")
        return [{**row, "content":row["body"], "source":row["source_label"]} for row in rows]

    def save_uploaded_document(self, document_id, filename, content=None):
        with self._connect() as c:
            c.execute("INSERT INTO knowledge_documents (document_id,filename,title,revision,owner,effective_date,status,keywords,body,source_label) VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET filename=excluded.filename,title=excluded.title,body=excluded.body,source_label=excluded.source_label", (
                document_id, filename, filename, "업로드", "업로드 사용자", "미확인", "OpenAI File Search 연결", filename, content or "", "업로드 문서"))

    def get_rules(self, query=None):
        rows = self._query("SELECT * FROM rules ORDER BY rule_id")
        return [r for r in rows if not query or self._terms(query) & self._terms(" ".join(map(str, r.values())))]

    def table_inventory(self):
        with self._connect() as c:
            return [{"table":t,"label":self.TABLE_LABELS[t],"rows":c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0],"count":c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0],"exists":True} for t in TABLES if t != "settings"]

    def table_records(self, table_name, limit=25, offset=0):
        if table_name not in TABLES or table_name == "settings": raise ValueError("조회할 수 없는 테이블입니다.")
        if not 1 <= int(limit) <= 100 or int(offset) < 0: raise ValueError("조회 범위가 올바르지 않습니다.")
        return self._query(f"SELECT * FROM {table_name} ORDER BY 1 LIMIT ? OFFSET ?", (int(limit), int(offset)))

    def setting(self, key):
        rows = self._query("SELECT value FROM settings WHERE key=?", (key,))
        return rows[0]["value"] if rows else None

    def save_setting(self, key, value):
        with self._connect() as c:
            c.execute("INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


class PostgresRepository(GoryeoSolderRepository):
    def __init__(self, url):
        import psycopg
        self.url = url
        with psycopg.connect(url) as raw:
            raw.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self._initialize()
        with self._connect() as c:
            c.execute("ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS embedding vector(1536)")
            c.execute("CREATE INDEX IF NOT EXISTS knowledge_documents_embedding_idx ON knowledge_documents USING hnsw (embedding vector_cosine_ops)")

    def _connect(self):
        import psycopg
        from pgvector.psycopg import register_vector
        raw = psycopg.connect(self.url, row_factory=_compat_row)
        register_vector(raw)
        return _PgConnection(raw)


class _PgConnection:
    def __init__(self, raw): self.raw = raw
    def __enter__(self): return self
    def __exit__(self, typ, value, tb):
        self.raw.rollback() if typ else self.raw.commit(); self.raw.close()
    def execute(self, sql, params=()): return self.raw.execute(sql.replace("?", "%s"), params)
    def executemany(self, sql, values): return self.raw.executemany(sql.replace("?", "%s"), values)
    def executescript(self, script):
        for statement in script.split(";"):
            if statement.strip(): self.execute(statement)


class _CompatRow(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def _compat_row(cursor):
    columns = [desc.name for desc in cursor.description]
    return lambda values: _CompatRow(zip(columns, values))


def create_repository(sqlite_path):
    url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    return PostgresRepository(url) if url else GoryeoSolderRepository(sqlite_path)
