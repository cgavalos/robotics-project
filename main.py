import threading
import numpy as np
from aprilmisc import *
from kin_commands import *
from dobot import *
from block import *
import random

class VideoStream:
    def __init__(self, n, fps):
        self.cap = cv2.VideoCapture(n)
        print('Camera %i opened' % n)
        self.stopped = False
        self.fps = fps
        self.started = False
        self.start()

    def start(self):
        self.thread = threading.Thread(target=self.update)
        self.thread.start()
        while not self.started:
            pass

    def update(self):
        while not self.stopped:
            grabbed, img = self.cap.read()
            if grabbed:
                self.img = img
                self.started = True
                time.sleep(1.0 / self.fps)

    def stop(self):
        self.stopped = True
        self.thread.join()
        self.cap.release()

    def image(self):
        return self.img

def center_demo():
    d = Dobot()
    print('Dobot found')
    d.zero()
    d.zero()
    d.move_zero()
    print('Dobot zeroed')

    # Block info
    block = Block()

    # Centering info
    times_per_second = 2
    fps = 30
    max_time = 5
    max_real_error = 10
    max_real_error_2 = 1
    sheight = d.pos_zero()[2]
    delta_z_closeup = block.dim[2] + 40 - sheight
    K = 0.9

    # Build site information
    q1bo = math.pi / 3
    theta_0dg = 0
    p0tdg = np.array([200, 0, 0])

    #n = 10
    #for i in range(n):
    #    cap = cv2.VideoCapture(i)
    #    if cap.isOpened():
    #        print('%i opened!' % i)
    #    cap.release()

    print('Starting stream')

    fps = 30
    vs = VideoStream(2, fps)
    vs.start()

    print('Stream started')

    img_func = vs.image

    num = 0

    while True:
        img, res = get_results(img_func())
        cv2.imshow('img', debugannotate(img, res))
        if len(res) == 0:
            print('No tags!')
            break
        if len(res) == 1:
            tag = res[0]
        else:
            tag = res[random.randrange(0, len(res) - 1)]
        if tag == None:
            print('No tags!')
            break
        else:
            id = tag.tag_id
            print('Choosing tag #' + str(id))

        # Center on april tag

        pe, re = d.tag_pos_error(img, tag, block.tagsize)
        d.camera_move([0, 0, delta_z_closeup], 0, 0)
        d.camera_move(-re, 0, 0)

        c2 = d.center_apriltag(img_func, fps, times_per_second, max_time, max_real_error_2, id, block.tagsize, K)
        if c2 == None:
            print('Tag not in frame')
            d.move_zero()
            break
        else:
            pe, re = c2
            print('Centered with error: %f mm' % norm(re))

        print('Centered on tag #%i' % id)

        # Find 'up' and 'right'
        # Calculate theta_0

        img = img_func()
        frame, block_top, theta_0 = d.locate_block(img, block, id)

        d.move_to(block_top + np.array([0, 0, 10]), 0, 0)
        print('Centered on block')

        d.move_to(block_top + np.array([0, 0, -2]), 0, 1)
        print('Picking up block')

        #d_theta = round(theta_0 / math.pi) * math.pi - theta_0
        p0td = np.matmul(Rz(q1bo), p0tdg)
        q1p = d.invkin(p0td)[0]
        dtheta = theta_0dg + q1bo - theta_0 + d.model_angles()[0] - q1p

        dtheta = (dtheta + math.pi / 2) % math.pi - math.pi / 2



        new_pos = d.pos()
        new_pos[2] = 160
        d.move_to(new_pos, 0, 1)
        print('Moving up')

        d.move_to(p0td + np.array([0, 0, block.dim[2] * (num + 1) + 3]), dtheta, 1)
        print('Moving to new spot')

        d.move_delta([0, 0, 0], dtheta, 0)
        print('Letting go')

        new_pos = d.pos()
        new_pos[2] = 150
        d.move_to(new_pos, 0, 0)
        num += 1
        print('Moving up')

        d.zero()
        print('Zeroing')

    vs.stop()
    cv2.destroyAllWindows()

def test_model_real():
    d = Dobot()
    d.zero()
    d.move_zero()
    p = d.pos()
    print('Zero pos: ' + str(p / 25.4))
    p[0] = 0
    d.move_delta(-p, 0, 0)
    print('z=0 pos:  ' + str(d.pos() / 25.4))

def jzero_vs_modelzero():
    d = Dobot()
    d.zero()
    print('Joint zero: ' + str(d.pos()))
    d.move_zero()
    print('Model zero: ' + str(d.pos()))

def debug(n):
    d = Dobot()
    d.move_zero()
    aprildebug(n)

def calib():
    d = Dobot()
    d.jmove(0, 0.1, 0.1, 0, 0)
    d.move_zero()

if __name__ == '__main__':
    #debug(6)
    center_demo()
    #wait_demo()
    #calib()
    #test_model_real()
