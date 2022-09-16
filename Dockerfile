FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine-2021-10-26
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install psycopg2-binary redis
COPY ./app /app
