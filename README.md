# Fokals

**Author:** Fokals
**Version:** 0.0.1
**Type:** tool
**Source:** https://github.com/fokals/dify-plugin

Fokals company intelligence for Dify agents and workflows: find, enrich and profile companies by technology, hiring, funding, buying intent and company health.

AI-powered company intelligence on how companies around the world grow, change and compete. Fokals derives advanced signals from company data, covering everything from technology and hiring to funding, buying intent and company health. Refreshed every day and brought together into a clear view of every market.

## Setup

1. Sign up at [fokals.com](https://www.fokals.com/signup).
2. Make a key on your [account page](https://www.fokals.com/account).
3. In Dify, install the Fokals plugin from the Marketplace, open it and paste the key into **Fokals key**. The key is checked against your account when you save it.

The plugin calls one service, `https://api.fokals.com/v1`, over HTTPS. Nothing else is needed.

## Use it

Add the Fokals tools to an agent and ask, for example:

- "Which US companies running HubSpot are hiring right now?"
- "Enrich stripe.com, shopify.com and notion.so."
- "Tell me about gymshark.com: its stack, its hiring and its buying topics."
- "Which companies changed their prices this week?"
- "Is HubSpot adoption growing, by industry?"

In a workflow, each tool returns its answer as text and as JSON (`message` and `data`).

Where a tool takes several companies, give them separated by commas.

## Tools

| Tool | What it does |
| --- | --- |
| `find_companies` | Companies by a technology they run, a buying topic, hiring, an announcement, a project in their job ads, a change of price, agent readiness, health, industry or country |
| `count_companies` | How many companies match the same filters, and what getting them would cost (free) |
| `enrich_companies` | Your own list of companies, by website or name, filled in |
| `company_profile` | One company in depth |
| `company_changes` | What is new at your companies since a date |
| `search_job_postings` | Open job postings by title, function, seniority, country, work mode, technology and pay |
| `similar_companies` | Lookalikes of a company, or its competitors |
| `company_connections` | The customers, partners, integrations and investors a company's website names, and who names it |
| `identify_company` | Which company a name or website address means (free) |
| `market_breakdown` | How a market divides by industry, country, technology, buying topic and more |
| `vendor_scorecard` | A technology vendor month by month: companies won and lost, and the rivals they came from or moved to |
| `companies_like_customers` | Companies that look today the way your customers looked when they bought |
| `company_health` | A company's health this week, with the reasons |
| `likely_next` | The technologies a company is likeliest to add next |
| `intent_history` | A company's buying topics week by week, with the signals behind them |
| `sales_team` | The sales team a company's job ads show, by role, segment and country |
| `funding_filings` | A company's notices of a private fundraise (Form D), with the amounts |
| `headcount_history` | How many people a company employed over the years |
| `traffic_history` | How popular a company's website has been, month by month |
| `signal_feed` | Every buying signal across all companies from a day on |
| `announcement_feed` | Every announcement across all companies from a day on |
| `change_feed` | Every website change across all companies from a day on |
| `listed_securities` | Stock listings with their identifiers and the company each belongs to |
| `market_trends` | How a measure of the market has moved over time |
| `market_movers` | The market figures that moved most on one day |
| `sales_pay_benchmarks` | Advertised sales pay by role and country |
| `list_filters` | The values the search tools filter by, the market measures and the sales roles (free) |
| `account_balance` | Your balance, this month's spend and the prices (free) |

## Prices

Paid tools take what they cost from your prepaid Fokals balance, at the prices on the [pricing page](https://www.fokals.com/pricing), also at [api.fokals.com/v1/prices](https://api.fokals.com/v1/prices). A company that is not found costs nothing.

A call that would cost more than your account lets run unasked does not run. It answers with its price instead, and the agent asks you before calling again with `max_usd`.

## Also from Fokals

Fokals is also a remote MCP server at `https://mcp.fokals.com/mcp`, with the same account, balance and prices. See [fokals.com/docs/connect](https://www.fokals.com/docs/connect).

## Support

Write to partners@fokals.com, or open an issue at https://github.com/fokals/dify-plugin/issues.
