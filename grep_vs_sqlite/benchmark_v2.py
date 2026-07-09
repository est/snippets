#!/usr/bin/env python3
"""
微信聊天记录存储方案基准测试 v2 —— "邪路"专场 (优化版)
利用聊天记录 append-only/不可变 的特性，测试各种非传统方案。
"""

import os
import sys
import time
import json
import mmap
import struct
import random
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import duckdb
import polars as pl
import zstandard as zstd

sys.path.insert(0, str(Path(__file__).parent))
from benchmark import (
    generate_messages, SEARCH_KEYWORDS, WORK_DIR,
    save_as_plaintext, save_as_sqlite, save_as_sqlite_fts,
    bench_grep, bench_sqlite_like, bench_sqlite_fts,
    TALKERS,
)

RG_PATH = "/Applications/Cursor.app/Contents/Resources/app/node_modules/@vscode/ripgrep/bin/rg"
ROUNDS = 3

def P(msg):
    print(msg, flush=True)


# ============ DuckDB ============

def save_as_duckdb(messages, filepath):
    if os.path.exists(filepath):
        os.remove(filepath)
    conn = duckdb.connect(filepath)
    conn.execute("""CREATE TABLE message (
        msgId INTEGER PRIMARY KEY, msgSvrId BIGINT, type INTEGER,
        isSend INTEGER, createTime INTEGER, talker VARCHAR,
        content VARCHAR, imgPath VARCHAR)""")
    conn.executemany(
        "INSERT INTO message VALUES (?,?,?,?,?,?,?,?)",
        [(m["msgId"], m["msgSvrId"], m["type"], m["isSend"],
          m["createTime"], m["talker"], m["content"], m["imgPath"]) for m in messages])
    conn.execute("PRAGMA create_fts_index('message', 'msgId', 'content', overwrite=1)")
    conn.close()


def bench_duckdb_contains(db_path, keyword):
    conn = duckdb.connect(db_path, read_only=True)
    start = time.perf_counter()
    r = conn.execute("SELECT COUNT(*) FROM message WHERE contains(content, ?)", [keyword]).fetchone()[0]
    elapsed = time.perf_counter() - start
    conn.close()
    return elapsed, r


def bench_duckdb_fts(db_path, keyword):
    conn = duckdb.connect(db_path, read_only=True)
    start = time.perf_counter()
    r = conn.execute("""SELECT COUNT(*) FROM (
        SELECT fts_main_message.match_bm25(msgId, ?) AS score FROM message
    ) WHERE score IS NOT NULL""", [keyword]).fetchone()[0]
    elapsed = time.perf_counter() - start
    conn.close()
    return elapsed, r


# ============ Parquet ============

def save_as_parquet(messages, filepath):
    df = pl.DataFrame(messages)
    df.write_parquet(filepath, compression="zstd")


def bench_parquet_duckdb(filepath, keyword):
    conn = duckdb.connect()
    start = time.perf_counter()
    r = conn.execute(f"SELECT COUNT(*) FROM read_parquet('{filepath}') WHERE contains(content, ?)", [keyword]).fetchone()[0]
    elapsed = time.perf_counter() - start
    conn.close()
    return elapsed, r


# ============ Polars ============

def bench_polars_scan(parquet_path, keyword):
    start = time.perf_counter()
    r = pl.scan_parquet(parquet_path).filter(
        pl.col("content").str.contains(keyword, literal=True)
    ).select(pl.len()).collect().item()
    elapsed = time.perf_counter() - start
    return elapsed, r


def bench_polars_inmemory(df, keyword):
    start = time.perf_counter()
    r = df.filter(pl.col("content").str.contains(keyword, literal=True)).height
    elapsed = time.perf_counter() - start
    return elapsed, r


# ============ mmap ============

