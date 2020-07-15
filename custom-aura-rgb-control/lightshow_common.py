from enum import Enum

class AnimationDirection(Enum):
    FORWARD = 1
    REVERSE = 2

class LedAnimationState:
    frame = None
    direction = None

    def __init__(self, frame, direction):
        self.frame = frame
        self.direction = direction