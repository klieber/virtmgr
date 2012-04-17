# -*- coding: utf-8 -*-
import libvirt, re
import socket
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def index(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')

	def creds(credentials, user_data):
		for credential in credentials:
			if credential[0] == libvirt.VIR_CRED_AUTHNAME:
				credential[4] = kvm_host.login
				if len(credential[4]) == 0:
					credential[4] = credential[3]
			elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
				credential[4] = kvm_host.passwd
			else:
				return -1
		return 0

	def get_hosts_status():
		kvm_host = Host.objects.filter(user=request.user.id)
		name_ipddr = {}
		for host in kvm_host:
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(1)
				s.connect((host.ipaddr, 16509))
				s.close()
				flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
				auth = [flags, creds, None]
				uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
				conn = libvirt.openAuth(uri, auth, 0)
				conn.getInfo()
				status = 1
			except:
				status = 2
			name_ipddr[host.hostname] = (host.id, host.ipaddr, host.login, host.passwd, status)
	   	return name_ipddr
	
	def del_host(host):
		hosts = Host.objects.get(user=request.user.id, hostname=host)
		hosts.delete()

	def add_host(host, ip, usr, passw):
		hosts = Host(user_id=request.user.id, hostname=host, ipaddr=ip, login=usr, passwd=passw)
		hosts.save()

	def get_host_status(hosts):
		for host, info in hosts.items():
			print host, info

	host_info = get_hosts_status()
	errors = []

	if request.method == 'POST':
		if request.POST.get('delete',''):
			host = request.POST.get('host','')
			del_host(host)
			return HttpResponseRedirect('/dashboard/')
		if request.POST.get('add',''):
			name = request.POST.get('name','')
			ipaddr = request.POST.get('ipaddr','')
			login = request.POST.get('sshusr','')
			passw = request.POST.get('passw','')
			have_host = Host.objects.filter(user=request.user, hostname=name)
			have_ip = Host.objects.filter(user=request.user, ipaddr=ipaddr)
			simbol = re.search('[^a-zA-Z0-9]+', name)
			if simbol:
				errors.append(u'Имя хоста не должно содержать символы')
			if have_host or have_ip:
				errors.append(u'Такой хост уже подключен')
			if not name:
				errors.append(u'Не было введено имя хоста')
			if not ipaddr:
				errors.append(u'Не был введен IP адрес')
			if not login:
				errors.append(u'Не был введен KVM логин')
			if not passw:
				errors.append(u'Не был введен KVM пароль')
			if not errors:
				add_host(name, ipaddr, login, passw)
				return HttpResponseRedirect('/dashboard/')
	return render_to_response('dashboard.html', locals())