def bench_mmap_search(filepath, keyword):
    keyword_bytes = keyword.encode("utf-8")
    start = time.perf_counter()
    count = 0
    with open(filepath, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        pos = 0
        while True:
            pos = mm.find(keyword_bytes, pos)
            if pos == -1:
                break
            count += 1
            pos += 1
        mm.close()
    elapsed = time.perf_counter() - start
    return elapsed, count


# ============ zstd 流式 ============

def save_as_zstd(src_path, dst_path, level=3):
    cctx = zstd.ZstdCompressor(level=level)
    with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
        cctx.copy_stream(fin, fout)


def bench_zstd_stream_search(compressed_path, keyword):
    keyword_bytes = keyword.encode("utf-8")
    dctx = zstd.ZstdDecompressor()
    count = 0
    start = time.perf_counter()
    with open(compressed_path, "rb") as f:
        reader = dctx.stream_reader(f)
        remainder = b""
        while True:
            chunk = reader.read(4 * 1024 * 1024)
            if not chunk:
                if remainder and keyword_bytes in remainder:
                    count += 1
                break
            data = remainder + chunk
            lines = data.split(b"\n")
            remainder = lines[-1]
            for line in lines[:-1]:
                if keyword_bytes in line:
                    count += 1
    elapsed = time.perf_counter() - start
    return elapsed, count


# ============ 倒排索引 (内存) ============

def build_inverted_index(messages, ngram_size=2):
    """2-gram 倒排索引，只用 msgId 列表（省内存用 array）"""
    from array import array
    index = defaultdict(lambda: array('I'))
    for msg in messages:
        content = msg["content"]
        mid = msg["msgId"]
        seen = set()
        for i in range(len(content) - ngram_size + 1):
            ng = content[i:i + ngram_size]
            if ng not in seen:
                index[ng].append(mid)
                seen.add(ng)
    return index


def bench_inverted_index(index, keyword, messages_dict, ngram_size=2):
    start = time.perf_counter()
    ngrams = [keyword[i:i + ngram_size] for i in range(len(keyword) - ngram_size + 1)]
    if not ngrams:
        return time.perf_counter() - start, 0

    candidate_ids = set(index.get(ngrams[0], []))
    for ng in ngrams[1:]:
        candidate_ids &= set(index.get(ng, []))
        if not candidate_ids:
            break

    count = sum(1 for mid in candidate_ids if keyword in messages_dict[mid])
    elapsed = time.perf_counter() - start
    return elapsed, count


# ============ Bloom Filter 分块 ============

class BloomFilter:
    __slots__ = ('bits', 'size', 'k')
    def __init__(self, size=262144, k=5):
        self.size = size
        self.k = k
        self.bits = bytearray(size // 8 + 1)

    def _positions(self, item_bytes):
        h = hashlib.md5(item_bytes).digest()
        a, b = struct.unpack_from("<HH", h, 0)
        for i in range(self.k):
            yield (a + i * b) % self.size

    def add(self, item_bytes):
        for p in self._positions(item_bytes):
            self.bits[p >> 3] |= (1 << (p & 7))

    def might_contain(self, item_bytes):
        return all(self.bits[p >> 3] & (1 << (p & 7)) for p in self._positions(item_bytes))


def build_bloom_chunks(messages, chunk_size=50000, ngram_size=2):
    chunks = []
    for i in range(0, len(messages), chunk_size):
        chunk_msgs = messages[i:i + chunk_size]
        bf = BloomFilter(size=1048576, k=5)
        for msg in chunk_msgs:
            content = msg["content"]
            for j in range(len(content) - ngram_size + 1):
                bf.add(content[j:j + ngram_size].encode("utf-8"))
        chunks.append((i, i + len(chunk_msgs), bf))
    return chunks


def bench_bloom_filter(bloom_chunks, messages, keyword, ngram_size=2):
    start = time.perf_counter()
    ng_bytes = [keyword[i:i+ngram_size].encode("utf-8") for i in range(len(keyword)-ngram_size+1)]
    count = 0
    scanned = 0
    skipped = 0
    for cs, ce, bf in bloom_chunks:
        if not all(bf.might_contain(ng) for ng in ng_bytes):
            skipped += 1
            continue
        scanned += 1
        for msg in messages[cs:ce]:
            if keyword in msg["content"]:
                count += 1
    elapsed = time.perf_counter() - start
    return elapsed, count, scanned, skipped


# ============ 分块 + ripgrep 并行 ============

def save_as_chunks(messages, chunk_dir, chunk_size=50000):
    os.makedirs(chunk_dir, exist_ok=True)
    for f in Path(chunk_dir).glob("*.tsv"):
        f.unlink()
    for i in range(0, len(messages), chunk_size):
        chunk_path = os.path.join(chunk_dir, f"chunk_{i//chunk_size:04d}.tsv")
        with open(chunk_path, "w", encoding="utf-8") as f:
            for msg in messages[i:i + chunk_size]:
                f.write(f"{msg['msgId']}\t{msg['type']}\t{msg['isSend']}\t{msg['createTime']}\t{msg['talker']}\t{msg['content']}\n")


def bench_rg_parallel_dir(chunk_dir, keyword):
    start = time.perf_counter()
    result = subprocess.run(
        [RG_PATH, "-c", "--no-ignore", "--no-heading", keyword, chunk_dir],
        capture_output=True, text=True)
    elapsed = time.perf_counter() - start
    count = 0
    if result.returncode == 0:
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                try:
                    count += int(line.rsplit(":", 1)[-1])
                except ValueError:
                    pass
    return elapsed, count


# ============ SQLite mmap ============

def bench_sqlite_mmap(db_path, keyword):
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA mmap_size={256*1024*1024};")
    start = time.perf_counter()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM message WHERE content LIKE ?", (f"%{keyword}%",))
    count = c.fetchone()[0]
    elapsed = time.perf_counter() - start
    conn.close()
    return elapsed, count


# ============ 主入口 ============

def run_extended_benchmark(msg_count=500000):
    P(f"\n{'='*70}")
    P(f"  微信聊天记录存储方案基准测试 v2 —— \"邪路\"专场")
    P(f"  消息数量: {msg_count:,} 条")
    P(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    P(f"{'='*70}\n")

    P("[1/8] 生成数据...")
    t0 = time.perf_counter()
    messages = generate_messages(msg_count)
    P(f"  {len(messages):,} 条消息 ({time.perf_counter()-t0:.2f}s)")

    tsv_path = str(WORK_DIR / "messages.tsv")
    parquet_path = str(WORK_DIR / "messages.parquet")
    duckdb_path = str(WORK_DIR / "messages.duckdb")
    zstd_path = str(WORK_DIR / "messages.tsv.zst")
    sqlite_path = str(WORK_DIR / "messages.db")
    sqlite_fts_path = str(WORK_DIR / "messages_fts.db")
    chunk_dir = str(WORK_DIR / "chunks")

    P("\n[2/8] 写入各格式...")
    t0 = time.perf_counter(); save_as_plaintext(messages, tsv_path); t_tsv = time.perf_counter()-t0
    P(f"  TSV:           {t_tsv:.3f}s  {os.path.getsize(tsv_path)/1024/1024:.1f}MB")

    t0 = time.perf_counter(); save_as_parquet(messages, parquet_path); t_pq = time.perf_counter()-t0
    P(f"  Parquet(zstd): {t_pq:.3f}s  {os.path.getsize(parquet_path)/1024/1024:.1f}MB")

    t0 = time.perf_counter(); save_as_duckdb(messages, duckdb_path); t_dk = time.perf_counter()-t0
    P(f"  DuckDB+FTS:    {t_dk:.3f}s  {os.path.getsize(duckdb_path)/1024/1024:.1f}MB")

    t0 = time.perf_counter(); save_as_sqlite(messages, sqlite_path); t_sq = time.perf_counter()-t0
    P(f"  SQLite:        {t_sq:.3f}s  {os.path.getsize(sqlite_path)/1024/1024:.1f}MB")

    t0 = time.perf_counter(); save_as_sqlite_fts(messages, sqlite_fts_path); t_fts = time.perf_counter()-t0
    P(f"  SQLite+FTS5:   {t_fts:.3f}s  {os.path.getsize(sqlite_fts_path)/1024/1024:.1f}MB")

    t0 = time.perf_counter(); save_as_zstd(tsv_path, zstd_path, level=3); t_zs = time.perf_counter()-t0
    P(f"  zstd压缩:      {t_zs:.3f}s  {os.path.getsize(zstd_path)/1024/1024:.1f}MB (压缩率{os.path.getsize(zstd_path)/os.path.getsize(tsv_path):.0%})")

    t0 = time.perf_counter(); save_as_chunks(messages, chunk_dir); t_ch = time.perf_counter()-t0
    n_chunks = len(list(Path(chunk_dir).glob("*.tsv")))
    P(f"  分块文件:      {t_ch:.3f}s  {n_chunks}块")

    P("\n[3/8] 构建倒排索引 (2-gram, 内存)...")
    t0 = time.perf_counter()
    inv_index = build_inverted_index(messages, ngram_size=2)
    t_inv = time.perf_counter() - t0
    P(f"  构建: {t_inv:.2f}s  ({len(inv_index):,} 个不同 2-gram)")
    messages_dict = {m["msgId"]: m["content"] for m in messages}

    P("\n[4/8] 构建 Bloom Filter...")
    t0 = time.perf_counter()
    bloom_chunks = build_bloom_chunks(messages, chunk_size=50000)
    t_bloom = time.perf_counter() - t0
    P(f"  构建: {t_bloom:.2f}s  ({len(bloom_chunks)} 块)")

    P("\n[5/8] 加载 Polars DataFrame...")
    t0 = time.perf_counter()
    df_polars = pl.read_parquet(parquet_path)
    t_pl_load = time.perf_counter() - t0
    P(f"  加载: {t_pl_load:.3f}s")

    # ============ 搜索测试 ============
    P(f"\n[6/8] 关键词搜索基准 (x{ROUNDS}轮, 取 min)")
    P(f"  关键词: {SEARCH_KEYWORDS}\n")

    results = {}

    def run_method(name, key, bench_fn):
        results[key] = {}
        P(f"  >>> {name}")
        for kw in SEARCH_KEYWORDS:
            times = []
            count = 0
            for _ in range(ROUNDS):
                elapsed, count = bench_fn(kw)
                times.append(elapsed)
            mn = min(times)
            results[key][kw] = {"min_ms": mn*1000, "count": count}
            P(f"      {kw}: {mn*1000:8.2f}ms  n={count}")

    def run_method_bloom(name, key):
        results[key] = {}
        P(f"  >>> {name}")
        for kw in SEARCH_KEYWORDS:
            times = []
            count = 0
            for _ in range(ROUNDS):
                elapsed, count, sc, sk = bench_bloom_filter(bloom_chunks, messages, kw)
                times.append(elapsed)
            mn = min(times)
            results[key][kw] = {"min_ms": mn*1000, "count": count}
            P(f"      {kw}: {mn*1000:8.2f}ms  n={count} (scan {sc}/skip {sk})")

    run_method("ripgrep (SIMD, TSV)", "rg",
               lambda kw: bench_grep(tsv_path, kw, "rg"))
    run_method("mmap 直接搜索", "mmap",
               lambda kw: bench_mmap_search(tsv_path, kw))
    run_method("grep (BSD)", "grep",
               lambda kw: bench_grep(tsv_path, kw, "grep"))
    run_method("SQLite LIKE", "sqlite_like",
               lambda kw: bench_sqlite_like(sqlite_path, kw))
    run_method("SQLite mmap模式 LIKE", "sqlite_mmap",
               lambda kw: bench_sqlite_mmap(sqlite_path, kw))
    run_method("SQLite FTS5 (trigram)", "sqlite_fts",
               lambda kw: bench_sqlite_fts(sqlite_fts_path, kw))
    run_method("DuckDB contains()", "duckdb_contains",
               lambda kw: bench_duckdb_contains(duckdb_path, kw))
    run_method("DuckDB FTS (BM25)", "duckdb_fts",
               lambda kw: bench_duckdb_fts(duckdb_path, kw))
    run_method("Parquet + DuckDB", "parquet_duckdb",
               lambda kw: bench_parquet_duckdb(parquet_path, kw))
    run_method("Polars lazy scan", "polars_lazy",
               lambda kw: bench_polars_scan(parquet_path, kw))
    run_method("Polars in-memory", "polars_mem",
               lambda kw: bench_polars_inmemory(df_polars, kw))
    run_method("zstd 流式解压搜索", "zstd_stream",
               lambda kw: bench_zstd_stream_search(zstd_path, kw))
    run_method("倒排索引 (2-gram)", "inverted",
               lambda kw: bench_inverted_index(inv_index, kw, messages_dict))
    run_method_bloom("Bloom Filter + 扫描", "bloom")
    run_method("ripgrep 多文件并行", "rg_parallel",
               lambda kw: bench_rg_parallel_dir(chunk_dir, kw))

    # ============ 复合查询 ============
    P(f"\n[7/8] 复合条件查询 (talker + 时间范围 + 关键词'会议')")
    test_talker = TALKERS[0]
    ts, te = int(datetime(2023,6,1).timestamp()), int(datetime(2023,12,31).timestamp())

    complex_results = {}

    conn = sqlite3.connect(sqlite_path)
    t0 = time.perf_counter()
    cnt = conn.execute("SELECT COUNT(*) FROM message WHERE talker=? AND createTime BETWEEN ? AND ? AND content LIKE '%会议%'",
                       (test_talker, ts, te)).fetchone()[0]
    complex_results["SQLite indexed"] = (time.perf_counter()-t0)*1000
    conn.close()
    P(f"  SQLite indexed:   {complex_results['SQLite indexed']:8.2f}ms  n={cnt}")

    conn = duckdb.connect(duckdb_path, read_only=True)
    t0 = time.perf_counter()
    cnt = conn.execute("SELECT COUNT(*) FROM message WHERE talker=? AND createTime BETWEEN ? AND ? AND contains(content,?)",
                       [test_talker, ts, te, "会议"]).fetchone()[0]
    complex_results["DuckDB"] = (time.perf_counter()-t0)*1000
    conn.close()
    P(f"  DuckDB:           {complex_results['DuckDB']:8.2f}ms  n={cnt}")

    t0 = time.perf_counter()
    cnt = df_polars.filter(
        (pl.col("talker")==test_talker)&
        (pl.col("createTime")>=ts)&(pl.col("createTime")<=te)&
        pl.col("content").str.contains("会议", literal=True)
    ).height
    complex_results["Polars in-mem"] = (time.perf_counter()-t0)*1000
    P(f"  Polars in-memory: {complex_results['Polars in-mem']:8.2f}ms  n={cnt}")

    t0 = time.perf_counter()
    subprocess.run(f"'{RG_PATH}' --no-ignore '{test_talker}' '{tsv_path}' | '{RG_PATH}' --no-ignore '会议'",
                   shell=True, capture_output=True)
    complex_results["ripgrep pipe"] = (time.perf_counter()-t0)*1000
    P(f"  ripgrep pipe:     {complex_results['ripgrep pipe']:8.2f}ms")

    t0 = time.perf_counter()
    subprocess.run(f"grep '{test_talker}' '{tsv_path}' | grep '会议'",
                   shell=True, capture_output=True)
    complex_results["grep pipe"] = (time.perf_counter()-t0)*1000
    P(f"  grep pipe:        {complex_results['grep pipe']:8.2f}ms")

    # ============ 存储大小 ============
    P(f"\n[8/8] 存储大小")
    sizes = {}
    for name, path in [("TSV", tsv_path), ("Parquet(zstd)", parquet_path),
                        ("DuckDB+FTS", duckdb_path), ("SQLite", sqlite_path),
                        ("SQLite+FTS5", sqlite_fts_path), ("zstd压缩", zstd_path)]:
        s = os.path.getsize(path)
        sizes[name] = s
        P(f"  {name:16s}: {s/1024/1024:6.1f} MB")

    # ============ 排名 ============
    P(f"\n{'='*70}")
    P(f"  最终排名 (按关键词搜索平均最小延迟)")
    P(f"{'='*70}")
    ranking = []
    for key, data in results.items():
        vals = [v["min_ms"] for v in data.values()]
        if vals:
            avg = sum(vals)/len(vals)
            ranking.append((key, avg))
    ranking.sort(key=lambda x: x[1])

    name_map = {
        "rg": "ripgrep (SIMD)", "mmap": "mmap 直接搜索", "grep": "grep (BSD)",
        "sqlite_like": "SQLite LIKE", "sqlite_mmap": "SQLite mmap LIKE",
        "sqlite_fts": "SQLite FTS5", "duckdb_contains": "DuckDB contains",
        "duckdb_fts": "DuckDB FTS", "parquet_duckdb": "Parquet+DuckDB",
        "polars_lazy": "Polars lazy", "polars_mem": "Polars in-mem",
        "zstd_stream": "zstd流式解压", "inverted": "倒排索引",
        "bloom": "Bloom+扫描", "rg_parallel": "rg多文件并行",
    }

    for rank, (key, avg) in enumerate(ranking, 1):
        name = name_map.get(key, key)
        bar = "█" * max(1, min(60, int(avg / 2)))
        P(f"  {rank:2d}. {name:22s} {avg:8.2f}ms {bar}")

    all_results = {"search": {}, "complex": complex_results, "sizes": sizes, "msg_count": msg_count}
    for k, v in results.items():
        all_results["search"][name_map.get(k,k)] = v
    with open(WORK_DIR / "results_v2.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str, ensure_ascii=False)
    P(f"\n  保存: bench_data/results_v2.json")
    P(f"{'='*70}\n")
    return all_results


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500000
    run_extended_benchmark(count)
