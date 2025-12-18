import yt_dlp
import subprocess
import os
import re
import requests

def download_video_and_captions(video_url):
    os.makedirs("downloads", exist_ok=True)
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        video_id = info['id']
        video_file = f"downloads/{video_id}.{info['ext']}"
        
        caption_file = None
        for lang in ['en', 'en-US', 'en-GB']:
            possible = f"downloads/{video_id}.{lang}.vtt"
            if os.path.exists(possible):
                caption_file = possible
                break
        
        return video_file, caption_file, video_id

def parse_vtt(vtt_file):
    with open(vtt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    captions = []
    for block in content.split('\n\n'):
        lines = block.strip().split('\n')
        if len(lines) >= 2 and '-->' in lines[0]:
            timestamp = lines[0].strip()
            text = ' '.join(lines[1:])
            text = re.sub(r'<[^>]+>', '', text).strip()
            if text:
                captions.append({'timestamp': timestamp, 'text': text})
    
    return captions

def process_with_ollama(captions, custom_style=None):
    full_text = '\n'.join([f"{i+1}. {cap['text']}" for i, cap in enumerate(captions)])
    
    style = custom_style if custom_style else "make more readable"
    
    prompt = f"""transform these captions:
- remove filler words (um uh like you know etc)
- fix grammar
- style: {style}
- return exactly {len(captions)} numbered lines
- keep similar length for timing

captions:
{full_text}

format:
1. [text]
2. [text]"""

    response = requests.post('http://localhost:11434/api/generate',
        json={
            'model': 'llama3.2',
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.3, 'num_predict': 4000}
        },
        timeout=180
    )
    
    result = response.json()['response']
    
    cleaned_lines = []
    for line in result.split('\n'):
        match = re.match(r'^\d+[\.):\s]+(.+)$', line.strip())
        if match:
            cleaned_lines.append(match.group(1).strip())
    
    for i, cap in enumerate(captions):
        if i < len(cleaned_lines):
            cap['text'] = cleaned_lines[i]
    
    return captions

def create_vtt(captions, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for cap in captions:
            f.write(f"{cap['timestamp']}\n{cap['text']}\n\n")

def overlay_captions(video_file, caption_file, output_file):
    caption_path = caption_file.replace('\\', '\\\\\\\\')
    
    subprocess.run([
        'ffmpeg', '-i', video_file,
        '-vf', f"subtitles={caption_path}",
        '-c:a', 'copy', '-y', output_file
    ], check=True, capture_output=True)

def main():
    url = input("youtube url: ").strip()
    if not url:
        return
    
    style = input("custom style (optional): ").strip() or None
    
    video_file, caption_file, video_id = download_video_and_captions(url)
    
    if not caption_file:
        print("no captions found")
        return
    
    captions = parse_vtt(caption_file)
    captions = process_with_ollama(captions, style)
    
    new_caption = f"downloads/{video_id}_cleaned.vtt"
    create_vtt(captions, new_caption)
    
    output = f"downloads/{video_id}_final.mp4"
    overlay_captions(video_file, new_caption, output)
    
    print(f"\ndone: {output}\n")

if __name__ == "__main__":
    main()
