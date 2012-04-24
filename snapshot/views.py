# -*- coding: utf-8 -*-
import libvirt, re, time
import virtinst.util as util
from virtmgr.network.IPy import IP
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from virtmgr.model.models import *

def get_vms(conn):
   try:
      vname = {}
      for id in conn.listDomainsID():
         id = int(id)
         dom = conn.lookupByID(id)
         vname[dom.name()] = dom.info()[0]
      for id in conn.listDefinedDomains():
         dom = conn.lookupByName(id)
         vname[dom.name()] = dom.info()[0]
      return vname
   except:
     return "error"

def get_vm_snapshots(conn):
   try:
      vname = {}
      for id in conn.listDomainsID():
         id = int(id)
         dom = conn.lookupByID(id)
         if dom.snapshotNum(0) != 0:
         	vname[dom.name()] = dom.info()[0]
      for id in conn.listDefinedDomains():
         dom = conn.lookupByName(id)
         if dom.snapshotNum(0) != 0:
         	vname[dom.name()] = dom.info()[0]
      return vname
   except:
     return "error"

def vm_conn(host_ip, creds):
   	try:
		flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
  		auth = [flags, creds, None]
		uri = 'qemu+tcp://' + host_ip + '/system'
	   	conn = libvirt.openAuth(uri, auth, 0)
	   	return conn
	except:
		return "error"

def index(request, host_id):
	
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

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

	conn = vm_conn(kvm_host.ipaddr, creds)
	all_vm_snapshots = get_vm_snapshots(conn)
	all_vm = get_vms(conn)

	if all_vm_snapshots:
		return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, all_vm_snapshots.keys()[0]))

	return render_to_response('snapshot.html', locals())

def snapshot(request, host_id, vname):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

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

	def get_dom(vname):
		try:
			dom = conn.lookupByName(vname)
			return dom
		except:
			return "error"

	def get_snapshots():
		try:
			snapshots = {}
			all_snapshot = dom.snapshotListNames(0)
			for snapshot in all_snapshot:
				snapshots[snapshot] = (time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(snapshot))), dom.info()[0])
			return snapshots
		except:
			return "error"

	def del_snapshot(name_snap):
		try:
			snap = dom.snapshotLookupByName(name_snap,0)
			snap.delete(0)
		except:
			return "error"

	def revert_snapshot(name_snap):
		try:
			snap = dom.snapshotLookupByName(name_snap,0)
			dom.revertToSnapshot(snap,0)
		except:
			return "error"

	conn = vm_conn(kvm_host.ipaddr, creds)
	all_vm_snapshots = get_vm_snapshots(conn)
	dom = get_dom(vname)
	vm_snapshot = get_snapshots()
	all_vm = get_vms(conn)

	if not vm_snapshot:
		return HttpResponseRedirect('/snapshot/%s/' % (host_id))

	if request.method == 'POST':
		if request.POST.get('delete',''):
			print "YES"
			name = request.POST.get('name','')
			del_snapshot(name)
			return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
        if request.POST.get('revert',''):
        	name = request.POST.get('name','')
        	revert_snapshot(name)
        	message = u'Восстановление снапшота "%s" прошло успешно' % (name)

	conn.close()

	return render_to_response('snapshot.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')
	else:
		return HttpResponseRedirect('/dashboard')