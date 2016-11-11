#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2016 Philemon <mmgen-py@yandex.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
test/tooltest.py:  Tests for the 'mmgen-tool' utility
"""

import sys,os
pn = os.path.dirname(sys.argv[0])
os.chdir(os.path.join(pn,os.pardir))
sys.path.__setitem__(0,os.path.abspath(os.curdir))

# Import this _after_ local path's been added to sys.path
from mmgen.common import *

start_mscolor()

from collections import OrderedDict
cmd_data = OrderedDict([
	('util', {
			'desc': 'base conversion, hashing and file utilities',
			'cmd_data': OrderedDict([
				('strtob58',     ()),
				('b58tostr',     ('strtob58','io')),
				('hextob58',     ()),
				('b58tohex',     ('hextob58','io')),
				('b58randenc',   ()),
				('hextob32',     ()),
				('b32tohex',     ('hextob32','io')),
				('randhex',      ()),
				('id8',          ()),
				('id6',          ()),
				('str2id6',      ()),
				('sha256x2',     ()),
				('hexreverse',   ()),
				('hexlify',      ()),
				('hexdump',      ()),
				('unhexdump',    ('hexdump','io')),
				('rand2file',    ()),
			])
		}
	),
	('bitcoin', {
			'desc': 'Bitcoin address/key commands',
			'cmd_data': OrderedDict([
				('randwif',      ()),
				('randpair',     ()),
				('wif2addr',     ('randpair','o2')),
				('wif2hex',      ('randpair','o2')),
				('privhex2addr', ('wif2hex','o2')), # wif from randpair o2
				('hex2wif',      ('wif2hex','io2')),
				('addr2hexaddr', ('randpair','o2')),
				('hexaddr2addr', ('addr2hexaddr','io2')),
# ('pubkey2addr',  ['<public key in hex format> [str]']),
# ('pubkey2hexaddr', ['<public key in hex format> [str]']),
			])
		}
	),
	('mnemonic', {
			'desc': 'mnemonic commands',
			'cmd_data': OrderedDict([
				('hex2mn',       ()),
				('mn2hex',       ('hex2mn','io3')),
				('mn_rand128',   ()),
				('mn_rand192',   ()),
				('mn_rand256',   ()),
				('mn_stats',     ()),
				('mn_printlist', ()),
			])
		}
	),
	('rpc', {
			'desc': 'Bitcoind RPC commands',
			'cmd_data': OrderedDict([
#				('keyaddrfile_chksum', ()), # interactive
				('addrfile_chksum', ()),
				('getbalance',      ()),
				('listaddresses',   ()),
				('txview',          ()),
			])
		}
	),
])

cfg = {
	'name':          'the tool utility',
	'enc_passwd':    'Ten Satoshis',
	'tmpdir':        'test/tmp10',
	'tmpdir_num':    10,
	'refdir':        'test/ref',
	'txfile':        'FFB367[1.234].rawtx',
	'addrfile':      '98831F3A[1,31-33,500-501,1010-1011].addrs',
	'addrfile_chk':  '6FEF 6FB9 7B13 5D91',
}

opts_data = {
	'desc': "Test suite for the 'mmgen-tool' utility",
	'usage':'[options] [command]',
	'options': """
-h, --help          Print this help message
-l, --list-cmds     List and describe the tests and commands in the test suite
-s, --system        Test scripts and modules installed on system rather than
                    those in the repo root
-v, --verbose       Produce more verbose output
""",
	'notes': """

