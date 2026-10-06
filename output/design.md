# Design — Campus Customs storefront

**Goal:** make the site feel like a real Yale shop with personality, not a template, and use design to keep shoppers browsing and moving toward checkout.

| What changed | Where | Why it helps customers stay and buy |
|---|---|---|
| **Yale blue on warm "paper"** (`#00356b` navy on `#f6f2ea` off-white, cream accents) instead of flat gray | Whole site (`index.css` design layer) | Feels like a printed campus catalogue and keeps the Yale identity front and center. Warm neutrals make the navy products pop and are easier on the eyes for long browsing. |
| **Collegiate serif headlines** (Fraunces) + **Inter** for body text | Headings, brand, prices on product pages | A traditional serif matches the Yale look. The italic accent in "Wear your *Bulldog* pride" gives the hero a voice. Inter keeps small text (descriptions, sizes) easy to read. |
| **Spirit ticker** scrolling under the nav ("Boola Boola ✦ 57 Broadway ✦ Ask the chat about any size…") | Every page | Adds energy and school spirit, and quietly advertises the two things we want shoppers to do: visit the store and use the chat. |
| **Hero "polaroid" collage**: three real products tilted like photos on a dorm wall, each with a caption ("Library nights", "The Game", "February walks"), floating gently | Home | Shows real merch right away and frames it as moments in Yale life, which is more emotional and giftable than a plain banner. The motion draws the eye without being busy. |
| **Diagonal-stripe hero texture** | Home | A subtle athletic-jersey feel that gives depth without stock photos. |
| **Shoppable cards**: category tag (HOODIE, TEE…), image zoom on hover, "View details →" pill slides up, lift and shadow | Products, Home, chat picks | Makes cards feel clickable and alive. The tag helps scanning, and the CTA gives a clear next step, which increases clicks into product pages (where buying decisions happen). |
| **Sticky product image** and size tiles that turn navy on hover (sold-out sizes stay striped and struck through) | Product page | The photo stays in view while reading sizes. Available sizes feel tappable, and sold-out ones are clearly unavailable, so there's no disappointment at checkout. |
| **Chat with personality**: "CC" avatar, green "Online · checks live stock" status, a pulsing bubble when closed, a panel that pops open, messages that pop in, and bouncing typing dots | Chat widget | The pulse invites people to try the assistant. The status line sets the right expectation (it really checks stock). Typing dots make the wait feel responsive. More chats lead to more answered questions and fewer abandoned carts. |
| **Page fade-in** on every navigation and a slide-down "Picked for you" panel | All pages | Smooth transitions make the site feel polished and fast, the way a real store app does. |
| **Reduced-motion support** (`prefers-reduced-motion` turns off all animation) | Global | Accessible to shoppers who get motion sickness. Polish shouldn't push anyone away. |
