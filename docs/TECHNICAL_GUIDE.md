# Lab 17 Technical Guide - Multi-Memory Agent voi Zep

Tai lieu nay la runbook de hoan thien lab theo dung thu tu ky thuat. Moi buoc
gom bon phan: muc tieu, lenh thuc hien, ket qua can dat va cach xu ly loi.

Pham vi cua phan 1:

1. Hieu kien truc va pham vi duoc phep sua.
2. Cau hinh Docker, Zep Cloud, Redis va Qdrant.
3. Smoke test va seed dataset.
4. Kiem tra short-term memory va compaction.

> Phan tiep theo se huong dan 4 TODO trong `src/memory_student.py`, benchmark
> E01-E11, privacy drill, golden set, UI va checklist nop bai.

## 1. Ket qua can dat

Sau khi hoan thanh toan bo lab, phan code hoc vien chi tap trung vao bon ham
trong `src/memory_student.py`:

| Ham | Memory layer | Case chinh |
| --- | --- | --- |
| `retrieve_long_term` | Long-term / declarative | E02, E03, E08, E09 |
| `retrieve_episodic` | Episodic | E04, E05 |
| `retrieve_semantic` | Semantic domain knowledge | E06, E11 |
| `assemble_context` | Router + token budget | E07 |

Muc tieu practice set la it nhat `9/11` case PASS. Mot case PASS khi tat ca
marker trong `must_contain_all` xuat hien trong retrieved text va khong co
marker nao trong `must_not_contain`.

Khong sua cac thanh phan sau:

- `src/memory_reference.py`: implementation mau de so sanh, khong phai bai lam.
- `src/evaluate.py`, `src/zep_common.py`, dataset va ground truth.
- `control_plane/*`: day la identity, policy va schema cua agent.
- Dockerfile, docker-compose va scoring logic.


```text
sessions.json
    |
    v
seed / ingestion
    |
    +--> Zep user graph: long-term facts + episodes
    |
    +--> Zep standalone graph: semantic/domain knowledge
    |
query --> router --> retrieve tung layer --> token budget --> merged context
                                      |
                                      v
                              evaluator / demo agent
```

### 2.1. Vai tro cua tung thanh phan

- **Short-term memory:** state nong cua thread hien tai. Lab cung cap buffer,
  summary va sliding window local, khong can Zep.
- **Long-term memory:** preference, decision va open loop cua user qua nhieu
  thread. Phai truy cap theo `user_id`.
- **Episodic memory:** trajectory da xay ra, gom tried/worked/reflection va
  provenance. Cung truy cap theo `user_id`, khong dung semantic graph.
- **Semantic memory:** tri thuc dung chung cua domain. Phai truy cap bang
  `graph_id`, khong gan voi mot user.
- **Context budget:** cat context theo ty le `10/4/3/3`, theo thu tu short-term,
  long-term, episodic, semantic.

### 2.2. Luat bao mat quan trong

- Khong commit `.env` hoac `ZEP_API_KEY`.
- Khong commit `data/golden_eval.json`; file nay duoc giang vien phat sau.
- Khong dung `user_id` de truy van semantic graph.
- Khong dung `graph_id` cua semantic graph cho episodic/user memory.
- Luon chay benchmark va luu report truoc khi chay lenh xoa user.

## 3. Chuan bi moi truong

### Buoc 1: Di chuyen vao thu muc lab

```bash
cd Day17-Track3-ZepMemory4Agent
```

Neu dang o workspace khac, dung duong dan tuyet doi den thu muc nay. Cac lenh
Docker trong tai lieu deu duoc chay tu root cua lab.

### Buoc 2: Tao file moi truong

```bash
cp .env.example .env
```

Mo `.env` va dien gia tri:

```dotenv
ZEP_API_KEY=<api-key-cua-ban>
```

Cac gia tri Redis, Qdrant va context token da co default phu hop voi
`docker-compose.yml`; khong can doi o lan chay dau.