If no command is given, the whole suite of tests is run.
"""
}

cmd_args = opts.init(opts_data,add_opts=['exact_output','profile'])

if opt.system: sys.path.pop(0)

if opt.list_cmds:
	fs = '  {:<{w}} - {}'
	Msg('Available commands:')
	w = max([len(i) for i in cmd_data])
	for cmd in cmd_data:
		Msg(fs.format(cmd,cmd_data[cmd]['desc'],w=w))
	Msg('\nAvailable utilities:')
	Msg(fs.format('clean','Clean the tmp directory',w=w))
	sys.exit()

import binascii
from mmgen.test import *
from mmgen.tx import is_wif,is_btc_addr,is_b58_str

class MMGenToolTestSuite(object):

	def __init__(self):
		pass

	def gen_deps_for_cmd(self,cmd,cdata):
		fns = []
		if cdata:
			name,code = cdata
			io,count = (code[:-1],int(code[-1])) if code[-1] in '0123456789' else (code,1)

			for c in range(count):
				fns += ['%s%s%s' % (
					name,
					('',c+1)[count > 1],
					('.out','.in')[ch=='i']
				) for ch in io]
		return fns

	def get_num_exts_for_cmd(self,cmd,dpy): # dpy required here
		num = str(tool_cfgs['tmpdir_num'])
		# return only first file - a hack
		exts = gen_deps_for_cmd(dpy)
		return num,exts

	def do_cmds(self,cmd_group):
		cdata = cmd_data[cmd_group]['cmd_data']
		for cmd in cdata: self.do_cmd(cmd,cdata[cmd])

	def do_cmd(self,cmd,cdata):

		fns = self.gen_deps_for_cmd(cmd,cdata)

		file_list = [os.path.join(cfg['tmpdir'],fn) for fn in fns]

		self.__class__.__dict__[cmd](*([self,cmd] + file_list))


	def run_cmd(self,name,tool_args,kwargs='',extra_msg='',silent=False,strip=True):
		mmgen_tool = 'mmgen-tool'
		if not opt.system:
			mmgen_tool = os.path.join(os.curdir,mmgen_tool)

		sys_cmd = ['python', mmgen_tool, '-d',cfg['tmpdir'], name] + tool_args + kwargs.split()
		if extra_msg: extra_msg = '(%s)' % extra_msg
		full_name = ' '.join([name]+kwargs.split()+extra_msg.split())
		if not silent:
			if opt.verbose:
				sys.stderr.write(green('Testing %s\nExecuting ' % full_name))
				sys.stderr.write('%s\n' % cyan(repr(sys_cmd)))
			else:
				msg_r('Testing %-31s%s' % (full_name+':',''))

		import subprocess
		p = subprocess.Popen(
			sys_cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			)
		a,b = p.communicate()
		retcode = p.wait()
		if retcode != 0:
			msg('%s\n%s\n%s'%(red('FAILED'),yellow('Command stderr output:'),b))
			die(1,red('Called process returned with an error (retcode %s)' % retcode))
		return (a,a.rstrip())[bool(strip)]

	def run_cmd_chk(self,name,f1,f2,kwargs='',extra_msg=''):
		idata = read_from_file(f1).rstrip()
		odata = read_from_file(f2).rstrip()
		ret = self.run_cmd(name,[odata],kwargs=kwargs,extra_msg=extra_msg)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		if ret == idata: ok()
		else:
			die(3,red(
	"Error: values don't match:\nIn:  %s\nOut: %s" % (repr(idata),repr(ret))))
		return ret

	def run_cmd_nochk(self,name,f1,kwargs=''):
		odata = read_from_file(f1).rstrip()
		ret = self.run_cmd(name,[odata],kwargs=kwargs)
		vmsg('In:   ' + repr(odata))
		vmsg('Out:  ' + repr(ret))
		return ret

	def run_cmd_out(self,name,carg=None,Return=False,kwargs='',fn_idx='',extra_msg='',literal=False,chkdata=''):
		if carg: write_to_tmpfile(cfg,'%s%s.in' % (name,fn_idx),carg+'\n')
		ret = self.run_cmd(name,([],[carg])[bool(carg)],kwargs=kwargs,extra_msg=extra_msg)
		if carg: vmsg('In:   ' + repr(carg))
		vmsg('Out:  ' + (repr(ret),ret)[literal])
		if ret or ret == '':
			write_to_tmpfile(cfg,'%s%s.out' % (name,fn_idx),ret+'\n')
			if chkdata:
				cmp_or_die(ret,chkdata)
				return
			if Return: return ret
			else:   ok()
		else:
			die(3,red("Error for command '%s'" % name))

	def run_cmd_randinput(self,name,strip=True):
		s = os.urandom(128)
		fn = name+'.in'
		write_to_tmpfile(cfg,fn,s,binary=True)
		ret = self.run_cmd(name,[get_tmpfile_fn(cfg,fn)],strip=strip)
		fn = name+'.out'
		write_to_tmpfile(cfg,fn,ret+'\n')
		ok()
		vmsg('Returned: %s' % ret)

	def str2id6(self,name):
		s = getrandstr(120,no_space=True)
		s2 = ' %s %s %s %s %s ' % (s[:3],s[3:9],s[9:29],s[29:50],s[50:120])
		ret1 = self.run_cmd(name,[s],extra_msg='unspaced input'); ok()
		ret2 = self.run_cmd(name,[s2],extra_msg='spaced input')
		cmp_or_die(ret1,ret2)
		vmsg('Returned: %s' % ret1)

	def mn_rand128(self,name):
		self.run_cmd_out(name)

	def mn_rand192(self,name):
		self.run_cmd_out(name)

	def mn_rand256(self,name):
		self.run_cmd_out(name)

	def mn_stats(self,name):
		self.run_cmd_out(name)

	def mn_printlist(self,name):
		self.run_cmd(name,[])
		ok()

	def id6(self,name):     self.run_cmd_randinput(name)
	def id8(self,name):     self.run_cmd_randinput(name)
	def hexdump(self,name): self.run_cmd_randinput(name,strip=False)

	def unhexdump(self,name,fn1,fn2):
		ret = self.run_cmd(name,[fn2],strip=False)
		orig = read_from_file(fn1,binary=True)
		cmp_or_die(orig,ret)

	def rand2file(self,name):
		of = name + '.out'
		dlen = 1024
		self.run_cmd(name,[of,str(1024),'threads=4','silent=1'],strip=False)
		d = read_from_tmpfile(cfg,of,binary=True)
		cmp_or_die(dlen,len(d))

	def strtob58(self,name):       self.run_cmd_out(name,getrandstr(16))
	def sha256x2(self,name):       self.run_cmd_out(name,getrandstr(16))
	def hexreverse(self,name):     self.run_cmd_out(name,getrandhex(24))
	def hexlify(self,name):        self.run_cmd_out(name,getrandstr(24))
	def b58tostr(self,name,f1,f2): self.run_cmd_chk(name,f1,f2)
	def hextob58(self,name):       self.run_cmd_out(name,getrandhex(32))
	def b58tohex(self,name,f1,f2): self.run_cmd_chk(name,f1,f2)
	def hextob32(self,name):       self.run_cmd_out(name,getrandhex(24))
	def b32tohex(self,name,f1,f2): self.run_cmd_chk(name,f1,f2)
	def b58randenc(self,name):
		ret = self.run_cmd_out(name,Return=True)
		ok_or_die(ret,is_b58_str,'base 58 string')
	def randhex(self,name):
		ret = self.run_cmd_out(name,Return=True)
		ok_or_die(ret,binascii.unhexlify,'hex string')
	def randwif(self,name):
		for n,k in enumerate(['','compressed=1']):
			ret = self.run_cmd_out(name,kwargs=k,Return=True,fn_idx=n+1)
			ok_or_die(ret,is_wif,'WIF key')
	def randpair(self,name):
		for n,k in enumerate(['','compressed=1']):
			wif,addr = self.run_cmd_out(name,kwargs=k,Return=True,fn_idx=n+1).split()
			ok_or_die(wif,is_wif,'WIF key',skip_ok=True)
			ok_or_die(addr,is_btc_addr,'Bitcoin address')
	def hex2wif(self,name,f1,f2,f3,f4):
		for n,fi,fo,k in (1,f1,f2,''),(2,f3,f4,'compressed=1'):
			ret = self.run_cmd_chk(name,fi,fo,kwargs=k)
	def wif2hex(self,name,f1,f2):
		for n,f,k in (1,f1,''),(2,f2,'compressed=1'):
			wif = read_from_file(f).split()[0]
			self.run_cmd_out(name,wif,kwargs=k,fn_idx=n)
	def wif2addr(self,name,f1,f2):
		for n,f,k in (1,f1,''),(2,f2,'compressed=1'):
			wif = read_from_file(f).split()[0]
			self.run_cmd_out(name,wif,kwargs=k,fn_idx=n)
	def addr2hexaddr(self,name,f1,f2):
		for n,f,m in (1,f1,''),(2,f2,'from compressed'):
			addr = read_from_file(f).split()[-1]
			self.run_cmd_out(name,addr,fn_idx=n,extra_msg=m)
	def hexaddr2addr(self,name,f1,f2,f3,f4):
		for n,fi,fo,m in (1,f1,f2,''),(2,f3,f4,'from compressed'):
			self.run_cmd_chk(name,fi,fo,extra_msg=m)
	def privhex2addr(self,name,f1,f2):
		key1 = read_from_file(f1).rstrip()
		key2 = read_from_file(f2).rstrip()
		for n,args in enumerate([[key1],[key2,'compressed=1']]):
			ret = self.run_cmd(name,args).rstrip()
			iaddr = read_from_tmpfile(cfg,'randpair%s.out' % (n+1)).split()[-1]
			cmp_or_die(iaddr,ret)
	def hex2mn(self,name):
		for n,size,m in(1,16,'128-bit'),(2,24,'192-bit'),(3,32,'256-bit'):
			hexnum = getrandhex(size)
			self.run_cmd_out(name,hexnum,fn_idx=n,extra_msg=m)
	def mn2hex(self,name,f1,f2,f3,f4,f5,f6):
		for f_i,f_o,m in (f1,f2,'128-bit'),(f3,f4,'192-bit'),(f5,f6,'256-bit'):
			self.run_cmd_chk(name,f_i,f_o,extra_msg=m)

	def getbalance(self,name):
		self.run_cmd_out(name,literal=True)
	def listaddresses(self,name):
		self.run_cmd_out(name,literal=True)
	def txview(self,name):
		fn = os.path.join(cfg['refdir'],cfg['txfile'])
		self.run_cmd_out(name,fn,literal=True)
	def addrfile_chksum(self,name):
		fn = os.path.join(cfg['refdir'],cfg['addrfile'])
		self.run_cmd_out(name,fn,literal=True,chkdata=cfg['addrfile_chk'])

# main()
import time
start_time = int(time.time())
ts = MMGenToolTestSuite()
mk_tmpdir(cfg)

if cmd_args:
	if len(cmd_args) != 1:
		die(1,'Only one command may be specified')

	cmd = cmd_args[0]
	if cmd in cmd_data:
		msg('Running tests for %s:' % cmd_data[cmd]['desc'])
		ts.do_cmds(cmd)
	elif cmd == 'clean':
		cleandir(cfg['tmpdir'])
		sys.exit()
	else:
		die(1,"'%s': unrecognized command" % cmd)
else:
	cleandir(cfg['tmpdir'])
	for cmd in cmd_data:
		msg('Running tests for %s:' % cmd_data[cmd]['desc'])
		ts.do_cmds(cmd)
		if cmd is not cmd_data.keys()[-1]: msg('')

t = int(time.time()) - start_time
msg(green(
	'All requested tests finished OK, elapsed time: %02i:%02i' % (t/60,t%60)))