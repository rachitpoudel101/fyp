import multiprocessing

bind = "0.0.0.0:$PORT"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
pythonpath = "/opt/render/project/src/"
wsgi_app = "wsgi_prod:application"
