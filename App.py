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

        # Release resources properly
        if cap is not None:
            cap.release()
        if out is not None:
            out.release()
        
        if frames_processed == 0:
            raise ValueError("No frames were processed successfully")

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
        # Clean up resources without using destroyAllWindows
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
