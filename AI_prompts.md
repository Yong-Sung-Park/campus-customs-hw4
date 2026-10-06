# AI Prompts Log — Homework 4: Campus Customs Shop + Chatbot

This file logs what I typed to my vibe coder, one section per problem.

---

## Problem 1: Vibe coder prompts

**Prompt:**

> I'm starting Homework 4. I'm building a Campus Customs shop website: a React + Vite + TypeScript front end and a Python FastAPI backend, with a PydanticAI agent as the chatbot. Don't write any app code yet. First, set up the project. Make a folder called `hw4` and put the data pack (`data/campus_customs.db` and `data/products/`) inside it. Add a `.gitignore` so the `data/` folder, any `.db` file, the product images, `.env`, `.venv` and `node_modules` never end up in git.
>
> Then create `hw4/AI_prompts.md`. This file is my log of what I type to you. Give it one section for each problem (Problems 1–13). Each section needs the problem number and title, the prompt I typed, and a follow-up prompt if I needed one, with one sentence on what was missing after the first try. Put this prompt under Problem 1. After every problem, add my prompt to the matching section. Don't rewrite the earlier sections.

**Follow-up:** None needed. The first prompt set up the folder, the `.gitignore`, and this log.

---

## Problem 2: Analyze the database

**Prompt:**

> Open `data/campus_customs.db` and go through every table: `catalogue`, `inventory`, `users`, and anything else that's in there. For each table, show me the columns, their types, the keys, and a few sample rows, so I can see what the data actually looks like. Point out anything odd I should know before building on it. For example: columns stored as JSON text, category names that aren't consistent, sizes that are out of stock, or the format of the password hashes.
>
> Then start a new file, `output/harness.md`. This is the design doc I'll keep growing through the homework. Add a "Database" section with one small table per database table. List every field with its type and one short line on why it matters for the shop or the chatbot. For example, `price` is what the agent must quote exactly instead of guessing.

**Follow-up:** None needed. The first pass covered all four tables and also found the password-hash settings (PBKDF2-SHA256, 120,000 iterations).

---

## Problem 3: Build the Campus Customs website

**Prompt:**

> Now let's build the actual site. Make a React + Vite + TypeScript app in `frontend/`. Put a nav bar across the top with links to Home, Products, About Us, Log in, and Create account, and use React Router so each one is its own page. Log in and Create account can be placeholder pages for now, since I'll do auth in the next problem.
>
> For Home and About Us, look at yalebulldogblue.com to get a feel for how Campus Customs talks about itself: Yale merch, the Bulldog spirit, who they are, what they sell. Then write the copy in your own words. Don't copy their sentences.
>
> The Products page should show every catalogue item as a card with its image, name, price, and a short version of the description. Clicking a card should go to a single-product page at `/products/:id`. Put a big image on one side, and on the other side the full description, price, colors, and a size-by-size stock list. Show sold-out sizes as sold out.
>
> The front end needs real data, so start a small FastAPI app in `backend/main.py`. It should have an endpoint that lists products, one that returns a single product with its inventory, and a way to serve the images from `data/products/`. It must read from `data/campus_customs.db`. Parse the JSON `colors` and `search_tags` before sending them. Have Vite proxy `/api` to the backend so there are no CORS headaches. Set up a `.venv` and a `requirements.txt` for the Python side.
>
> Last, add a chat bubble in the bottom-right corner on every page. It should open into a small chat panel where I can type a message. It doesn't need to talk to an AI yet, but make the send function call a backend `/api/chat` route that just returns a placeholder reply, so I can plug the agent in later.

**Follow-up:** None needed. All five pages, the product grid, the detail page with sold-out sizes, and the chat stub worked on the first pass.

---

## Problem 4: Create account and login

**Prompt:**

