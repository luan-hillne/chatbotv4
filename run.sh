nohup python app_chat1.py >logs/log/logs1.txt 2>&1 & echo $! > logs/pid/run1.pid
nohup python app_chat2.py >logs/log/logs2.txt 2>&1 & echo $! > logs/pid/run2.pid
nohup python app_chat3.py >logs/log/logs3.txt 2>&1 & echo $! > logs/pid/run3.pid
nohup python app_chat4.py >logs/log/logs4.txt 2>&1 & echo $! > logs/pid/run4.pid
nohup python app_chat5.py >logs/log/logs5.txt 2>&1 & echo $! > logs/pid/run5.pid
nohup python app_chat6.py >logs/log/logs6.txt 2>&1 & echo $! > logs/pid/run6.pid
nohup python app_chat7.py >logs/log/logs7.txt 2>&1 & echo $! > logs/pid/run7.pid
nohup python app_chat8.py >logs/log/logs8.txt 2>&1 & echo $! > logs/pid/run8.pid

