import cv2
import imutils


def get_contours(current_frame, prev_frame) -> tuple:
    diff = cv2.absdiff(current_frame, prev_frame)
    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return imutils.grab_contours(cnts)

def mosaic_roi(frame, x, y, w, h):
    roi = frame[y:y+h, x:x+w]
    # Resize to tiny then back up = pixelation
    small = cv2.resize(roi, (8, 8), interpolation=cv2.INTER_LINEAR)
    mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
    frame[y:y+h, x:x+w] = mosaic
    return frame

def process_video(input_path, output_path):
    prev_frame = None
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print("Error opening video file")
        return

    # Get frame properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is None:
            prev_frame = gray_frame
            continue
        
        contours = get_contours(gray_frame, prev_frame)
        prev_frame = gray_frame

        for contour in contours:
            peri = cv2.arcLength(contour,True)
            apprx = cv2.approxPolyDP(contour, 0.1*peri, True)
            x,y,w,h = cv2.boundingRect(apprx)
            frame = mosaic_roi(frame, x, y, w, h)

        out.write(frame)

        cv2.imshow('Censored Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    INPUT_VIDEO = 'data/example.mp4'
    OUTPUT_VIDEO = INPUT_VIDEO.replace('.', '_censored.')

    process_video(INPUT_VIDEO, OUTPUT_VIDEO)
