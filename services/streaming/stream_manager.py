import subprocess
import os
from typing import Dict, Optional
import signal
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self, output_dir: str = "stream_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.active_streams: Dict[str, subprocess.Popen] = {}

    def start_stream(self, camera_id: str, rtsp_url: str) -> bool:
        output_path = self.output_dir / f"{camera_id}"
        output_path.mkdir(exist_ok=True)

        command = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-hls_time', '2',
            '-hls_list_size', '10',
            '-f', 'hls',
            '-hls_flags', 'delete_segments',
            str(output_path / 'stream.m3u8')
        ]

        try:
            logger.info(f"Executing FFmpeg command: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.active_streams[camera_id] = process

            logger.info(f"Checking if {output_path / 'stream.m3u8'} exists...")
            if not (output_path / 'stream.m3u8').exists():
                logger.error(f"{output_path / 'stream.m3u8'} was not created!")

            logger.info(f"Stream started for camera {camera_id} with PID {process.pid}")
            return True
        except Exception as e:
            logger.error(f"Error starting stream for camera {camera_id}: {e}")
            return False


    def stop_stream(self, camera_id: str) -> bool:
        """Stop streaming for a camera."""
        if camera_id not in self.active_streams:
            logger.warning(f"No active stream found for camera {camera_id}")
            return False

        try:
            process = self.active_streams[camera_id]
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=5)
            del self.active_streams[camera_id]

            # Cleanup stream files
            output_path = self.output_dir / f"{camera_id}"
            if output_path.exists():
                for file in output_path.glob("*.ts"):
                    file.unlink()
                for file in output_path.glob("*.m3u8"):
                    file.unlink()
                output_path.rmdir()

            logger.info(f"Successfully stopped stream for camera {camera_id}")
            return True

        except Exception as e:
            logger.error(f"Error stopping stream for camera {camera_id}: {str(e)}")
            return False

    def get_stream_url(self, camera_id: str) -> Optional[str]:
        """Get the HLS URL for a camera stream."""
        if camera_id not in self.active_streams:
            return None
        return f"/streams/{camera_id}/stream.m3u8"

    def cleanup(self):
        """Stop all active streams."""
        for camera_id in list(self.active_streams.keys()):
            self.stop_stream(camera_id)


stream_manager = StreamManager()