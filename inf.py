#!/usr/bin/python3
import sys,os,os.path,collections,argparse,binascii

##########################################################################
##########################################################################

INFFile=collections.namedtuple('INFFile','path data name attrs extra_info tape next')

##########################################################################
##########################################################################

def isspace(c): return c==32 or c==9
def iseol(c): return c==10 or c==13

def isxdigit(c): return c in b"0123456789ABCDEFabcdef"

def get_printable(s):
    assert type(s) is bytes,type(s)
    return s.decode('ascii',errors='backslashreplace')

DQUOTE=ord('"')
EQ=ord('=')
SPACE=ord(' ')

ACCESS_TYPE='access'
DFS_ACCESS_TYPE='dfs_access'
HEX_TYPE='hex'

# long bbcim_data_crc(void *data, int length) {
# 	int  i;
# 	unsigned char *d = (unsigned char *) data;
# 	unsigned int crc;

# 	crc = 0;

# 	for (i=0; i<length; i++) {
# 		int  k;

# 		crc ^= ((*d++) << 8);
# 		for(k=0; k<8; k++) {
# 			if (crc & 32768) crc = (((crc ^ 0x0810) & 32767) << 1)+1;
# 			else crc <<= 1;
# 		}
# 	}

# 	return crc;
# }

def CRC16(data): return binascii.crc_hqx(data,0)
    # assert type(data) is bytes,type(data)

    # crc=0
    # for byte in data:
    #     crc^=byte<<8
    #     for k in range(8):
    #         if crc&32768:
    #             crc=(((crc^0x0810)&32767)<<1)+1
    #         else: crc<<=1
        
    # return crc

def is_locked(s):
    if s==b'Locked': return True
    elif s==b'LOCKED':
        # Quite a lot of files in The BBC Lives! collection have it
        # specified as "LOCKED". Also, Zalaga from STH.
        return True
    else: return False

class INFError(Exception):
    def __init__(self,message): super().__init__(message)

