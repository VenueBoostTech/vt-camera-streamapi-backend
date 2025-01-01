module.exports = {
  apps: [
    {
      name: "Camera_Stream_API_Backend",
      script: "/home/ubuntu/miniconda3/envs/vision-track-backend/bin/uvicorn",
      args: "main:app --host 0.0.0.0 --port 8000",
      interpreter: "/home/ubuntu/miniconda3/envs/vision-track-backend/bin/python",
      log_file: "/home/ubuntu/pm2_logs/fastapi-app.log",  // New log path
      out_file: "/home/ubuntu/pm2_logs/fastapi-app-out.log",
      error_file: "/home/ubuntu/pm2_logs/fastapi-app-error.log",
    }
  ]
};