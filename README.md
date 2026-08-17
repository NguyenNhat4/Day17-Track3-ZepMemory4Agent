# Lab 17 - Multi-Memory Agent voi Zep

Bo starter kit cho buoi lab 150-180 phut ve Memory Systems for Agents.

## Kien truc

- **Zep Cloud V3**: user graph, thread, context block, facts, episodes, standalone semantic graph.
- **Short-term memory local**: buffer / summary / sliding window + compaction.
- **Redis local**: baseline KV cho profile, TTL va open-loop task.
- **Qdrant local**: baseline vector store de so sanh voi managed semantic memory.
- **LangGraph**: orchestration skeleton cho route -> retrieve -> assemble -> answer.
- **Ground-truth evaluator**: doc `data/sessions.json` chua session chat + expected layer + expected evidence.

> Luu y 2026: lab dung **Zep Cloud V3 SDK**. Docker dong goi app/client va cac local baseline; khong khoi dong Zep Community Edition cu.

## Quick start

```bash
cp .env.example .env
# dien ZEP_API_KEY vao .env

docker compose build
docker compose up -d redis qdrant
docker compose run --rm app python -m src.seed

docker compose run --rm app python -m src.evaluate --impl reference --reuse-seeded
```

Ket qua reference duoc ghi vao `reports/benchmark_reference.json` va `reports/benchmark_reference.md`. Student run ghi vao `reports/benchmark.json` va `reports/benchmark.md`.

## Che do hoc vien

Huong dan day du, checklist tung pha va **bang diem 80+10+10**: xem [`LAB.md`](LAB.md).

Hoc vien **viet code** tai 4 marker `LAB TODO` trong `src/memory_student.py`:

| TODO | Ham | Viec can lam | Case cham |
| --- | --- | --- | --- |
| 1/4 | `retrieve_long_term` | `prime_eval_thread` (da co) → `thread.get_user_context` → return `.context` | E02, E03, E08, E09 |
| 2/4 | `retrieve_episodic` | `graph.search(user_id=..., scope="episodes")` + `render_graph_search` | E04, E05 |
| 3/4 | `retrieve_semantic` | `graph.search(graph_id=..., scope="episodes")`; fallback `nodes`. Tranh `scope="auto"` (mat marker literal) | E06, E11 |
| 4/4 | `assemble_context` | `ContextBudgetManager.assemble` (budget 10/4/3/3, priority STM→LT→EP→SEM) | E07 |

Cac task **khong viet code** nhung van tinh diem: smoke/seed, demo short-term (E01/E10), no-memory baseline, comparison, privacy forget, `README_submission.md`.

```bash
docker compose run --rm app python -m src.smoke
docker compose run --rm app python -m src.seed
docker compose run --rm app python -m src.demo_short_term
docker compose run --rm app python -m src.evaluate --impl no_memory
docker compose run --rm app python -m src.evaluate --impl student --reuse-seeded
docker compose run --rm app python -m src.compare_reports
# CHI sau khi da commit reports/ practice. Chup privacy, roi seed lai neu can golden.
# Phut 110: copy data/golden_eval.json (giang vien phat), roi:
docker compose run --rm app python -m src.evaluate --impl student --reuse-seeded --golden
# Bonus UI:
# OPENAI_API_KEY trong .env de chat; retrieval van chay khong can OpenAI
# make ui   # http://localhost:8501
```

### Bang diem (tran 80 + cong)

| Khoi | Diem | Nguon cham |
| --- | ---: | --- |
| 11 case E01-E11 | **56** | `reports/benchmark.json` |
| Privacy drill | **6** | screenshot forget + verify-only |
| 4 cau phan tich + `comparison.md` | **6** | `README_submission.md` |
| 3 cau thuc hanh | **6** | `README_submission.md` |
| Artefact | **6** | repo |
| **Tran nen** | **80** | |
| Golden 20/20 | **+10 hoac 0** | `reports/golden_benchmark.json` |
| UI demo (hoac report dep toi da 6) | **+10** | `src/demo_ui.py` |
| **Tong toi da** | **100** | |

Golden: giang vien phat file **60 phut cuoi**. `data/golden_eval.json` **gitignore**. 20/20 moi duoc 10; thieu 1 case = 0.

**Dat lab:** >= 56/80 **va** hit rate >= 80% (9/11 PASS) **va** nop du code + `benchmark.md` + `README_submission.md` **va** khong commit secret. Golden/UI khong bat buoc de pass.

### Nop bai (tom tat)

1. `src/memory_student.py` — 4 ham xong.
2. `reports/benchmark.md` + `reports/benchmark.json` + `reports/comparison.md`.
3. `README_submission.md` <= 400 tu.
4. 4 screenshot: long-term, episodic, semantic, privacy.
5. Khong nop `.env` / `ZEP_API_KEY` / `data/golden_eval.json`. Khong copy `memory_reference.py` roi doi ten.
6. Neu tranh diem cong: `reports/golden_benchmark.json` va/hoac UI demo.

## Demo them

```bash
# Demo 3 chien luoc short-term
docker compose run --rm app python -m src.demo_short_term

# Demo local Redis + Qdrant baseline
docker compose run --rm app python -m src.local_baseline

# Demo 3 session lay truc tiep tu data/sessions.json
docker compose run --rm app python -m src.demo_sessions

# Demo LangGraph retrieval agent
docker compose run --rm app python -m src.demo_agent --impl reference --reset

# Demo curated/compiled knowledge graph
docker compose run --rm app python -m src.compiled_kb --reset

# Privacy drill: xoa user memory
# CHI chay sau khi benchmark xong
docker compose run --rm app python -m src.forget --user-id minh-lab17
```

## Cau truc thu muc

```text
.
├── LAB.md
├── README.md
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
├── .env.example
├── control_plane/
│   ├── AGENTS.md
│   ├── CONTEXT_LAYERS.md
│   ├── SOUL.md
│   ├── MEMORY.md
│   ├── MEMORY_SCHEMA.md
│   └── TASKS.md
├── data/
│   ├── sessions.json
│   ├── ground_truth.json
│   ├── consent.json
│   ├── knowledge.jsonl
│   └── compiled_kb.jsonl
├── src/
│   ├── short_term.py
│   ├── context_budget.py
│   ├── router.py
│   ├── zep_common.py
│   ├── memory_reference.py
│   ├── memory_student.py
│   ├── seed.py
│   ├── evaluate.py
│   ├── no_memory.py
│   ├── compare_reports.py
│   ├── demo_sessions.py
│   ├── demo_agent.py
│   ├── demo_ui.py
│   ├── local_baseline.py
│   ├── episodic_maintenance.py
│   ├── compiled_kb.py
│   ├── privacy_guard.py
│   ├── heartbeat.py
│   └── forget.py
├── tests/
└── scripts/quickstart.sh
```

## Muc tieu benchmark

Co **11 evaluation cases** (E01-E11) phu 4 memory layer + 1 case mixed. Score chinh la **retrieval hit rate** tren ground truth (`must_contain_all` / `must_not_contain`). Benchmark danh gia memory retrieval truc tiep, khong de chat model che lap loi retrieval.

Muc tieu: **>= 9/11 PASS (80%)** tren practice set. Tran nen **80**. Golden 20/20 **+10**. UI **+10**. Chi tiet: [`LAB.md` muc 5](LAB.md#5-kiem-tra-ket-qua).
