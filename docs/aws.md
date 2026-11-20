# AWS mapping (prototype)

| Local | AWS |
|---|---|
| Keycloak (`QOD_AUTH_KEYCLOAK_*`) | Entra ID (`QOD_AUTH_AZURE_*`) or Cognito (`QOD_AUTH_AWS_*`); users and groups provisioned by SCIM |
| `qod` container | ECS/EKS (Helm chart in the QoD repo); nodes scale per pool |
| Postgres | RDS for PostgreSQL (QoD control plane + DuckLake catalog) |
| SeaweedFS | S3, accessed only by QoD nodes through an IAM role |
| Plain HTTP on 9494 | `QOD_QUACK_TLS_ENABLED=true` or TLS at the load balancer; session-sticky for Quack |

Clients never get S3 or Postgres credentials, so QoD is the only enforcement point. Per-user identity does not reach S3.