Kiem tra file khong bi commit:

```bash
git status --short
```

Neu `.env` xuat hien trong danh sach can commit, bo file khoi staging va kiem
tra `.gitignore` truoc khi tiep tuc. Khong paste API key vao report hoac
screenshot.

### Buoc 3: Build image

```bash
docker compose build
```

Lenh nay cai dependencies Python trong image, gom Zep SDK, Redis client,
Qdrant client, requests va pytest. Neu build loi do cache hoac image cu, thu:

```bash
docker compose build --no-cache
```

Chi dung `--no-cache` khi can; build binh thuong nhanh hon cho cac lan sau.

### Buoc 4: Khoi dong local services

```bash
docker compose up -d redis qdrant
docker compose ps
```

Can thay:

- Redis o trang thai `Up` va health check `healthy`.
- Qdrant o trang thai `Up`.

`app` khong can chay foreground. Moi lenh `docker compose run --rm app ...`
tao mot container app tam thoi, dung chung hai service local va mount source
code vao `/workspace`.

## 4. Smoke test

Chay smoke test truoc khi sua code:

```bash
docker compose run --rm app python -m src.smoke
```

Ket qua dung phai co bon dong `[OK]` tuong tu:

```text
[OK] Redis reachable
[OK] Qdrant reachable
[OK] sessions.json valid: 11 evaluations
[OK] ZEP_API_KEY is present
```

### Xu ly loi smoke test

| Loi | Nguyen nhan | Cach xu ly |
| --- | --- | --- |
| `Redis unreachable` | Container chua san sang hoac da dung | Chay `docker compose up -d redis qdrant`, sau do `docker compose ps` |
| `Qdrant unreachable` | Qdrant dang khoi dong | Cho vai giay va chay lai smoke |
| `sessions.json is incomplete` | Sai thu muc hoac dataset bi sua | Chay lenh tu root lab, khong sua dataset |
| `ZEP_API_KEY is missing` | `.env` chua co key | Dien key vao `.env`, khong dat key truc tiep trong source |

Neu Docker bao loi port `6379` hoac `6333` da duoc su dung, dung process dang
chiem port hoac doi port host trong local compose. Khong doi URL noi bo
`redis:6379` va `qdrant:6333` ma code dang su dung trong network Docker.

## 5. Seed Zep va dataset

Chi seed sau khi smoke test PASS:

```bash
docker compose run --rm app python -m src.seed
```

`src.seed` thuc hien cac viec sau:

1. Reset hai synthetic user cua lab.
2. Tao user va thread tren Zep Cloud V3.
3. Ingest cac session trong `data/sessions.json`.
4. Seed standalone semantic graph tu `data/knowledge.jsonl`.
5. Poll den khi cac marker chinh co the search duoc.

Seed co the mat vai phut vi graph ingestion cua Zep la bat dong bo. Khong
terminate container khi script dang poll. Neu seed loi giua chung, chay lai
`docker compose run --rm app python -m src.seed`; script se reset lai du lieu
synthetic truoc khi ingest lai.

Sau khi seed, khong can ingest lai moi lan evaluate. Su dung flag:

```bash
--reuse-seeded
```

Vi du chay implementation reference de kiem tra moi truong:

```bash
docker compose run --rm app python -m src.evaluate \
  --impl reference --reuse-seeded
```

Khong dung ket qua `reference` de nop bai student. Reference chi la moc ky
thuat de xac nhan Zep va evaluator hoat dong.

## 6. Kiem tra data va ground truth

Mo `data/sessions.json` va doc mot vai evaluation. Moi case co dang:

```json
{
  "id": "E04",
  "expected_layer": "episodic",
  "query": "Lan truoc ta fix async HTTP timeout bang cach nao?",
  "must_contain_all": ["ClientSession", "concurrency=20"]
}
```

