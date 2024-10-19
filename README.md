# Video Background Removal App

This is a Streamlit-based web application that allows users to upload a video, remove its background, and keep the audio. The app provides three background options:
- **Solid Color**: Replace the background with a solid color.
- **Image**: Replace the background with an uploaded image.
- **Transparent**: Remove the background and set it as transparent.

The processed video is outputted with the original audio intact.

## Features

- **Background Removal**: Removes the background from videos while retaining the subject using MediaPipe's Selfie Segmentation.
- **Custom Background**: Users can choose between a solid color, an image, or transparency for the background.
- **Audio Preservation**: The app retains the original audio in the processed video.
- **Simple UI**: Built using Streamlit for easy and intuitive user interaction.
- **Video Processing**: Efficient processing of videos with progress indication.

## Installation

### Prerequisites
- Python 3.x
- FFmpeg (for audio extraction and combining)
- Git (optional, for cloning the repository)

### Step-by-Step Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2. Install required Python libraries:
    ```bash
    pip install -r requirements.txt
    ```

3. Install FFmpeg:
    - **Ubuntu**:  
      ```bash
      sudo apt update
      sudo apt install ffmpeg
      ```
    - **Windows**:
      - Download from [here](https://ffmpeg.org/download.html) and follow the instructions.
    - **macOS** (via Homebrew):
      First, install Homebrew (if not already installed):
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      Once Homebrew is installed, update it:
      brew update



4. Run the application:
    ```bash
    streamlit run app.py
    ```

## Usage

1. Open the app in your browser at the displayed local URL (usually `http://localhost:8501`).
2. Upload a video in one of the supported formats (`mp4`, `mov`, `avi`, `mkv`).
3. Select a background option:
    - **Solid Color**: Choose a color from the color picker.
    - **Image**: Upload a background image in `jpg`, `jpeg`, or `png` format.
    - **Transparent**: Set the background to transparent.
4. Click "Process Video" to start background removal. The processing time will depend on the video length.
5. Once processing is complete, download the processed video with the original audio.

## Code Overview

### Key Components
- **`remove_background` function**:  
  This function handles background removal using MediaPipe's Selfie Segmentation model and OpenCV for video processing.
  
- **Audio Processing**:  
  Audio is extracted from the original video using FFmpeg and re-added to the processed video to preserve the original soundtrack.

- **Streamlit UI**:  
  The user interface is built using Streamlit, allowing easy interaction with the app, video uploads, and background customization.

### Important Functions:
- `check_video_writer(writer)`: Ensures the video writer is initialized correctly.
- `extract_audio(video_path, output_audio_path)`: Extracts audio from the input video.
- `combine_audio_video(video_path, audio_path, output_path)`: Combines the processed video with the extracted audio.
- `remove_background(...)`: Handles background removal based on user selection (solid color, image, or transparent).

## File Structure

```bash
.
├── app.py                       # Main application file
├── requirements.txt             # Python dependencies
├── README.md                    # Documentation (this file)
└── assets/                      # Optional: store example videos or images for demos
```

## Requirements

The project requires the following Python libraries, which are listed in `requirements.txt`:
- `opencv-python`
- `numpy`
- `streamlit`
- `mediapipe`
- `Pillow`

Additionally, you will need to have FFmpeg installed on your machine.

## Known Issues

- Processing long videos might take a significant amount of time depending on the hardware used.
- Transparent backgrounds may result in larger output video files.
- If FFmpeg is not installed, the application won't be able to extract or combine audio.

## Future Improvements

- Add support for batch video processing.
- Improve real-time processing speed.
- Allow more background customization options like gradient backgrounds.

## License

This project is licensed under the MIT License
