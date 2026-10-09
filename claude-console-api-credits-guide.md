# Your $100 Claude Console credit: what it is and how to use it

Prepared 9 October 2026. Prices are from Anthropic's pricing page on that date and change over time.

## 1. What this is

Your Claude subscription (Max) and the Claude Console are two separate products with two separate balances.

| | Claude app / Claude Code (Max plan) | Claude Console (API) |
|---|---|---|
| What you pay | Flat monthly fee | Pay per use, from a prepaid balance |
| How you use it | Chat window, Claude Code | Your own code, scripts, apps, automations |
| Limit | Usage caps that reset | Runs until the balance hits zero |
| Your $100 | Cannot be used here | Used here |

The email states the credit applies to: the Claude API, Claude Managed Agents, the Claude Agent SDK, and the Console Playground. It states it cannot be used for Claude Code sessions or for extra usage in the Claude apps. It expires 6 November 2026, about 4 weeks from today.

Verification status: the email is the source for the $100 amount and the expiry. I could not find a public Anthropic page describing this exact Max-linked Console credit, so check the balance yourself (step 2 below). A separate, older promotion gave extra-usage credit inside the subscription and excluded Console accounts, so do not confuse the two.

## 2. First five minutes

1. Open platform.claude.com and sign in with the same account.
2. Settings, Billing: confirm the $100 balance and the expiry date.
3. Settings, API keys: create a key. Treat it like a password. Anyone with it spends your credit.
4. Settings, Limits: set a monthly spend limit so a bug cannot drain the balance.
5. Open the Workbench/Playground to try prompts with no code.

## 3. What it costs (the one concept you need)

The API charges per token. A token is roughly three quarters of a word. You pay for tokens going in (your prompt) and tokens coming out (the answer). Prices are per million tokens (MTok).

| Model | Input per MTok | Output per MTok | Use for |
|---|---|---|---|
| Haiku 5.5 | $0.10 | $0.50 | Bulk, simple, fast jobs |
| Sonnet 5.5 | $2 | $10 | Default for most work |
| Opus 5.5 | $4 | $20 | Hard reasoning, final review |
| Fable 5.1 | $10 | $50 | Top end, only if needed |

Worked example on Sonnet 5.5. One exchange with a 1,000 token prompt and a 500 token answer costs:
1,000 x $2 / 1,000,000 = $0.002 in, plus 500 x $10 / 1,000,000 = $0.005 out, so $0.007.
$100 / $0.007 is about 14,000 such exchanges. On Haiku 5.5 the same exchange costs about $0.00035, so roughly 285,000.

Savings levers (all documented on the pricing page):
- Batch API: 50% off for jobs that can wait (results come back asynchronously).
- Prompt caching: re-reading repeated context costs 10% of the normal input price (5% on Sonnet 5.5 and Opus 5.5).
- Web search tool: $10 per 1,000 searches on top of tokens. Web fetch adds no extra fee.
- Managed Agents: tokens plus $0.08 per session-hour of running time.

## 4. What it is good for, ranked for a non-developer

1. Playground/Workbench experiments. No code. Good for learning what models do and drafting reusable prompts. Cheapest way to start.
2. Bulk document jobs. Summarise, extract or classify hundreds of files, bills, emails or invoices with a short script on Haiku or Sonnet via Batch. This is where the API beats the chat app: the chat app handles one thing at a time, a script handles a thousand.
3. Small automations. A script that reads a spreadsheet, asks Claude for a judgement on each row, and writes results back.
4. Agent SDK / Managed Agents projects. Powerful but needs real setup and costs more per run. Wait until one of the above works.

## 5. What it will not do

- It will not extend your Claude app or Claude Code limits.
- It will not roll over. Unused credit disappears on 6 November 2026.
- It is not a free chatbot. Using Playground chats spends it too, just slowly.

## 6. Recommended plan for the next four weeks

1. Do section 2 (10 minutes), with a spend limit of $20.
2. Run 5 to 10 prompts in the Playground on Sonnet 5.5 to see real token costs on the Usage page.
3. Pick one repetitive job you already do by hand (for example sorting a folder of documents) and automate it with a script. Claude Code can write that script for you in your normal session, which does not touch the credit. Only the script's own API calls do.
4. Check the Usage page weekly. Use Haiku until quality is not good enough, then move up a model.

## Sources

- Pricing: https://platform.claude.com/docs/en/about-claude/pricing
- First API call: https://platform.claude.com/docs/en/get-started
- Credit terms: the Anthropic email you received (not independently verified)
