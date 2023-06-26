from typing import Sequence, Tuple

import cv2

from norfair.drawing.text_on_line import put_entry_text, put_out_text


# Counter: count the vehicle who pass the line
class Incremental:
    def __init__(self):
        self.L_in = {0}  # left line entry
        self.L_out = {0}  # left line out
        self.R_in = {0}  # right line entry
        self.R_out = {0}  # right line out

    # Update the new entry
    def update_left_in(self, id):
        self.L_in.add(id)

    def update_left_out(self, id):
        self.L_out.add(id)

    def update_right_in(self, id):
        self.R_in.add(id)

    def update_right_out(self, id):
        self.R_out.add(id)


# OOP concept for counting well working on runtime counting
incremental_obj = Incremental()


def get_center_of_the_object(id, frame, points: Sequence[Tuple[int, int]]):
    #   Define the start/end zone for the Left line
    # Start
    Lstart_l1 = (0, 650)  # (x, y) coordinates of the start point
    Lend_l1 = (1130, 650)  # (x, y) coordinates of the end point

    # End
    Lstart_l2 = (0, 170)  # (x, y) coordinates of the start point
    Lend_l2 = (630, 170)  # (x, y) coordinates of the end point

    # ---------------------------------------------------------------

    """
        Define the start/end zone for the Right line
    """
    # Start
    Rstart_l1 = (800, 260)  # (x, y) coordinates of the start point
    Rend_l1 = (1260, 260)  # (x, y) coordinates of the end point

    # End
    Rstart_l2 = (1000, 500)  # (x, y) coordinates of the start point
    Rend_l2 = (19000, 500)  # (x, y) coordinates of the end point

    # -----------------------------------------------------------------

    # Set the line color and thickness
    color = (0, 0, 255)  # BGR color tuple (red in this case)
    thickness = 4

    # -----------------------------------------------------------------

    """
        Draw the Left side line on the frame with counting analysis
    """

    # Draw the entry line at left
    frame = cv2.line(frame, Lstart_l1, Lend_l1, color, thickness)

    # -1 is for remove the initialization entry on set data-structure
    total_entry_at_left_line = (len(incremental_obj.L_in) - 1)
    # Draw text on frame with proper counting
    frame = put_entry_text(frame, Lstart_l1, Lend_l1, str(total_entry_at_left_line))

    # Draw the out zone line at left
    frame = cv2.line(frame, Lstart_l2, Lend_l2, color, thickness)
    total_out_at_left_line = (len(incremental_obj.L_out) - 1)
    frame = put_out_text(frame, Lstart_l2, Lend_l2, str(total_out_at_left_line))

    """
        Draw the Right side line on the frame with counting analysis
    """

    # Draw the entry line at right
    frame = cv2.line(frame, Rstart_l1, Rend_l1, color, thickness)
    total_entry_at_right_line = (len(incremental_obj.R_in) - 1)
    frame = put_entry_text(frame, Rstart_l1, Rend_l1, str(total_entry_at_right_line))

    # Draw the out zone line at right
    total_out_at_right_line = (len(incremental_obj.R_out) - 1)
    frame = cv2.line(frame, Rstart_l2, Rend_l2, color, thickness)
    frame = put_out_text(frame, Rstart_l2, Rend_l2, str(total_out_at_right_line))

    # Calculate the center the (x,y) coordinate of the detected object
    center_x = int((points[0][0] + points[1][0]) / 2)
    center_y = int((points[0][1] + points[1][1]) / 2)

    # print("The X: ", center_x, "The Y: ", center_y)

    """
        Left side Zone to count the object to pass the line
    """
    # Check if object enter the zone
    if 0 <= center_x <= 1130:
        if 649 <= center_y <= 651:
            # the blinking concept
            color = (0, 255, 0)  # BGR color tuple (red in this case)
            frame = cv2.line(frame, Lstart_l1, Lend_l1, color, thickness + 20)
            # Update the increment approach
            incremental_obj.update_left_in(id)
            total_entry_at_left_line = (len(incremental_obj.L_in) - 1)
            frame = put_entry_text(frame, Lstart_l1, Lend_l1, str(total_entry_at_left_line))

    # Check if object exit the zone
    if 0 <= center_x <= 630:
        if 169 <= center_y <= 171:
            color = (0, 255, 0)  # BGR color tuple (red in this case)
            frame = cv2.line(frame, Lstart_l2, Lend_l2, color, thickness + 20)
            incremental_obj.update_left_out(id)
            total_out_at_left_line = (len(incremental_obj.L_out) - 1)
            frame = put_out_text(frame, Lstart_l2, Lend_l2, str(total_out_at_left_line))

    """
        Right side Zone to count the object to pass the line
    """
    if 800 <= center_x <= 1260:
        if 259 <= center_y <= 261:
            color = (0, 255, 0)  # BGR color tuple (red in this case)
            frame = cv2.line(frame, Rstart_l1, Rend_l1, color, thickness + 20)
            incremental_obj.update_right_in(id)
            total_entry_at_right_line = (len(incremental_obj.R_in) - 1)
            frame = put_entry_text(frame, Rstart_l1, Rend_l1, str(total_entry_at_right_line))

    if 1000 <= center_x <= 19000:
        if 499 <= center_y <= 501:
            color = (0, 255, 0)  # BGR color tuple (red in this case)
            frame = cv2.line(frame, Rstart_l2, Rend_l2, color, thickness + 20)
            incremental_obj.update_right_out(id)
            total_out_at_right_line = (len(incremental_obj.R_out) - 1)
            frame = put_out_text(frame, Rstart_l2, Rend_l2, str(total_out_at_right_line))

    # frame = cv2.resize(frame, (800, 600))
    return frame
