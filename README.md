# Kazakh Subtitle Translator and Embedder

This project translates subtitles from Russian to Kazakh using OpenAI's ChatGPT API and embeds the translated subtitles into a video using FFmpeg.

---

## Installation

### 1. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/AmankeldinovaMadina/kaz_sub.git
cd kaz_sub
```
### 2. Clone the Repository
```
pip install -r requirements.txt
```
### 3. Install FFmpeg

For ubuntu 
```
sudo apt update
sudo apt install ffmpeg
```
For macOS
```
brew install ffmpeg
```
For windows, search in the google and download from the website

### 4. Create a .env File
In the root directory of the project, create a .env file and add your OpenAI API key. 

### 5. Add .vtt and .mp4 files to the same folder and change input file names in the script 
```
input_vtt_file = "example_subtitles.vtt"
input_video_file = "example_video.mp4"
```

### 6. Run the script 
```
python convert.py
```

