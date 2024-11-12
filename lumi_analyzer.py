import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# see https://ffmpeg.org/ffprobe-all.html#:~:text=corresponding%20stream%20section.-,%2Dread_intervals,-read_intervals
read_intervals = "%+20" 
sdr_max_nits = 300 
hdr_video_file = 'hdr.mp4'  # HDR 10-bit
hdr_y_file = 'hdr.txt'
sdr_video_file = 'sdr.mp4'  # SDR 8-bit
sdr_y_file = 'sdr.txt'
frame_interval = 4 



def gen_stats():
    ffprobe_cmd_hdr = [
        'ffprobe','-hide_banner',
        '-f', 'lavfi', 
        '-i', f"movie={hdr_video_file},signalstats", 
        '-show_entries', 'frame_tags=lavfi.signalstats.YAVG,lavfi.signalstats.YMAX', 
        '-of', 'csv=p=0'
    ]

    ffprobe_cmd_sdr = [
        'ffprobe','-hide_banner',
        '-f', 'lavfi', 
        '-i', f"movie={sdr_video_file},signalstats", 
        '-show_entries', 'frame_tags=lavfi.signalstats.YAVG,lavfi.signalstats.YMAX', 
        '-of', 'csv=p=0'
    ]

    if read_intervals != "":
        ffprobe_cmd_hdr.append('-read_intervals')
        ffprobe_cmd_hdr.append(read_intervals)
        ffprobe_cmd_sdr.append('-read_intervals')
        ffprobe_cmd_sdr.append(read_intervals)

    with open(hdr_y_file, 'w') as hdr_file, open(sdr_y_file, 'w') as sdr_file:
        process_hdr = subprocess.Popen(ffprobe_cmd_hdr, stdout=hdr_file)
        process_sdr = subprocess.Popen(ffprobe_cmd_sdr, stdout=sdr_file)

        # wait for finishing
        process_hdr.wait()
        process_sdr.wait()

def clean_trailing_commas(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    cleaned_lines = [line.rstrip(',\n') for line in lines]
    return cleaned_lines

def draw():
    hdr_brightness_data = np.loadtxt(clean_trailing_commas(hdr_y_file), delimiter=',', usecols=(0, 1))
    sdr_brightness_data = np.loadtxt(clean_trailing_commas(sdr_y_file), delimiter=',', usecols=(0, 1))

    hdr_yavg_values = hdr_brightness_data[:, 0]
    hdr_ymax_values = hdr_brightness_data[:, 1]
    sdr_yavg_values = sdr_brightness_data[:, 0]
    sdr_ymax_values = sdr_brightness_data[:, 1]

    pq10_table = pd.read_csv('Limited10.csv', sep=',')
    y_values_pq10 = pq10_table['Y'].values
    nits_values = pq10_table['nits'].values

    yavg_hdr_nits = np.interp(hdr_yavg_values, y_values_pq10, nits_values)
    ymax_hdr_nits = np.interp(hdr_ymax_values, y_values_pq10, nits_values)
    yavg_sdr_nits = (sdr_yavg_values / 255) ** 2.4 * sdr_max_nits
    ymax_sdr_nits = (sdr_ymax_values / 255) ** 2.4 * sdr_max_nits


    sampled_frames = range(0, len(hdr_yavg_values), frame_interval)

    plt.figure(figsize=(12, 6))
    plt.plot(sampled_frames, yavg_hdr_nits[sampled_frames], label='HDR Avg', color='orange', linewidth=1, alpha=0.8)
    plt.plot(sampled_frames, ymax_hdr_nits[sampled_frames], label='HDR Max', color='red', linewidth=1, alpha=0.8)
    plt.plot(sampled_frames, yavg_sdr_nits[sampled_frames], label='SDR Avg', color='blue', linewidth=1, alpha=0.8)
    plt.plot(sampled_frames, ymax_sdr_nits[sampled_frames], label='SDR Max', color='green', linewidth=1, alpha=0.8)
    plt.axhline(y=300, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.axhline(y=600, color='red', linestyle='--', linewidth=0.5, alpha=0.5)
    plt.xlabel(f'Frame (every {frame_interval} frames)')
    plt.ylabel('Luminance Value (nits)')
    plt.yscale('log') 
    plt.title('Luminance Analysis for HDR and SDR')
    plt.legend() 
    plt.grid()
    plt.show()

def main():
    gen_stats()
    draw()


if __name__ == "__main__":
    main()