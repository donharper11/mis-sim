# Host scope live preflight

Read-only SQLAlchemy inspection of disposable PostgreSQL16 database mis_sim_browser_seedproof. No migration applied.

```json
{
  "revision": "20261004_0011",
  "tables": {
    "team": {
      "foreign_keys": [
        {
          "name": "fk_team_created_by",
          "constrained_columns": [
            "created_by"
          ],
          "referred_schema": null,
          "referred_table": "user",
          "referred_columns": [
            "id"
          ],
          "options": {
            "ondelete": "SET NULL"
          },
          "comment": null
        },
        {
          "name": "fk_team_instance_section",
          "constrained_columns": [
            "instance_id",
            "section_id"
          ],
          "referred_schema": null,
          "referred_table": "simulation_instance",
          "referred_columns": [
            "instance_id",
            "section_id"
          ],
          "options": {
            "ondelete": "CASCADE"
          },
          "comment": null
        },
        {
          "name": "fk_team_section",
          "constrained_columns": [
            "section_id"
          ],
          "referred_schema": null,
          "referred_table": "section",
          "referred_columns": [
            "id"
          ],
          "options": {
            "ondelete": "CASCADE"
          },
          "comment": null
        }
      ],
      "unique_constraints": [
        {
          "column_names": [
            "id",
            "instance_id"
          ],
          "name": "uq_team_instance_identity",
          "comment": null
        },
        {
          "column_names": [
            "id",
            "section_id"
          ],
          "name": "uq_team_section_identity",
          "comment": null
        }
      ],
      "rows": 4
    },
    "host_platform": {
      "foreign_keys": [
        {
          "name": "host_platform_instance_id_fkey",
          "constrained_columns": [
            "instance_id"
          ],
          "referred_schema": null,
          "referred_table": "simulation_instance",
          "referred_columns": [
            "instance_id"
          ],
          "options": {
            "ondelete": "CASCADE"
          },
          "comment": null
        },
        {
          "name": "host_platform_team_id_fkey",
          "constrained_columns": [
            "team_id"
          ],
          "referred_schema": null,
          "referred_table": "team",
          "referred_columns": [
            "id"
          ],
          "options": {
            "ondelete": "CASCADE"
          },
          "comment": null
        }
      ],
      "unique_constraints": [
        {
          "column_names": [
            "instance_id",
            "team_id",
            "platform_code"
          ],
          "name": "uq_host_platform_code",
          "comment": null
        }
      ],
      "rows": 0
    },
    "host_platform_member": {
      "foreign_keys": [
        {
          "name": "host_platform_member_platform_id_fkey",
          "constrained_columns": [
            "platform_id"
          ],
          "referred_schema": null,
          "referred_table": "host_platform",
          "referred_columns": [
            "id"
          ],
          "options": {
            "ondelete": "CASCADE"
          },
          "comment": null
        }
      ],
      "unique_constraints": [
        {
          "column_names": [
            "platform_id",
            "asset_key"
          ],
          "name": "uq_host_platform_member_asset",
          "comment": null
        }
      ],
      "rows": 0
    }
  }
}
```
