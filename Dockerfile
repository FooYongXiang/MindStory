FROM python:3.10

WORKDIR /mindstory

COPY ./mindstory/requirements.txt .

RUN pip install -r requirements.txt

COPY ./mindstory .

EXPOSE 80

ENTRYPOINT [ "python" ]

CMD ["./app/routes.py"]