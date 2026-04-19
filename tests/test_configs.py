"""Validate monitoring config files without running containers."""
import os
import yaml
import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")


def load_yaml(path):
    with open(os.path.join(REPO_ROOT, path)) as f:
        return yaml.safe_load(f)


class TestPrometheusConfig:
    def test_prometheus_yml_parses(self):
        cfg = load_yaml("prometheus/prometheus.yml")
        assert cfg is not None

    def test_global_scrape_interval(self):
        cfg = load_yaml("prometheus/prometheus.yml")
        assert "global" in cfg
        assert "scrape_interval" in cfg["global"]

    def test_alertmanager_configured(self):
        cfg = load_yaml("prometheus/prometheus.yml")
        am = cfg.get("alerting", {}).get("alertmanagers", [])
        assert len(am) > 0

    def test_rule_files_configured(self):
        cfg = load_yaml("prometheus/prometheus.yml")
        assert len(cfg.get("rule_files", [])) > 0

    def test_scrape_configs_present(self):
        cfg = load_yaml("prometheus/prometheus.yml")
        jobs = [s["job_name"] for s in cfg.get("scrape_configs", [])]
        assert "prometheus" in jobs
        assert "node" in jobs
        assert "blackbox-http" in jobs

    def test_alert_rules_parse(self):
        cfg = load_yaml("prometheus/rules/alerts.yml")
        assert "groups" in cfg
        assert len(cfg["groups"]) > 0

    def test_alert_rules_have_required_fields(self):
        cfg = load_yaml("prometheus/rules/alerts.yml")
        for group in cfg["groups"]:
            for rule in group.get("rules", []):
                if "alert" in rule:
                    assert "expr" in rule, f"Alert {rule['alert']} missing expr"
                    assert "labels" in rule, f"Alert {rule['alert']} missing labels"
                    assert "annotations" in rule, f"Alert {rule['alert']} missing annotations"
                    assert "severity" in rule["labels"], f"Alert {rule['alert']} missing severity"

    def test_recording_rules_parse(self):
        cfg = load_yaml("prometheus/rules/recording_rules.yml")
        assert "groups" in cfg
        for group in cfg["groups"]:
            for rule in group.get("rules", []):
                if "record" in rule:
                    assert "expr" in rule


class TestAlertmanagerConfig:
    def test_alertmanager_yml_parses(self):
        cfg = load_yaml("alertmanager/alertmanager.yml")
        assert cfg is not None

    def test_route_configured(self):
        cfg = load_yaml("alertmanager/alertmanager.yml")
        assert "route" in cfg
        assert "receiver" in cfg["route"]

    def test_receivers_present(self):
        cfg = load_yaml("alertmanager/alertmanager.yml")
        names = [r["name"] for r in cfg.get("receivers", [])]
        assert "default" in names
        assert "critical" in names

    def test_inhibit_rules_present(self):
        cfg = load_yaml("alertmanager/alertmanager.yml")
        assert len(cfg.get("inhibit_rules", [])) > 0


class TestBlackboxConfig:
    def test_blackbox_yml_parses(self):
        cfg = load_yaml("blackbox/blackbox.yml")
        assert cfg is not None

    def test_http_module_present(self):
        cfg = load_yaml("blackbox/blackbox.yml")
        assert "http_2xx" in cfg.get("modules", {})

    def test_icmp_module_present(self):
        cfg = load_yaml("blackbox/blackbox.yml")
        assert "icmp" in cfg.get("modules", {})


class TestDockerCompose:
    def test_docker_compose_parses(self):
        cfg = load_yaml("docker-compose.yml")
        assert cfg is not None

    def test_required_services(self):
        cfg = load_yaml("docker-compose.yml")
        services = list(cfg.get("services", {}).keys())
        for svc in ["prometheus", "alertmanager", "grafana", "node-exporter", "blackbox-exporter"]:
            assert svc in services, f"Service {svc} not in docker-compose.yml"

    def test_all_services_have_healthchecks(self):
        cfg = load_yaml("docker-compose.yml")
        for name, svc in cfg.get("services", {}).items():
            assert "healthcheck" in svc, f"Service {name} missing healthcheck"

    def test_grafana_provisioning_volume(self):
        cfg = load_yaml("docker-compose.yml")
        volumes = cfg["services"]["grafana"].get("volumes", [])
        has_provisioning = any("provisioning" in str(v) for v in volumes)
        assert has_provisioning

    def test_grafana_datasource_provision_parses(self):
        cfg = load_yaml("grafana/provisioning/datasources/prometheus.yml")
        assert "datasources" in cfg
        ds = cfg["datasources"][0]
        assert ds["type"] == "prometheus"
