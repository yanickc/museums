FROM python:3

RUN pip install poetry

WORKDIR museums

# Install dependencies
ADD poetry.lock .
ADD pyproject.toml .
RUN poetry install --no-dev

EXPOSE 8080
ENV STREAMLIT_SERVER_PORT=8080

ADD museums/dashboard.py .
CMD [ "poetry", "run", "streamlit", "run", "dashboard.py" ]

