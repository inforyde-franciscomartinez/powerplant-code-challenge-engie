FROM python:3.12


WORKDIR /code


COPY ./requirements.txt ./requirements.txt


RUN pip install --no-cache-dir --upgrade -r ./requirements.txt


COPY ./application ./application

EXPOSE 8888

CMD ["fastapi", "run", "application.main:app", "--port", "8888"]
