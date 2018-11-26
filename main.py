#!/usr/bin/env python3
import cv2
import requests
import numpy as np
import datetime


FPS = 15
OUTPUT_DIR = "video/"


def get_current_date():
    return datetime.datetime.today().strftime("%Y%m%d")


def init_video(fourcc, current_date):
    output = OUTPUT_DIR + current_date + ".mp4"
    video_writer = cv2.VideoWriter(output, fourcc, FPS, (640, 480))
    return video_writer


def get_image():
    r = requests.get('http://192.168.1.103/image/jpeg.cgi', stream=True)
    if r.status_code == 200:
        data = bytes()
        for chunk in r.iter_content(chunk_size=1024):
            data += chunk
            a = data.find(b'\xff\xd8')
            b = data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = data[a:b + 2]
                data = data[b + 2:]
                i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return i
    return None


if __name__ == "__main__":
    current_date = get_current_date()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps_sleep_time = 1 / FPS
    video_writer = init_video(fourcc, current_date)
    while True:
        run_date = get_current_date()
        if run_date != current_date:
            video_writer.release()
            current_date = run_date
            video_writer = init_video(fourcc, current_date)
        jpg = get_image()
        if jpg is not None:
            video_writer.write(jpg)
        # r = requests.get('http://192.168.1.103/image/jpeg.cgi', stream=True)
        # if r.status_code == 200:
        #     data = bytes()
        #     for chunk in r.iter_content(chunk_size=1024):
        #         data += chunk
        #         a = data.find(b'\xff\xd8')
        #         b = data.find(b'\xff\xd9')
        #         if a != -1 and b != -1:
        #             jpg = data[a:b + 2]
        #             data = data[b + 2:]
        #             i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
        #             video_writer.write(i)
