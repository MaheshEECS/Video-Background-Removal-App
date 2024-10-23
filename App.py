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

def get_video_format(filename):
    """Extract the video format from filename."""
    return os.path.splitext(filename)[1].lower()

def get_video_codec(format_ext):
    """Get the appropriate codec based on video format."""
    codec_map = {
        '.mp4': 'mp4v',
        '.avi': 'XVID',
        '.mov': 'mp4v',
        '.mkv': 'mp4v',
        '.wmv': 'WMV1'
    }
    return codec_map.get(format_ext, 'mp4v')

def extract_audio(video_path, output_audio_path):
    """Extract audio maintaining original format."""
    command = f"ffmpeg -i {video_path} -q:a 0 -map a {output_audio_path} -y"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def combine_audio_video(video_path, audio_path, output_path):
    """Combine audio and video maintaining original format."""
    command = f"ffmpeg -i {video_path} -i {audio_path} -c copy -map 0:v:0 -map 1:a:0 {output_path} -y"
    subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def remove_background(video_path, output_path, bg_type, bg_color=(0, 255, 0), bg_image=None, transparent=False):
    cap = None
    out = None
    temp_video_no_audio = None
    temp_audio = None
    
    try:
        # Get input video format
        input_format = get_video_format(video_path)
        
        # Initialize video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open input video")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        # Create temporary file with same format as input
        temp_video_no_audio = tempfile.NamedTemporaryFile(delete=False, suffix=input_format).name
        
        # Get appropriate codec for the format
        codec = get_video_codec(input_format)
        fourcc = cv2.VideoWriter_fourcc(*codec)
        
        # Initialize video writer with the same format
        out = cv2.VideoWriter(temp_video_no_audio, fourcc, fps, (width, height))
        if not out.isOpened():
            raise ValueError(f"Could not initialize video writer with codec {codec}")

        # Prepare background image if provided
        if bg_type == "Image" and bg_image is not None:
            bg_image = cv2.resize(bg_image, (width, height))

        # Process video frames
        frames_processed = 0
        with mp_selfie_segmentation.SelfieSegmentation(model_selection=1) as selfie_segmentation:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = selfie_segmentation.process(rgb_frame)
                
                if results.segmentation_mask is None:
                    continue
                    
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
                frames_processed += 1

                # Update progress
                if frames_processed % 30 == 0:
                    progress_text = f"Processing frame {frames_processed}"
                    st.sidebar.text(progress_text)

        # Release resources
        cap.release()
        out.release()
        
        if frames_processed == 0:
            raise ValueError("No frames were processed successfully")

        # Extract and combine audio with same format
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.aac').name
        extract_audio(video_path, temp_audio)
        combine_audio_video(temp_video_no_audio, temp_audio, output_path)

        return True

    except Exception as e:
        st.error(f"Error during video processing: {str(e)}")
        return False
        
    finally:
        # Clean up resources
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()
        
        # Cleanup temporary files
        for temp_file in [temp_video_no_audio, temp_audio]:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    st.warning(f"Failed to remove temporary file {temp_file}: {str(e)}")

def main():
    st.set_page_config(
        page_title="Video Background Removal App",
        page_icon="🎥",
        layout="wide"
    )

    st.title("🎥 Video Background Removal App")
    st.write("Upload a video and remove its background while keeping the audio and original format!")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_video = st.file_uploader("Upload your video", type=["mp4", "mov", "avi", "mkv", "wmv"])
        if uploaded_video:
            video_format = get_video_format(uploaded_video.name)
            st.write(f"Detected format: {video_format}")
            st.video(uploaded_video)

    with col2:
        if uploaded_video:
            try:
                # Create temporary input file with original format
                input_format = get_video_format(uploaded_video.name)
                with tempfile.NamedTemporaryFile(delete=False, suffix=input_format) as temp_input:
                    temp_input.write(uploaded_video.read())
                    
                # Create temporary output file with same format
                temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=input_format)
                temp_output.close()

                # Background options
                st.write("Select background type:")
                bg_type = st.radio("Background Type", ["Solid Color", "Image", "Transparent"])
                
                bg_color_bgr = (0, 255, 0)
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

                if st.button("Process Video", type="primary"):
                    if bg_type == "Image" and bg_image is None:
                        st.error("Please upload a background image.")
                    else:
                        with st.spinner("Processing video..."):
                            start_time = time.time()
                            
                            success = remove_background(
                                temp_input.name,
                                temp_output.name, 
                                bg_type=bg_type,
                                bg_color=bg_color_bgr, 
                                bg_image=bg_image,
                                transparent=(bg_type == "Transparent")
                            )
                            
                            if success:
                                processing_time = time.time() - start_time
                                st.success(f"Video processed successfully in {processing_time:.2f} seconds!")

                                st.write("Processed Video Preview:")
                                st.video(temp_output.name)

                                # Offer download with original format
                                with open(temp_output.name, 'rb') as video_file:
                                    video_bytes = video_file.read()
                                    output_filename = f"processed_video{input_format}"
                                    st.download_button(
                                        label="Download Processed Video",
                                        data=video_bytes,
                                        file_name=output_filename,
                                        mime=f"video/{input_format[1:]}"
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

    st.markdown("---")
    st.markdown("""
        <div style='text-align: center'>
            <p>Made with ❤️ using Streamlit, OpenCV, and MediaPipe</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
