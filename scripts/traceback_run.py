#!/usr/bin/env python
import sys,traceback,os
sys.path.insert(0,'.')

if 'TMUX' in os.environ: del os.environ['TMUX']
os.environ['MMGEN_TRACEBACK'] = '1'

tb_source = open(sys.argv[1])
tb_file = os.path.join(os.environ['PWD'],'my.err')

def process_exception():
	l = traceback.format_exception(*sys.exc_info())
	l_save = l[:]
	exc = l.pop()
	if exc[:11] == 'SystemExit:': l.pop()
	def red(s):    return '{e}[31;1m{}{e}[0m'.format(s,e='\033')
	def yellow(s): return '{e}[33;1m{}{e}[0m'.format(s,e='\033')
	sys.stdout.write('{}{}'.format(yellow(''.join(l)),red(exc)))
	with open(tb_file,'w') as f:
		f.write(''.join(l_save))

try:
	sys.argv.pop(0)
	exec tb_source
except SystemExit as e:
	if e.code != 0:
		process_exception()
	sys.exit(e.code)
except:
	process_exception()
	sys.exit(1)
