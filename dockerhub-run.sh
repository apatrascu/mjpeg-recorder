#!/bin/bash

docker pull palecsandru/mjpeg-recorder
docker run -dit --restart=always --name mjpegrecorder -v `pwd`/video:/root/video palecsandru/mjpeg-recorder
