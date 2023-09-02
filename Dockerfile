FROM python:3.10

WORKDIR /mindstory

COPY ./mindstory/requirements.txt .

RUN pip install -r requirements.txt

COPY ./mindstory .
COPY ./storage.db.bak .
COPY ./storage.db.dat .
COPY ./storage.db.dir .
COPY ./transaction_code.bak .
COPY ./transaction_code.dat .
COPY ./transaction_code.dir .

EXPOSE 80

ENTRYPOINT [ "python" ]

CMD ["./app/routes.py"]