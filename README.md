# CustomCaptionCreator
downloads a youtube video, generates custom captions with ollama, and burns them back into the video

## what you need

- python 3
- ollama with a model installed (llama3.2 recommended)
- ffmpeg
- yt-dlp and requests: `pip install yt-dlp requests`

## how to use
```bash
python main.py
```

paste a youtube url, optionally add a custom style (like "pirate speak" or "no cussing"), and recieve a video with your custom captions on the original video in the downloads folder
