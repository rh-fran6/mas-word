.PHONY: lint test prepare-cluster prepare-fleet validate report clean

ANSIBLE_ARGS ?=
CLUSTER ?=
ENVIRONMENT ?= development
SEAT ?=

lint:
	ansible-lint playbooks/ roles/
	yamllint -c .yamllint.yml playbooks/ roles/ acm/ config/
	python -m ruff check cli/ plugins/ tests/

test:
	python -m pytest tests/ -v

prepare-cluster:
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required. Usage: make prepare-cluster CLUSTER=cluster01" && exit 1)
	ansible-playbook playbooks/prepare-cluster.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

prepare-fleet:
	ansible-playbook playbooks/prepare-fleet.yml \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

validate:
	@if [ -n "$(CLUSTER)" ]; then \
		ansible-playbook playbooks/validate-cluster.yml \
			-e masworld_cluster_id=$(CLUSTER) \
			-e @config/environments/$(ENVIRONMENT).yaml \
			$(ANSIBLE_ARGS); \
	else \
		ansible-playbook playbooks/validate-fleet.yml \
			-e @config/environments/$(ENVIRONMENT).yaml \
			$(ANSIBLE_ARGS); \
	fi

report:
	@if [ -n "$(CLUSTER)" ]; then \
		ansible-playbook playbooks/validate-cluster.yml \
			-e masworld_cluster_id=$(CLUSTER) \
			-e @config/environments/$(ENVIRONMENT).yaml \
			-t environment_report \
			$(ANSIBLE_ARGS); \
	else \
		echo "Usage: make report CLUSTER=cluster01"; \
	fi

rotate-credentials:
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required." && exit 1)
	ansible-playbook playbooks/rotate-credentials.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e masworld_seat_number=$(SEAT) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

reset-exercises:
	@test -n "$(CLUSTER)" || (echo "ERROR: CLUSTER is required." && exit 1)
	ansible-playbook playbooks/reset-exercises.yml \
		-e masworld_cluster_id=$(CLUSTER) \
		-e @config/environments/$(ENVIRONMENT).yaml \
		$(ANSIBLE_ARGS)

clean:
	find . -name '*.retry' -delete
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name '.pytest_cache' -type d -exec rm -rf {} + 2>/dev/null || true
