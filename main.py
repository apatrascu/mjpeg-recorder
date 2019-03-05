#!/usr/bin/env python3
import argparse
import cv2
import requests
import numpy as np
import datetime
import queue
import os
import threading
import shutil
from apscheduler.schedulers.background import BlockingScheduler


FPS = 10
OUTPUT_DIR = "video/"
MINUTE_DIR = OUTPUT_DIR + "minute/"
DAILY_DIR = OUTPUT_DIR + "daily/"
FOURCC = cv2.VideoWriter_fourcc(*'mp4v')
image_queue = queue.Queue()
PRODUCTION = True


def log(message):
    print("[%s] %s" % (datetime.datetime.today().strftime("%Y.%m.%d-%H:%M:%S"), message))


def get_uid():
    return datetime.datetime.today().strftime("%Y%m%d%H%M%S%f")


def get_minute():
    return datetime.datetime.today().strftime("%Y%m%d%H%M")


def get_previous_day():
    yesterday = datetime.date.today() - datetime.timedelta(1)
    return yesterday.strftime("%Y%m%d")


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
                i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                return i
    return None


def image_pusher_runner():
    while True:
        jpg = get_image()
        if jpg is not None:
            image_queue.put(jpg)


def dump_frames_from_queue_to_video_file():
    log("dump_frames_from_queue_to_video_file")
    output = MINUTE_DIR + get_uid() + ".mp4"
    video_writer = cv2.VideoWriter(output, FOURCC, FPS, (640, 480))
    frame_count = image_queue.qsize()
    for i in range(frame_count):
        frame = image_queue.get()
        video_writer.write(frame)
    video_writer.release()


def daily_backup_videos_to_single_video_file():
    # https://gist.github.com/nkint/8576156
    log("backup_videos_to_single_video_file")
    if not PRODUCTION:
        output = DAILY_DIR + get_minute() + ".mp4"
    else:
        output = DAILY_DIR + get_previous_day() + ".mp4"

    videos = os.listdir(MINUTE_DIR)
    if len(videos) == 0:
        return
    if len(videos) == 1:
        shutil.move(MINUTE_DIR + videos[0], output)
        return

    video_writer = cv2.VideoWriter(output, FOURCC, FPS, (640, 480))
    written_into_video = False
    for video in videos:
        filename = MINUTE_DIR + video
        cap = cv2.VideoCapture(filename)
        ret, frame = cap.read()
        while frame is not None:
            video_writer.write(frame)
            ret, frame = cap.read()
            written_into_video = True
        cap.release()
        os.remove(filename)
    video_writer.release()
    if not written_into_video:
        if os.path.exists(output):
            os.remove(output)


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MJPEG Recorder")
    parser.add_argument(
        '-p', '--production',
        help='production mode: (default) --production yes ; testing mode: --production no',
        type=str2bool,
        default=True
    )
    args = parser.parse_args()

    PRODUCTION = args.production
    log("Running with PRODUCTION=%s" % str(PRODUCTION))

    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    if not os.path.isdir(DAILY_DIR):
        os.mkdir(DAILY_DIR)
    if not os.path.isdir(MINUTE_DIR):
        os.mkdir(MINUTE_DIR)

    scheduler = BlockingScheduler()
    image_pusher_thread = threading.Thread(target=image_pusher_runner)

    if not PRODUCTION:
        scheduler.add_job(dump_frames_from_queue_to_video_file, trigger='interval', seconds=10)
        scheduler.add_job(daily_backup_videos_to_single_video_file, trigger='cron', minute='*', hour='*', day='*', month='*', week='*')
    else:
        scheduler.add_job(dump_frames_from_queue_to_video_file, trigger='interval', seconds=60)
        scheduler.add_job(daily_backup_videos_to_single_video_file, trigger='cron', hour='00', minute='00', second='30')

    image_pusher_thread.start()
    scheduler.start()
