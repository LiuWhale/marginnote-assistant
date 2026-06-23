#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


HOME = Path.home()
DB_PATH = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
PARK_BOOK_MD5 = "253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246"
PARK_TOPIC_ID = "CA970092-A137-40D7-9A78-DD76EB407C05"
PARK_CANONICAL_TOPIC = "AAFA4811-8B3A-46AF-8511-6037060FA23B"


def rows_to_dicts(cursor: sqlite3.Cursor, rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    names = [item[0] for item in cursor.description or []]
    return [{names[i]: row[i] for i in range(len(names))} for row in rows]


def query_all(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return rows_to_dicts(cur, cur.fetchall())


def audit(db_path: Path, book_md5: str, topic_id: str) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        summary = query_all(
            conn,
            """
            select ZTOPICID as topicid,
                   coalesce(ZAUTHOR, '') as author,
                   ZTYPE as type,
                   count(*) as rows,
                   sum(case when ZHIGHLIGHTS is not null then 1 else 0 end) as highlight_blob_rows,
                   sum(case when ZHIGHLIGHT_PIC is not null then 1 else 0 end) as highlight_pic_rows,
                   min(ZSTARTPAGE) as first_page,
                   max(ZSTARTPAGE) as last_page
              from ZBOOKNOTE
             where ZBOOKMD5=?
             group by ZTOPICID, ZAUTHOR, ZTYPE
             order by rows desc
            """,
            (book_md5,),
        )
        target = query_all(
            conn,
            """
            select coalesce(ZAUTHOR, '') as author,
                   ZTYPE as type,
                   count(*) as rows,
                   sum(case when ZHIGHLIGHTS is not null then 1 else 0 end) as highlight_blob_rows,
                   sum(case when ZHIGHLIGHT_PIC is not null then 1 else 0 end) as highlight_pic_rows
              from ZBOOKNOTE
             where ZBOOKMD5=? and ZTOPICID=?
             group by ZAUTHOR, ZTYPE
             order by rows desc
            """,
            (book_md5, topic_id),
        )
        examples = query_all(
            conn,
            """
            select Z_PK as pk,
                   ZTOPICID as topicid,
                   coalesce(ZAUTHOR, '') as author,
                   ZTYPE as type,
                   ZSTARTPAGE as page,
                   length(ZHIGHLIGHTS) as highlight_blob_bytes,
                   length(ZHIGHLIGHT_PIC) as highlight_pic_bytes,
                   substr(coalesce(ZHIGHLIGHT_TEXT, ''), 1, 120) as highlight_text,
                   substr(coalesce(ZNOTETITLE, ''), 1, 120) as title
              from ZBOOKNOTE
             where ZBOOKMD5=?
               and ZHIGHLIGHTS is not null
             order by Z_PK desc
             limit 20
            """,
            (book_md5,),
        )
    finally:
        conn.close()

    target_blob_rows = sum(int(row.get("highlight_blob_rows") or 0) for row in target)
    target_rows = sum(int(row.get("rows") or 0) for row in target)
    return {
        "db_path": str(db_path),
        "book_md5": book_md5,
        "topic_id": topic_id,
        "target_rows": target_rows,
        "target_highlight_blob_rows": target_blob_rows,
        "target_has_native_highlight_blobs": target_blob_rows > 0,
        "canonical_topic": PARK_CANONICAL_TOPIC if book_md5 == PARK_BOOK_MD5 else "",
        "topic_summary": summary,
        "target_summary": target,
        "blob_examples": examples,
        "interpretation": (
            "Visible MN4 PDF highlights appear to require ZHIGHLIGHTS/ZHIGHLIGHT_PIC blobs. "
            "Rows without these blobs may exist as notes/cards but are not reliable visible highlights."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only audit of MarginNote native highlight blob state.")
    parser.add_argument("--db", default=str(DB_PATH), help="Path to MarginNote SQLite database.")
    parser.add_argument("--bookmd5", default=PARK_BOOK_MD5, help="MarginNote document md5.")
    parser.add_argument("--topicid", default=PARK_TOPIC_ID, help="MarginNote topic/notebook id.")
    args = parser.parse_args()

    db_path = Path(args.db).expanduser()
    if not db_path.exists():
        raise SystemExit(f"database not found: {db_path}")
    result = audit(db_path, args.bookmd5, args.topicid)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["target_has_native_highlight_blobs"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
