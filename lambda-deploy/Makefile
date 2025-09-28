# ====== Parámetros ======
PROFILE       ?= default
REGION        ?= us-east-1
ACCOUNT_ID    ?= $(shell aws sts get-caller-identity --query Account --output text --profile $(PROFILE))

REPO          ?= hello-world-lambda
FUNCTION_NAME ?= hello-world-lambda
ROLE_ARN      ?= arn:aws:iam::$(ACCOUNT_ID):role/lambda-exec-hello-world

# Tags para distinguir formatos
TAG_OCI       ?= lambda-oci     # imagen "normal" pushed por Docker (manifiesto OCI dependiendo del builder)
TAG_V2S2      ?= lambda-v2      # imagen convertida a Docker v2 schema2 (lo que Lambda consume sin sorpresas)

# Registro y URIs
ECR_REGISTRY  := $(ACCOUNT_ID).dkr.ecr.$(REGION).amazonaws.com
IMAGE_LOCAL   := $(REPO):$(TAG_OCI)
IMAGE_ECR_OCI := $(ECR_REGISTRY)/$(REPO):$(TAG_OCI)
IMAGE_ECR_V2  := $(ECR_REGISTRY)/$(REPO):$(TAG_V2S2)

# ====== Phony ======
.PHONY: help build run logs stop \
        ecr-create ecr-login push-oci v2s2 check-manifest digest print-uri \
        lambda-create lambda-update lambda-invoke

# ====== Ayuda ======
help:
	@echo "Targets disponibles:"
	@echo "  build           - Buildx arm64 -> imagen local (docker daemon)"
	@echo "  run/logs/stop   - Levanta/ver logs/para docker compose (local)"
	@echo "  ecr-create      - Crea repo ECR $(REPO) si no existe"
	@echo "  ecr-login       - Login en ECR (docker y skopeo)"
	@echo "  push-oci        - Push de $(IMAGE_LOCAL) a $(IMAGE_ECR_OCI)"
	@echo "  v2s2            - Copia/convierte OCI -> Docker v2 schema2 en tag $(TAG_V2S2)"
	@echo "  check-manifest  - Muestra el mediaType del tag $(TAG_V2S2)"
	@echo "  digest          - Imprime el digest del tag $(TAG_V2S2)"
	@echo "  print-uri       - Imprime la URI '@digest' para Lambda"
	@echo "  lambda-create   - Crea la función Lambda con la imagen @digest"
	@echo "  lambda-update   - Actualiza el código de Lambda al último @digest"
	@echo "  lambda-invoke   - Invoca remotamente la función y muestra la respuesta"

# ====== Build local (arm64) ======
build:
	docker buildx build \
		--platform linux/arm64 \
		-t $(IMAGE_LOCAL) \
		--output type=docker \
		.

# ====== Local compose ======
run:
	docker compose up --build -d

logs:
	docker compose logs -f

stop:
	docker compose down

# ====== ECR: repo y login ======
ecr-create:
	aws ecr create-repository --repository-name $(REPO) --region $(REGION) --profile $(PROFILE) || true

ecr-login:
	aws ecr get-login-password --region $(REGION) --profile $(PROFILE) | \
		docker login --username AWS --password-stdin $(ECR_REGISTRY)
	# login para skopeo (si está instalado)
	@command -v skopeo >/dev/null 2>&1 && \
	aws ecr get-login-password --region $(REGION) --profile $(PROFILE) | \
		skopeo login --username AWS --password-stdin $(ECR_REGISTRY) || \
	echo "skopeo no instalado (opcional, solo necesario para 'v2s2')."

# ====== Push inicial (OCI segun builder) ======
push-oci: build ecr-create ecr-login
	docker tag $(IMAGE_LOCAL) $(IMAGE_ECR_OCI)
	docker push $(IMAGE_ECR_OCI)

# ====== Convertir a Docker v2 schema2 (Lambda-friendly) ======
# Requiere 'skopeo'. En macOS: 'brew install skopeo'
v2s2: push-oci
	@command -v skopeo >/dev/null 2>&1 || (echo "ERROR: skopeo no encontrado. Instálalo (p.ej. brew install skopeo)"; exit 1)
	skopeo copy --format v2s2 \
	  docker://$(IMAGE_ECR_OCI) \
	  docker://$(IMAGE_ECR_V2)

# ====== Verificación de mediaType ======
check-manifest:
	@aws ecr describe-images \
	  --repository-name $(REPO) \
	  --image-ids imageTag=$(TAG_V2S2) \
	  --query 'imageDetails[0].imageManifestMediaType' \
	  --output text --region $(REGION) --profile $(PROFILE)

# ====== Digest y URI '@digest' ======
digest:
	@aws ecr describe-images \
	  --repository-name $(REPO) \
	  --image-ids imageTag=$(TAG_V2S2) \
	  --query 'imageDetails[0].imageDigest' \
	  --output text --region $(REGION) --profile $(PROFILE)

print-uri:
	@echo "$(IMAGE_ECR_V2)@$$(
		aws ecr describe-images \
		  --repository-name $(REPO) \
		  --image-ids imageTag=$(TAG_V2S2) \
		  --query 'imageDetails[0].imageDigest' \
		  --output text --region $(REGION) --profile $(PROFILE) \
	)"

# ====== Lambda (create/update/invoke) ======
lambda-create: v2s2
	aws lambda create-function \
	  --function-name $(FUNCTION_NAME) \
	  --package-type Image \
	  --code ImageUri=$(IMAGE_ECR_V2)@$$(
		aws ecr describe-images \
		  --repository-name $(REPO) \
		  --image-ids imageTag=$(TAG_V2S2) \
		  --query 'imageDetails[0].imageDigest' \
		  --output text --region $(REGION) --profile $(PROFILE) \
	  ) \
	  --role $(ROLE_ARN) \
	  --timeout 5 \
	  --memory-size 128 \
	  --architectures arm64 \
	  --region $(REGION) --profile $(PROFILE)

lambda-update: v2s2
	aws lambda update-function-code \
	  --function-name $(FUNCTION_NAME) \
	  --image-uri $(IMAGE_ECR_V2)@$$(
		aws ecr describe-images \
		  --repository-name $(REPO) \
		  --image-ids imageTag=$(TAG_V2S2) \
		  --query 'imageDetails[0].imageDigest' \
		  --output text --region $(REGION) --profile $(PROFILE) \
	  ) \
	  --region $(REGION) --profile $(PROFILE)

# Invocación remota (payload vacío)
lambda-invoke:
	aws lambda invoke \
	  --function-name $(FUNCTION_NAME) \
	  --payload '{}' \
	  --cli-binary-format raw-in-base64-out \
	  --region $(REGION) --profile $(PROFILE) \
	  response.json >/dev/null && cat response.json && echo