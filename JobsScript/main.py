#!/bin/python

import sys, os, getopt, re, time, string, logging, logging.config, fcntl, atexit, pickle

import time, getpass, multiprocessing
from signal import signal, SIGTERM

import JobsWeb.models


def daemon():	
	pid=os.fork()
	if pid==-1:
		logger.error("fork fail 1")
		#print "fork fail 1\n"
	elif pid>0:
		exit(0)
	
	os.setsid()
	
	pid=os.fork()
	if pid==-1:
		logger.error("fork fail 2")
		#print "fork fail 2\n"
	elif pid>0:
		exit(0)

	os.umask(0)

	
def regcron():
    user=getpass.getuser()
    path=os.path.split(os.path.realpath(__file__))[0]
    print "update crontab"
    cron="""####worker<####
#* * * * * {path}/jqueueprod.py
* * * * * source ~/.bashrc;python {path}/jqueuecons.py | python {path}/logger.py
#* * * * * {path}/logger.py
* * * * * {path}/jmonitor.py
####worker>####""".format(path=path)
    fpath='/tmp/'+user+'.cron'
    if user=='octopus':
	os.system('touch '+fpath)
	cronf=open(fpath,'w')
	cronf.write(cron)
	cronf.close()
	os.system('crontab '+fpath)
    else:
	print "please run me for octopus!"
	exit(-1)
	#cronf=open('/var/spool/cron/'+getpass.getuser(),'r')
	#crons=cronf.read()
	#cronf.close()
	#cronf=open('/var/spool/cron/'+getpass.getuser(),'w')
	#reg=re.compile('####worker<####[\s\S]*####worker>####')
	#crons=reg.sub(cron,crons)
	#cronf.write(crons)
	#cronf.close()


def regdb(host,env):
	print "update Alerthostlist set name=%s, env=%s" % (host,env)
	if not JobsWeb.models.Alertjobhost.objects.filter(name=host):
		h=JobsWeb.models.Alertjobhost(name=host,env=env)
		h.save()
	pass


def regconf(host,env):
	path=os.path.split(os.path.realpath(__file__))[0]
	db=open(path+'/host','w')
	pickle.dump((host,env),db)
	db.close()


def capacity():
	l=open("/proc/loadavg").read().split()[0]
	c=multiprocessing.cpu_count()
	return string.atof(l)/c


def updb(host,env):
	try:
		h=JobsWeb.models.Alertjobhost.objects.filter(name=host)
	except:
		pass
	while h:
		time.sleep(1)
		#print "heartbeat"
		#print "update Alerthostlist set time=%s" % (time.time())
		logger.info("heartbeat")
		#logger.info("update Alerthostlist set time=%s" % (time.time()))
		#h.time=time.time() #
		#h.capacity=capacity() #
		h.update(time=time.time(), capacity=capacity())


def do(host,env):
	regdb(host,env)
	regcron()
	updb(host,env)


def reg(host,env):
	regconf(host,env)
	regdb(host,env)
	regcron()


def unreg(host,env):
	JobsWeb.models.Alertjobhost.objects.filter(name=host).delete()
	path=os.path.split(os.path.realpath(__file__))[0]
	os.remove(path+'/host')


def upreg(host,env):
	JobsWeb.models.Alertjobhost.objects.filter(name=host).update(env=env)
	regconf(host,env)


def main():
	pid_file='/tmp/main.pid'
	if os.path.isfile(pid_file):
		logger.info("The program is running")
		exit()
	else:
		signal(SIGTERM, lambda signum, stack_frame: exit(1))
		atexit.register(lambda:os.remove(pid_file))
		fd=os.open(pid_file,os.O_CREAT|os.O_EXCL|os.O_RDWR)
		os.write(fd,"%s\n" % str(os.getpid()))
		os.close(fd)

	opts=()
	args=()
	try:
		opts,args=getopt.getopt(sys.argv[1:],"dDU")
	except:
		pass
	if len(args)!=2:
		print "Uasge: %s [options] <host_name> <host_env>\noptions: \n-d --debug  \n-D --delete  \n-U --Update" % sys.argv[0]
		exit(-1)
	if ('-D', '') in opts:
		unreg(args[0],args[1])
	if ('-U', '') in opts:
		upreg(args[0],args[1])
		
	else:
		#daemon()
		reg(args[0],args[1])
		updb(args[0],args[1])


if __name__ == "__main__":
	logging.config.fileConfig("JobsProject/log4p.conf")
	logger = logging.getLogger("main")
	sys.exit(main())


__all__ = []
