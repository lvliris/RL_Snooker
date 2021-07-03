import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from SnookerEngine import Ball, Table, SnookerEngine


class Game(object):
    def __init__(self, engine, table: Table, balls: list):
        self.engine = engine
        self.table = table
        assert len(balls) > 0
        self.balls = balls
        self.cue_ball = balls[0]
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
        self.engine.step()
        self.plot()

    def check_goal(self):
        for ball in self.balls:
            if not 0 < ball.x < self.table.length or not 0 < ball.y < self.table.width:
                self.balls.remove(ball)

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
    table = Table(200, 100, 10)
    b1 = Ball(50, 50, 5, 'white')
    b2 = Ball(90, 50, 5, 'red')
    b3 = Ball(100, 45, 5, 'red')
    b4 = Ball(100, 55, 5, 'red')
    b5 = Ball(110, 40, 5, 'red')
    b6 = Ball(110, 50, 5, 'red')
    b7 = Ball(110, 60, 5, 'red')
    b1.set_velocity([0, 0])
    engine = SnookerEngine(table, [b1, b2, b3, b4, b5, b6, b7])
    game = Game(engine, table, [b1, b2, b3, b4, b5, b6, b7])
    # game.test_ball_collision()

    while True:
        game.step()
