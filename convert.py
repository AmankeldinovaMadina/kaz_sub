import openai
import os
import subprocess
from dotenv import load_dotenv
import asyncio
import aiofiles
import aiohttp
from typing import List

# Load environment variables from the .env file
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("API")  # Ensure the key is set in the .env file
if not openai.api_key:
    raise ValueError("API key not found. Ensure it is defined in the .env file.")

async def read_vtt(input_vtt: str) -> List[str]:
    """
    Read a VTT file and return its lines.
    """
    async with aiofiles.open(input_vtt, "r", encoding="utf-8") as file:
        lines = await file.readlines()
    return lines

async def write_vtt(output_vtt: str, lines: List[str]):
    """
    Write lines to a VTT file.
    """
    async with aiofiles.open(output_vtt, "w", encoding="utf-8") as file:
        await file.write("\n".join(lines) + "\n")

def is_translatable(line: str) -> bool:
    """
    Determine if a line should be translated.
    """
    return not (("-->" in line) or line.strip() == "" or line.startswith("WEBVTT") or line.strip().isdigit())

async def batch_translate(texts: List[str], max_retries: int = 3) -> List[str]:
    """
    Translate a batch of texts from Russian to Kazakh using OpenAI's ChatGPT API.
    Implements retry logic for robustness.
    """
    prompt = (
        "Translate the following lines from Russian to Kazakh. Maintain the timing and formatting.\n\n"
        + "\n".join([f"{i+1}. {text}" for i, text in enumerate(texts)])
    )
    
    for attempt in range(max_retries):
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",  # You can switch to "gpt-3.5-turbo" if needed
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more accurate translations
                max_tokens=2048  # Adjust based on your needs
            )
            translated_text = response.choices[0].message["content"].strip()
            # Assuming the response is in the same numbered format
            translated_lines = [line.partition('. ')[2] if '. ' in line else line for line in translated_text.split('\n')]
            return translated_lines
        except openai.error.OpenAIError as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    # If all retries fail, return original texts
    print("All translation attempts failed. Falling back to original texts.")
    return texts

async def translate_vtt_to_kazakh(input_vtt: str, output_vtt: str, batch_size: int = 10):
    """
    Translate the text in a VTT file to Kazakh using OpenAI's ChatGPT API.
    Optimizes token usage by sending batches of text lines.
    """
    lines = await read_vtt(input_vtt)
    translated_lines = []
    batch = []
    batch_indices = []

    for idx, line in enumerate(lines):
        stripped_line = line.strip()
        if is_translatable(stripped_line):
            batch.append(stripped_line)
            batch_indices.append(idx)
            if len(batch) == batch_size:
                # Translate the current batch
                translated_batch = await batch_translate(batch)
                for i, translated_line in zip(batch_indices, translated_batch):
                    translated_lines.append((i, translated_line))
                batch = []
                batch_indices = []
        else:
            # Non-translatable lines are added directly
            translated_lines.append((idx, stripped_line))
    
    # Translate any remaining lines
    if batch:
        translated_batch = await batch_translate(batch)
        for i, translated_line in zip(batch_indices, translated_batch):
            translated_lines.append((i, translated_line))
    
    # Sort the translated lines based on original indices
    translated_lines.sort(key=lambda x: x[0])
    final_lines = [line for idx, line in translated_lines]
    
    await write_vtt(output_vtt, final_lines)
    print(f"Translated VTT saved as {output_vtt}")

def add_vtt_to_video(input_video: str, subtitle_file: str, output_video: str):
    """
    Embed VTT subtitles into a video as an optional track using FFmpeg.
    """
    try:
        command = [
            "ffmpeg",
            "-i", input_video,
            "-i", subtitle_file,
            "-c", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=kaz",
            output_video
        ]
        subprocess.run(command, check=True)
        print(f"Subtitles successfully added to {output_video}")
    except subprocess.CalledProcessError as e:
        print(f"Error adding subtitles to video: {e}")

async def main(input_vtt: str, input_video: str):
    """
    Main function to translate subtitles, save them, and add to a video.
    """
    print(f"Input VTT file: {input_vtt}")
    print(f"Input video file: {input_video}")
    
    # Define the new output file names
    output_vtt = input_vtt.replace(".vtt", "_kazakh_translated.vtt")
    output_video = input_video.replace(".mp4", "_with_kazakh_subtitles.mp4")

    print("Translating subtitles in batches...")
    await translate_vtt_to_kazakh(input_vtt, output_vtt)

    print("Adding subtitles to video...")
    add_vtt_to_video(input_video, output_vtt, output_video)

    print(f"Process complete. Video with subtitles saved as {output_video}")

if __name__ == "__main__":
    # Update the input file names to match your actual files
    input_vtt_file = "GMT20241227-140457_Recording.transcript.vtt"
    input_video_file = "GMT20241227-140457_Recording_1920x1080.mp4"

    asyncio.run(main(input_vtt_file, input_video_file))
