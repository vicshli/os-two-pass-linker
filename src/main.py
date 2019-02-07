import os, sys, re
from collections import ChainMap

DEF = "def"
USE = "use"
PROG = "prog"
BASE = "base"
MOD_COUNT = "mod_count"
MODS = "mods"
TYPE = "type"
WORD = "word"
PROG_ERR = "error"
PROG_SYM_USED_FLAG = "used_flag"
SYM_VAL = "symbol_value"
SYM_ERR = "symbol_error_msg"

def print_list(l):
    for item in l: 
        print(item)

def get_input():
    print("Paste your input, then enter Ctrl-D to exit input mode:")
    user_input = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        user_input.append(line)
    user_input = " ".join(user_input).split()
    return user_input

def uin_frist_pass(uin): 
    mods = { MOD_COUNT: int(uin[0]), MODS: [] }
    buffer = uin[1:]
    base_accum = 0
    syms = {}
    for _ in range(mods[MOD_COUNT]): 
        mod, buffer, base_accum, syms = parse_mod(buffer, base_accum, syms)
        mods[MODS].append(mod)
    return mods, syms

def parse_mod(mod_in, base, sym_table): 
    '''
    Input: a string containing a module
    Return: the remaining string after a module is parsed and removed from str.  
    '''
    mod_out = { DEF: {}, USE: {}, PROG: {} }
    cur = 0

    mod_out[DEF], cur, sym_table = p_mod_def(mod_in, cur, sym_table, base)
    mod_out[USE], cur = p_mod_use(mod_in, cur)
    mod_out[PROG], cur = p_mod_prog(mod_in, cur, base)

    base += mod_out[PROG]['prog_count']

    return mod_out, mod_in[cur:], base, sym_table

def p_mod_def(mod, cur, sym_table, base): 
    COUNT = 'def_count'
    LIST = 'def_list'
    def_list = { COUNT: int(mod[cur]), LIST: {} }
    cur += 1
    while cur < len(mod):
        if len(def_list[LIST]) >= def_list[COUNT]:
            break
        else:
            sym = mod[cur]
            sym_val = mod[cur + 1]
            def_list[LIST][sym] = int(sym_val)
            if sym in sym_table: 
                sym_table[sym][SYM_ERR] = "Error: This variable is multiply defined; last value used."
            else:
                sym_table[sym] = { SYM_VAL: None, SYM_ERR: "" }
            sym_table[sym][SYM_VAL] = int(sym_val) + base
            cur += 2
    return def_list, cur, sym_table

def p_mod_use(mod, cur): 
    COUNT = 'use_count'
    LIST = 'use_list'
    use_list = { COUNT: int(mod[cur]), LIST: {} }
    cur += 1
    while cur < len(mod):
        if len(use_list[LIST]) >= use_list[COUNT]: 
            break
        else:
            use_list[LIST][mod[cur]] = int(mod[cur + 1])
            cur += 2
    return use_list, cur

def p_mod_prog(mod, cur, base): 
    COUNT = 'prog_count'
    LIST = 'prog_list'
    prog_list = { COUNT: int(mod[cur]), BASE: base, LIST: [] }
    cur += 1
    while cur < len(mod):
        if len(prog_list[LIST]) >= prog_list[COUNT]: 
            break
        else: 
            prog_list[LIST].append({ 
                TYPE: mod[cur], 
                WORD: int(mod[cur + 1]), 
                PROG_SYM_USED_FLAG: False,
                PROG_ERR: ""
            })
            cur += 2
    return prog_list, cur

def process_external_addr(old_addr, new_addr):
    first_digit = int(str(old_addr)[0])
    return (first_digit * 1000 + new_addr)

def format_sym_table_out(syms):
    syms_out = "Symbol Table\n"
    for sym, sym_info in syms.items():
        syms_out += "{}={} {}\n".format(sym, sym_info[SYM_VAL], sym_info[SYM_ERR])
    return syms_out

def format_mmap_out(mmap, sym_use_stat):
    mmap_str = "Memory Map\n"
    for index, item in enumerate(mmap):
        mmap_str += "{}:\t{}\n".format(str(index), item)
    for sym in sym_use_stat: 
        if sym_use_stat[sym] == False: 
            mmap_str += 'Warning: ' + sym + ' was defined but never used.'
    return mmap_str

def check_multiple_sym_usage(progpair):
    if progpair[PROG_SYM_USED_FLAG] == True: 
        progpair[PROG_ERR] = 'Error: Multiple symbols used here; last one used'
    else: 
        progpair[PROG_SYM_USED_FLAG] = True
    return progpair

def uin_sec_pass(mods, sym_table): 
    mmap = []
    sym_use_stat = {}
    for sym in sym_table: 
        sym_use_stat[sym] = False
    c = 0
    for mod in mods[MODS]:
        use_list = mod[USE]['use_list']
        prog = mod[PROG]
        prog_list = prog['prog_list']
        print('this is mod ' + str(c))
        c += 1
        for usym, uaddr in use_list.items():
            '''Resolve external addresses'''
            is_sym_used_not_defined = False
            old_sym_addr = prog_list[uaddr][WORD]
            addr_cur = str(old_sym_addr)
            new_sym_addr = None
            if usym in sym_table: 
                new_sym_addr = sym_table[usym][SYM_VAL]
                sym_use_stat[usym] = True
            else: 
                is_sym_used_not_defined = True
                new_sym_addr = '111'
                prog_list[uaddr][PROG_ERR] = 'Error: ' + usym + ' was used but not defined. It has been given the value 111.'
            prog_list[uaddr][WORD] = process_external_addr(old_sym_addr, int(new_sym_addr))
            print_list(prog_list)
            print('addrcur: ' + addr_cur)
            prog_list[uaddr] = check_multiple_sym_usage(prog_list[uaddr])
            while addr_cur[-3:] != '777':
                next_index = int(addr_cur[-3:])
                print('next idx is ' + str(next_index))
                print_list(prog_list)
                next_addr = str(prog_list[next_index][WORD])
                prog_list[next_index][WORD] = process_external_addr(int(next_addr), int(new_sym_addr))
                prog_list[next_index] = check_multiple_sym_usage(prog_list[next_index])
                if is_sym_used_not_defined == True: 
                    prog_list[next_index][PROG_ERR] = 'Error: ' + usym + ' was used but not defined. It has been given the value 111.'
                addr_cur = next_addr

        for progpair in prog_list: 
            if progpair[TYPE] == 'R': 
                '''Resolve relative addresses'''
                if int(str(progpair[WORD])[-3:]) >= len(prog_list):
                    progpair[PROG_ERR] = 'Error: Type R address exceeds module size; 0 (relative) used'
                    progpair[WORD] = int(str(progpair[WORD])[0]) * 1000
                progpair[WORD] += prog[BASE]
            mmap.append(str(progpair[WORD]) + ' ' + progpair[PROG_ERR])

    mmap_out = format_mmap_out(mmap, sym_use_stat)
    return mmap_out

def main():
    uin = get_input()
    mods, sym_table = uin_frist_pass(uin)
    print('\n' + format_sym_table_out(sym_table))
    mmap_out = uin_sec_pass(mods, sym_table)
    print(mmap_out)
    
if __name__ == "__main__":
    main()