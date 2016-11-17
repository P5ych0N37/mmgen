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
mmgen-addrgen: Generate a series or range of addresses from an MMGen
               deterministic wallet
"""

from mmgen.common import *
from mmgen.crypto import *
from mmgen.addr import *
from mmgen.seed import SeedSource

if sys.argv[0].split('-')[-1] == 'keygen':
	gen_what = 'keys'
	opt_filter = None
	note1 = """
By default, both addresses and secret keys are generated.
""".strip()
else:
	gen_what = 'addresses'
	opt_filter = 'hbcdeiHOKlpzPqrSv-'
	note1 = """
If available, the external 'keyconv' program will be used for address
generation.
""".strip()

opts_data = {
	'sets': [('print_checksum',True,'quiet',True)],
	'desc': """Generate a range or list of {what} from an {pnm} wallet,
                  mnemonic, seed or password""".format(what=gen_what,pnm=g.proj_name),
	'usage':'[opts] [infile] <address range or list>',
	'options': """
-h, --help            Print this help message
--, --longhelp        Print help message for long options (common options)
-A, --no-addresses    Print only secret keys, no addresses
-c, --print-checksum  Print address list checksum and exit
-d, --outdir=      d  Output files to directory 'd' instead of working dir
-e, --echo-passphrase Echo passphrase or mnemonic to screen upon entry
-i, --in-fmt=      f  Input is from wallet format 'f' (see FMT CODES below)
-H, --hidden-incog-input-params=f,o  Read hidden incognito data from file
                      'f' at offset 'o' (comma-separated)
-O, --old-incog-fmt   Specify old-format incognito input
-K, --key-generator=m Use method 'm' for public key generation
                      Options: {kgs} (default: {kg})
-l, --seed-len=    l  Specify wallet seed length of 'l' bits.  This option
                      is required only for brainwallet and incognito inputs
                      with non-standard (< {g.seed_len}-bit) seed lengths
-p, --hash-preset= p  Use the scrypt hash parameters defined by preset 'p'
                      for password hashing (default: '{g.hash_preset}')
-z, --show-hash-presets Show information on available hash presets
-P, --passwd-file= f  Get wallet passphrase from file 'f'
-q, --quiet           Produce quieter output; suppress some warnings
-r, --usr-randchars=n Get 'n' characters of additional randomness from user
                      (min={g.min_urandchars}, max={g.max_urandchars}, default={g.usr_randchars})
-S, --stdout          Print {what} to stdout
-v, --verbose         Produce more verbose output
-x, --b16             Print secret keys in hexadecimal too
""".format(
	seed_lens=', '.join([str(i) for i in g.seed_lens]),
	pnm=g.proj_name,
	kgs=' '.join(['{}:{}'.format(n,k) for n,k in enumerate(g.key_generators,1)]),
	kg=g.key_generator,
	what=gen_what,g=g
),
	'notes': """

Addresses are given in a comma-separated list.  Hyphen-separated ranges are
also allowed.

{n}

{o.pw_note}

{o.bw_note}

FMT CODES:
  {f}
""".format(
		n=note1,
		f='\n  '.join(SeedSource.format_fmt_codes().splitlines()),
		o=opts
	)
}

cmd_args = opts.init(opts_data,add_opts=['b16'],opt_filter=opt_filter)

nargs = 2
if len(cmd_args) < nargs and not (opt.hidden_incog_input_params or opt.in_fmt):
	opts.usage()
elif len(cmd_args) > nargs - int(bool(opt.hidden_incog_input_params)):
	opts.usage()

addridxlist_str = cmd_args.pop()
idxs = AddrIdxList(fmt_str=addridxlist_str)

do_license_msg()

ss = SeedSource(*cmd_args) # *(cmd_args[0] if cmd_args else [])

i = (gen_what=='addresses') or bool(opt.no_addresses)*2
al = (KeyAddrList,AddrList,KeyList)[i](seed=ss.seed,addr_idxs=idxs)
al.format()

if al.gen_addrs and opt.print_checksum:
	Die(0,al.checksum)

if al.gen_keys and keypress_confirm('Encrypt key list?'):
	al.encrypt()

al.write_to_file()
