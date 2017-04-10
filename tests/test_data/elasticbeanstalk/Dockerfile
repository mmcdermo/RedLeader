FROM python
COPY ./ /var/code/
RUN pip install -r /var/code/requirements.txt
EXPOSE 5000
ENTRYPOINT ["python", "/var/code/server.py"]
