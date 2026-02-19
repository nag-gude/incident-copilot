# Incident Copilot - Makefile
# DeveloperWeek 2026 Hackathon

.PHONY: local deploy-dev deploy-staging deploy-prod provision-lke build push

# Local development
local:
	docker-compose up -d

local-down:
	docker-compose down

# Build images
build:
	./deploy/build-and-push.sh dev

# Provision LKE (requires LINODE_TOKEN)
provision-lke:
	./deploy/provision-lke.sh dev

# Deploy to environments
deploy-dev:
	./deploy/deploy.sh dev build

deploy-staging:
	./deploy/deploy.sh staging build

deploy-prod:
	./deploy/deploy.sh prod build

# Deploy without build (use existing images)
deploy-dev-only:
	./deploy/deploy.sh dev

# Seed demo data (local)
seed:
	python scripts/seed_demo_data.py

# Sanity Studio (requires SANITY_PROJECT_ID in .env; run 'sanity login' once)
sanity-install:
	cd sanity-studio && npm install

sanity-deploy:
	./scripts/sanity-deploy.sh

sanity-dev:
	cd sanity-studio && npm run dev
