# Usability Improvements — Campus Customs

Four improvements: two on the front end, two in the agent/backend. Each one is visible in the running app.

---

## Front end

### 1. Product finder: search, category chips, size filter, and sort (Products page)

**What I added:** A toolbar above the product grid on `/products`:
- a **search box** that matches name, description, colors, and tags as you type
- **category chips**: All · Hoodies · Crewnecks · Quarter-zips · Jackets · Tees · Long-sleeve, with counts. These use the normalized category, so "pullover hoodie", "hooded sweatshirt", etc. all land under Hoodies.
- a **"My size in stock"** dropdown (XS–XXL) that hides items sold out in that size
- **sort**: Featured / Price low→high / Price high→low
- a live "Showing N of 102" count, plus a "Reset filters" link when nothing matches

**Why it helps:** 102 products in one long grid is a lot of scrolling. A parent who wants "a navy hoodie in L under $70" can get there in two clicks. The size filter is the big one for the business: shoppers stop clicking into items only to find their size sold out, which is a common reason people leave a store site.

### 2. Context-aware chat starters + "Ask about this item"

**What I added:**
- **Suggestion chips** inside the chat panel that change with the page. On a product page: "Is this in stock in M?", "What colors does it come in?", "Show me similar items". Elsewhere: "What hoodies do you have?", "Gift ideas under $40", "What's good for winter?". One tap sends the question.
- An **"Ask about this item" button** on every product page that opens the chat and asks about the item's sizes and stock right away.

**Why it helps:** Many shoppers don't know what a store chatbot can do, and an empty text box makes them stop. The chips show what it's good at (stock, colors, search) and save typing on phones. The product-page button turns "I wonder if they have my size" into one click, at the moment the shopper is deciding to buy.

---

## Agent / backend

### 3. `find_alternatives` tool: no dead ends on sold-out sizes

**What I added:** A new agent tool, `find_alternatives(product, size)`. It looks up the product, then returns up to 4 **other items in the same category that have that exact size in stock**. Items sharing the most colors/tags rank first, then closest price. The prompt tells the agent to use it whenever a requested size is sold out, and the results show up as product cards on the page.

**Why it helps:** "Sorry, M is sold out" ends the sale. "M is sold out, but these 4 similar hoodies have M in stock" (with cards to click) keeps it going. That's what a good store employee would do, and it directly saves lost sales. 145 of the 612 size rows are at zero, so this comes up a lot.

### 4. Price guard (output validator): no made-up prices

**What I added:** A check that runs on every agent answer before it reaches the shopper. It finds every dollar amount in the reply (e.g. "$68" or "$45.00") and verifies each one equals a price a tool returned **in this turn**, or a number the shopper typed themselves (like "under $40"). If it finds an unverified price, the reply is rejected and the agent is told to look it up or remove it (PydanticAI `ModelRetry`). It works alongside Problem 7's check that card ids came from tools.

**Why it helps:** Quoting a wrong price is the most damaging mistake a shop bot can make. It costs trust, and the store may have to honor it. The prompt already says "never guess", but this makes it **enforced in code** instead of just a request to the model. This makes the agent more accurate and safer.
