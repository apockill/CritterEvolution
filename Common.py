from time import time, sleep

class FpsTimer:
    def __init__(self, fps):
        self.stepDelay = (1 / float(fps))
        self.lastTime = time()
        self.delay = 0

    def wait(self):
        waitTime = self.stepDelay - (time() - self.lastTime)
        if waitTime > .005: sleep(waitTime)

    def ready(self):
        isReady = time() - self.lastTime >= self.stepDelay
        if isReady: self.lastTime = time()

        return isReady