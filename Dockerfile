FROM palecsandru/mjpeg-recorder-base

RUN mkdir -p /root/video
ADD * /root/
RUN pip3 install -r /root/requirements.txt
VOLUME ["/root/video"]
WORKDIR /root
ENTRYPOINT ./main.py
