import cv2
import time

# Define the mouse callback function
def select_line_x(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Scale back the x-coordinate to the original frame size
        scale_factor = param['scale_factor']
        original_x = int(x / scale_factor)
        print(f"Selected x-coordinate (scaled to original): {original_x}")
        cv2.destroyAllWindows()

# Main function to process video or image
def main(video_or_image_path, display_width=1280):
    # Check if the input is a video
    if video_or_image_path.endswith(('.mp4', '.avi', '.mov', '.dav')):
        cap = cv2.VideoCapture(video_or_image_path)
        if not cap.isOpened():
            print("Error: Cannot open video.")
            return
        ret, frame = cap.read()
        if not ret:
            print("Error: Cannot read frame.")
            return
        cap.release()
    # Otherwise, assume it's an image
    else:
        frame = cv2.imread(video_or_image_path)
        if frame is None:
            print("Error: Cannot open image.")
            return

    # Calculate the scaling factor to resize the frame for display
    original_height, original_width = frame.shape[:2]
    scale_factor = display_width / original_width
    display_height = int(original_height * scale_factor)

    # Resize the frame for display while maintaining aspect ratio
    display_frame = cv2.resize(frame, (display_width, display_height))

    # Use an ASCII window name
    window_name = 'Select Counting Line'
    cv2.imshow(window_name, display_frame)
    time.sleep(1)  # Small delay to ensure the window is created

    # Pass the scale factor to the callback function
    cv2.setMouseCallback(window_name, select_line_x, {'scale_factor': scale_factor})
    cv2.waitKey(0)  # Wait for a key press
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Replace with the actual path to your video or image
    # video_or_image_path = './cam1_2.mp4'  # or 'path/to/your/image.jpg'
    video_or_image_path = '/home/sadraafzar/Desktop/Share-Tavakol/cam1.dav'
    main(video_or_image_path)