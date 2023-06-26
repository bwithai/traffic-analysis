# Add text to the image
import cv2


def put_entry_text(frame, start_line, end_line, entry):
    text = ('In: ' + entry)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    text_color = (255, 0, 0)  # BGR color tuple (blue in this case)
    text_thickness = 2
    text_position = (start_line[0], end_line[1] - 10)  # Position the text above the line

    frame = cv2.putText(frame, text, text_position, font, font_scale, text_color, text_thickness,
                                  cv2.LINE_AA)
    return frame


def put_out_text(frame, start_line, end_line, out):
    text = ('Out: ' + out)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    text_color = (255, 0, 0)  # BGR color tuple (blue in this case)
    text_thickness = 2
    text_position = (start_line[0], end_line[1] - 10)  # Position the text above the line

    frame = cv2.putText(frame, text, text_position, font, font_scale, text_color, text_thickness,
                                  cv2.LINE_AA)
    return frame