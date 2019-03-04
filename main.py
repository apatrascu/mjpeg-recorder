#!/usr/bin/env python3
import cv2
import requests
import numpy as np
import datetime
import queue
import os
import time
# import threading


FPS = 15
OUTPUT_DIR = "video/"
queue = queue.Queue()
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
sleep_time = 1 / FPS
current_video_name = ""


def get_uid():
    return datetime.datetime.today().strftime("%Y%m%d%H%M%S%f")


def get_day():
    return datetime.datetime.today().strftime("%Y%m%d")


def get_minute():
    return datetime.datetime.today().strftime("%Y%m%d%H%M")


def get_hour():
    return datetime.datetime.today().strftime("%Y%m%d%H")


def init_video():
    global current_video_name
    output = OUTPUT_DIR + get_uid() + ".mp4"
    current_video_name = output
    video_writer = cv2.VideoWriter(output, fourcc, FPS, (640, 480))
    return video_writer


def is_new_day(base):
    current = get_day()
    return base != current


def is_new_minute(base):
    current = get_minute()
    return base != current


def is_new_hour(base):
    current = get_hour()
    return base != current


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


def join_videos():
    # https://gist.github.com/nkint/8576156
    output = OUTPUT_DIR + get_uid() + ".mp4"
    video_writer = cv2.VideoWriter(output, fourcc, FPS, (640, 480))
    video_created = False
    while not queue.empty():
        filename = queue.get()
        cap = cv2.VideoCapture(filename)
        frame = cap.read()
        while frame is not None:
            video_writer.write(frame)
            ret, frame = cap.read()
            video_created = True
        cap.release()
        os.remove(filename)
    video_writer.release()
    if not video_created:
        if os.path.exists(output):
            os.remove(output)


if __name__ == "__main__":
    start_day = get_day()
    start_minute = get_minute()
    start_hour = get_hour()
    video_writer = init_video()
    # video_joiner_thread = threading.Thread(target=join_videos)
    # video_joiner_thread.start()
    while True:
        start = time.time()
        if is_new_day(start_day):
            video_writer.release()
            queue.put(current_video_name)
            start_day = get_day()
            video_writer = init_video()
        elif is_new_minute(start_minute):
            video_writer.release()
            queue.put(current_video_name)
            start_minute = get_minute()
            video_writer = init_video()
        elif is_new_hour():
            video_writer.release()
            queue.put(current_video_name)
            start_hour = get_hour()
            video_writer = init_video()
            join_videos()
        jpg = get_image()
        if jpg is not None:
            video_writer.write(jpg)
        end = time.time()
        delta = end - start
        if delta < sleep_time:
            time.sleep(sleep_time - delta)
