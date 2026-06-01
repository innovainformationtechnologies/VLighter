import os
import subprocess
import argparse
from pathlib import Path
import datetime


def run_cmd(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with return code {result.returncode}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def download_video_clip(video_url: str, start_time: str, end_time: str, output_path: str = "clip.mp4") -> str:
    cmd = [
        "yt-dlp",
        "--download-sections", f"*{start_time}-{end_time}",
        "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
        "-S", "vcodec:h264,res,acodec:m4a,ext",
        "--merge-output-format", "mp4",
        "--fixup", "never",
        "-o", output_path,
        video_url,
    ]
    run_cmd(cmd)
    return output_path


def make_timelapse(
    clip_path: str,
    speed_multiplier: float = 20.0,
    output_path: str = None,
) -> str:
    input_file = Path(clip_path)

    if output_path is None:
        output_path = str(input_file.parent / f"{input_file.stem}_timelapse.mp4")

    if speed_multiplier <= 0:
        raise ValueError("speed_multiplier must be greater than 0")

    pts_factor = 1.0 / speed_multiplier

    cmd = [
        "ffmpeg", "-y",
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


def full_pipeline(
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download a YouTube video segment and convert it to a timelapse."
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("start", help="Clip start time (HH:MM:SS)")
    parser.add_argument("end", help="Clip end time (HH:MM:SS)")
    parser.add_argument("--speed", type=float, default=20.0, help="Timelapse speed multiplier")
    parser.add_argument("--keep-clip", action="store_true", help="Keep the downloaded clip")
    parser.add_argument("--output-dir", default=".", help="Directory to save output files")

    args = parser.parse_args()

    output_dir = os.join(os.getcwd(), "temp", f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")

    result = full_pipeline(
        video_url=args.url,
        start_time=args.start,
        end_time=args.end,
        speed_multiplier=args.speed,
        keep_clip=args.keep_clip,
        output_dir=output_dir,
    )

    print(f"Done! Timelapse saved at: {result}")