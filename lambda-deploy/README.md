# Deploy de una función Lambda con contenedor (Docker + ECR)

Este documento describe paso a paso cómo empaquetar y desplegar una función **AWS Lambda** basada en un contenedor Docker.  
El flujo incluye:

1. Creación del rol de ejecución en IAM.
2. Construcción y publicación de la imagen en Amazon ECR.
3. Conversión opcional de la imagen a formato Docker v2.
4. Creación e invocación de la función Lambda.

> ⚠️ **Nota**: Este instructivo es **agnóstico**. Debes reemplazar valores como:
- `REGION` → la región de AWS (ejemplo: `us-east-1`)  
- `ACCOUNT_ID` → el ID de tu cuenta de AWS  
- `PROFILE` → el perfil de credenciales de AWS CLI (ejemplo: `default`)  
- `REPO_NAME` → nombre del repositorio en ECR  
- `FUNCTION_NAME` → nombre de la función Lambda  

---

```bash
aws sso login --profile PROFILE
```

## 1. Crear rol de ejecución

```bash
aws iam create-role \
  --role-name lambda-exec-hello-world \
  --assume-role-policy-document file://trust.json --profile PROFILE
```


Adjuntar la política básica para escribir logs en  **CloudWatch Logs**:

```bash
aws iam attach-role-policy \
  --role-name lambda-exec-hello-world \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole --profile PROFILE
```

(Esperar unos segundos a que el rol esté listo)

```bash
ROLE_ARN=$(aws iam get-role \
  --role-name lambda-exec-hello-world \
  --query 'Role.Arn' --profile PROFILE \
  --output text)
echo $ROLE_ARN
```

## **2. Construir la imagen Docker**

Construir la imagen para  linux/arm64  y cargarla en el  **Docker daemon local**:

```bash
docker buildx build \
  --platform linux/arm64 \
  -t hello-world-lambda:lambda-d2-v2 \
  --output type=docker \
  .
```

## **3. Publicar en Amazon ECR**

Autenticarse contra ECR:

```bash
aws ecr get-login-password --region REGION --profile PROFILE \
| docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
```bash
aws ecr create-repository --repository-name hello-world-lambda --profile PROFILE
```

Etiquetar y subir:

```bash
docker tag hello-world-lambda:lambda-d2-v2 ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPO_NAME:lambda-d2-v2
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPO_NAME:lambda-d2-v2
```

## **4. (Opcional) Convertir imagen OCI → Docker v2**

Algunas funciones Lambda requieren el formato  Docker v2. Para ello se usa  **skopeo**:

Instalar  skopeo:

```bash
brew install skopeo
```

Login en ECR para  skopeo:

```bash
aws ecr get-login-password --region REGION --profile PROFILE \
| skopeo login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
```

Copiar/convertir la imagen a un nuevo tag:

```bash
skopeo copy --format v2s2 \
  docker://ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPO_NAME:lambda-d2-v2 \
  docker://ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPO_NAME:lambda-v2
```

Verificar el tipo de manifiesto:

```bash
aws ecr describe-images \
  --repository-name REPO_NAME \
  --image-ids imageTag=lambda-v2 \
  --query 'imageDetails[0].imageManifestMediaType' \
  --output text --region REGION --profile PROFILE
```

Debe mostrar:

```bash
application/vnd.docker.distribution.manifest.v2+json
```

Obtener el  digest  de la imagen:

```bash
DIGEST=$(aws ecr describe-images \
  --repository-name REPO_NAME \
  --image-ids imageTag=lambda-v2 \
  --query 'imageDetails[0].imageDigest' \
  --output text --region REGION --profile PROFILE)
```

## **5. Crear la función Lambda**

```bash
aws lambda create-function \
  --function-name FUNCTION_NAME \
  --package-type Image \
  --code ImageUri=ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/REPO_NAME@${DIGEST} \
  --role $ROLE_ARN \
  --timeout 5 \
  --memory-size 128 \
  --architectures arm64 \
  --region REGION --profile PROFILE
```

## **6. Invocar la función**

```bash
aws lambda invoke \
  --function-name FUNCTION_NAME \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  --region REGION --profile PROFILE \
  response.json && cat response.json && echo
```

## **Resultado esperado**

La salida debe ser el  **payload de la función Lambda**  en el archivo  response.json.

Ejemplo:

```bash
{
  "statusCode": 200,
  "body": "Hello World!"
}
```

# Usando Makefile

```bash
make build
make push-oci
make v2s2
make check-manifest   # Debe imprimir: application/vnd.docker.distribution.manifest.v2+json
make lambda-create    # O 'make lambda-update' si la función ya existe
make lambda-invoke
```

## **Referencias**

-   [AWS Lambda – Contenedores como paquete](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
-   [Docker Buildx](https://docs.docker.com/buildx/working-with-buildx/)
-   [Skopeo](https://github.com/containers/skopeo)