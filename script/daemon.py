import sys, os, json
from datetime import datetime

# We need to set both the Python module path and system environment path, to make sure that the daemon
#  can find both the psutil library and its compiled libraries.
sys.path.insert(0, "%s/lib" % os.path.split(os.path.realpath(__file__))[0])
os.environ['PATH'] = "%s/lib:%s" % (os.path.split(os.path.realpath(__file__))[0], os.environ['PATH'])

import psutil

import urlparse
import SocketServer, SimpleHTTPServer

bind_ip = ""
port = 8081

def generate_stats(get_processes):
	listed_filesystems = ["ext2", "ext3", "ext4", "reiserfs", "removable", "fixed", "simfs"]
	
	mem = psutil.virtual_memory()
	swap = psutil.swap_memory()
	disks = {}
	
	for disk in psutil.disk_partitions(True):
		if disk.fstype in listed_filesystems:
			usage = psutil.disk_usage(disk.mountpoint)
			
			disks[disk.mountpoint] = {
				"device": disk.device,
				"options": disk.opts,
				"filesystem": disk.fstype,
				"total": usage.total,
				"free": usage.free
			}
	
	return_data = {
		"uptime": (datetime.now() - datetime.fromtimestamp(psutil.BOOT_TIME)).total_seconds(),
		"memory": {
			"total": mem.total,
			"available": mem.available,
			"used": mem.used,
			"unused": mem.free
		},
		"swap": {
			"total": swap.total,
			"used": swap.used,
			"unused": swap.free,
			"in": swap.sin,
			"out": swap.sout
		},
		"disk": disks,
		"cpu": psutil.cpu_percent(percpu=True),
		"load": list(os.getloadavg())
	}
	
	if get_processes:
		processes = []
		
		for proc in psutil.process_iter():
			try:
				cwd = proc.getcwd()
			except psutil.AccessDenied, e:
				cwd = None
				
			processes.append({
				"pid": proc.pid, 
				"parent": proc.ppid, 
				"name": proc.name, 
				"command": proc.cmdline, 
				"user": proc.username, 
				"status": str(proc.status),  # If we don't explicitly use str() here, json module will get confused
				"cwd": cwd, 
				"cpu": proc.get_cpu_percent(interval=0.1), 
				"rss": proc.get_memory_info()[0]
			})
		
		return_data['process'] = processes
		
	return return_data

class StatsHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def do_GET(self):
		req = urlparse.urlparse(self.path)
		get_params = urlparse.parse_qs(req.query)
		path = req.path
		
		try:
			get_processes = (get_params['processes'][0] == "1")
		except:
			get_processes = False
		
		if path=='/':
			self.send_response(200)
			self.send_header('Content-type','text/json')
			self.end_headers()
			self.wfile.write(json.dumps(generate_stats(get_processes)))
			return
		else:
			self.send_response(404)
			self.send_header('Content-type','text/plain')
			self.end_headers()
			self.wfile.write("404 Not Found")
			return

#### Hacky way to daemonize the whole thing

# Fork away
if os.fork(): exit(0)
os.umask(0) 
os.setsid() 
if os.fork(): exit(0)

# Write PID to file
outfile = open("pylsa.pid", "w")
outfile.write('%i' % os.getpid())
outfile.close()

# Bind the server
httpd = SocketServer.ThreadingTCPServer((bind_ip, port), StatsHandler, False)
httpd.allow_reuse_address = True
httpd.server_bind()
httpd.server_activate()

# If all went well, we'll redirect streams to silence them
sys.stdout.flush()
sys.stderr.flush()
si = file('/dev/null', 'r')
so = file('/dev/null', 'a+')
se = file('/dev/null', 'a+', 0)
os.dup2(si.fileno(), sys.stdin.fileno())
os.dup2(so.fileno(), sys.stdout.fileno())
os.dup2(se.fileno(), sys.stderr.fileno())

# Done!
print 'Port=',port
httpd.serve_forever()
