# Glossary (prototype)

**Quack on Demand (QoD)**: the gateway every Client talks to. Authenticates, authorizes and rewrites each statement, then runs it on a DuckDB node.

**Tenant / tenant database / pool**: QoD's isolation units. Here: tenant `demo`, DuckLake database `flights`, pool `bi` of one node.

**Role**: a named set of table grants plus row and column policies (`engineer`, `analyst`, `partner`).

**Group**: maps an IdP group (the token's `groups` claim) to roles.

**Row policy**: a predicate QoD adds to every query on a table for that role.

**Column policy**: hides or masks one column for a role.
