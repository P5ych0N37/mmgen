#!/usr/bin/env python
#
# mmgen = Multi-Mode GENerator, command-line Bitcoin cold storage solution
# Copyright (C)2013-2018 The MMGen Project <mmgen@tuta.io>
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
util.py:  Low-level routines imported by other modules in the MMGen suite
"""

import sys,os,time,stat,re,unicodedata
from hashlib import sha256
from binascii import hexlify,unhexlify
from string import hexdigits
from mmgen.color import *
from mmgen.exception import *

def msg(s):    sys.stderr.write(s.encode('utf8') + '\n')
def msg_r(s):  sys.stderr.write(s.encode('utf8'))
def Msg(s):    sys.stdout.write(s.encode('utf8') + '\n')
def Msg_r(s):  sys.stdout.write(s.encode('utf8'))
def msgred(s): msg(red(s))
def rmsg(s):   msg(red(s))
def rmsg_r(s): msg_r(red(s))
def ymsg(s):   msg(yellow(s))
def ymsg_r(s): msg_r(yellow(s))
def gmsg(s):   msg(green(s))
def gmsg_r(s): msg_r(green(s))

def mmsg(*args):
	for d in args: Msg(repr(d))
def mdie(*args):
	mmsg(*args); sys.exit(0)

def die_wait(delay,ev=0,s=''):
	assert type(delay) == int
	assert type(ev) == int
	if s: msg(s)
	time.sleep(delay)
	sys.exit(ev)
def die_pause(ev=0,s=''):
	assert type(ev) == int
	if s: msg(s)
	raw_input('Press ENTER to exit')
	sys.exit(ev)
def die(ev=0,s=''):
	assert type(ev) == int
	if s: msg(s)
	sys.exit(ev)
def Die(ev=0,s=''):
	assert type(ev) == int
	if s: Msg(s)
	sys.exit(ev)

def rdie(ev=0,s=''): die(ev,red(s))
def ydie(ev=0,s=''): die(ev,yellow(s))
def hi(): sys.stdout.write(yellow('hi'))

def pformat(d):
	import pprint
	return pprint.PrettyPrinter(indent=4).pformat(d)
def pmsg(*args):
	if not args: return
	msg(pformat(args if len(args) > 1 else args[0]))
def pdie(*args):
	if not args: sys.exit(1)
	die(1,(pformat(args if len(args) > 1 else args[0])))

def set_for_type(val,refval,desc,invert_bool=False,src=None):
	src_str = (''," in '{}'".format(src))[bool(src)]
	if type(refval) == bool:
		v = unicode(val).lower()
		if v in ('true','yes','1'):          ret = True
		elif v in ('false','no','none','0'): ret = False
		else: die(1,"'{}': invalid value for '{}'{} (must be of type '{}')".format(
				val,desc,src_str,'bool'))
		if invert_bool: ret = not ret
	else:
		try:
			ret = type(refval)((val,not val)[invert_bool])
		except:
			die(1,u"'{}': invalid value for '{}'{} (must be of type '{}')".format(
				val,desc,src_str,type(refval).__name__))
	return ret

# From 'man dd':
# c=1, w=2, b=512, kB=1000, K=1024, MB=1000*1000, M=1024*1024,
# GB=1000*1000*1000, G=1024*1024*1024, and so on for T, P, E, Z, Y.

def parse_nbytes(nbytes):
	import re
	m = re.match(r'([0123456789]+)(.*)',nbytes)
	smap = ('c',1),('w',2),('b',512),('kB',1000),('K',1024),('MB',1000*1000),\
			('M',1024*1024),('GB',1000*1000*1000),('G',1024*1024*1024)
	if m:
		if m.group(2):
			for k,v in smap:
				if k == m.group(2):
					return int(m.group(1)) * v
			else:
				msg("Valid byte specifiers: '{}'".format("' '".join([i[0] for i in smap])))
		else:
			return int(nbytes)

	die(1,"'{}': invalid byte specifier".format(nbytes))

def check_or_create_dir(path):
	try:
		os.listdir(path)
	except:
		try:
			os.makedirs(path,0700)
		except:
			die(2,u"ERROR: unable to read or create path '{}'".format(path))

from mmgen.opts import opt

def qmsg(s,alt=None):
	if opt.quiet:
		if alt != None: msg(alt)
	else: msg(s)
def qmsg_r(s,alt=None):
	if opt.quiet:
		if alt != None: msg_r(alt)
	else: msg_r(s)
def vmsg(s,force=False):
	if opt.verbose or force: msg(s)
def vmsg_r(s,force=False):
	if opt.verbose or force: msg_r(s)
def Vmsg(s,force=False):
	if opt.verbose or force: Msg(s)
def Vmsg_r(s,force=False):
	if opt.verbose or force: Msg_r(s)
def dmsg(s):
	if opt.debug: msg(s)

def suf(arg,suf_type='s'):
	suf_types = { 's':  ('s',''), 'es': ('es','') }
	assert suf_type in suf_types
	t = type(arg)
	if t == int:
		n = arg
	elif any(issubclass(t,c) for c in (list,tuple,set,dict)):
		n = len(arg)
	else:
		die(2,'{}: invalid parameter for suf()'.format(arg))
	return suf_types[suf_type][n==1]

def get_extension(f):
	a,b = os.path.splitext(f)
	return ('',b[1:])[len(b) > 1]

def remove_extension(f,e):
	a,b = os.path.splitext(f)
	return (f,a)[len(b)>1 and b[1:]==e]

def make_chksum_N(s,nchars,sep=False):
	if nchars%4 or not (4 <= nchars <= 64): return False
	s = sha256(sha256(s).digest()).hexdigest().upper()
	sep = ('',' ')[bool(sep)]
	return sep.join([s[i*4:i*4+4] for i in range(nchars/4)])

def make_chksum_8(s,sep=False):
	from mmgen.obj import HexStr
	s = HexStr(sha256(sha256(s).digest()).hexdigest()[:8].upper(),case='upper')
	return '{} {}'.format(s[:4],s[4:]) if sep else s
def make_chksum_6(s):
	from mmgen.obj import HexStr
	if type(s) == unicode: s = s.encode('utf8')
	return HexStr(sha256(s).hexdigest()[:6])
def is_chksum_6(s): return len(s) == 6 and is_hex_str_lc(s)

def make_iv_chksum(s): return sha256(s).hexdigest()[:8].upper()

def splitN(s,n,sep=None):                      # always return an n-element list
	ret = s.split(sep,n-1)
	return ret + ['' for i in range(n-len(ret))]
def split2(s,sep=None): return splitN(s,2,sep) # always return a 2-element list
def split3(s,sep=None): return splitN(s,3,sep) # always return a 3-element list

def split_into_cols(col_wid,s):
	return ' '.join([s[col_wid*i:col_wid*(i+1)]
					for i in range(len(s)/col_wid+1)]).rstrip()

def screen_width(s):
	return len(s) + len([1 for ch in s if unicodedata.east_asian_width(ch) in ('F','W')])

def capfirst(s): # different from str.capitalize() - doesn't downcase any uc in string
	return s if len(s) == 0 else s[0].upper() + s[1:]

def decode_timestamp(s):
# 	with open('/etc/timezone') as f:
# 		tz_save = f.read().rstrip()
	os.environ['TZ'] = 'UTC'
	ts = time.strptime(s,'%Y%m%d_%H%M%S')
	t = time.mktime(ts)
# 	os.environ['TZ'] = tz_save
	return int(t)

def make_timestamp(secs=None):
	t = int(secs) if secs else time.time()
	tv = time.gmtime(t)[:6]
	return '{:04d}{:02d}{:02d}_{:02d}{:02d}{:02d}'.format(*tv)

def make_timestr(secs=None):
	t = int(secs) if secs else time.time()
	tv = time.gmtime(t)[:6]
	return '{:04d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}'.format(*tv)

def secs_to_dhms(secs):
	dsecs = secs/3600
	return '{}{:02d}:{:02d}:{:02d}'.format(
		('','{} day{}, '.format(dsecs/24,suf(dsecs/24)))[dsecs > 24],
		dsecs % 24, (secs/60) % 60, secs % 60)

def secs_to_hms(secs):
	return '{:02d}:{:02d}:{:02d}'.format(secs/3600, (secs/60) % 60, secs % 60)

def secs_to_ms(secs):
	return '{:02d}:{:02d}'.format(secs/60, secs % 60)

def is_int(s):
	try:
		int(str(s))
		return True
	except:
		return False

# https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
# https://tools.ietf.org/html/rfc4648
def is_hex_str(s):    return set(list(s.lower())) <= set(list(hexdigits.lower()))
def is_hex_str_lc(s): return set(list(s))         <= set(list(hexdigits.lower()))
def is_hex_str_uc(s): return set(list(s))         <= set(list(hexdigits.upper()))
def is_b58_str(s):    return set(list(s))         <= set(baseconv.digits['b58'])
def is_b32_str(s):    return set(list(s))         <= set(baseconv.digits['b32'])

def is_ascii(s,enc='ascii'):
	try:    s.decode(enc)
	except: return False
	else:   return True

def is_utf8(s): return is_ascii(s,enc='utf8')

class baseconv(object):

	mn_base = 1626 # tirosh list is 1633 words long!
	digits = {
		'electrum': tuple(__import__('mmgen.mn_electrum',fromlist=['words']).words.split()),
		'tirosh': tuple(__import__('mmgen.mn_tirosh',fromlist=['words']).words.split()[:mn_base]),
		'b58': tuple('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'),
		'b32': tuple('ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'),
		'b16': tuple('0123456789abcdef'),
		'b10': tuple('0123456789'),
		'b8':  tuple('01234567'),
	}
	wl_chksums = {
		'electrum': '5ca31424',
		'tirosh':   '48f05e1f', # tirosh truncated to mn_base (1626)
		# 'tirosh1633': '1a5faeff'
	}
	b58pad_lens =     [(16,22), (24,33), (32,44)]
	b58pad_lens_rev = [(v,k) for k,v in b58pad_lens]

	@classmethod
	def b58encode(cls,s,pad=None):
		pad = cls.get_pad(s,pad,'en',cls.b58pad_lens,[bytes])
		return cls.fromhex(hexlify(s),'b58',pad=pad,tostr=True)

	@classmethod
	def b58decode(cls,s,pad=None):
		pad = cls.get_pad(s,pad,'de',cls.b58pad_lens_rev,[bytes,unicode])
		return unhexlify(cls.tohex(s,'b58',pad=pad*2 if pad else None))

	@staticmethod
	def get_pad(s,pad,op,pad_map,ok_types):
		m = "b58{}code() input must be one of {}, not '{}'"
		assert type(s) in ok_types, m.format(op,repr([t.__name__ for t in ok_types]),type(s).__name__)
		if pad:
			assert type(pad) == bool, "'pad' must be boolean type"
			d = dict(pad_map)
			assert len(s) in d, 'Invalid data length for b58{}code(pad=True)'.format(op)
			return d[len(s)]
		else:
			return None

	@classmethod
	def get_wordlist_chksum(cls,wl_id):
		return sha256(' '.join(cls.digits[wl_id])).hexdigest()[:8]

	@classmethod
	def check_wordlists(cls):
		for k,v in cls.wl_chksums.items(): assert cls.get_wordlist_chksum(k) == v

	@classmethod
	def check_wordlist(cls,wl_id):

		wl = baseconv.digits[wl_id]
		Msg('Wordlist: {}\nLength: {} words'.format(capfirst(wl_id),len(wl)))
		new_chksum = cls.get_wordlist_chksum(wl_id)

		a,b = 'generated checksum','saved checksum'
		compare_chksums(new_chksum,a,cls.wl_chksums[wl_id],b,die_on_fail=True)

		Msg('Checksum {} matches'.format(new_chksum))
		Msg('List is sorted') if tuple(sorted(wl)) == wl else die(3,'ERROR: List is not sorted!')


	@classmethod
	def tohex(cls,words_arg,wl_id,pad=None):

		words = words_arg if type(words_arg) in (list,tuple) else tuple(words_arg.strip())

		wl = cls.digits[wl_id]
		base = len(wl)

		if not set(words) <= set(wl):
			die(2,'{} is not in {} (base{}) format'.format(repr(words_arg),wl_id,base))

		deconv =  [wl.index(words[::-1][i])*(base**i) for i in range(len(words))]
		ret = ('{:0{w}x}'.format(sum(deconv),w=pad or 0))
		return ('','0')[len(ret) % 2] + ret

	@classmethod
	def fromhex(cls,hexnum,wl_id,pad=None,tostr=False):

		hexnum = hexnum.strip()
		if not is_hex_str(hexnum):
			die(2,"'{}': not a hexadecimal number".format(hexnum))

		wl = cls.digits[wl_id]
		base = len(wl)
		num,ret = int(hexnum,16),[]
		while num:
			ret.append(num % base)
			num /= base
		o = [wl[n] for n in [0] * ((pad or 0)-len(ret)) + ret[::-1]]
		return ''.join(o) if tostr else o

baseconv.check_wordlists()

def match_ext(addr,ext):
	return addr.split('.')[-1] == ext

def file_exists(f):
	try:
		os.stat(f)
		return True
	except:
		return False

def file_is_readable(f):
	from stat import S_IREAD
	try:
		assert os.stat(f).st_mode & S_IREAD
	except:
		return False
	else:
		return True

def get_from_brain_opt_params():
	l,p = opt.from_brain.split(',')
	return(int(l),p)

def pretty_hexdump(data,gw=2,cols=8,line_nums=False):
	r = (0,1)[bool(len(data) % gw)]
	return ''.join(
		[
			('' if (line_nums == False or i % cols) else '{:06x}: '.format(i*gw)) +
				hexlify(data[i*gw:i*gw+gw]) + ('\n',' ')[bool((i+1) % cols)]
					for i in range(len(data)/gw + r)
		]
	).rstrip() + '\n'

def decode_pretty_hexdump(data):
	from string import hexdigits
	pat = r'^[{}]+:\s+'.format(hexdigits)
	lines = [re.sub(pat,'',l) for l in data.splitlines()]
	try:
		return unhexlify(''.join((''.join(lines).split())))
	except:
		msg('Data not in hexdump format')
		return False

def strip_comments(line):
	return re.sub(ur'\s+$',u'',re.sub(ur'#.*',u'',line,1))

def remove_comments(lines):
	return [m for m in [strip_comments(l) for l in lines] if m != '']

from mmgen.globalvars import g

def start_mscolor():
	try:
		import colorama
		colorama.init(strip=True,convert=True)
	except:
		msg('Import of colorama module failed')

def get_hash_params(hash_preset):
	if hash_preset in g.hash_presets:
		return g.hash_presets[hash_preset] # N,p,r,buflen
	else: # Shouldn't be here
		die(3,"{}: invalid 'hash_preset' value".format(hash_preset))

def compare_chksums(chk1,desc1,chk2,desc2,hdr='',die_on_fail=False,verbose=False):

	if not chk1 == chk2:
		fs = "{} ERROR: {} checksum ({}) doesn't match {} checksum ({})"
		m = fs.format((hdr+':\n   ' if hdr else 'CHECKSUM'),desc2,chk2,desc1,chk1)
		if die_on_fail:
			die(3,m)
		else:
			vmsg(m,force=verbose)
			return False

	vmsg('{} checksum OK ({})'.format(capfirst(desc1),chk1))
	return True

def compare_or_die(val1, desc1, val2, desc2, e='Error'):
	if cmp(val1,val2):
		die(3,"{}: {} ({}) doesn't match {} ({})".format(e,desc2,val2,desc1,val1))
	dmsg('{} OK ({})'.format(capfirst(desc2),val2))
	return True

def open_file_or_exit(filename,mode,silent=False):
	try:
		f = open(filename, mode)
	except:
		op = ('writing','reading')['r' in mode]
		die(2,("Unable to open file '{}' for {}".format(filename,op),'')[silent])
	return f

def check_file_type_and_access(fname,ftype,blkdev_ok=False):

	a = ((os.R_OK,'read'),(os.W_OK,'writ'))
	access,m = a[ftype in ('output file','output directory')]

	ok_types = [
		(stat.S_ISREG,'regular file'),
		(stat.S_ISLNK,'symbolic link')
	]
	if blkdev_ok: ok_types.append((stat.S_ISBLK,'block device'))
	if ftype == 'output directory': ok_types = [(stat.S_ISDIR, 'output directory')]

	try: mode = os.stat(fname).st_mode
	except:
		die(1,u"Unable to stat requested {} '{}'".format(ftype,fname))

	for t in ok_types:
		if t[0](mode): break
	else:
		die(1,"Requested {} '{}' is not a {}".format(ftype,fname,' or '.join([t[1] for t in ok_types])))

	if not os.access(fname, access):
		die(1,"Requested {} '{}' is not {}able by you".format(ftype,fname,m))

	return True

def check_infile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'input file',blkdev_ok=blkdev_ok)
def check_outfile(f,blkdev_ok=False):
	return check_file_type_and_access(f,'output file',blkdev_ok=blkdev_ok)
def check_outdir(f):
	return check_file_type_and_access(f,'output directory')
def make_full_path(outdir,outfile):
	return os.path.normpath(os.path.join(outdir, os.path.basename(outfile)))

def get_seed_file(cmd_args,nargs,invoked_as=None):
	from mmgen.filename import find_file_in_dir
	from mmgen.seed import Wallet

	wf = find_file_in_dir(Wallet,g.data_dir)

	wd_from_opt = bool(opt.hidden_incog_input_params or opt.in_fmt) # have wallet data from opt?

	import mmgen.opts as opts
	if len(cmd_args) + (wd_from_opt or bool(wf)) < nargs:
		if not wf:
			msg('No default wallet found, and no other seed source was specified')
		opts.usage()
	elif len(cmd_args) > nargs:
		opts.usage()
	elif len(cmd_args) == nargs and wf and invoked_as != 'gen':
		msg('Warning: overriding default wallet with user-supplied wallet')

	if cmd_args or wf:
		check_infile(cmd_args[0] if cmd_args else wf)

	return cmd_args[0] if cmd_args else (wf,None)[wd_from_opt]

def get_new_passphrase(desc,passchg=False):

	w = '{}passphrase for {}'.format(('','new ')[bool(passchg)], desc)
	if opt.passwd_file:
		pw = ' '.join(get_words_from_file(opt.passwd_file,w))
	elif opt.echo_passphrase:
		pw = ' '.join(get_words_from_user('Enter {}: '.format(w)))
	else:
		for i in range(g.passwd_max_tries):
			pw = ' '.join(get_words_from_user('Enter {}: '.format(w)))
			pw2 = ' '.join(get_words_from_user('Repeat passphrase: '))
			dmsg('Passphrases: [{}] [{}]'.format(pw,pw2))
			if pw == pw2:
				vmsg('Passphrases match'); break
			else: msg('Passphrases do not match.  Try again.')
		else:
			die(2,'User failed to duplicate passphrase in {} attempts'.format(g.passwd_max_tries))

	if pw == '': qmsg('WARNING: Empty passphrase')
	return pw

def confirm_or_raise(message,q,expect='YES',exit_msg='Exiting at user request'):
	m = message.strip()
	if m: msg(m)
	a = q+'  ' if q[0].isupper() else 'Are you sure you want to {}?\n'.format(q)
	b = "Type uppercase '{}' to confirm: ".format(expect)
	if my_raw_input(a+b).strip() != expect:
		raise UserNonConfirmation,exit_msg

def write_data_to_file( outfile,data,desc='data',
						ask_write=False,
						ask_write_prompt='',
						ask_write_default_yes=True,
						ask_overwrite=True,
						ask_tty=True,
						no_tty=False,
						silent=False,
						binary=False,
						ignore_opt_outdir=False,
						check_data=False,
						cmp_data=None):

	if silent: ask_tty = ask_overwrite = False
	if opt.quiet: ask_overwrite = False

	if ask_write_default_yes == False or ask_write_prompt:
		ask_write = True

	if not binary and type(data) == unicode:
		data = data.encode('utf8')

	def do_stdout():
		qmsg('Output to STDOUT requested')
		if sys.stdout.isatty():
			if no_tty:
				die(2,'Printing {} to screen is not allowed'.format(desc))
			if (ask_tty and not opt.quiet) or binary:
				confirm_or_raise('','output {} to screen'.format(desc))
		else:
			try:    of = os.readlink('/proc/{}/fd/1'.format(os.getpid())) # Linux
			except: of = None # Windows

			if of:
				if of[:5] == 'pipe:':
					if no_tty:
						die(2,'Writing {} to pipe is not allowed'.format(desc))
					if ask_tty and not opt.quiet:
						confirm_or_raise('','output {} to pipe'.format(desc))
						msg('')
				of2,pd = os.path.relpath(of),os.path.pardir
				msg(u"Redirecting output to file '{}'".format((of2,of)[of2[:len(pd)] == pd]))
			else:
				msg('Redirecting output to file')

		if binary and g.platform == 'win':
			import msvcrt
			msvcrt.setmode(sys.stdout.fileno(),os.O_BINARY)

		sys.stdout.write(data)

	def do_file(outfile,ask_write_prompt):
		if opt.outdir and not ignore_opt_outdir and not os.path.isabs(outfile):
			outfile = make_full_path(opt.outdir,outfile)

		if ask_write:
			if not ask_write_prompt: ask_write_prompt = 'Save {}?'.format(desc)
			if not keypress_confirm(ask_write_prompt,
						default_yes=ask_write_default_yes):
				die(1,'{} not saved'.format(capfirst(desc)))

		hush = False
		if file_exists(outfile) and ask_overwrite:
			q = u"File '{}' already exists\nOverwrite?".format(outfile)
			confirm_or_raise('',q)
			msg(u"Overwriting file '{}'".format(outfile))
			hush = True

		# not atomic, but better than nothing
		# if cmp_data is empty, file can be either empty or non-existent
		if check_data:
			try:
				d = open(outfile,('r','rb')[bool(binary)]).read()
			except:
				d = ''
			finally:
				if d != cmp_data:
					m = u"{} in file '{}' has been altered by some other program!  Aborting file write"
					die(3,m.format(desc,outfile))

		f = open_file_or_exit(outfile,('w','wb')[bool(binary)])
		try:
			f.write(data)
		except:
			die(2,u"Failed to write {} to file '{}'".format(desc,outfile))
		f.close

		if not (hush or silent):
			msg(u"{} written to file '{}'".format(capfirst(desc),outfile))

		return True

	if opt.stdout or outfile in ('','-'):
		do_stdout()
	elif sys.stdin.isatty() and not sys.stdout.isatty():
		do_stdout()
	else:
		do_file(outfile,ask_write_prompt)

def get_words_from_user(prompt):
	# split() also strips
	words = my_raw_input(prompt, echo=opt.echo_passphrase).split()
	dmsg(u'Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_words_from_file(infile,desc,silent=False):
	if not silent:
		qmsg(u"Getting {} from file '{}'".format(desc,infile))
	f = open_file_or_exit(infile, 'r')
	try: words = f.read().decode('utf8').split() # split() also strips
	except: die(1,'{} data must be UTF-8 encoded.'.format(capfirst(desc)))
	f.close()
	dmsg(u'Sanitized input: [{}]'.format(' '.join(words)))
	return words

def get_words(infile,desc,prompt):
	if infile:
		return get_words_from_file(infile,desc)
	else:
		return get_words_from_user(prompt)

def mmgen_decrypt_file_maybe(fn,desc='',silent=False):
	d = get_data_from_file(fn,desc,binary=True,silent=silent)
	have_enc_ext = get_extension(fn) == g.mmenc_ext
	if have_enc_ext or not is_utf8(d):
		m = ('Attempting to decrypt','Decrypting')[have_enc_ext]
		msg(u"{} {} '{}'".format(m,desc,fn))
		from mmgen.crypto import mmgen_decrypt_retry
		d = mmgen_decrypt_retry(d,desc)
	return d

def get_lines_from_file(fn,desc='',trim_comments=False,silent=False):
	dec = mmgen_decrypt_file_maybe(fn,desc,silent=silent)
	ret = dec.decode('utf8').splitlines() # DOS-safe
	if trim_comments: ret = remove_comments(ret)
	dmsg(u"Got {} lines from file '{}'".format(len(ret),fn))
	return ret

def get_data_from_user(desc='data',silent=False): # user input MUST be UTF-8
	p = ('',u'Enter {}: '.format(desc))[g.stdin_tty]
	data = my_raw_input(p,echo=opt.echo_passphrase)
	dmsg(u'User input: [{}]'.format(data))
	return data

def get_data_from_file(infile,desc='data',dash=False,silent=False,binary=False,require_utf8=False):
	if dash and infile == '-': return sys.stdin.read()
	if not opt.quiet and not silent and desc:
		qmsg(u"Getting {} from file '{}'".format(desc,infile))
	f = open_file_or_exit(infile,('r','rb')[bool(binary)],silent=silent)
	data = f.read()
	f.close()
	if require_utf8:
		try: data = data.decode('utf8')
		except: die(1,'{} data must be UTF-8 encoded.'.format(capfirst(desc)))
	return data

def pwfile_reuse_warning():
	if 'passwd_file_used' in globals():
		qmsg(u"Reusing passphrase from file '{}' at user request".format(opt.passwd_file))
		return True
	globals()['passwd_file_used'] = True
	return False

def get_mmgen_passphrase(desc,passchg=False):
	prompt ='Enter {}passphrase for {}: '.format(('','old ')[bool(passchg)],desc)
	if opt.passwd_file:
		pwfile_reuse_warning()
		return ' '.join(get_words_from_file(opt.passwd_file,'passphrase'))
	else:
		return ' '.join(get_words_from_user(prompt))

def my_raw_input(prompt,echo=True,insert_txt='',use_readline=True):

	try: import readline
	except: use_readline = False # Windows

	if use_readline and sys.stdout.isatty():
		def st_hook(): readline.insert_text(insert_txt)
		readline.set_startup_hook(st_hook)
	else:
		msg_r(prompt)
		prompt = ''

	from mmgen.term import kb_hold_protect
	kb_hold_protect()
	if echo or not sys.stdin.isatty():
		reply = raw_input(prompt.encode('utf8'))
	else:
		from getpass import getpass
		reply = getpass(prompt.encode('utf8'))
	kb_hold_protect()

	try:
		return reply.strip().decode('utf8')
	except:
		die(1,'User input must be UTF-8 encoded.')

def keypress_confirm(prompt,default_yes=False,verbose=False,no_nl=False):

	from mmgen.term import get_char

	q = ('(y/N)','(Y/n)')[bool(default_yes)]
	p = u'{} {}: '.format(prompt,q)
	nl = ('\n','\r{}\r'.format(' '*len(p)))[no_nl]

	if opt.accept_defaults:
		msg(p)
		return (False,True)[default_yes]

	while True:
		reply = get_char(p).strip('\n\r')
		if not reply:
			if default_yes: msg_r(nl); return True
			else:           msg_r(nl); return False
		elif reply in 'yY': msg_r(nl); return True
		elif reply in 'nN': msg_r(nl); return False
		else:
			if verbose: msg('\nInvalid reply')
			else: msg_r('\r')

def prompt_and_get_char(prompt,chars,enter_ok=False,verbose=False):

	from mmgen.term import get_char

	while True:
		reply = get_char('{}: '.format(prompt)).strip('\n\r')

		if reply in chars or (enter_ok and not reply):
			msg('')
			return reply

		if verbose: msg('\nInvalid reply')
		else: msg_r('\r')

def do_pager(text):

	pagers = ['less','more']
	end_msg = '\n(end of text)\n\n'
	# --- Non-MSYS Windows code deleted ---
	# raw, chop, horiz scroll 8 chars, disable buggy line chopping in MSYS
	os.environ['LESS'] = (('--shift 8 -RS'),('-cR -#1'))[g.platform=='win']

	if 'PAGER' in os.environ and os.environ['PAGER'] != pagers[0]:
		pagers = [os.environ['PAGER']] + pagers

	for pager in pagers:
		try:
			from subprocess import Popen,PIPE
			p = Popen([pager],stdin=PIPE,shell=False)
		except: pass
		else:
			p.communicate(text.encode('utf8')+(end_msg,'')[pager=='less'])
			msg_r('\r')
			break
	else: Msg(text+end_msg)

def do_license_msg(immed=False):

	if opt.quiet or g.no_license or opt.yes or not g.stdin_tty: return

	import mmgen.license as gpl

	p = "Press 'w' for conditions and warranty info, or 'c' to continue:"
	msg(gpl.warning)
	prompt = '{} '.format(p.strip())

	from mmgen.term import get_char

	while True:
		reply = get_char(prompt, immed_chars=('','wc')[bool(immed)])
		if reply == 'w':
			do_pager(gpl.conditions)
		elif reply == 'c':
			msg(''); break
		else:
			msg_r('\r')
	msg('')

def get_daemon_cfg_options(cfg_keys):
	cfg_file = os.path.join(g.proto.daemon_data_dir,g.proto.name+'.conf')
	try:
		lines = get_lines_from_file(cfg_file,'',silent=bool(opt.quiet))
		kv_pairs = [split2(str(line).translate(None,'\t '),'=') for line in lines]
		cfg = dict([(k,v) for k,v in kv_pairs if k in cfg_keys])
	except:
		vmsg("Warning: '{}' does not exist or is unreadable".format(cfg_file))
		cfg = {}
	for k in set(cfg_keys) - set(cfg.keys()): cfg[k] = ''
	return cfg

def get_coin_daemon_auth_cookie():
	f = os.path.join(g.proto.daemon_data_dir,g.proto.daemon_data_subdir,'.cookie')
	return get_lines_from_file(f,'')[0] if file_is_readable(f) else ''

def rpc_init_parity():

	def resolve_token_arg(token_arg):
		from mmgen.tw import TrackingWallet
		from mmgen.obj import CoinAddr
		from mmgen.altcoins.eth.contract import Token

		try:    addr = CoinAddr(token_arg,on_fail='raise')
		except: addr = TrackingWallet().sym2addr(token_arg)
		else:   Token(addr) # test for presence in blockchain

		if not addr:
			m = "'{}': unrecognized token symbol"
			raise UnrecognizedTokenSymbol,m.format(token_arg)

		sym = Token(addr).symbol().upper()
		vmsg('ERC20 token resolved: {} ({})'.format(addr,sym))
		return addr,sym

	from mmgen.rpc import EthereumRPCConnection
	g.rpch = EthereumRPCConnection(
				g.rpc_host or 'localhost',
				g.rpc_port or g.proto.rpc_port)

	g.rpch.daemon_version = g.rpch.parity_versionInfo()['version'] # fail immediately if daemon is geth
	g.rpch.coin_amt_type = str
	g.chain = g.rpch.parity_chain().replace(' ','_')
	if g.token:
		(g.token,g.dcoin) = resolve_token_arg(g.token)

	g.rpch.caps = ()
	return g.rpch

def rpc_init_bitcoind():

	def check_chainfork_mismatch(conn):
		block0 = conn.getblockhash(0)
		latest = conn.getblockcount()
		try:
			assert block0 == g.proto.block0,'Incorrect Genesis block for {}'.format(g.proto.__name__)
			for fork in g.proto.forks:
				if fork[0] == None or latest < fork[0]: break
				assert conn.getblockhash(fork[0]) == fork[1], (
					'Bad block hash at fork block {}. Is this the {} chain?'.format(fork[0],fork[2].upper()))
		except Exception as e:
			die(2,"{}\n'{c}' requested, but this is not the {c} chain!".format(e.message,c=g.coin))

	def check_chaintype_mismatch():
		try:
			if g.regtest: assert g.chain == 'regtest','--regtest option selected, but chain is not regtest'
			if g.testnet: assert g.chain != 'mainnet','--testnet option selected, but chain is mainnet'
			if not g.testnet: assert g.chain == 'mainnet','mainnet selected, but chain is not mainnet'
		except Exception as e:
			die(1,'{}\nChain is {}!'.format(e.message,g.chain))

	cfg = get_daemon_cfg_options(('rpcuser','rpcpassword'))

	from mmgen.rpc import CoinDaemonRPCConnection
	conn = CoinDaemonRPCConnection(
				g.rpc_host or 'localhost',
				g.rpc_port or g.proto.rpc_port,
				g.rpc_user or cfg['rpcuser'], # MMGen's rpcuser,rpcpassword override coin daemon's
				g.rpc_password or cfg['rpcpassword'],
				auth_cookie=get_coin_daemon_auth_cookie())

	if g.bob or g.alice:
		import regtest as rt
		rt.user(('alice','bob')[g.bob],quiet=True)
	conn.daemon_version = int(conn.getnetworkinfo()['version'])
	conn.coin_amt_type = (float,str)[conn.daemon_version>=120000]
	g.chain = conn.getblockchaininfo()['chain']
	if g.chain != 'regtest': g.chain += 'net'
	assert g.chain in g.chains
	check_chaintype_mismatch()

	if g.chain == 'mainnet': # skip this for testnet, as Genesis block may change
		check_chainfork_mismatch(conn)

	conn.caps = ()
	for func,cap in (
		('setlabel','label_api'),
		('signrawtransactionwithkey','sign_with_key') ):
		if len(conn.request('help',func).split('\n')) > 3:
			conn.caps += (cap,)
	return conn

def rpc_init(reinit=False):
	if not 'rpc' in g.proto.mmcaps:
		die(1,'Coin daemon operations not supported for coin {}!'.format(g.coin))
	if g.rpch != None and not reinit: return g.rpch
	g.rpch = globals()['rpc_init_'+g.proto.daemon_family]()
	return g.rpch

def format_par(s,indent=0,width=80,as_list=False):
	words,lines = s.split(),[]
	assert width >= indent + 4,'width must be >= indent + 4'
	while words:
		line = ''
		while len(line) <= (width-indent) and words:
			if line and len(line) + len(words[0]) + 1 > width-indent: break
			line += ('',' ')[bool(line)] + words.pop(0)
		lines.append(' '*indent + line)
	return lines if as_list else '\n'.join(lines) + '\n'

# module loading magic for tx.py and tw.py
def altcoin_subclass(cls,mod_id,cls_name):
	if cls.__name__ != cls_name: return cls
	mod_dir = g.proto.base_coin.lower()
	pname = g.proto.class_pfx if hasattr(g.proto,'class_pfx') else capfirst(g.proto.name)
	tname = 'Token' if g.token else ''
	e1 = 'from mmgen.altcoins.{}.{} import {}{}{}'.format(mod_dir,mod_id,pname,tname,cls_name)
	e2 = 'cls = {}{}{}'.format(pname,tname,cls_name)
	try: exec e1; exec e2; return cls
	except ImportError: return cls

# decorator for TrackingWallet
def write_mode(orig_func):
	def f(self,*args,**kwargs):
		if self.mode != 'w':
			m = '{} opened in read-only mode: cannot execute method {}()'
			die(1,m.format(type(self).__name__,locals()['orig_func'].__name__))
		return orig_func(self,*args,**kwargs)
	return f
