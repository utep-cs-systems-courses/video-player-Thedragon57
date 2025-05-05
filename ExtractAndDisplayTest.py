#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import queue
import base64

buffer = 50

# Locks (not strictly necessary with queue.Queue, but included for learning)
extractionLock = threading.Lock()

# Semaphores for producer-consumer coordination
extractionEmptySemaphore = threading.Semaphore(buffer)
extractionFullSemaphore = threading.Semaphore(0)

# Shared queue
extractionQueue = queue.Queue(maxsize=buffer)

# Extract video frames and put into queue
def extractFrames(fileName, maxFramesToLoad=9999):
    count = 0
    vidcap = cv2.VideoCapture(fileName)
    success, image = vidcap.read()

    if not success:
        print("Failed to open video or read first frame.")
        return

    while success and count < maxFramesToLoad:
        if image is None or not isinstance(image, np.ndarray) or image.size == 0:
            print(f"[Extract] Skipping invalid frame {count}")
            success, image = vidcap.read()
            continue

        extractionEmptySemaphore.acquire()
        extractionLock.acquire()
        extractionQueue.put(image)
        extractionLock.release()
        extractionFullSemaphore.release()

        print(f"[Extract] Read frame {count}")
        success, image = vidcap.read()
        count += 1

    # Put sentinel to signal end
    extractionEmptySemaphore.acquire()
    extractionLock.acquire()
    extractionQueue.put(None)
    extractionLock.release()
    extractionFullSemaphore.release()
    print("[Extract] Done.")

# Display video frames from queue
def displayFrames():
    count = 0
    while True:
        extractionFullSemaphore.acquire()
        extractionLock.acquire()
        frame = extractionQueue.get()
        extractionLock.release()
        extractionEmptySemaphore.release()

        if frame is None:
            print("[Display] Reached sentinel. Exiting.")
            break

        if not isinstance(frame, np.ndarray) or frame.size == 0:
            print(f"[Display] Skipping invalid frame {count}")
            continue


        cv2.imshow("Video", frame)
        if cv2.waitKey(42) & 0xFF == ord("q"):
            print("User interrupted.")
            break
        print(f"Displayed frame {count}")
        count += 1

    cv2.destroyAllWindows()
    print("Done.")

# === MAIN PROGRAM ===

filename = "clip.mp4"

if __name__ == "__main__":
    # Start extractor in a thread
    producer = threading.Thread(target=extractFrames, args=(filename, 1000))
    producer.start()

    # Display runs in main thread
    displayFrames()

    # Wait for extractor to finish
    producer.join()