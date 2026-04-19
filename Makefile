.PHONY: up down restart logs ps test lint validate clean help

COMPOSE := docker compose
SERVICES := prometheus alertmanager grafana node-exporter blackbox-exporter

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  up         Start all services (detached)"
	@echo "  down       Stop and remove containers"
	@echo "  restart    Restart all services"
	@echo "  logs       Follow logs for all services"
	@echo "  ps         Show running containers"
	@echo "  test       Run config validation tests"
	@echo "  lint       Validate YAML configs"
	@echo "  validate   Run promtool + amtool checks"
	@echo "  clean      Remove volumes and containers"
	@echo "  help       Show this help"

up:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up -d
	@echo "Services started:"
	@echo "  Prometheus:  http://localhost:9090"
	@echo "  Grafana:     http://localhost:3000"
	@echo "  Alertmanager: http://localhost:9093"

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

test:
	pip3 install -q -r tests/requirements.txt --break-system-packages
	python3 -m pytest tests/ -v

lint:
	$(COMPOSE) config -q
	@echo "docker-compose.yml OK"
	@for f in prometheus/prometheus.yml prometheus/rules/*.yml alertmanager/alertmanager.yml blackbox/blackbox.yml grafana/provisioning/**/*.yml; do \
		python3 -c "import yaml,sys; yaml.safe_load(open('$$f'))" && echo "$$f OK"; \
	done

validate:
	@docker run --rm -v $$(pwd)/prometheus:/prometheus prom/prometheus:v2.51.2 \
		promtool check config /prometheus/prometheus.yml
	@docker run --rm -v $$(pwd)/prometheus/rules:/rules prom/prometheus:v2.51.2 \
		promtool check rules /rules/alerts.yml /rules/recording_rules.yml
	@docker run --rm -v $$(pwd)/alertmanager:/alertmanager prom/alertmanager:v0.27.0 \
		amtool check-config /alertmanager/alertmanager.yml

clean:
	$(COMPOSE) down -v --remove-orphans
