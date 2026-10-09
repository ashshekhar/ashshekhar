# Claude Console deep dive: what the API is for, and what to do with your $100

Prepared 9 October 2026. Companion to `claude-console-api-credits-guide.md` (setup and prices). Pricing and limits are from Anthropic's docs on this date. Facts about your data come from your own HiRise and Tally skill notes. Anything I did not verify is marked.

## 1. Verdict

The credit is worth less to you than the reel implies, and that is fine. Your Max plan already covers everything you do interactively, and Claude Code already runs your skills against your files at a flat price. The API earns its keep in exactly three situations:

1. **Volume.** The same small judgement repeated thousands of times (284,243 Tally vouchers is the obvious candidate).
2. **Unattended.** A job that runs without you opening a chat.
3. **Your own software.** Something a customer, staff member or script calls directly.

Recommendation: spend about $10 of the $100 on one bulk-text pilot (section 4, idea 1), learn the Console on the side, and let the rest expire. Do not invent projects to burn credit. A leftover balance on 6 November costs you nothing.

## 2. The five ways to use Claude, side by side

| | Claude app | Claude Code | Messages API (Console) | Agent SDK | Managed Agents |
|---|---|---|---|---|---|
| What it is | Chat window | Terminal/desktop agent that reads and edits your files | Raw model access: you send text, get text back | Claude Code's engine as a library inside your own program | Anthropic hosts the agent and its sandbox |
| Who drives it | You, by typing | You, by typing | Your code | Your code | Your code or a schedule |
| Billing | Max, flat | Max, flat | Per token, from your credit | Per token (API key) | Per token plus $0.08 per running session-hour |
| Runs while you sleep | No | Only via routines | Yes | Yes | Yes (scheduled deployments) |
| Your $100 applies | No | No | Yes | Yes | Yes |

Source for the last row: your email. Sources for the rest: Anthropic's Agent SDK and Managed Agents docs.

What the API does that the app cannot:
- **Scale.** The Batch API accepts up to 100,000 requests in one batch at 50% off, and most batches finish within an hour. The app handles one conversation at a time.
- **Control.** You pick the model per task, set the output format (structured JSON that always matches a schema), cache repeated instructions at a tenth of the input price, and read PDFs or images programmatically.
- **Integration.** Claude becomes a function other programs call.

What the app does that the API does not: memory of you, connectors (Gmail, Robinhood, Canva), skills, artifacts, projects. The API is a blank engine. Everything you built in your skills would have to be rebuilt around it, which is what the Agent SDK is for.

## 3. What people use the API for

General patterns (my knowledge of common practice, not sourced statistics):

- **Extraction.** Pull fields out of invoices, forms, statements and PDFs into a spreadsheet.
- **Classification and tagging.** Label thousands of tickets, transactions or reviews.
- **Customer-facing assistants.** Support and enquiry bots on a website or messaging app.
- **Drafting at scale.** Personalised messages, product descriptions, translations.
- **Internal agents.** A bot in Slack or a scheduled agent that reads data and files a report.
- **Evaluation.** Run the same questions against different models to pick the cheapest one that is good enough.
- **Developer tools.** Claude Code itself is built on this API.

## 4. What fits you, ranked

**Honest limit first.** Most of your dealership data is numbers, and a script beats an LLM at numbers. Your own skill notes also say several HiRise fields are junk: the PSF satisfaction score reads 100% everywhere, the service advisor on repeat jobs is a system account, and "Customer usage" is the repeat-complaint reason on 3,139 of 3,234 rows. An LLM cannot rescue a field that is empty or defaulted. It only helps where there is real free text. So the list below is shorter than you might hope.

### Idea 1 (recommended): classify Tally voucher narrations

- **What:** 284,243 vouchers are already extracted on your Mac. Many carry a free-text narration. Claude labels each (expense type, scheme income, finance commission, discount reason, vendor), and a script then sums the labels. Claude never does the arithmetic.
- **Why it wins:** the data exists, it is text, the volume is real, and it is read-only on exported files, so nothing in Tally is touched. It would sharpen the "discounts actually given" and "scheme income" answers your Tally skill says HiRise cannot give.
- **Cost, one worked instance:** assume 150 input tokens and 30 output tokens per voucher (my assumption). On Haiku 5.5 with Batch: 284,243 x 150 = 42.6M input tokens x $0.05 per million = $2.13, plus 284,243 x 30 = 8.5M output tokens x $0.25 per million = $2.13. Total about $4 to $6. On Sonnet 5.5 with Batch the same job is about $85, almost the whole credit, so do not run Sonnet on everything.
- **Method:** (1) a free script first measures how many narrations are non-empty and how varied they are, (2) pilot 2,000 vouchers on both models (about $0.60 on Sonnet), (3) you spot-check 100 labels, (4) run the full set on whichever model passes.
- **Unverified:** whether the narrations carry useful text. Step 1 answers that for free, and if they do not, this idea dies cheaply.

