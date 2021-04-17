FROM python:3.9.4-slim
WORKDIR /tests/python
RUN pip install pipenv
COPY python/Pipfile python/Pipfile.lock /tests/python/
RUN pipenv install
CMD ["pipenv", "run", "tests"]
COPY python/conftest.py python/tests.py /tests/python/
