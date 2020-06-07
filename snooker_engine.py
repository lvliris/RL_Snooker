import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


class Table(object):
    def __init__(self, length=200, width=100):
        self.length = length
        self.width = width
        self.hole_size = 10
        self.hole = [
            (0, 0), (self.length / 2, 0), (self.length, 0),
            (0, self.width), (self.length / 2, self.width), (self.length, self.width),
        ]
        self.cushion = [
            [(self.hole_size, self.length / 2 - self.hole_size), (0, 0)],
            [(self.length / 2 + self.hole_size, self.length - self.hole_size), (0, 0)],
            [(self.hole_size, self.length / 2 - self.hole_size), (self.width, self.width)],
            [(self.length / 2 + self.hole_size, self.length - self.hole_size), (self.width, self.width)],
            [(0, 0), (self.hole_size, self.width - self.hole_size)],
            [(self.length, self.length), (self.hole_size, self.width - self.hole_size)]
        ]


class Ball(object):
    def __init__(self, x, y, r=10, color='r'):
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.vx = 0
        self.vy = 0
        self.dv = 0

    def set_velocity(self, v):
        self.vx = v[0]
        self.vy = v[1]

    def set_damp(self, dv):
        self.dv = dv

    def is_stopped(self):
        if abs(self.vx) < self.dv and abs(self.vy) < self.dv:
            self.vx = 0
            self.vy = 0
            return True
        else:
            return False

    def move(self, t):
        self.x += self.vx * t
        self.y += self.vy * t

    def slow_down(self):
        if self.is_stopped():
            return
        v = np.sqrt(self.vx**2 + self.vy**2)
        alpha = (v - self.dv) / v
        self.vx *= alpha
        self.vy *= alpha


