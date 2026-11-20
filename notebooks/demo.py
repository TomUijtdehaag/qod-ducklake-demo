import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import duckdb
    import marimo as mo

    # PROTOTYPE. Each persona is a Keycloak user; Keycloak checks the password, QoD maps its `groups` claim to a role.
    PERSONAS = {
        "carol": "engineers: full access",
        "alice": "analysts: reads all, owner_email masked",
        "bob": "partners: only Dutch position reports",
        "mallory": "no group: nothing",
    }

    def connect(user):
        con = duckdb.connect()
        con.execute(
            f"ATTACH 'quack:localhost:9494' AS qod (TYPE quack, TOKEN 'tenant=demo&pool=bi&user={user}&password={user}')"
        )
        return con


    return PERSONAS, connect, mo


@app.cell
def _(mo):
    mo.md(r"""
    # Governed DuckLake with Quack on Demand

    Every query goes through **Quack on Demand** (QoD). It signs the user in with the identity provider
    (Keycloak here; Entra ID or Cognito in AWS), maps the token's groups to roles, then rewrites or refuses
    each statement: table grants, row filters, column masks and filtered metadata.
    The access model is one file: [`qod/governance.yaml`](../qod/governance.yaml).
    Who ran what: [statement history](http://localhost:20900/ui/audit/statements) in the QoD admin UI (admin / admin).
    """)
    return


@app.cell(hide_code=True)
def _(PERSONAS, connect, mo):
    # Live access matrix: every cell is a real query through QoD as that user.
    def _check(user, sql, show):
        try:
            return show(connect(user).sql(sql).fetchall())
        except Exception:
            return "❌"

    _checks = {
        "read `aircraft`": ("SELECT count(*) FROM qod.main.aircraft", lambda r: f"✅ {r[0][0]} rows"),
        "`owner_email`": ("SELECT owner_email FROM qod.main.aircraft LIMIT 1", lambda r: "🔒 masked" if r[0][0] == "***" else "✅ visible"),
        "read `position_reports`": ("SELECT count(*) FROM qod.main.position_reports", lambda r: f"✅ {r[0][0]} rows"),
        "countries": ("SELECT string_agg(DISTINCT country, ', ' ORDER BY country) FROM qod.main.position_reports", lambda r: r[0][0] or "-"),
        "write (`DELETE … WHERE false`)": ("DELETE FROM qod.main.aircraft WHERE false", lambda r: "✅"),
        "tables visible": ("SELECT count(*) FROM (SHOW ALL TABLES)", lambda r: str(r[0][0])),
    }
    _rows = ["| user | role | " + " | ".join(_checks) + " |", "|---" * (len(_checks) + 2) + "|"]
    for _user, _role in PERSONAS.items():
        _rows.append(f"| **{_user}** | {_role} | " + " | ".join(_check(_user, s, f) for s, f in _checks.values()) + " |")
    mo.vstack([mo.md("## Who can do what"), mo.md("\n".join(_rows)), mo.md("❌ = refused, or the table is invisible to that user.")])
    return


@app.cell
def _(PERSONAS, mo):
    queries = {
        "read aircraft": "SELECT * FROM qod.main.aircraft",
        "positions by country": "SELECT country, count(*) AS reports FROM qod.main.position_reports GROUP BY ALL ORDER BY 1",
        "filter on masked email": "SELECT * FROM qod.main.aircraft WHERE owner_email LIKE 'fleet%'",
        "copy filtered rows": "INSERT INTO qod.main.position_reports SELECT * FROM qod.main.position_reports",
        "tables I can see": "SELECT database, schema, name FROM (SHOW ALL TABLES)",
        "delete aircraft": "DELETE FROM qod.main.aircraft WHERE false",
    }
    user = mo.ui.dropdown(options=PERSONAS, value="bob", label="Run as")
    query = mo.ui.dropdown(options=queries, value="read aircraft", label="Query")
    mo.vstack([
        mo.md("## Try it\nPick a user and a query; it runs through QoD as that user. The SQL cell after it runs anything you type as the same user."),
        mo.hstack([user, query], justify="start"),
    ])
    return query, user


@app.cell
def _(connect, user):
    as_user = connect(user.selected_key)
    return (as_user,)


@app.cell
def _(as_user, mo, query):
    try:
        _out = as_user.sql(query.value).pl()
    except Exception as e:
        _out = mo.callout(str(e).splitlines()[0], kind="danger")
    mo.vstack([mo.md(f"```sql\n{query.value}\n```"), _out])
    return


@app.cell
def _(as_user, mo):
    _df = mo.sql(
        f"""
        SELECT * FROM qod.main.position_reports
        """,
        engine=as_user
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Scaling compute (not in this demo)

    In the QoD UI, a **tenant** (`demo`) owns users, roles and DuckLake databases (`flights`). A **pool** (`bi`) is a group
    of DuckDB **nodes** serving one database; this demo runs one node inside the `qod` container.

    QoD is the single front door for many nodes: it routes each statement to the least-loaded node of the pool
    (`readonly`, `writeonly` or `dual`) and every node checks the user's grants with QoD before running it.
    More nodes means more concurrent queries, not a faster single query (no distributed joins).

    Nodes run as child processes (here), Kubernetes pods (Helm chart), or "fleet" workers on your own servers, which
    QoD's repo emulates in Docker Compose with `docker-compose.fleet.yml`. Clients don't change: same `ATTACH`, same token.
    """)
    return


if __name__ == "__main__":
    app.run()