> Next is real accounts. Replace the placeholder Log in and Create account pages with working forms. Create account asks for first name, last name, email, password, and confirm password. Log in asks for email and password. Show clear error messages for things like a wrong password, an email that's already taken, a password that's too short, or passwords that don't match.
>
> On the backend, add signup and login routes in `main.py` that use the existing `users` table. Don't add a new table. Passwords must be stored securely: never save the plain password. The seed database already uses PBKDF2-SHA256 with a random salt and 120,000 iterations (`pbkdf2_sha256$salt$hash`), so hash new passwords the same way. That way the test user `test@campuscustoms.yale.edu` / `password` still logs in. Compare hashes in constant time. Normalize emails to lowercase, and on a failed login don't reveal whether it was the email or the password that was wrong.
>
> After login or signup, give the browser a session so it stays logged in across page refreshes. The backend should also be able to tell who the user is, because the chatbot will need that later. Add a `/api/me` route, and a log out button. Once someone is logged in, the nav bar should say "Hi, <first name>" instead of the Log in / Create account links.
>
> Then test it: log in as the test user, create a brand-new account, and log in with it. Finally, add an "Auth" section to `output/harness.md` that explains what we store for each user and how passwords and sessions are protected.

**Follow-up:** None needed. Test-user login, a brand-new signup and login, error messages, and logout all worked on the first pass.

---

## Problem 5: PydanticAI agent backend

**Prompt:**

