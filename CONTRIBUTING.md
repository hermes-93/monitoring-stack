# Contributing

## Development Setup

```bash
git clone https://github.com/hermes-93/monitoring-stack.git
cd monitoring-stack
cp .env.example .env
make up
```

## Making Changes

1. Create a feature branch: `git checkout -b feature/my-change`
2. Make your changes
3. Run tests: `make test`
4. Run linting: `make lint`
5. Validate configs: `make validate`
6. Open a pull request

## Adding Alert Rules

Alert rules live in `prometheus/rules/alerts.yml`. Each rule must have:

```yaml
- alert: MyAlert
  expr: <promql expression>
  for: <duration>
  labels:
    severity: warning|critical
  annotations:
    summary: "Short description ({{ $labels.instance }})"
    description: "Detailed description with value {{ $value }}"
```

Run `make validate` to check with `promtool check rules` before committing.

## Adding Dashboards

Place dashboard JSON files in `grafana/provisioning/dashboards/`. Grafana reloads
provisioned dashboards every 30 seconds (configurable in `dashboard.yml`).

Export from Grafana UI: **Dashboard → Share → Export → Save to file**.

## Code Style

- YAML: 2-space indent, no tabs
- Prometheus expressions: one clause per line for readability
- Alert names: PascalCase (e.g. `HighCPUUsage`)
- Recording rule names: `level:metric:operation` convention

## Running Tests Locally

```bash
pip3 install -r tests/requirements.txt
python3 -m pytest tests/ -v
```
