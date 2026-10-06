"""Campus Customs shop assistant: a PydanticAI agent on gpt-5.6-luna via Portkey.

main.py calls `run_chat(...)`. The agent is built lazily on the first chat, so
the API (products, auth) still starts when PORTKEY_API_KEY is missing.
"""

import os
import re
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

import db
from audit import AuditRun, truncate
from models import MAX_CARDS, MAX_HISTORY_TURNS, AgentReply, ChatReply, ChatTurn, PageInfo, ProductCard
from tools import TOOLS, AgentDeps

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR.parent / ".env")

MODEL = "gpt-5.6-luna"  # per AGENTS.md; no custom temperature (only the default is supported)
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
REQUEST_LIMIT = 8  # model requests per chat turn (each tool round trip adds one)
OUTPUT_RETRIES = 2  # retries for a rejected answer or a bad tool call


CONTENT_FILTER_REPLY = (
    "Sorry, I can't help with that. I'm the Campus Customs shop assistant. "
    "Want help finding a hoodie, a gift, or checking a size?"
)


class AgentNotConfigured(RuntimeError):
    pass


def is_content_filter(e: ModelHTTPError) -> bool:
    body = e.body if isinstance(e.body, dict) else {}
    return body.get("code") == "content_filter" or "content_filter" in str(e.body)


def make_client() -> AsyncOpenAI:
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set in .env")
    return AsyncOpenAI(
        api_key=key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": key},
    )


@lru_cache(maxsize=1)
def get_agent() -> Agent[AgentDeps, AgentReply]:
    model = OpenAIChatModel(MODEL, provider=OpenAIProvider(openai_client=make_client()))
    agent = Agent(model, deps_type=AgentDeps, output_type=AgentReply, retries=OUTPUT_RETRIES)

    # `instructions` (not `system_prompt`) are sent on every request, even when
    # we pass earlier turns as message_history. The file is re-read each turn,
    # so editing prompt.md takes effect without restarting the server.
    @agent.instructions
    def shop_instructions(ctx: RunContext[AgentDeps]) -> str:
        return PROMPT_PATH.read_text(encoding="utf-8")

    @agent.instructions
    def session_context(ctx: RunContext[AgentDeps]) -> str:
        """Who is chatting and what page they're on, injected into every request."""
        u = ctx.deps.user
        who = (
            f"Logged in as {u['first_name']} {u['last_name']} ({u['email']}). Greet them by first name."
            if u else "A guest (not logged in). You don't know their name; don't ask for personal details."
        )
        p = ctx.deps.page_product
        where = (
            f"Viewing the product page for \"{p['name']}\" (product_id {p['product_id']}). "
            "Words like \"this\", \"it\", or \"this one\" refer to this product."
            if p else f"On page {ctx.deps.page_path} (not a product page)."
        )
        return f"## Current session\n- Shopper: {who}\n- Page: {where}"

    @agent.output_validator
    def check_reply(ctx: RunContext[AgentDeps], out: AgentReply) -> AgentReply:
        # API contract: cards may only show products a tool returned this turn.
        unseen = [pid for pid in out.product_ids if pid not in ctx.deps.seen_products]
        if unseen:
            raise ModelRetry(
                f"product_ids {unseen} were not returned by a tool in this turn. "
                "Call search_products or get_product_details first, or remove them."
            )
        out.product_ids = list(dict.fromkeys(out.product_ids))[:MAX_CARDS]
        check_prices(ctx.deps, out.reply)
        return out

    for tool in TOOLS:
        agent.tool(tool)
    return agent


_PRICE_RE = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")
_NUMBER_RE = re.compile(r"\d+(?:\.\d{1,2})?")


def check_prices(deps: AgentDeps, reply: str) -> None:
    """Price guard: every $ amount in the reply must be a price a tool returned this
    turn, or a number the shopper typed (e.g. a budget). Otherwise ask for a fix."""
    allowed = {round(p, 2) for p in deps.seen_products.values()}
    allowed |= {round(float(n), 2) for n in _NUMBER_RE.findall(deps.user_message)}
    bad = [m for m in _PRICE_RE.findall(reply) if round(float(m.replace(",", "")), 2) not in allowed]
    if bad:
        raise ModelRetry(
            f"Your reply mentions price(s) {', '.join('$' + b for b in bad)} that no tool returned in this turn. "
            "Look the price up with a tool (get_price / search_products) and quote it exactly, or remove it."
        )


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn the widget's recent turns into PydanticAI messages (last N only)."""
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


def build_cards(product_ids: list[str]) -> list[ProductCard]:
    """Cards are built from the database, never from model text."""
    cards = []
    for pid in product_ids:
        product = db.get_product(pid)
        if product:
            cards.append(ProductCard(**db.card(product)))
    return cards


async def run_chat(
    message: str,
    history: list[ChatTurn],
    user: dict | None = None,
    page: PageInfo | None = None,
) -> ChatReply:
    agent = get_agent()
    page = page or PageInfo()
    page_product = db.get_product(page.product_id) if page.product_id else None
    deps = AgentDeps(user=user, user_message=message, page_path=page.path, page_product=page_product)
    if page_product:
        deps.remember(page_product)  # "this" item may be shown as a card without another lookup
    audit = AuditRun(user, page.path)
    # agent.iter() runs the same loop as agent.run(), one node at a time, so
    # every model request / tool call / result lands in the audit trail.
    try:
        async with agent.iter(
            message,
            deps=deps,
            message_history=to_message_history(history),
            usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
        ) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    audit.log_request(node.request)
                elif Agent.is_call_tools_node(node):
                    audit.log_response(node.model_response)
            result = run.result
    except UsageLimitExceeded as e:
        audit.log("error", stop_reason="usage_limit", result=truncate(e))
        raise
    except ModelHTTPError as e:
        if is_content_filter(e):
            # The provider's safety filter blocked the message (e.g. a jailbreak attempt).
            # Treat it as a polite refusal, not a server error.
            audit.log("refused", stop_reason="content_filter", result="Provider content filter blocked the request")
            return ChatReply(reply=CONTENT_FILTER_REPLY)
        audit.log("error", stop_reason="error", result=truncate(f"ModelHTTPError {e.status_code}"))
        raise
    except Exception as e:
        audit.log("error", stop_reason="error", result=truncate(f"{type(e).__name__}: {e}"))
        raise
    out = result.output
    usage = result.usage
    audit.log(
        "final",
        result=truncate(f"{out.reply} | cards={out.product_ids}"),
        stop_reason="final_answer",
        args={"model_requests": usage.requests, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
    )
    return ChatReply(reply=out.reply.strip(), products=build_cards(out.product_ids))
