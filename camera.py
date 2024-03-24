import pygame


class Camera:
    def __init__(self, follow_target, width, height, zoom=1.0, inner_rect_factor=0.5):
        self.follow_target = follow_target
        self.width, self.height = width, height
        self.zoom = zoom
        # Initialize the camera's offset to center on the follow_target
        self.offset_x = -self.follow_target.x * self.zoom + self.width // 2
        self.offset_y = -self.follow_target.y * self.zoom + self.height // 2
        # Define the inner rectangle
        self.inner_rect_width = self.width * inner_rect_factor
        self.inner_rect_height = self.height * inner_rect_factor

        self.sliding = False
        self.slide_time = 0.5
        self.slide_start_time = 0
        self.target_offset_x = self.offset_x
        self.target_offset_y = self.offset_y

    def start_slide(self, dx, dy):
        self.sliding = True
        self.slide_start_time = pygame.time.get_ticks() / 1000
        self.original_offset_x = self.offset_x
        self.original_offset_y = self.offset_y
        self.target_offset_x = self.offset_x + dx
        self.target_offset_y = self.offset_y + dy

    def update(self):
        current_time = pygame.time.get_ticks() / 1000
        if self.sliding:
            # Calculate the fraction of the slide that is completed
            slide_fraction = min(
                1, (current_time - self.slide_start_time) / self.slide_time)

            # Smoothly move the camera towards the target offset
            self.offset_x = self.original_offset_x + \
                (self.target_offset_x - self.original_offset_x) * slide_fraction
            self.offset_y = self.original_offset_y + \
                (self.target_offset_y - self.original_offset_y) * slide_fraction

            # Check if the slide is completed
            if slide_fraction >= 1.0:
                self.sliding = False
            return

        if self.follow_target:
            # Calculate the screen position where the player should appear
            target_x_on_screen = -self.follow_target.x * self.zoom + self.width // 2
            target_y_on_screen = -self.follow_target.y * self.zoom + self.height // 2

            # Calculate the inner rectangle's bounds
            inner_left = self.offset_x - self.inner_rect_width // 2
            inner_right = inner_left + self.inner_rect_width
            inner_top = self.offset_y - self.inner_rect_height // 2
            inner_bottom = inner_top + self.inner_rect_height

            if False:
                # Camera follows player
                if target_x_on_screen < inner_left:
                    self.offset_x -= self.inner_left - target_x_on_screen
                elif target_x_on_screen > inner_right:
                    self.offset_x += self.target_x_on_screen - inner_right

                if target_y_on_screen < inner_top:
                    self.offset_y -= self.inner_top - target_y_on_screen
                elif target_y_on_screen > inner_bottom:
                    self.offset_y += self.target_y_on_screen - inner_bottom
            else:
                # Check if the camera needs to start sliding
                if target_x_on_screen < inner_left:
                    self.start_slide(-self.inner_rect_width, 0)
                elif target_x_on_screen > inner_right:
                    self.start_slide(self.inner_rect_width, 0)
                if target_y_on_screen < inner_top:
                    self.start_slide(0, -self.inner_rect_height)
                elif target_y_on_screen > inner_bottom:
                    self.start_slide(0, self.inner_rect_height)
