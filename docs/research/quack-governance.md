# Governance on top of Quack / DuckDB / DuckLake: what already exists

_Researched 2026-11-13. "Last activity" = the latest commit on `main` (from the GitHub atom feed)._

## TL;DR
- **Quack itself** gives you two hooks and nothing more. The defaults are `quack_check_token`, a shared-secret check, and `quack_nop_authorization`, which allows everything. There are no users or roles. ([docs](https://duckdb.org/docs/2.0/quack/security.html), [DeepWiki](https://deepwiki.com/duckdb/duckdb-quack/4.2-authentication-and-authorization))
- **`quack_oauth` (DataZooDE) is the only shipped governance layer built specifically for Quack.** It is a community extension that plugs real OIDC/OAuth into both hooks. It also adds a claims- or SQL-table-driven policy (action × object × column), plus audit logging.
- **Row-level security:** the `CHRV/duckdb-extension-rls` extension is usable. It has Postgres-style policies keyed on `getvariable(...)` but no notion of users or roles. It is not in the community repo.
- **DuckLake** lists "Roles and access control" as a **top priority for DuckLake 2.0, which is still planned and not shipped**. Today the docs only describe coarse access control at the storage and catalog level.
- Other DuckDB servers that ship auth (GizmoSQL, duckgres) use **other protocols** (Flight SQL and pgwire). They are alternatives to Quack, not add-ons.

## Comparison

| Project | What it does | Status | License | Last activity | Fit for Quack→DuckLake on AWS |
|---|---|---|---|---|---|
| [Quack built-in hooks](https://duckdb.org/docs/2.0/quack/security.html) | `quack_authentication_function(sid, client_token, server_token)` and `quack_authorization_function(sid, query)`, which can rewrite SQL. Stub defaults. | Shipped (DuckDB 2.0) | MIT | core | The base everything else plugs into |
| [quack_oauth](https://github.com/DataZooDE/quack-oauth) ([community ext](https://duckdb.org/community_extensions/extensions/quack_oauth)) | OIDC/OAuth 2.1 auth via JWKS, RFC 7662 introspection, or Google tokeninfo. Client side handles device_code, client_credentials and refresh flows, with `ATTACH … (token quack_oauth_acquire('cli'))`. Server side parses SQL with DuckDB's parser and classifies the action (Attach/Scan/Insert/Update/Delete/Ddl/Pragma/CopyTo…). Allow/deny comes from scopes or a SQL `policies` table (objects and projected columns). Audit is an in-memory ring plus an optional audit table, with tokens redacted to a SHA-256 prefix. | **Shipped**, early. Tested end-to-end against Keycloak, with replay tests for Entra and Google. ~32★, ~900 downloads/week | MIT | 2026-10-22 | **Best fit.** It sits directly in the Quack hooks and works from CLI, Python and marimo through ATTACH. Cognito/Entra can serve as the IdP. It **allows or denies whole queries; it does not rewrite rows.** Its README warns that `duckdb_tables()`/`duckdb_columns()` leak metadata across tenants. |
| [CHRV/duckdb-extension-rls](https://github.com/CHRV/duckdb-extension-rls) | Postgres-like `CREATE POLICY … USING (…)`, injected as a filter by an optimizer extension. Has `enable_rls`, `rls_policies()`. No users or roles; `TO <role>` is rejected. | Shipped, small (5★), not a community extension, so you build it yourself | MIT | 2026-09-14 | Can be **combined** with quack_oauth. Set a session variable from the token claims, and RLS filters on it. Untested on DuckLake tables and under Quack sessions. |
| [RFC: RBAC extension](https://github.com/duckdb/duckdb/discussions/20264) ([gist](https://gist.github.com/dufferzafar/f12081d4f32e640966d984b33e7077e6)) | Proposal for GRANT/ROLE syntax, column privileges and row policies, enforced via ParserExtension and OptimizerExtension | **Proposal only** (Dec 2025), no replies | – | 2025-12 | Shows the design space. Nothing usable. |
| [DuckLake access-control guide](https://ducklake.select/docs/stable/duckdb/guides/access_control) | Superuser/writer/reader split using Postgres catalog grants and S3 IAM per prefix. Requires trusted writers and data inlining turned off. Readers can see all metadata. | Shipped (docs only) | MIT | – | Defense in depth for the Quack server's own credentials. Not per-user. |
| [DuckLake 2.0 roadmap](https://ducklake.select/roadmap) | "Roles and access control" and "REST API" are listed as top priority. Issue [#107](https://github.com/duckdb/ducklake/issues/107) was moved to discussion #888 in March 2026. | **Planned**, no date or design published | MIT | roadmap updated Oct 2026 | Watch it. It may make DIY policy partly redundant later. |
| [GizmoSQL](https://github.com/gizmodata/gizmosql) | Arrow Flight SQL server for DuckDB. Supports username/password and JWT token auth. **Enterprise edition** adds server-side OAuth/SSO (Keycloak, Entra, Google, Cognito, Clerk) and roles. | Shipped, active | Apache-2.0 core plus a commercial Enterprise edition | 2026-11-10 | Alternative to Quack. Clients need ADBC/JDBC Flight SQL drivers, not native DuckDB ATTACH. |
| [PostHog/duckgres](https://github.com/PostHog/duckgres) | pgwire server for DuckDB/DuckLake. Password auth over TLS, per-user databases, query logging per SQL user, multi-org control plane, OPA-checked Trino grants | Shipped, production at PostHog, 188★ | MIT | 2026-11-10 | Alternative (pgwire). Heavyweight multi-tenant platform. Its auth model fits per-user isolation better than shared-lake RBAC. |
| [Airport](https://github.com/Query-farm/airport) | DuckDB client for Arrow Flight servers. Auth tokens are passed through to a server you write. | Shipped | MIT | 2026-09-04 | Lets you put governance in your own Flight server. Not Quack. |
| [buenavista](https://github.com/jwills/buenavista) | Python pgwire proxy for DuckDB | Stale | Apache-2.0 | 2024-12 | Not recommended |
| [Lakekeeper](https://github.com/lakekeeper/lakekeeper) | Iceberg REST catalog with OpenFGA authorization | Active | Apache-2.0 | 2026-11-13 | No DuckLake integration found. Only relevant if you move to Iceberg. Polaris and Unity Catalog are the same story. |
| MotherDuck | Commented on Quack ([InfoQ](https://www.infoq.com/news/2026/05/duckdb-quack-protocol/)) but has no public plans for Quack governance | – | proprietary | – | n/a |

No Hacker News or Reddit thread turned up another Quack auth/RBAC implementation.

## Gaps to remember
- Nothing ships **column masking**. quack_oauth can only deny a query that projects a column. Row filtering needs the RLS extension or your own SQL rewrite in the authorization hook.
- Parsing the SQL of every query is the only enforcement point. Watch for `read_parquet('s3://…')`, `ATTACH`, `COPY`, `INSTALL`/`LOAD` and secrets. Also lock down the server with `enable_external_access`, `allowed_paths`, `lock_configuration`, and by not exposing S3 secrets to sessions.
- Per-user identity does **not** carry through to S3 or Postgres. The server runs with one IAM role, so the Quack server is the trust boundary.

## Recommendation for this PoC
1. **AuthN:** `quack_oauth` with **Amazon Cognito**, or the corporate Entra ID, as the OIDC issuer. Use JWKS validation. Clients use device_code (CLI, marimo) or client_credentials (services) via `quack_oauth_acquire`.
2. **AuthZ v1:** the quack_oauth **SQL policy table** (roles from token groups/scopes → allowed actions and objects), with the audit table written to a local table and shipped to S3/CloudWatch.
3. **Row-level security, if needed:** evaluate `duckdb-extension-rls`. Have the auth hook set a session variable from claims, and use RLS policies on DuckLake tables. Alternative: write a small custom authorization function that rewrites SQL to governed views.
4. **Defense in depth:** use DuckLake's documented split. The server gets a Postgres reader/writer role and an IAM role scoped to the lake prefix. No S3 credentials for clients. Lock the configuration after startup.
5. **Re-evaluate** when DuckLake 2.0 ships roles and access control. Pick GizmoSQL Enterprise only if you need off-the-shelf SSO and roles with JDBC/BI tools rather than DuckDB-native clients.

## Update 2026-11-20: Quack on Demand, and Unity Catalog OSS

- **[Quack on Demand](https://github.com/starlake-ai/quack-on-demand)** (Starlake, Apache-2.0, v0.14.0): a gateway in front of DuckDB/DuckLake with native Quack and Flight SQL. OIDC (Keycloak, Entra, Cognito, Google), SCIM, RBAC with groups, row policies, column masks, filtered metadata, statement history. Prototyped on branch `prototype/qod-governance`: everything above worked. Young, single vendor.
- **quack_oauth** is now a weaker fit: its latest release fails closed on stock Quack's auth callback; only the older community build works.
- **Unity Catalog OSS** self-hosted: catalog/schema/table grants and credential vending (AWS IAM), but users only (no groups), no row filters or column masks (Databricks-only), Delta not DuckLake. DuckDB's `unity_catalog` extension reads/inserts Delta but enforces nothing itself. No public production write-ups of self-hosted UC OSS with DuckDB found.
