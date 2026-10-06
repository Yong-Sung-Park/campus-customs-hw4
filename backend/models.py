"""Pydantic types shared by the API and the agent."""

from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 12


class ChatTurn(BaseModel):
    """One earlier message in the conversation, as the chat widget shows it."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS * 4)


class PageInfo(BaseModel):
    """Where the shopper is on the site when they send a message."""

    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=120, description="Set on /products/:id pages.")


class ChatRequest(BaseModel):
    """What the chat widget POSTs to /api/chat."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Recent turns so the agent remembers the conversation (used for guests;
    # logged-in users' history comes from the database). Capped server-side.
    history: list[ChatTurn] = Field(default_factory=list)
    page: PageInfo | None = None


class ProductCard(BaseModel):
    """A product the front end can render as a card. Filled in by Problem 7's search."""

    product_id: str = Field(description="catalogue.product_id; also the /products/:id route.")
    name: str
    price: float = Field(description="Exact catalogue price in USD.")
    image_url: str = Field(description="Served by FastAPI under /media/products/.")
    short_description: str


# ---------- tool results (Problem 6) ----------

Size = Literal["XS", "S", "M", "L", "XL", "XXL"]


class ProductNotFound(BaseModel):
    """Returned instead of guessing when a product reference doesn't match."""

    found: Literal[False] = False
    query: str
    did_you_mean: list[str] = Field(description="Up to 3 close product names; ask the shopper which one.")


class ProductDetails(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    category: str = Field(description="Normalized type: hoodie, crewneck, quarter-zip, jacket, t-shirt, long-sleeve.")
    garment_type: str = Field(description="Original catalogue wording, e.g. 'pullover hoodie'.")
    description: str
    colors: list[str] = Field(description="The only colors this item comes in.")
    price: float = Field(description="Exact price in USD. Quote exactly.")


class PriceInfo(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    price: float = Field(description="Exact catalogue price. Quote exactly, never round.")
    currency: Literal["USD"] = "USD"


class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool = Field(description="quantity > 0. False means SOLD OUT in this size.")


class StockInfo(BaseModel):
    found: Literal[True] = True
    product_id: str
    name: str
    requested_size: str | None = Field(description="The size asked about, if any.")
    requested_size_status: str | None = Field(
        description="Plain-English answer for the requested size, e.g. 'M: SOLD OUT' or 'L: 8 in stock'."
    )
    sizes: list[SizeStock] = Field(description="Every size, XS to XXL, with live quantity.")
    sold_out_sizes: list[str]
    total_in_stock: int


# ---------- customer + page context (Problem 8) ----------


class CustomerInfo(BaseModel):
    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class CurrentPage(BaseModel):
    path: str
    page_type: Literal["home", "products", "product", "about", "login", "signup", "other"]
    product: ProductDetails | None = Field(
        default=None, description='The product on screen. "this"/"it" in the shopper\'s message usually means this item.'
    )


# ---------- search + agent output (Problem 7) ----------

Category = Literal["hoodie", "crewneck", "quarter-zip", "jacket", "t-shirt", "long-sleeve"]
MAX_CARDS = 8


class ProductSummary(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str] = Field(description="Sizes with quantity > 0. Empty means fully sold out.")
    short_description: str


class SearchResult(BaseModel):
    total_matches: int = Field(description="How many products matched in total (only the top ones are listed).")
    matches: list[ProductSummary]
    filters_used: dict = Field(description="The filters that were applied, so you can explain the results.")


class AlternativesResult(BaseModel):
    original: str
    size: str
    original_has_size: bool = Field(description="True if the original item actually has this size in stock.")
    alternatives: list[ProductSummary] = Field(description="Same-category items with this size IN STOCK, most similar first.")


class AgentReply(BaseModel):
    """The agent's structured final answer. The backend turns product_ids into cards."""

    reply: str = Field(description="Short plain-text chat message for the shopper (1-4 sentences).")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values to show as product cards on the page, most relevant first, max 8. "
            "Only ids returned by a tool in THIS turn. Empty when you're not recommending specific products."
        ),
    )


class ChatReply(BaseModel):
    """What /api/chat returns to the chat widget."""

    reply: str = Field(description="The assistant's message, plain text.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Product cards to show on the page (empty until Problem 7).",
    )
