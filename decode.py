import os
import subprocess
import shutil
from tqdm import tqdm

# ---------- REPLACE THESE BEFORE RUN----------
DATASET_ROOT = r"PATH OF ENCODED VIDEO FOLDER" 
OUTPUT_ROOT  = r"PATH WHERE TO SAVE DECODED VIDEOS"
CRF = "23"
PRESET = "fast"
# --------------------------------

def ffmpeg_available():
    return shutil.which("ffmpeg") is not None

if not ffmpeg_available():
    raise SystemExit("ffmpeg not found in PATH. Install ffmpeg and add to PATH, then re-run.")

# collect all video files
video_files = []
for root, dirs, files in os.walk(DATASET_ROOT):
    for fname in files:
        if fname.lower().endswith((".mp4", ".mkv", ".avi")):   # add other extensions if needed
            in_path = os.path.join(root, fname)
            rel_path = os.path.relpath(in_path, DATASET_ROOT)  # keep folder structure
            out_path = os.path.join(OUTPUT_ROOT, rel_path)
            out_dir = os.path.dirname(out_path)
            os.makedirs(out_dir, exist_ok=True)
            video_files.append((in_path, out_path))

print(f"Found {len(video_files):,} video files under: {DATASET_ROOT}")
if len(video_files) == 0:
    raise SystemExit("No videos found. Check DATASET_ROOT path and the file extensions.")

log_path = os.path.join(OUTPUT_ROOT, "reencode_log.txt")
with open(log_path, "w", encoding="utf-8") as log:
    succeeded = 0
    skipped = 0
    failed = 0

    for in_path, out_path in tqdm(video_files, desc="Re-encoding", unit="video"):
        # sanity checks
        if not os.path.isfile(in_path):
            log.write(f"NOT_FOUND\t{in_path}\n")
            failed += 1
            continue

        if os.path.exists(out_path):
            skipped += 1
            continue

        # ffmpeg command: force yuv420p, movflags for streaming, remove audio if none (-an)
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", in_path,
            "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-an",
            out_path
        ]

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except Exception as e:
            log.write(f"EXCEPTION\t{in_path}\t{repr(e)}\n")
            failed += 1
            tqdm.write(f"Exception on {os.path.basename(in_path)}")
            continue

        if proc.returncode != 0:
            failed += 1
            log.write(f"FAILED\t{in_path}\treturncode={proc.returncode}\n{proc.stderr}\n\n")
            tqdm.write(f"Failed: {os.path.basename(in_path)}  (see log)")
        else:
            succeeded += 1

    # summary
    log.write(f"\nSUMMARY: succeeded={succeeded}, skipped={skipped}, failed={failed}\n")
    print(f"\nDone. Succeeded: {succeeded}, Skipped: {skipped}, Failed: {failed}")
    print("See log for details:", log_path)
