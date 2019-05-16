FROM nbase_py37_opencv3
LABEL author="ggopalan"
LABEL project="neutrino"
MAINTAINER Giri Gopalan <ggopalan42@gmail.com>

# RUN pip install <something>  # Consolidate as each RUN adds a layer

# ENTRYPOINT ["/bin/echo", "Hello World!"]
COPY neutrino/* /opt/neutrino/


# ENTRYPOINT ["python", "hello.py"]
# ENTRYPOINT ["ls"]
ENTRYPOINT ["python", "-m", "http.server"]