`must_contain_all` la evidence ma retrieval phai tra ve. Evaluator khong cham
cau tra loi nghe hop ly cua LLM; no cham text duoc retrieve. Cach nay ngan
retrieval sai bi che lap bang hallucination.

Doc them `data/consent.json`: durable ingestion chi duoc phep cho user co
`memory_opt_in: true`. Day la mot gate privacy co y trong lab.

## 7. Short-term memory va compaction

### Buoc 1: Chay demo ba strategy

```bash
docker compose run --rm app python -m src.demo_short_term
```

So sanh ba che do:

- **Buffer:** giu toan bo message, de hieu nhat nhung token tang tuyen tinh.
- **Summary:** nen cac turn cu thanh summary, tiet kiem context nhung de mat
  chi tiet neu summary khong co cau truc.
- **Sliding:** giu summary, durable notes va mot so turn gan nhat. Day la
  strategy mac dinh cua lab.

### Buoc 2: Doc flow compaction

Trong `src/short_term.py`, doc theo thu tu:

1. `add`: them message va kich hoat compaction khi co pressure.
2. `detect_pressure`: kiem tra so message va estimated token.
3. `extract_durable_notes`: giu TODO, deadline, decision, constraint va marker.
4. `compact`: tach old messages, ghi notes, cap nhat summary, giu recent turns.
5. `render`: tao context co cac block `SESSION_SUMMARY`, `DURABLE_NOTES` va
   `RECENT_TURNS`.

Compaction dung khong phai la viet lai tuy y. No phai uu tien:

```text
state -> decision -> TODO/open loop -> constraint/deadline -> recent turns
```

### Buoc 3: Giam cua so recent

Trong demo hoac constructor local, thu giam:

```python
max_recent_messages=6
```

thanh:

```python
max_recent_messages=4
```

Chay lai demo va xac nhan marker `REVIEW-DEADLINE-1600` van con trong
`DURABLE_NOTES` hoac summary, du raw message cu da bi evict. Khong sua
`src/evaluate.py`; E10 co fixture va compaction flow rieng.

### Buoc 4: Kiem tra unit test local

```bash
docker compose run --rm app pytest -q tests/test_short_term.py
```

Ket qua can dat la tat ca test short-term PASS. Neu E01/E10 fail sau khi sua
short-term:

- Kiem tra durable marker co duoc giu lai khong.
- Kiem tra `render()` co giu `RECENT_TURNS` khong.
- Khong cat summary tu tuy y o phan tail neu marker nam o head.
- Khong dung buffer lam implementation chinh cua sliding.

### Buoc 5: Ghi nhan xet vao bai nop

Trong `README_submission.md`, viet 2-4 cau ve:

- Vi sao buffer khong phu hop khi conversation dai.
- Compaction giu constraint/deadline bang durable notes nhu the nao.
- Vi sao summary co cau truc tot hon viec cat ky tu ngau nhien.

Phan nhan xet nay se duoc dung khi giai thich E10 trong report.

## 8. Checkpoint phan 1

Chi chuyen sang phan 2 khi cac dieu kien sau deu dung:

```text
[ ] docker compose build thanh cong
[ ] Redis va Qdrant dang chay
[ ] src.smoke PASS
[ ] src.seed hoan tat
[ ] reference benchmark chay duoc
[ ] demo_short_term chay duoc
[ ] test_short_term PASS
[ ] Hieu vi tri 4 TODO trong memory_student.py
```

Lenh checkpoint tong hop:

```bash
docker compose run --rm app python -m src.smoke
docker compose run --rm app pytest -q tests/test_short_term.py
docker compose run --rm app python -m src.evaluate \
  --impl reference --reuse-seeded
```

Neu checkpoint PASS, moi truong va short-term layer da san sang. Khong chay
privacy drill o giai doan nay vi lenh forget se xoa user memory can cho cac
buoc benchmark tiep theo.
