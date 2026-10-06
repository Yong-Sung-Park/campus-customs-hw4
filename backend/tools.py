"""Tools the Campus Customs agent can call, plus the per-run deps they share.

Every fact the agent states about a product (price, stock, colors) must come
from one of these tools, which read data/campus_customs.db.
"""

from dataclasses import dataclass, field

from pydantic_ai import RunContext

import db
from models import (
    MAX_CARDS,
    AlternativesResult,
    Category,
    CurrentPage,
    CustomerInfo,
    PriceInfo,
    ProductDetails,
    ProductNotFound,
    ProductSummary,
    SearchResult,
    Size,
    SizeStock,
    StockInfo,
)


@dataclass
class AgentDeps:
    """Per-request context handed to the agent and its tools.

    `user` is the logged-in shopper's public fields (id, first_name, last_name,
    name, email), or None for guests.
    """

    user: dict | None = None
    user_message: str = ""
    page_path: str = "/"
    # The product on screen (resolved from the page's product_id), if any.
    page_product: dict | None = None
    # Filled by tools during a run: ids and prices the agent has actually looked up.
    seen_products: dict[str, float] = field(default_factory=dict)

    def remember(self, product: dict) -> None:
        self.seen_products[product["product_id"]] = product["price"]


def _resolve(ctx: RunContext[AgentDeps], product: str) -> tuple[dict | None, ProductNotFound | None]:
    found, suggestions = db.resolve_product(product)
    if found is None:
        return None, ProductNotFound(query=product, did_you_mean=suggestions)
    ctx.deps.remember(found)
    return found, None


def get_product_details(ctx: RunContext[AgentDeps], product: str) -> ProductDetails | ProductNotFound:
    """Look up a product's description, colors, type, and price.

    Args:
        product: The product's name as the shopper said it (e.g. "basic hoodie big yale") or its product_id.
    """
    p, missing = _resolve(ctx, product)
    if missing:
        return missing
    return _details(p)


def _details(p: dict) -> ProductDetails:
    return ProductDetails(
        product_id=p["product_id"],
        name=p["name"],
        category=p["category"],
        garment_type=p["garment_type"],
        description=p["description"],
        colors=p["colors"],
        price=p["price"],
    )


def get_price(ctx: RunContext[AgentDeps], product: str) -> PriceInfo | ProductNotFound:
    """Get the exact current price of a product.

    Args:
        product: Product name or product_id.
    """
    p, missing = _resolve(ctx, product)
    if missing:
        return missing
    return PriceInfo(product_id=p["product_id"], name=p["name"], price=p["price"])


def check_stock(ctx: RunContext[AgentDeps], product: str, size: str | None = None) -> StockInfo | ProductNotFound:
    """Check live stock for a product, for every size or for one size.

    Args:
        product: Product name or product_id.
        size: Optional size the shopper asked about: XS, S, M, L, XL, or XXL.
    """
    p, missing = _resolve(ctx, product)
    if missing:
        return missing
    sizes = [SizeStock(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0) for s in p["inventory"]]
    requested = size.strip().upper() if size else None
    status = None
    if requested:
        match = next((s for s in sizes if s.size == requested), None)
        if match is None:
            status = f"{requested}: not a size we carry (sizes are {', '.join(db.SIZE_ORDER)})"
        elif match.in_stock:
            status = f"{requested}: {match.quantity} in stock"
        else:
            status = f"{requested}: SOLD OUT"
    return StockInfo(
        product_id=p["product_id"],
        name=p["name"],
        requested_size=requested,
        requested_size_status=status,
        sizes=sizes,
        sold_out_sizes=[s.size for s in sizes if not s.in_stock],
        total_in_stock=sum(s.quantity for s in sizes),
    )


def search_products(
    ctx: RunContext[AgentDeps],
    query: str = "",
    category: Category | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size_in_stock: Size | None = None,
) -> SearchResult:
    """Search the catalogue. Use for "what hoodies do you have?", "anything navy under $60?", "bulldog shirts".

    Put the product type in `category` when the shopper names one, and the remaining keywords
    (team, college, graphic, occasion) in `query`.

    Args:
        query: Free-text keywords, e.g. "bulldog", "hockey", "Harvard Yale", "Grace Hopper". Can be empty when filters are enough.
        category: hoodie, crewneck, quarter-zip, jacket (incl. fleece/bomber), t-shirt, or long-sleeve.
        color: Color the shopper wants, e.g. "navy", "gray" (loosely matched).
        max_price: Highest price in USD the shopper will pay.
        size_in_stock: Only return items that have this size in stock.
    """
    matches, total = db.search_products(query, category, color, max_price, size_in_stock, limit=MAX_CARDS)
    for p in matches:
        ctx.deps.remember(p)
    filters = {k: v for k, v in dict(query=query, category=category, color=color,
                                      max_price=max_price, size_in_stock=size_in_stock).items() if v}
    return SearchResult(
        total_matches=total,
        matches=[ProductSummary(**db.summarize(p)) for p in matches],
        filters_used=filters,
    )


def find_alternatives(ctx: RunContext[AgentDeps], product: str, size: Size) -> AlternativesResult | ProductNotFound:
    """Find similar items (same type) that HAVE a given size in stock. Use whenever a requested size is sold out.

    Args:
        product: The sold-out product's name or product_id.
        size: The size the shopper needs: XS, S, M, L, XL, or XXL.
    """
    p, missing = _resolve(ctx, product)
    if missing:
        return missing
    alts = db.find_alternatives(p, size)
    for a in alts:
        ctx.deps.remember(a)
    return AlternativesResult(
        original=p["name"],
        size=size,
        original_has_size=any(s["size"] == size and s["quantity"] > 0 for s in p["inventory"]),
        alternatives=[ProductSummary(**db.summarize(a)) for a in alts],
    )


def get_current_customer(ctx: RunContext[AgentDeps]) -> CustomerInfo:
    """Who is chatting: the logged-in shopper's name and email, or a guest."""
    u = ctx.deps.user
    if not u:
        return CustomerInfo(logged_in=False)
    return CustomerInfo(logged_in=True, first_name=u["first_name"], last_name=u["last_name"], email=u["email"])


def page_type(path: str) -> str:
    if path == "/":
        return "home"
    if path.startswith("/products/"):
        return "product"
    return {"/products": "products", "/about": "about", "/login": "login", "/signup": "signup"}.get(path, "other")


def get_current_page(ctx: RunContext[AgentDeps]) -> CurrentPage:
    """What page the shopper is looking at. On a product page this is the item "this"/"it" refers to."""
    p = ctx.deps.page_product
    if p:
        ctx.deps.remember(p)
    return CurrentPage(path=ctx.deps.page_path, page_type=page_type(ctx.deps.page_path), product=_details(p) if p else None)


# Registered in agent.py with agent.tool(...).
TOOLS = [
    search_products,
    get_product_details,
    get_price,
    check_stock,
    find_alternatives,
    get_current_customer,
    get_current_page,
]
