from lightshow_common import AnimationDirection, LedAnimationState

class LightShowEffect:
    def set_initial_state_for_led(self, dram_stick, led_on_stick, colors):
        pass

class UpwardScroll(LightShowEffect):
    def set_initial_state_for_led(self, dram_stick, led_on_stick, colors):
        return LedAnimationState(led_on_stick % len(colors), AnimationDirection.FORWARD)

class ColorTrail(LightShowEffect):
    def set_initial_state_for_led(self, dram_stick, led_on_stick, colors):
        return LedAnimationState(((dram_stick * 8) + led_on_stick) % len(colors), AnimationDirection.FORWARD)

class Shimmer(LightShowEffect):
    def set_initial_state_for_led(self, dram_stick, led_on_stick, colors):
        return LedAnimationState((dram_stick + (led_on_stick * 8)) % len(colors), AnimationDirection.FORWARD)
