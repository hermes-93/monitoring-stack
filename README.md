# monitoring-stack

Production-grade observability stack with **Prometheus**, **Grafana**, **Alertmanager**, **Node Exporter**, and **Blackbox Exporter** — fully containerised and deployable in one command.

[![CI](https://github.com/hermes-93/monitoring-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/hermes-93/monitoring-stack/actions/workflows/ci.yml)
[![Security](https://github.com/hermes-93/monitoring-stack/actions/workflows/security.yml/badge.svg)](https://github.com/hermes-93/monitoring-stack/actions/workflows/security.yml)

## Components

| Service | Image | Port | Purpose |
|---|---|---|---|
| Prometheus | `prom/prometheus:v2.51.2` | 9090 | Metrics collection & alerting engine |
| Alertmanager | `prom/alertmanager:v0.27.0` | 9093 | Alert routing, deduplication, silencing |
| Grafana | `grafana/grafana:10.4.2` | 3000 | Dashboards & visualisation |
| Node Exporter | `prom/node-exporter:v1.8.0` | 9100 | Host metrics (CPU/memory/disk/network) |
| Blackbox Exporter | `prom/blackbox-exporter:v0.25.0` | 9115 | Endpoint probing (HTTP/ICMP/TCP/DNS) |

## Quick Start

```bash
git clone https://github.com/hermes-93/monitoring-stack.git
cd monitoring-stack
cp .env.example .env          # edit passwords and webhook URLs
make up
```

| URL | Credentials |
|---|---|
| http://localhost:3000 | admin / changeme |
| http://localhost:9090 | — |
| http://localhost:9093 | — |

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │              Docker Network: monitoring      │
                    │                                             │
  ┌──────────────┐  │  ┌────────────┐    ┌───────────────────┐   │
  │ Node Exporter│──┼─▶│ Prometheus │───▶│   Alertmanager    │   │
  └──────────────┘  │  │  :9090     │    │     :9093         │   │
                    │  └─────┬──────┘    └───────────────────┘   │
  ┌──────────────┐  │        │                                    │
  │  Blackbox    │──┼────────┘           ┌───────────────────┐   │
  │  Exporter    │  │                    │      Grafana       │   │
  └──────────────┘  │                    │      :3000         │   │
                    │                    └───────────────────┘   │
                    └─────────────────────────────────────────────┘
```

## Alert Rules

### Node Alerts
| Alert | Condition | Severity |
|---|---|---|
| `NodeDown` | Node exporter unreachable for 2m | critical |
| `HighCPUUsage` | CPU > 85% for 5m | warning |
| `HighMemoryUsage` | Memory > 85% for 5m | warning |
| `DiskSpaceLow` | Disk > 80% for 10m | warning |
| `DiskSpaceCritical` | Disk > 95% for 5m | critical |
| `HighNetworkErrors` | Network errors > 10/s for 5m | warning |

### Blackbox Alerts
| Alert | Condition | Severity |
|---|---|---|
| `EndpointDown` | Probe failing for 2m | critical |
| `SlowResponseTime` | Response > 2s for 5m | warning |
| `SSLCertExpiringSoon` | Cert expiry < 14 days | warning |

### Infrastructure Alerts
| Alert | Condition | Severity |
|---|---|---|
| `PrometheusDown` | Prometheus unreachable for 1m | critical |
| `AlertmanagerDown` | Alertmanager unreachable for 2m | critical |

## Recording Rules

Pre-computed metrics for efficient dashboard queries:

| Metric | Description |
|---|---|
| `instance:node_cpu_utilisation:rate5m` | CPU utilisation % per instance |
| `instance:node_memory_utilisation:ratio` | Memory utilisation ratio per instance |
| `instance:node_disk_utilisation:ratio` | Disk utilisation ratio per instance |
| `instance:node_network_receive_bytes:rate5m` | Inbound network bytes/s |
| `instance:node_network_transmit_bytes:rate5m` | Outbound network bytes/s |
| `job:probe_success:avg` | Average probe success ratio per job |

## Grafana Dashboards

Dashboard **Node Overview** is auto-provisioned:
- CPU, memory and disk gauges with threshold colouring
- CPU/memory time-series overlay
- Network traffic (RX/TX bytes/s)
- Instance variable filter

## Configuration

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `changeme` | Grafana admin password |
| `ALERTMANAGER_SLACK_WEBHOOK` | — | Slack incoming webhook URL |
| `ALERTMANAGER_EMAIL_FROM` | — | Sender address for email alerts |
| `ALERTMANAGER_EMAIL_TO` | — | Recipient address for email alerts |
| `ALERTMANAGER_SMTP_HOST` | — | SMTP server host:port |

### Adding Scrape Targets

Edit `prometheus/prometheus.yml` and add a new `scrape_configs` entry:

```yaml
- job_name: my-app
  static_configs:
    - targets:
        - my-app:8080
```

Reload config without restarting:

```bash
curl -X POST http://localhost:9090/-/reload
```

## Make Targets

```
make up        # start all services
make down      # stop all services
make logs      # tail logs
make test      # run config validation tests (20 tests)
make lint      # yamllint all configs
make validate  # promtool + amtool checks (requires Docker)
make clean     # remove containers + volumes
```

## Testing

```bash
make test
# 20 passed in 0.11s
```

Tests cover:
- All YAML files parse without errors
- Prometheus scrape jobs and alertmanager routing are configured
- Alert rules have required fields (expr, labels, severity, annotations)
- All Docker Compose services have healthchecks
- Grafana datasource provisioning is correct

## CI/CD

```
push / PR
   │
   ├── lint-yaml       → yamllint on all config files
   ├── validate-configs → promtool check config + check rules + amtool check-config
   ├── unit-tests      → 20 pytest tests
   └── integration-test (after all pass)
          ├── docker compose up
          ├── health-check all 5 services
          └── verify Prometheus scrape targets
```

Security workflow (weekly + on push to main):
- Trivy config scan → SARIF → GitHub Security tab
- Trivy image scan for all 5 images (CRITICAL/HIGH only)
- Semgrep secrets + YAML scan

## Project Structure

```
monitoring-stack/
├── docker-compose.yml
├── .env.example
├── Makefile
├── prometheus/
│   ├── prometheus.yml          # scrape configs, alertmanager, rule files
│   └── rules/
│       ├── alerts.yml          # 13 alert rules across 3 groups
│       └── recording_rules.yml # 7 pre-computed metrics
├── alertmanager/
│   └── alertmanager.yml        # routing tree, receivers, inhibit rules
├── blackbox/
│   └── blackbox.yml            # http_2xx, icmp, tcp, dns modules
├── grafana/
│   └── provisioning/
│       ├── datasources/        # auto-provision Prometheus datasource
│       └── dashboards/         # auto-provision Node Overview dashboard
├── tests/
│   ├── requirements.txt
│   └── test_configs.py         # 20 config validation tests
└── .github/
    └── workflows/
        ├── ci.yml              # lint → validate → test → integration
        └── security.yml        # trivy + semgrep weekly scan
```
