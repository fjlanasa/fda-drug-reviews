# build stage
FROM python:3.10 AS builder

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# install tesserac
RUN apt-get update \
    && apt-get -y install tesseract-ocr \
    && apt-get -y install ffmpeg libsm6 libxext6 # required for opencv

# copy files
COPY pyproject.toml pdm.lock README.md /project/
COPY fda/ /project/fda

# install dependencies and project into the local packages directory
WORKDIR /project
RUN mkdir __pypackages__ && pdm sync --prod --no-editable


# run stage
FROM python:3.10

# retrieve packages from build stage
ENV PYTHONPATH=/project/pkgs
COPY --from=builder /project/fda /fda
COPY --from=builder /project/__pypackages__/3.10/lib /project/pkgs

# retrieve executables
COPY --from=builder /project/__pypackages__/3.10/bin/* /bin/

# set command/entrypoint, adapt to fit your needs
CMD ["python"]