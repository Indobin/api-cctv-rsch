import subprocess
import os

# Fungsi untuk memulai proses FFmpeg
def start_ffmpeg_process(cctv_id: int, rtsp_url: str):
    # Tentukan di mana file HLS akan disimpan
    stream_dir = os.path.join("static", "videos", str(cctv_id))
    os.makedirs(stream_dir, exist_ok=True)
    
    # Jalur lengkap untuk file playlist .m3u8
    output_path = os.path.join(stream_dir, "stream.m3u8")

    # Ini adalah perintah FFmpeg yang akan dieksekusi
    ffmpeg_command = [
        'ffmpeg',
        # Parameter input
        '-rtsp_transport', 'tcp',  # Gunakan TCP untuk koneksi yang stabil
        '-i', rtsp_url,             # URL RTSP dari CCTV
        
        # Parameter output dan konversi
        '-c:v', 'copy',            # Menyalin codec video (H.264/H.265) tanpa konversi, sangat efisien!
        '-an',                     # Menghilangkan audio jika tidak dibutuhkan
        '-f', 'hls',               # Format output adalah HLS
        '-hls_time', '2',          # Setiap segmen video berdurasi 2 detik
        '-hls_list_size', '3',     # Playlist hanya menyimpan 3 segmen terakhir
        '-hls_flags', 'delete_segments', # Secara otomatis menghapus segmen lama
        '-y',                      # Timpa file output jika sudah ada
        
        # Jalur file output
        output_path
    ]
    
    # Jalankan perintah FFmpeg sebagai proses background
    process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process