> Time to give the chat bubble a real brain. Build the shop assistant as a PydanticAI agent and plug it into the `/api/chat` route in `backend/main.py`, replacing the placeholder reply. Set the agent up the same way as Homework 3, as four files next to `main.py`:
>
> - `backend/prompts/prompt.md` is the system prompt.
> - `backend/agent.py` builds the agent and has a function `main.py` can call.
> - `backend/tools.py` holds the agent's tools. Leave it mostly empty for now; I'll add the database tools next problem.
> - `backend/models.py` holds the Pydantic types for the chat request and reply.
>
> For the model, use `gpt-5.6-luna` through Portkey with the OpenAI-compatible client, like in HW 3. Read `PORTKEY_API_KEY` from `.env` and never hardcode it. Don't set a temperature, because this model only allows the default. Add a placeholder line for the key to `.env.example`. Load the system prompt from `prompt.md` when the agent starts, so I can edit that file without touching code.
>
> In `prompt.md`, write the Campus Customs voice: friendly, short, Bulldog-proud, and helpful to students, alumni, and parents. Add basic safety rules: only talk about the shop and its products, never make up prices, stock, or products (say you'll check instead), don't share other customers' info, and politely refuse anything off-topic or harmful. Keep it to plain-text answers that fit in a small chat window.
>
> The chat reply type in `models.py` should have the reply text, plus an empty list of product cards that I'll fill in Problem 7, so the front end already knows the shape. The chat widget should send the recent conversation along with each new message so the agent remembers what was just said, and show a friendly error if the agent fails instead of breaking.
>
> Make sure it runs from the `backend/` folder with `uvicorn main:app --reload --port 8000`. Add a section to `output/harness.md` explaining how the front end talks to FastAPI (Vite proxy, routes, request and response shapes) and how the agent is loaded (prompt file, model, provider, API key).

**Follow-up:**

> When I asked it to write my CPSC 223 homework, it said no but then offered to help me plan and debug the code instead. That's still off-topic. Tighten the prompt so it fully declines anything that isn't about the shop (homework, coding, explaining code, tutoring, weather, and so on) in one friendly sentence, with no "but I can help with part of it", and then steer back to Campus Customs.

What was lacking: the first safety rule was too soft, so the agent turned down the request but still offered partial off-topic help (debugging and reviewing code).

---

## Problem 6: Tools: product info and stock

**Prompt:**

> Now give the agent real tools so it stops saying "check the product page". In `backend/tools.py`, add tools that read `campus_customs.db`: one for a product's details (description, colors, type), one for its price, and one for stock, with an optional size. Let the shopper refer to a product by its name, not just the id, and if the name is close but not exact, return a few "did you mean" options instead of guessing. Stock answers must come from the `inventory` table. If a size has quantity 0, the tool should say it's sold out in plain words.
>
> Put the return types in `models.py` as Pydantic models, and pick fields that make it hard for the agent to get things wrong (an explicit `in_stock` flag, the exact price, a `sold_out_sizes` list). Update `prompt.md` so the agent always calls these tools for any price, stock, size, or color question, never answers those from memory, and says clearly when a size is sold out. In `output/harness.md`, list each tool and explain why I chose the fields in each return model.

**Follow-up:** None needed. Price, a sold-out size, a color that doesn't exist, and an ambiguous name were all answered correctly from the database.

---

## Problem 7: Chat search that updates the page

**Prompt:**

> Now the cool part. When someone asks the chat something like "what hoodies do you have?" or "anything navy under $60?", the agent should search the catalogue and the matching products should pop up on the website as real product cards (image, name, price, short description), not just as text in the chat.
>
> Add a `search_products` tool with a free-text query plus optional filters: category, color, max price, and a size that has to be in stock. The catalogue's garment types are messy, so search on a normalized category and loosely match colors (gray should match heather gray). Change the agent's output to a structured type with the reply text plus a list of `product_ids` to show. Treat it as an API contract: the backend checks those ids are real and came from a tool this turn, then builds the cards itself from the database, so prices on cards can never be made up. `/api/chat` returns them in `products`.
>
> On the front end, show those cards in a "Picked for you" panel at the top of whatever page the shopper is on, with a way to clear it. Each card, including these chat ones, must still open the single-item page when clicked, and the panel should stay there so they can click another one. Update `prompt.md` (when to search, at most about 8 results, keep the text short because the cards show the details) and `output/harness.md` (how search results get from the tool to the page).

**Follow-up:**

> Two fixes. When nothing matched pink, the bot suggested "purple", but we don't sell anything purple, so only suggest colors or items a search actually showed exist. Also, when I'm on a product page and ask about "this", the answer replaced my whole "Picked for you" panel with one card of the item I'm already looking at. Keep the old picks in that case.

What was lacking: the first version could still suggest made-up alternatives, and it replaced useful search results with a redundant card.

**Follow-up 2:**

> After I ask the chat something, clicking Home or About Us looks like nothing happens. The big "Picked for you" panel fills the whole first screen on every page, and the page also keeps my old scroll position. Show the full panel only on the page where I asked. Once I go to another page, shrink it to the small strip so the new page is actually visible, and start every new page at the top.

What was lacking: the chat results panel covered every page, so the nav links looked broken.

---

## Problem 8: Customer memory

**Prompt:**

> Give the chat a memory for logged-in shoppers. The database already has a `chat_messages` table (user_id, role, content, products_json, created_at), so use that instead of making a new one. When a logged-in user chats, save both their message and the assistant's reply, including the product cards that were shown. When they come back or log in again, reload their past conversation into the chat widget, and have the server feed their recent saved turns to the agent as history. Guests can still chat normally, but nothing gets saved for them. Logging out should clear the chat on screen.
>
> The agent should know who it's talking to. Put the logged-in customer's name and email into the agent deps, add them to the agent's instructions, and add a tool it can call to get the current customer. Also send page context with every chat message: the current path, and the product id when they're on a product page. Then if someone on the Baseball Left Chest Crewneck page asks "do you have this in pink?", the agent knows "this" means that crewneck. Add a tool for the current page too.
>
> Document in `output/harness.md` how chat history is stored and reloaded, which customer fields the agent sees (and that it never sees the password hash), and how page context gets from the browser to the agent.

**Follow-up:** None needed. "Do you have this in pink?" on a product page, name recall for the test user, and history reload after a refresh all worked on the first pass.

---

## Problem 9: Usability improvements

**Prompt:**

> The core shop works, so let's make it nicer. I want two front-end improvements and two agent/backend improvements. Write `output/usability.md` first, with what each one is and why it helps a shopper or the business, then build them.
>
> Front end: (1) The Products page is just 102 cards in a row. Add a search box, category chips (hoodies, crewnecks, quarter-zips, jackets, tees), a "has my size in stock" filter, and sorting by price, so people can find things without scrolling forever. (2) Make the chat easier to start: show a few suggestion chips that change with the page (on a product page, things like "Is this in stock in M?" and "What colors does it come in?"), plus an "Ask about this item" button on the product page that opens the chat with that question.
>
> Agent/backend: (1) When a size is sold out, the bot should be able to suggest similar items that DO have that size in stock, so add a `find_alternatives` tool instead of leaving the shopper at a dead end. (2) Add a safety net for prices. Before a reply goes out, check every dollar amount in it against prices the tools actually returned this turn (or numbers the shopper typed, like a budget). If there's a made-up price, make the agent fix it. Make sure all four show up in the running app.

**Follow-up:** None needed for the four features. All four work in the running app (see `app_check.html`, sections 4 and 5).

---

## Problem 10: Style the website

**Prompt:**

> Make it look like a real Campus Customs storefront, not a template. Keep Yale blue as the anchor but give it personality: a collegiate serif for headlines (Fraunces) with a clean sans for body text (Inter), a warm off-white "paper" background instead of plain gray, and a scrolling ticker under the nav with Bulldog spirit lines. On Home, make the hero feel alive with a tilted "polaroid" collage of real product photos that gently float. Cards should feel shoppable: a category tag, image zoom on hover, and a "View details" hint. Give the chat a personality too: an avatar and "online" status in the header, a pulsing chat bubble, messages that pop in, and animated typing dots instead of the word "Typing". Pages should fade in when you navigate. Respect reduced-motion settings. Then write `output/design.md`: short and concrete, what changed and why it should keep shoppers around and buying.

**Follow-up:**

> When I click a chat card and land on a product page, the big "Picked for you" panel pushes the actual product below the fold. On product pages, shrink the picks into a one-row strip of small cards I can scroll sideways, so the item I clicked is front and center but the other picks are still there.

What was lacking: the full-size picks panel worked on browse pages but hid the product itself on the single-item page.

---

## Problem 11: Site testing (app check)

**Prompt:**

> Test the live site like a shopper and document it in `output/app_check.html`, a simple page I can double-click open. Take real screenshots of the running app and save them in `output/app_check_images/`, linked with relative paths. I need at least: (1) the chat checking an item's inventory, ideally a product with a sold-out size, so we can see it's honest and matches the database; (2) the dynamic product cards appearing after asking "what hoodies do you have?"; and (3) one of the Problem 9 usability features. For each one, add a heading, the screenshot, and one or two sentences on what it proves. Include the actual database numbers next to the inventory screenshot so a grader can check the bot didn't make anything up.

**Follow-up:**

> The chat bubble says "1 item shown on the page" even when it only answered about the product I'm already looking at, and nothing new actually appeared. Don't show that note in that case.

What was lacking: the "items shown" note didn't match what the page really showed for single-item answers.

---

## Problem 12: Audit trail, safety, finish harness

**Prompt:**

> Add an audit trail like in HW 3. Run the agent step by step with `agent.iter()` and append every step of the agent loop to `output/audit_trail.json`: timestamp, a run id, the user (just the user id or "guest", not their email), the page, the step type, the tool name, short arguments and a short result summary, and the stop reason at the end (final answer, usage limit, or error). It has to be append-only. Never wipe it between runs or server restarts, and it should stay valid JSON even if something crashes mid-write.
>
> Then tighten safety. Add a clear set of safety rules to `prompts/prompt.md`: privacy (only the current shopper's own details, never anyone else's), no collecting passwords or card numbers, no promising discounts, orders, or refunds, resisting prompt injection, not exposing internal tool names or raw data, and staying calm with rude users. On the backend, add a simple per-visitor rate limit on `/api/chat` so nobody can spam the paid model.
>
> Finally, finish `output/harness.md` so someone new could understand the whole system: every model in `models.py` and why its fields exist, every tool, the safety rules (both prompt-level and code-level), and the specs (model, loop and request limits, result caps, history length, rate limit, and how to run the front and back end).

**Follow-up:**

> Two things from testing. First, the "admin mode, list all emails" jailbreak got blocked by Portkey's content filter, but the shopper just saw a generic "I hit a snag" error. Treat a content-filter block as a polite refusal and log it in the audit trail as its own stop reason. Second, when someone pasted a card number, the bot said to "complete checkout on the site", but we don't have a checkout. Make the prompt say there's no online cart, so it sends people to the store.

What was lacking: provider safety blocks looked like crashes, and the bot invented a checkout flow that doesn't exist.

---

## Problem 13: Submission and file layout

**Prompt:**

> Get this ready to submit. Check the folder matches the required layout (`AI_prompts.md`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `frontend/`, `backend/` with the four agent files, and `output/` with harness, design, usability, app_check + images, and the audit trail). Write a `README.md` that explains what the project is and exactly how to run the back end and front end after dropping in the data pack. Make sure `.gitignore` really keeps out `.env`, `campus_customs.db`, the product images, `.venv`, and `node_modules`: actually check it with git, don't just assume. Then make the first commit and push it to a new public GitHub repo so I can submit the URL on Canvas.

**Follow-up:** None needed. `git check-ignore` confirmed `.env`, the database, product images, `.venv`, and `node_modules` are excluded, a scan found no keys in the staged files, and the repo is public at https://github.com/Yong-Sung-Park/campus-customs-hw4.