class Game(object):
    def __init__(self, table: Table, balls: list, damp=0.01, dt=0.01):
        self.table = table
        assert len(balls) > 0
        self.balls = balls
        self.cue_ball = balls[0]
        self.damp = damp
        for ball in self.balls:
            ball.set_damp(damp)
        self.dt = dt
        self.fig = plt.figure('snooker')
        self.ax = self.fig.add_subplot(1, 1, 1)
        # self.ax.set_animated(True)
        self.ax.axis("equal")
        plt.grid(True)
        # plt.ion()

        self.aiming = False
        self.release = False

        self.aiming_x = 0
        self.aiming_y = 0
        self.mouse_x = 0
        self.mouse_y = 0

        self.cue_ball_velocity = [0, 0]

        canvas = self.fig.canvas
        # canvas.mpl_connect('draw_event', self.draw_callback)
        canvas.mpl_connect('button_press_event', self.button_press_callback)
        canvas.mpl_connect('button_release_event', self.button_release_callback)
        canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas = canvas

    def step(self):
        for ball in self.balls:
            ball.move(self.dt)
            ball.slow_down()
        self.check_collision()
        self.check_goal()
        self.plot()

    def ball_collision(self):
        for i in range(len(self.balls)):
            b1 = self.balls[i]
            for j in range(i+1, len(self.balls)):
                b2 = self.balls[j]
                l2_distance = (b1.x - b2.x)**2 + (b1.y - b2.y)**2
                if l2_distance < (b1.r + b2.r)**2 and (b1.x - b2.x)*(b1.vx - b2.vx) + (b1.y - b2.y)* (b1.vy - b2.vy) < 0:
                    self.calcu_ball_collision_velocity(b1, b2)

    def calcu_ball_collision_velocity(self, b1: Ball, b2: Ball):
        if b1.x == b2.x:
            theta = np.pi / 2
        else:
            theta = np.arctan((b1.y - b2.y)/(b1.x - b2.x))

        cos2 = np.cos(theta)**2
        sin2 = np.sin(theta)**2
        cs = np.cos(theta) * np.sin(theta)

        b1_vx = b2.vx * cos2 + b2.vy * cs + b1.vx * sin2 - b1.vy * cs
        b1_vy = b2.vx * cs + b2.vy * sin2 - b1.vx * cs + b1.vy * cos2

        b2_vx = b1.vx * cos2 + b1.vy * cs + b2.vx * sin2 - b2.vy * cs
        b2_vy = b1.vx * cs + b1.vy * sin2 - b2.vx * cs + b2.vy * cos2

        b1.vx, b1.vy = b1_vx, b1_vy
        b2.vx, b2.vy = b2_vx, b2_vy

    def test_ball_collision(self):
        for theta in np.arange(0, np.pi/2, 0.1):
            b1 = Ball(20, 20)
            b2 = Ball(20+20*np.cos(theta), 20+20*np.sin(theta))
            b2.set_velocity(-10, 0)
            self.calcu_ball_collision_velocity(b1, b2)
            if abs(b1.vx + b2.vx + 10) > 0.01 or abs(b1.vy + b2.vy) > 0.01:
                print('\033[31mcalculate error\033[0m:',abs(b1.vx + b2.vx + 10), abs(b1.vy + b2.vy))
            print('angle', theta)
            print('v1,v2', b1.vx, b1.vy, b2.vx, b2.vy)

    def table_collision(self):
        for i in range(len(self.balls)):
            ball = self.balls[i]
            table = self.table
            for x_range, y_range in table.cushion:
                if x_range[0] == x_range[1] and abs(ball.x - x_range[0]) < ball.r and (y_range[0] < ball.y < y_range[1])\
                        and ball.vx * (ball.x - x_range[0]) < 0:
                    ball.vx = -ball.vx
                    break
                if y_range[0] == y_range[1] and abs(ball.y - y_range[0]) < ball.r and (x_range[0] < ball.x < x_range[1])\
                        and ball.vy * (ball.y - y_range[0]) < 0:
                    ball.vy = -ball.vy
                    break

    def check_goal(self):
        for ball in self.balls:
            if not 0 < ball.x < self.table.length or not 0 < ball.y < self.table.width:
                self.balls.remove(ball)

    def check_collision(self):
        self.table_collision()
        self.ball_collision()

    def button_press_callback(self, event):
        self.aiming = True

    def button_release_callback(self, event):
        self.aiming = False
        self.release = True
        strength = np.sqrt((self.mouse_x - self.aiming_x)**2 + (self.mouse_y - self.aiming_y)**2)
        norm = np.sqrt((self.cue_ball.x - self.aiming_x)**2 + (self.cue_ball.y - self.aiming_y)**2)
        alpha = 4 * strength / norm
        self.cue_ball_velocity = [(self.aiming_x - self.cue_ball.x) * alpha, (self.aiming_y - self.cue_ball.y) * alpha]

    def motion_notify_callback(self, event):
        if event.xdata is None or event.ydata is None:
            return
        self.mouse_x = np.clip(event.xdata, 0, self.table.length)
        self.mouse_y = np.clip(event.ydata, 0, self.table.width)
        if not self.aiming:
            self.aiming_x = np.clip(event.xdata, 0, self.table.length)
            self.aiming_y = np.clip(event.ydata, 0, self.table.width)

    def plot(self):
        rect = plt.Rectangle((0, 0), self.table.length, self.table.width, color='green')
        self.ax.add_patch(rect)
        for cushion in self.table.cushion:
            self.ax.plot(cushion[0], cushion[1], c='black')
        for ball in self.balls:
            circle = Circle(xy=(ball.x, ball.y), radius=ball.r, alpha=0.5, color=ball.color)
            self.ax.add_patch(circle)
        self.ax.plot([self.cue_ball.x, self.aiming_x], [self.cue_ball.y, self.aiming_y], color='gray', linestyle=':')

        if self.release:
            self.cue_ball.set_velocity(self.cue_ball_velocity)
            self.release = False

        plt.pause(0.001)
        plt.cla()
        # plt.show()


if __name__ == '__main__':
    table = Table(200, 100)
    b1 = Ball(50, 50, r=5, color='white')
    b2 = Ball(90, 50, r=5, color='red')
    b3 = Ball(100, 45, r=5, color='red')
    b4 = Ball(100, 55, r=5, color='red')
    b5 = Ball(110, 40, r=5, color='red')
    b6 = Ball(110, 50, r=5, color='red')
    b7 = Ball(110, 60, r=5, color='red')
    b1.set_velocity([0, 0])
    game = Game(table=table, balls=[b1, b2, b3, b4, b5, b6, b7], damp=3, dt=0.01)
    # game.test_ball_collision()

    while True:
        game.step()
