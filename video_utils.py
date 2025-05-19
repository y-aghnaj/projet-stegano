import cv2
import os

def video_to_frames(video_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_paths = []
    count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_path = os.path.join(output_folder, f"frame_{count:05d}.png")
        cv2.imwrite(frame_path, frame)
        frame_paths.append(frame_path)
        count += 1
    cap.release()
    return frame_paths

def frames_to_video(frame_folder, output_video_path, fps=30):
    frames = sorted(
        [os.path.join(frame_folder, f) for f in os.listdir(frame_folder) if f.endswith(".png")]
    )
    if not frames:
        raise ValueError("No frames found to build video.")

    frame = cv2.imread(frames[0])
    height, width, layers = frame.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # or 'XVID'
    video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    for frame_path in frames:
        img = cv2.imread(frame_path)
        video.write(img)

    video.release()
