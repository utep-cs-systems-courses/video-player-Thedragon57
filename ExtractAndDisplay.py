#!/usr/bin/env python3

import threading
import cv2
import numpy as np
import base64
import queue

"""
q.put(item):
     empty.acquire()
     qlock.acquire()
     simpleq.put(item)
     qlock.release()
     full.release()
q.get()
    full.acquire()
    qlock.acquire()
    i=simpleQ.get()
   qlock.release()
    empty.release()
"""
buffer = 75
# shared Lock  
extractionLock = threading.Lock()
displayLock = threading.Lock()

# shared Semaphore  
extractionEmptySemaphore = threading.Semaphore(buffer)
extractionFullSemaphore = threading.Semaphore(0)

displayEmptySemaphore = threading.Semaphore(buffer)
displayFullSemaphore = threading.Semaphore(0)

extractionQueue = queue.Queue(maxsize=buffer)
displayQueue = queue.Queue(maxsize=buffer)


def extractFrames(fileName, maxFramesToLoad=9999):
    # Initialize frame count 
    count = 0

    # open video file
    vidcap = cv2.VideoCapture(fileName)

    # read first image
    success,image = vidcap.read()
            
    if not success:
        print("Failed to open video or read first frame.")
        return
    print(f'Reading frame {count} {success}')
    while success and count < maxFramesToLoad:
        # get a jpg encoded frame
        success, jpgImage = cv2.imencode('.jpg', image)

        #encode the frame as base 64 to make debugging easier
        jpgAsText = base64.b64encode(jpgImage)
        # add the frame to the buffer

        extractionEmptySemaphore.acquire()
        extractionLock.acquire()
        extractionQueue.put(image)
        extractionLock.release()
        extractionFullSemaphore.release()
        
       
        success,image = vidcap.read()
        print(f'Reading frame {count} {success}')
        count += 1

    extractionEmptySemaphore.acquire()
    extractionLock.acquire()
    extractionQueue.put(None)
    extractionLock.release()
    extractionFullSemaphore.release()

    print('Frame extraction complete')

def changeToGray():
    
    count = 0

    

    while True:
        print(f'Converting frame {count}')

        extractionFullSemaphore.acquire()
        extractionLock.acquire()
        grayscaleFrame = extractionQueue.get()
        extractionLock.release()
        extractionEmptySemaphore.release()

        if (grayscaleFrame is None):
            displayEmptySemaphore.acquire()
            displayLock.acquire()
            displayQueue.put(None)
            displayLock.release()
            displayFullSemaphore.release()
            break

        # convert the image to grayscale
        outputFrame = cv2.cvtColor(grayscaleFrame, cv2.COLOR_BGR2GRAY)

        displayEmptySemaphore.acquire()
        displayLock.acquire()
        displayQueue.put(outputFrame)
        displayLock.release()
        displayFullSemaphore.release()
        count += 1

def displayFrames():
    # initialize frame count
    count = 0

    # go through each frame in the buffer until the buffer is empty
    while True:

        displayFullSemaphore.acquire()
        displayLock.acquire()
        frame = displayQueue.get()
        displayLock.release()
        displayEmptySemaphore.release()

        
        if(frame is None):
            print("thats all!")
            break
        
        # get the next frame
        print(f'Displaying frame {count}')        

        # display the image in a window called "video" and wait 42ms
        # before displaying the next frame
        #print(frame)

        cv2.imshow('Video', frame)
        if cv2.waitKey(42) and 0xFF == ord("q"):
            break

        count += 1

    print('Finished displaying all frames')
    # cleanup the windows
    cv2.destroyAllWindows()





# filename of clip to load
filename = 'clip.mp4'

# shared queues  


producer = threading.Thread(target=extractFrames, args=(filename, 1000))
transformer = threading.Thread(target=changeToGray)
#displayer = threading.Thread(target=displayFrames)

# Start both threads
producer.start()
transformer.start()
#displayer.start()

#Displaying frames in the main
displayFrames()

# Wait for both to finish
producer.join()
transformer.join()
#displayer.join()

