import os
import numpy as np
from moviepy.editor import *
from moviepy.config import change_settings
from requests import get
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from openai import OpenAI
from nltk.tokenize import sent_tokenize
import shutil
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Adjust ImageMagick binary path for Windows
if os.name == 'nt':
    change_settings({"IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"})

def setup_folders():
    folders = ["static/rawdata/audio", "static/rawdata/images", "static/rawdata/videos", "static/result"]
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)
        os.makedirs(folder, exist_ok=True)

def generate_text(prompt):
    full_prompt = f"{prompt}\n\nPlease generate a response that is exactly 6 sentences long."
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=full_prompt,
            max_tokens=150,
            n=1,
            temperature=0.5,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return None

def generate_image_description(sentence, previous_description=None):
    prompt = (
        f"Create a detailed image description based on the following sentence: {sentence}"
        if not previous_description else
        f"""Based on the following sentence and the previous image description, create a new image description that maintains consistency with the previous image but incorporates new elements from the sentence. 
        
        Previous image description: {previous_description}
        
        New sentence: {sentence}
        
        New image description:"""
    )
    
    try:
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=100,
            n=1,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error generating image description: {e}")
        return None

def generate_image(image_description, index):
    try:
        response = client.images.generate(
            prompt=image_description,
            n=1,
            size="1024x1024"
        )
        image_url = response.data[0].url
        img = Image.open(BytesIO(get(image_url).content))
        img_path = f"static/rawdata/images/image{index}.png"
        img.save(img_path)
        return img_path
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None

def generate_speech(text, index):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            input=text,
            voice="nova",
        )
        audio_file_path = f"static/rawdata/audio/voiceover{index}.mp3"
        response.stream_to_file(audio_file_path)
        time.sleep(1)  # Ensure the file is fully written
        return audio_file_path
    except Exception as e:
        logger.error(f"Error generating speech: {e}")
        return None

def create_video_clip(sentence, index, previous_description=None):
    image_description = generate_image_description(sentence, previous_description)
    if not image_description:
        return None, f"Failed to generate image description for sentence {index}."
    
    image_path = generate_image(image_description, index)
    if not image_path:
        return None, f"Failed to generate image for sentence {index}."
    
    audio_file_path = generate_speech(sentence, index)
    if not audio_file_path:
        return None, f"Failed to generate audio for sentence {index}."
    
    audio_clip = AudioFileClip(audio_file_path)
    image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
    
    def make_text_slide(t):
        remaining_time = max(0, audio_clip.duration - t)
        return (TextClip(sentence, fontsize=30, color="white", bg_color='rgba(0,0,0,0.5)', font='Arial', size=(image_clip.w, None))
                .set_position(('center', 'bottom'))
                .set_duration(remaining_time)
                .set_start(t)
                .crossfadein(0.5)
                .crossfadeout(0.5))
    
    text_clips = [make_text_slide(t) for t in np.arange(0, audio_clip.duration, 0.1)]
    video = CompositeVideoClip([image_clip.set_audio(audio_clip), *text_clips])
    video_path = f"static/rawdata/videos/video{index}.mp4"
    video.write_videofile(video_path, fps=24, threads=4, logger=None)
    return video_path, None

def create_final_video():
    video_dir = "static/rawdata/videos"
    clips = [VideoFileClip(os.path.join(video_dir, file)) for file in sorted(os.listdir(video_dir)) if file.endswith(".mp4")]
    final_video = concatenate_videoclips(clips, method="compose")
    final_video_path = "static/result/final_video.mp4"
    final_video.write_videofile(final_video_path, threads=4, logger=None)
    
    setup_folders()  # Recreate the necessary directories after cleanup
    
    return final_video_path

def process_text_to_video(prompt):
    generated_text = generate_text(prompt)
    if not generated_text:
        return None, "Failed to generate text."
    
    sentences = sent_tokenize(generated_text)
    
    previous_description = None
    for index, sentence in enumerate(sentences):
        video_path, error = create_video_clip(sentence, index, previous_description)
        if error:
            return None, error
        previous_description = generate_image_description(sentence, previous_description)

    final_video_path = create_final_video()
    return final_video_path, None
