import os
import subprocess, sys
import requests
from pathlib import Path
import datetime
import platform

ON_WINDOWS = platform.system() == "Windows"
FFMPEG = "ffmpeg"
if ON_WINDOWS:
    FFMPEG = os.path.join(os.getcwd(), "bin", "ffmpeg.exe")

def run_cmd(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with return code {result.returncode}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def import_video_clip(clip_path: str, start_time: str, end_time: str, output_path: str = "clip.mp4") -> str:
    cmd = [
        FFMPEG, "-y",
        "-ss", start_time,
        "-to", end_time,
        "-i", clip_path,
        output_path
    ]
    run_cmd(cmd)
    return output_path


def download_video_clip(video_url: str, start_time: str, end_time: str, output_path: str = "clip.mp4") -> str:
    temp_path = output_path.replace(".mp4", "_temp.mp4")
    base_cmd = [
        "yt-dlp",
        "--download-sections", f"*{start_time}-{end_time}",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "-S", "vcodec:h264,res,acodec:m4a,ext",
        "--merge-output-format", "mp4",
        "--no-part",
        "--fixup", "never",
        "-o", output_path,
        video_url,
    ]
    if ON_WINDOWS:
        temp_template = output_path.replace(".mp4", "_%(id)s.%(ext)s")

        base_cmd = [
            sys.executable, "-m", "yt-dlp",
            "--ffmpeg-location", FFMPEG,
            "--extractor-args", "youtube:player_client=tv_embedded,web_creator",
            "--download-sections", f"*{start_time}-{end_time}",
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "-S", "vcodec:h264,res,acodec:m4a,ext",
            "--merge-output-format", "mp4",
            "--no-part",
            "--fixup", "never",
            "-o", temp_template,
            video_url,
        ]

        def try_download(cmd):
            run_cmd(cmd)
            # Find whatever yt-dlp named the file and rename it
            pattern = output_path.replace(".mp4", "_*.mp4")
            matches = glob.glob(pattern)
            if matches:
                os.rename(matches[0], output_path)

        try:
            try_download(base_cmd)
            return output_path
        except Exception:
            pass

        for browser in ["firefox", "chrome", "edge"]:
            try:
                print(f"Trying {browser}")
                try_download(base_cmd + ["--cookies-from-browser", browser])
                return output_path
            except Exception:
                continue

        raise RuntimeError("Failed to download video. Please make sure you are signed into YouTube in your browser.")
    run_cmd(base_cmd)
    return output_path


def make_timelapse(
    clip_path: str,
    speed_multiplier: float = 20.0,
    output_path: str = None,
) -> str:
    input_file = Path(clip_path)
    speed_multiplier = float(speed_multiplier)
    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}_timelapse.mp4")

    if speed_multiplier <= 0:
        raise ValueError("speed_multiplier must be greater than 0")

    pts_factor = 1.0 / speed_multiplier

    cmd = [
        FFMPEG, "-y",
        "-i", clip_path,
        "-vf", f"setpts={pts_factor}*PTS",
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        output_path,
    ]
    run_cmd(cmd)

    return output_path

def make_podcast(clip_path: str, output_path: str = None) -> str:
    input_file = Path(clip_path)

    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}_podcast.mp3")

    cmd = [
        FFMPEG, "-y",
        "-i", clip_path,
        "-vn",
        "-c:a", "libmp3lame",
        output_path,
    ]
    run_cmd(cmd)

    return output_path

def make_clip(clip_path: str):
    output_path = clip_path
    return output_path

def make_short(
    clip_path: str,
    blur: int = 20,
    gamma: float = 2.5,
    output_path: str = None) -> str:    

    input_file = Path(clip_path)
    
    if output_path is None:        
        output_path = str(input_file.parent / f"{input_file.stem}_shorts.mp4")    
    
    cmd = [
        FFMPEG, "-y",
        "-i", clip_path,
        "-filter_complex", (
            # Background: scale to fill 1080x1920, then blur
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,curves=all='0/0 1/{gamma}',"
            f"boxblur={blur}:5[bg];"

            # Foreground: scale to fit, ensure even dims
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            "scale=trunc(iw/2)*2:trunc(ih/2)*2[fg];"

            # Overlay fg centered on bg
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[out]"
        ),
        "-map", "[out]",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        output_path,
    ]
    run_cmd(cmd)
    
    return output_path

services = {
    "import_video":import_video_clip,
    "download_video":download_video_clip,
    "make_timelapse":make_timelapse,
    "make_podcast":make_podcast,
    "make_clip":make_clip,
    "make_short":make_short
}

def full_video_pipeline(
    video_url: str,
    start_time: str,
    end_time: str,
    speed_multiplier: float = 20.0,
    keep_clip: bool = False,
    output_dir: str = ".",
) -> str:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    clip_path = str(out_dir / "clip.mp4")
    timelapse_path = str(out_dir / "timelapse.mp4")

    download_video_clip(video_url, start_time, end_time, clip_path)
    make_timelapse(clip_path, speed_multiplier, timelapse_path)

    if not keep_clip:
        try:
            os.remove(clip_path)
        except FileNotFoundError:
            pass

    return timelapse_path


def run_pipeline(pipeline, output_dir) -> str:
    '''
    pipeline = {
        "download_video":{
            "video_url":"",
            "start_time":"",
            "end_time":""
        },
        "make_timelapse":{
            "clip_path":"",
            "speed_multiplier":20.0
        }
    }
    '''
    timelapse_path = os.path.join(os.getcwd(), "temp", f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    clip_path = str(out_dir / "clip.mp4")
    timelapse_path = str(out_dir / "timelapse.mp4")
    short_path = str(out_dir / "short.mp4")
    podcast_path = str(out_dir / "podcast.mp3")
    for node in pipeline:
        step = node
        args = pipeline[node]
        print(step, args)
        match step:
            case "import_video":
                import_video_clip(args["path"], args["start"], args["end"], clip_path)
            case "download_video":
                download_video_clip(args["url"], args["start"], args["end"], clip_path)
            case "make_timelapse":
                make_timelapse(clip_path, args["speed"], timelapse_path)
            case "make_podcast":
                make_podcast(clip_path, podcast_path)
            case "make_clip":
                make_clip(clip_path)
            case "make_short":
                make_short(clip_path, args["blur"], args["gamma"], short_path)

    # open file explorer
    import webbrowser
    webbrowser.open(str(out_dir))

    return {"success":True, "output":str(out_dir)}




if __name__ == "__main__":
    pass