def main2(options):
    inf_paths=[]
    for input_folder_path in options.input_folder_paths:
        for dir_path,dir_names,file_names in os.walk(input_folder_path):
            for file_name in file_names:
                ext=os.path.splitext(file_name)[1]
                if ext=='.inf' or ext=='.INF':
                    inf_paths.append(os.path.join(dir_path,file_name))

    print('found %d .inf files'%len(inf_paths))

    inf_files=[]
    num_INFErrors_caught=0
    for inf_index,inf_path in enumerate(inf_paths):
        if inf_index%1000==0:
            print('%d/%d...'%(inf_index,len(inf_paths)))
        with open(inf_path,'rb') as f: inf=f.read()

        try:
            # must be printable 7-bit ASCII.
            for c_index,c in enumerate(inf):
                if (c>=32 and c<=126) or c==9 or c==10 or c==13: pass
                else:
                    if not options.accept_all_chars:
                        raise INFError('+%d: invalid char: 0x%02x'%
                                       (c_index,c))

            index=0

            def skip_spaces():
                nonlocal index
                
                while index<len(inf) and isspace(inf[index]):
                    index+=1

            def scan_space_separated_field():
                nonlocal index

                assert not isspace(inf[index])
                begin=index
                while (index<len(inf) and
                       not isspace(inf[index]) and
                       not iseol(inf[index])):
                    index+=1

                return inf[begin:index]

            def parse_quoted_string():
                nonlocal index

                assert inf[index]==DQUOTE
                index+=1
                begin=index
                while index<len(inf) and inf[index]!=DQUOTE: index+=1
                if index==len(inf): raise INFError('+%d: unterminated quoted string'%index)

                end=index

                index+=1        # skip the DQUOTE

                chars=[]

                i=begin
                while i<end:
                    if inf[i]=='%':
                        if (i+2>end or 
                            not isxdigit(inf[i+1]) or
                            not isxdigit(inf[i+2])):
                            raise INFError('+%d: invalid percent encoding'%i)
                        chars.append(int(inf[i+1:i+3],16))
                        i+=1
                    else:
                        chars.append(inf[i])
                        i+=1

                return bytes(chars)

            def parse_string_field():
                nonlocal index

                if inf[index]==DQUOTE:
                    return (parse_quoted_string(),True)
                else:
                    return (scan_space_separated_field(),False)

            def parse_hex_field(s,sign_extend_24_bit=False):
                try: value=int(s,16)
                except ValueError:
                    raise INFError('invalid hex field: "%s"'%get_printable(s))

                if sign_extend_24_bit:
                    if len(s)==6:
                        if (value&0x00ff0000)==0xff0000:
                            value|=0xffff0000

                return value

            def try_parse_access(s):
                # handle annoying amnbiguous cases. (DE isn't an
                # option.)
                if s==b'E' or s==b'e' or s==b'D' or s==b'd':
                    return str(s)

                # Handle Locked.
                if is_locked(s): return 'L'

                # If it otherwise looks like hex, assume not access.
                try:
                    int(s,16)
                    return None
                except ValueError: pass

                # If there's any non-access chars, assume not access.
                for i,c in enumerate(s):
                    if c not in b'EeLlWwRrDd': return None

                # Assume access.
                return str(s)

            def try_parse_dfs_access(s):
                if is_locked(s): return 'L'
                elif s==b'L': return str(s)
                else: return None

            skip_spaces()
            if index==len(inf):
                raise INFError('first field not found')

            inf_name,was_quoted=parse_string_field()
            inf_tape=False
            if not was_quoted and inf_name==b'TAPE':
                # print('%s : found TAPE'%inf_path)
                inf_tape=True
                skip_spaces()
                inf_name,was_quoted=parse_string_field()

            if was_quoted:
                print('%s: quoted name'%inf_path)

            # Pre-book space for the standard set of attributes.
            hex_fields=[None,   # load
                        None,   # exec
                        None,   # length
                        None]   # attr

            done=False
            hex_field_index=0
            while True:
                skip_spaces()
                if index==len(inf) or iseol(inf[index]):
                    field=None
                    # hit end of file/line.
                    break

                field_begin=index
                field=scan_space_separated_field()

                if b'=' in field:
                    # ran into start of extra info section.
                    index=field_begin
                    break
                elif field==b'NEXT':
                    # ran into NEXT.
                    break
                elif done: raise INFError('field after done: "%s"'%get_printable(field))
                
                if hex_field_index==0:
                    # Load (syntax 1/2)/Access (syntax 3)
                    access=try_parse_access(field)
                    if access is not None:
                        # Access (syntax 3)
                        hex_fields[3]=access
                        done=True
                    else:
                        # Load (syntax 1/2)
                        hex_fields[0]=parse_hex_field(field,True)
                elif hex_field_index==1:
                    # Exec (syntax 1/2)
                    hex_fields[1]=parse_hex_field(field,True)
                elif hex_field_index==2:
                    # Length (syntax 1)/DFS access (syntax 2)
                    access=try_parse_dfs_access(field)
                    if access is not None:
                        # DFS access (syntax 2)
                        hex_fields[3]=access
                        done=True
                    else:
                        # Length (syntax 1)
                        hex_fields[2]=parse_hex_field(field)
                elif hex_field_index==3:
                    # Access (syntax 1)
                    access=try_parse_access(field)
                    if access is None: access=parse_hex_field(field)
                    hex_fields[3]=access
                else:
                    # Ongoing hex fields (syntax 1)
                    assert hex_field_index==len(hex_fields)
                    hex_fields.append(parse_hex_field(field))

                hex_field_index+=1

            #
            inf_extra_info={}
            if field is not None and b'=' in field:
                # must rescan, which is a bit ugly.
                while index<len(inf) and not iseol(inf[index]):
                    assert not isspace(inf[index])
                    key_begin=index
                    while (index<len(inf) and
                           inf[index]!=EQ and
                           not isspace(inf[index]) and
                           not iseol(inf[index])):
                        index+=1

                    key_or_field=inf[key_begin:index]

                    if key_or_field==b'NEXT':
                        field=key_or_field
                        break

                    # print('key_or_field="%s"'%get_printable(key_or_field))
                    
                    if index==len(inf) or inf[index]!=EQ:
                        raise INFError('invalid extra info syntax (%s)'%get_printable(inf[key_begin:]))

                    index+=1    # skip the '='

                    # A lot of files in The BBC Lives! collection have
                    # the CRC value set with something like "CRC=
                    # 1234" - possibly a bug in some early version of
                    # the tools?
                    #
                    # This is pretty ugly but should be safe for this
                    # attribute specifically.
                    if key_or_field==b'CRC':
                        if index<len(inf) and inf[index]==SPACE:
                            index+=1

                    # there may be no value.
                    assert index<=len(inf)
                    if (index==len(inf) or
                        iseol(inf[index]) or
                        isspace(inf[index])):
                        value=b''
                    else: value,was_quoted=parse_string_field()

                    inf_extra_info[key_or_field]=value
                    # print('key=%s value=%s'%(get_printable(key_or_field),get_printable(value)))

                    skip_spaces()

                    field=None

            #
            inf_next=None
            if field==b'NEXT':
                # all good (probably) - don't actually care about
                # this.
                skip_spaces()
                begin=index
                while index<len(inf) and not iseol(inf[index]):
                    index+=1
                inf_next=inf[begin:index]

            if index<len(inf) and not iseol(inf[index]):
                raise INFError('unexpected suffix: "%s"'%get_printable(inf[index:]))

            if options.no_crc: data=None
            else:
                data_path=os.path.splitext(inf_path)[0]
                if os.path.isfile(data_path):
                    if type(access) is str:
                        if 'd' in access or 'D' in access:
                            raise INFError('data dir is file')

                    try:
                        with open(data_path,'rb') as f: data=f.read()
                    except IOError as err:
                        raise INFError('error reading data file: %s'%err)
                elif os.path.isdir(data_path):
                    if type(access) is str:
                        if 'd' not in access and 'D' not in access:
                            raise INFError('data file is dir')

                    data=None
                else:
                    data=None
                    print('%s : data file neither file nor dir'%inf_path)
                
            inf_file=INFFile(path=inf_path,
                             data=data,
                             name=inf_name,
                             attrs=hex_fields,
                             extra_info=inf_extra_info,
                             tape=inf_tape,
                             next=inf_next)
            inf_files.append(inf_file)
        except INFError as err:
            print('hex_field_index=%d'%hex_field_index)
            sys.stderr.write('%s : %s\n'%(inf_path,err))
            num_INFErrors_caught+=1
        except AssertionError as err:
            print('inf_path: %s'%inf_path)
            raise err

    print('loaded %d/%d .inf files'%(len(inf_files),len(inf_paths)))
    print('%d failed'%(len(inf_paths)-len(inf_files)))
    print('caught %d INFErrors'%num_INFErrors_caught)

    if not options.no_crc:
        num_by_key={}

        class CRCCounters:
            def __init__(self):
                self.num_seen=0
                self.num_valid=0

            def get_description(self):
                return '%d/%d'%(self.num_valid,self.num_seen)

        crc16_counters=CRCCounters()
        crc32_counters=CRCCounters()

        for inf_file in inf_files:
            for k,v in inf_file.extra_info.items():
                num_by_key[k]=num_by_key.get(k,0)+1

            def check_crc(name,num_bits,crc_fun,counters,invalid_crcs):
                crc=inf_file.extra_info.get(name)
                if crc is None: return

                counters.num_seen+=1

                try: crc=int(crc,16)
                except ValueError:
                    print('%s : invalid %s: %s'%(inf_file.path,
                                                 name,
                                                 get_printable(crc)))
                    return

                if crc in invalid_crcs: return

                mask=(1<<num_bits)-1
                if (crc&~mask)!=0:
                    print('%s : %s not %d bits: 0x%x'%(inf_file.path,
                                                       name,
                                                       num_bits,
                                                       crc))
                    return

                actual_crc=None
                if inf_file.data is None:
                    print('%s : no data for %s (expecting 0x%x)'%(inf_file.path,name,crc))
                else:
                    if crc_fun is not None:
                        actual_crc=crc_fun(inf_file.data)

                        if actual_crc!=crc:
                            print('%s : %s mismatch: expected 0x%x, got 0x%x'%(inf_file.path,name,crc,actual_crc))
                        else: counters.num_valid+=1

            check_crc(b'CRC',16,CRC16,crc16_counters,[0xffffffff])
            check_crc(b'CRC32',32,binascii.crc32,crc32_counters,[])

        print(num_by_key)

        print('CRC16: %s'%crc16_counters.get_description())
        print('CRC32: %s'%crc32_counters.get_description())

##########################################################################
##########################################################################

def main(argv):
    parser=argparse.ArgumentParser()

    parser.add_argument('input_folder_paths',nargs='+',metavar='DIR',help='''search %(metavar)s for .inf files''')
    parser.add_argument('--no-crc',action='store_true',help='''don't check CRCs''')
    parser.add_argument('--accept-all-chars',action='store_true',help='''accept any chars in attribute files''')

    main2(parser.parse_args(argv))

##########################################################################
##########################################################################

if __name__=='__main__': main(sys.argv[1:])
