module.exports = {
  apps: [{
    name: 'runninghub-workflow',
    script: 'app.py',
    interpreter: 'python',
    env: {
      FLASK_APP: 'app.py',
      FLASK_ENV: 'production',
      PORT: '17910'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/error.log',
    out_file: './logs/output.log',
    log_file: './logs/combined.log',
    time: true,
    merge_logs: true
  }]
};
