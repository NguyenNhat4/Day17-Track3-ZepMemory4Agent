from __future__ import annotations

from typing import Any

from .config import settings
from .context_budget import ContextBudgetManager
from .utils import cap_query, join_nonempty
from .zep_common import prime_eval_thread, render_graph_search


class StudentMemory:
    """Only this file needs to be edited by students."""

    def __init__(self, client: Any):
        self.client = client
        self.budget = ContextBudgetManager(settings.context_tokens)

    # NOTE: Zep rejects graph.search queries longer than 400 characters. Some
    # eval queries are longer than that, so wrap every query with
    # `cap_query(query)` (see src/utils.py) before passing it to graph.search.

    def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
        # LAB TODO 1/4
        # 1) prime_eval_thread(...) has already been provided as scaffolding.
        # 2) call thread.get_user_context(thread_id=...)
        # 3) return the .context string.
        # Bonus: append graph.search(scope="edges", limit>=20) facts with
        #        validity ranges (a low limit can miss deadline/open-loop facts).
        prime_eval_thread(self.client, user_id, thread_id, query)

        user_context = self.client.thread.get_user_context(thread_id=thread_id)
        context_block = getattr(user_context, "context", "") or ""

        # Bổ sung facts để giữ thông tin có validity range và tăng khả năng
        # tìm được deadline/open-loop khi Context Block bị rút gọn.
        try:
            facts = self.client.graph.search(
                user_id=user_id,
                query=cap_query(query),
                scope="edges",
                limit=20,
            )
            fact_text = render_graph_search(facts)
        except Exception:
            fact_text = ""

        return join_nonempty([context_block, fact_text], sep="\n\n")

    def retrieve_episodic(self, user_id: str, query: str) -> str:
        # LAB TODO 2/4
        # Use client.graph.search(user_id=..., query=cap_query(query),
        #     scope="episodes", limit=...) then render_graph_search(...).
        # Tip: verbose session episodes can crowd out concise, marker-bearing
        # reflections under the tight episodic budget — render_graph_search
        # accepts an `episode_char_cap` to keep more distinct episodes.
        # Bước 1: giới hạn query vì Zep từ chối graph.search dài hơn 400 ký tự.
        safe_query = cap_query(query)
        # Bước 2: tìm các episode thuộc user; episode là dữ liệu/raw event từ
        # các cuộc hội thoại trước, khác với Context Block đã được tổng hợp.
        results = self.client.graph.search(
            user_id=user_id,
            query=safe_query,
            scope="episodes",
            limit=15,
        )
        # Bước 3: chuyển object response của Zep thành text để đưa vào prompt.
        return render_graph_search(results, episode_char_cap=180)

    def retrieve_semantic(self, graph_id: str, query: str) -> str:
        # LAB TODO 3/4
        # Search the standalone graph (graph_id, NOT user_id).
        # Recommended: scope="episodes" — it returns raw document text that keeps
        # literal markers (e.g. PAYMENT-RULE-3). The "auto" scope returns
        # extracted facts that DROP those literal codes, so avoid it here.
        # Fallback: scope="nodes".
        # Bước 1: dùng graph_id để tìm knowledge dùng chung, không lấy memory
        # riêng của user hiện tại.
        safe_query = cap_query(query)
        try:
            # scope="episodes" giữ lại raw document và các marker nghiệp vụ.
            results = self.client.graph.search(
                graph_id=graph_id,
                query=safe_query,
                scope="episodes",
                limit=8,
            )
        except Exception:
            # Một số account/SDK không hỗ trợ scope episodes cho graph độc lập;
            # khi đó dùng nodes làm fallback để vẫn lấy được knowledge.
            results = self.client.graph.search(
                graph_id=graph_id,
                query=safe_query,
                scope="nodes",
                limit=8,
            )
        # Bước 2: render kết quả thành text semantic context cho agent.
        return render_graph_search(results)

    def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
        # LAB TODO 4/4
        # Use ContextBudgetManager to enforce 10/4/3/3 budget and priority order.
        # ContextBudgetManager cắt từng memory layer theo ngân sách 10/4/3/3,
        # rồi đóng gói theo thứ tự short-term -> long-term -> episodic -> semantic.
        return self.budget.assemble(layers)
