# Lambda como imagen de contenedor (Python 3.12)
FROM public.ecr.aws/lambda/python:3.12

# Código de la función
WORKDIR /var/task
COPY src/ ./src/
COPY requirements.txt ./

# Instalar dependencias (si hubiera)
# (Aquí no hay externas; se deja por si luego agregas)
RUN if [ -s requirements.txt ]; then pip install -r requirements.txt -t .; fi

# Handler (módulo.función)
CMD ["src.handler.lambda_handler"]