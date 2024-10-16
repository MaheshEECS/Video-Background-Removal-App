import cv2
import numpy as np
import streamlit as st
import tempfile
import mediapipe as mp
import time
import os
import subprocess
from PIL import Image

# Initialize the MediaPipe Selfie Segmentation model
mp_selfie_segmentation = mp.solutions.selfie_segmentation

# Function to check if video writer is valid
def check_video_writer(writer):
    return writer is not None and writer.isOpened()

# Function to extract audio from video
def extract_audio(video_path, output_audio_path):
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {output_audio_path} -y"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Function to combine audio with processed video
def combine_audio_video(video_path, audio_path, output_path):
    command = f"ffmpeg -i {video_path} -i {audio_path} -c copy -map 0:v:0 -map 1:a:0 {output_path} -y"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def remove_background(video_path, output_path, bg_type, bg_color=(0, 255, 0), bg_image=None, transparent=False):
    cap = None
    out = None
    temp_video_no_audio = None
    temp_audio = None
    try:
        # Initialize video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open input video")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Create temporary file for processed video without audio
        temp_video_no_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
        
        # Choose codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_video_no_audio, fourcc, fps, (width, height))
        if not check_video_writer(out):
            raise ValueError("Could not initialize video writer")

        # Prepare background image if provided
        if bg_type == "Image" and bg_image is not None:
            bg_image = cv2.resize(bg_image, (width, height))

        # Process video frames
        with mp_selfie_segmentation.SelfieSegmentation(model_selection=1) as selfie_segmentation:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = selfie_segmentation.process(rgb_frame)
                mask = results.segmentation_mask > 0.5

                if transparent:
                    output_frame = np.zeros_like(frame)
                    output_frame[mask] = frame[mask]
                elif bg_type == "Image":
                    output_frame = np.where(mask[..., None], frame, bg_image)
                else:
                    background = np.full_like(frame, bg_color, dtype=np.uint8)
                    output_frame = np.where(mask[..., None], frame, background)

                out.write(output_frame)

        # Release resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()

        # Extract audio from the original video
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.aac').name
        extract_audio(video_path, temp_audio)

        # Combine processed video with original audio
        combine_audio_video(temp_video_no_audio, temp_audio, output_path)

        # Small delay to ensure all processes are finished
        time.sleep(1)

        return True

    except Exception as e:
        st.error(f"Error during video processing: {str(e)}")
        return False
    finally:
        # Cleanup resources
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        
        # Cleanup temporary files
        for temp_file in [temp_video_no_audio, temp_audio]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    st.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")

# Streamlit App Interface
st.title("Fast Video Background Removal App")
st.write("Upload a video and remove its background while keeping the audio!")

# Video upload
uploaded_video = st.file_uploader("Upload your video", type=["mp4", "mov", "avi", "mkv"])

if uploaded_video:
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_input:
            temp_input.write(uploaded_video.read())
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_output.close()

        # Background options
        st.write("Select background type:")
        bg_type = st.radio("Background Type", ["Solid Color", "Image", "Transparent"])
        
        bg_color_bgr = (0, 255, 0)  # Default green
        bg_image = None

        if bg_type == "Solid Color":
            st.write("Select background color:")
            bg_color = st.color_picker("Background Color", "#00FF00")
            bg_color_bgr = tuple(int(bg_color.lstrip("#")[i:i+2], 16) for i in (4, 2, 0))
        elif bg_type == "Image":
            st.write("Upload background image:")
            uploaded_bg = st.file_uploader("Choose a background image", type=["jpg", "jpeg", "png"])
            if uploaded_bg:
                bg_image = cv2.imdecode(np.frombuffer(uploaded_bg.read(), np.uint8), 1)

        # Start processing the video and remove the background
        if st.button("Process Video"):
            if bg_type == "Image" and bg_image is None:
                st.error("Please upload a background image.")
            else:
                with st.spinner("Processing video..."):
                    start_time = time.time()
                    
                    success = remove_background(temp_input.name, temp_output.name, 
                                                bg_type=bg_type,
                                                bg_color=bg_color_bgr, 
                                                bg_image=bg_image,
                                                transparent=(bg_type == "Transparent"))
                    
                    if success:
                        processing_time = time.time() - start_time
                        st.success(f"Video processed successfully in {processing_time:.2f} seconds!")

                        # Offer the user to download the processed video
                        with open(temp_output.name, 'rb') as video_file:
                            video_bytes = video_file.read()
                            st.download_button(
                                label="Download Processed Video",
                                data=video_bytes,
                                file_name="processed_video.mp4",
                                mime="video/mp4"
                            )
                    else:
                        st.error("Failed to process video.")
    finally:
        # Cleanup temporary files
        for temp_file in [temp_input.name, temp_output.name]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    st.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")
