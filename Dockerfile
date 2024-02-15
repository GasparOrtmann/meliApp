# Usa una imagen base apropiada
FROM python:3.12

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /meliApp

# Copia los archivos de la aplicación al contenedor
COPY . /meliApp

# Instala las dependencias de la aplicación
RUN pip install mysql-connector-python pandas

# Comando para ejecutar la aplicación
CMD ["python3", "main.py"]


