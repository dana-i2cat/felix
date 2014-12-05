import pprint

COLORS={"reset":"\x1b[00m",
    "blue":   "\x1b[01;34m",
    "cyan":   "\x1b[01;36m",
    "green":  "\x1b[01;32m",
    "yellow": "\x1b[01;33m",
    "red":    "\x1b[01;05;37;41m"}

def print_call(method_name, params, res):
    # output stuff
    print COLORS["blue"],
    print "--> %s(%s)" % (method_name, params)
    print COLORS["cyan"],
    pprint.pprint(res, indent=4, width=20)
    print COLORS["reset"]