### Idea 2: call briefs for the lapsed-customer list

- **What:** 19,853 service customers have lapsed, 5,666 are callable with a mobile number, and 3,586 of those still hold an extended warranty. Claude writes a one-line opener per customer in Hindi or English for a telecaller.
- **Honest verdict:** a fixed template covers 90% of this (name, model, last visit, warranty status). Claude adds value only if you have per-customer free text such as past complaints. Cost is trivial either way (about $0.30 on Haiku, about $6.50 on Sonnet, both Batch, at 400 input and 150 output tokens per customer), so the money is not the issue. Whether it beats a template is. Try 50 customers by hand in Claude Code before using the API.
- **A human sends the messages.** The API drafts only.

### Idea 3: a customer enquiry assistant (month two, not now)

A website or WhatsApp assistant for test-ride bookings, service slots and "is my bike ready". Per conversation the model cost is small (a few cents or less on Haiku). The real costs are hosting, the WhatsApp Business setup (I have not verified its fees or approval process), and the risk of a wrong price or offer being quoted to a customer. It also needs a person watching it. Revisit after idea 1 shows you the workflow.

### Idea 4: model bake-off as a skill-building exercise

Run the same 100 narrations through Haiku, Sonnet and Opus and compare. This teaches you what each tier is worth, which helps every later decision, and costs under $2.

## 5. What not to spend it on

- **The Daily Portfolio Advisor routine.** It already runs on your subscription. Moving it to the API adds cost for no gain.
- **Training readiness, trip planning, Gmail, Canva.** These depend on app connectors that the raw API does not have.
- **Family documents.** Passport, Aadhaar and similar data should not go through any new pipeline.
- **Anything customer-facing without a human check.**

## 6. Safety rules for this setup

1. **Keep the key out of your shell profile.** Claude Code can pick up `ANTHROPIC_API_KEY` from the environment and use it instead of your subscription login (documented for Anthropic's `ant` CLI, not tested on your machine). Your email says credits do not cover Claude Code, so a global key could break or mis-bill your normal sessions. Put the key in a `.env` file inside the job's own folder and have the script read it from there.
2. **Never commit the key.** Add `.env` to `.gitignore` before the first commit.
3. **Send the minimum.** For narrations send the voucher ID and text only, not party names, phone numbers or addresses where avoidable. Join results back by ID locally.
4. **Data handling.** Anthropic's docs state retained API data is never used for model training without your express permission. The Batch API is not eligible for zero data retention, so batch inputs follow Anthropic's standard retention policy. Customer PII (names, mobiles) should not go in batches at all.
5. **Spend limit.** Set it at $20 in Settings, Billing before the first run.
6. **Limits.** New organisations may start on lower rate limits than the published Start tier (the docs say so). Check Settings, Limits. A small pilot will not hit them.
7. **Where this runs.** Your Tally and HiRise files live on your Mac, not in this cloud session, so the pilot runs from a Claude Code session on your Mac. I cannot reach those files from here.

## 7. Four-week plan

| Week | Step | Spend |
|---|---|---|
| 1 (to 16 Oct) | Check balance, create key, set $20 limit, run the free narration-quality measurement | $0 |
| 2 | Pilot 2,000 vouchers on Haiku and Sonnet, spot-check 100 | about $1 |
| 3 | Full run on the winning model, script sums the labels | $4 to $85 |
| 4 (to 6 Nov) | Review results, decide on idea 2 or 3, let the rest expire | optional |

## 8. Unresolved questions

1. Do the Tally narrations hold useful text? One free script answers it.
2. Does the harvested HiRise job-card data include remark text, or only coded fields?
3. Did the $100 land in the Console balance as the email says? I could not verify the program publicly.
4. Do you want idea 2 tried by hand first, or skipped?
5. Which Mac folder should the pilot live in, given the rule that PII never enters git?

## Sources

- Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- Batch processing: https://platform.claude.com/docs/en/build-with-claude/batch-processing
- Rate limits and spend caps: https://platform.claude.com/docs/en/api/rate-limits
- Managed Agents: https://platform.claude.com/docs/en/managed-agents/overview
- Agent SDK: https://code.claude.com/docs/en/agent-sdk/overview
- Feature list: https://platform.claude.com/docs/en/build-with-claude/overview
- Data retention: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- Your data facts: personal-hirise-portal and personal-tally-books skill notes
