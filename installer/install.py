#!/usr/bin/env python

import os, sys, pwd, glob, setuplib, subprocess

def get_uid_gid():
	try:
		target_user = pwd.getpwnam("pylsa")
	except KeyError, e:
		raise Exception("The PyLSA installation appears to have been corrupted.")
	
	return (target_user[2], target_user[3])

def switch_user():
	target_uid, target_gid = get_uid_gid()
	
	os.setgid(target_gid)
	os.setuid(target_uid)

def install(as_root=False):
	try:
		target_uid, target_gid = get_uid_gid()
	except Exception, e:
		target_uid, target_gid = (-1, -1)
	
	if as_root == True:
		target_path = "/home/pylsa/.pylsa"
	else:
		target_path = os.path.expanduser("~/.pylsa")
	
	setuplib.create_directory(target_path, True, target_uid, target_gid)
	setuplib.copy_file("src/daemon.py", "%s/daemon.py" % target_path, False, target_uid, target_gid)
	setuplib.copy_file("pylsa.conf", "%s/pylsa.conf" % target_path, True, target_uid, target_gid)
	subprocess.call(["tar", "-xzf", "psutil-0.6.1.tar.gz"])
	os.chdir("psutil-0.6.1")
	
	stfu = open("/dev/null", "w")
	if subprocess.call(["python", "setup.py", "build"], stdout=stfu, stderr=stfu) != 0:
		sys.stderr.write("An error occurred during compilation.\n")
		exit(1)
	
	try:
		build_dir = glob.glob("build/lib.*")[0]
	except IndexError, e:
		sys.stderr.write("Compilation appears to have failed, exiting...\n")
		exit(1)
	
	setuplib.copy_directory(build_dir, "%s/lib" % target_path, False, target_uid, target_gid)
	
def add_user(uname):
	# Lock /etc/passwd and /etc/group so we can safely add a user.
	open("/etc/passwd.lock", "w").close()
	open("/etc/group.lock", "w").close()

	# Find highest non-reserved UID in the user list
	passwd = open("/etc/passwd", "r+")
	highest_uid = 1000

	for line in passwd:
		username, password, uid, gid, name, homedir, shell = line.split(":")
		
		if username == uname:
			return True
		
		if int(uid) < 32000 and int(uid) > highest_uid:
			highest_uid = int(uid)
	
	new_uid = highest_uid + 1

	# Find highest non-reserved GID in the group list - we will assume same restrictions as for UID
	grp = open("/etc/group", "r+")
	highest_gid = 1000

	for line in grp:
		groupname, password, gid, users = line.split(":")
		
		if groupname == uname:
			return True
		
		if int(gid) < 32000 and int(gid) > highest_gid:
			highest_gid = int(gid)

	new_gid = highest_gid + 1

	# Append new user and group
	passwd.seek(0, 2)
	grp.seek(0, 2)
	
	setuplib.create_directory("/home/%s" % uname, True, new_uid, new_gid, "u+rwx g+rx")
	passwd.write("%s::%d:%d::/home/cvm:/bin/false\n" % (uname, new_uid, new_gid))
	grp.write("%s::%d:\n" % (uname, new_gid))

	# We're done with /etc/passwd and /etc/group
	passwd.close()
	grp.close()

	# Remove the locks on /etc/passwd and /etc/group
	os.remove("/etc/passwd.lock")
	os.remove("/etc/group.lock")
	
	return True

if os.getuid() == 0:
	# Script is run as root
	if os.path.isdir("/home/pylsa/.pylsa"):
		# Already installed, run as pylsa user
		switch_user()
		exit(subprocess.call(["python", "/home/pylsa/.pylsa/daemon.py"]))
	else:
		# Not installed yet, install as pylsa user then run
		add_user("pylsa")
		install(True)
		switch_user()
		exit(subprocess.call(["python", "/home/pylsa/.pylsa/daemon.py"]))
else:
	# Script is run as unprivileged user
	if os.path.isdir(os.path.expanduser("~/.pylsa")):
		# Already installed
		exit(subprocess.call(["python", os.path.expanduser("~/.pylsa/daemon.py")]))
	else:
		# Not installed yet
		install(False)
		exit(subprocess.call(["python", os.path.expanduser("~/.pylsa/daemon.py")]))
