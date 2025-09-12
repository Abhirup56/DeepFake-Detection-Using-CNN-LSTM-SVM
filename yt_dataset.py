import pandas as pd
import subprocess
import os

# -----------------------
# SETTINGS
# -----------------------
csv_file = "youtube.csv"   # CSV with column 'link'
output_dir = "downloads"
os.makedirs(output_dir, exist_ok=True)

# Clip settings
start_time = 10    # skip first 10s
duration = 35      # keep 35s clip (≈30-40s)

# -----------------------
# MAIN LOOP
# -----------------------
df = pd.read_csv(csv_file)

for idx, row in df.iterrows():
    url = str(row["link"]).strip()
    if not url or not url.startswith("http"):
        print(f"[{idx}] Skipped invalid link: {url}")
        continue

    out_file = os.path.join(output_dir, f"video_{idx+1}.mp4")

    # yt-dlp command
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=360][ext=mp4]",  # 360p video only
        "--output", out_file,
        "--download-sections", f"*{start_time}-{start_time+duration}",  # cut clip
        "--no-playlist",
        url,
    ]

    print(f"[{idx+1}/{len(df)}] Downloading: {url}")
    try:
        subprocess.run(cmd, check=True)
        # Strip audio afterwards with ffmpeg
        silent_file = out_file.replace(".mp4", "_silent.mp4")
        subprocess.run([
            "ffmpeg", "-i", out_file, "-an", "-c:v", "copy", silent_file, "-y"
        ], check=True)
        os.remove(out_file)  # remove original with audio
        os.rename(silent_file, out_file)
        print(f"   ✅ Saved: {out_file}")
    except Exception as e:
        print(f"   ❌ FAILED: {url} -> {e}")
