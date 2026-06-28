# This file contains AI-generated parsers.
import re, json


import re
import json

def parse_adhoc(text_content):
    records = []
    for line in text_content.split('\n'):
        match = re.match(r'row (\d+) ; (.+?) ;', line)
        if match:
            row_number, command = match.groups()
            try:
                parsed_command = json.loads(f'{{"command": "{command}"}}')
                records.append({"row_number": int(row_number), **parsed_command})
            except json.JSONDecodeError:
                continue
    return records


import re
import json

def parse_storageservers(text_content):
    records = []
    for line in text_content.splitlines():
        match = re.match(r'([a-z]{3}[a-z]{2}xx[0-9]{1,2}\.ccsrm\.in)', line)
        if match:
            record = {'server_name': match.group(1)}
            records.append(record)
    return records


import re
import json

def parse_tafcoppstafcopsvsdetails(text_content):
    records = []
    lines = text_content.strip().split('\n')
    i = 0
    while i < len(lines):
        if lines[i].startswith('Storage VM:'):
            record = {'Storage VM': lines[i + 1]}
            i += 2
        elif lines[i].startswith('S3 Server Name:'):
            record['S3 Server Name'] = lines[i + 1]
            i += 2
        elif lines[i].startswith('Network IP Interfaces:'):
            record['Network IP Interfaces'] = lines[i + 1]
            i += 2
        elif lines[i].startswith('CERTIFICATE SERIAL NUMBER:'):
            record['CERTIFICATE SERIAL NUMBER'] = lines[i + 1]
            i += 2
        elif lines[i].startswith('CERTIFICATE DETAILS:'):
            cert_details = []
            while i < len(lines) and not lines[i].startswith('CERTIFICATE EXPIRATION DATE:'):
                if lines[i].strip():
                    cert_details.append(lines[i])
                i += 1
            record['CERTIFICATE DETAILS'] = '\n'.join(cert_details)
        elif lines[i].startswith('CERTIFICATE EXPIRATION DATE:'):
            record['CERTIFICATE EXPIRATION DATE'] = lines[i + 1]
            records.append(record)
            i += 2
        else:
            i += 1
    return records


import re
import json

def parse_saudit(text_content):
    records = []
    lines = text_content.strip().split('\n')
    
    for line in lines:
        if line.startswith('Sample output:'):
            break
        
        match = re.match(r'(\d+\.\s+)(.*)', line)
        if match:
            record = {}
            key, value = match.groups()
            record[key.strip()] = value.strip()
            records.append(record)
    
    return records


import re
import json

def parse_cmdro(text_content):
    records = []
    for line in text_content.split('\n'):
        match = re.match(r'^(?P<id>\w+)::> ro (?P<index>\d+)', line)
        if match:
            record = {
                'id': match.group('id'),
                'index': int(match.group('index'))
            }
            records.append(record)
    return records


import re
import json

def parse_cmdsnapmshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    headers = None
    
    for line in lines:
        if not headers:
            headers = [header.strip() for header in re.split(r'\s+', line) if header]
            continue
        
        fields = re.split(r'\s+', line)
        if len(fields) != len(headers):
            continue
        
        record = {headers[i]: fields[i].strip() for i in range(len(headers))}
        records.append(record)
    
    return records


import re
import json

def parse_cmdvservershow(text_content):
    lines = text_content.strip().split('\n')
    headers = [h.strip() for h in lines[2].split()]
    result = []
    
    for line in lines[3:-1]:
        if not line.strip():
            continue
        fields = [f.strip() for f in line.split()]
        if len(fields) != len(headers):
            continue
        record = {headers[i]: fields[i] for i in range(len(headers))}
        result.append(record)
    
    return result


import re
import json

def parse_cmdnfsconnectedclientsshow(text_content):
    lines = text_content.strip().split('\n')
    headers = [h.strip() for h in lines[3].split()]
    data = []
    for line in lines[4:]:
        if not line.strip():
            continue
        values = [v.strip() for v in line.split()]
        if len(values) != len(headers):
            continue
        record = {headers[i]: values[i] for i in range(len(headers))}
        data.append(record)
    return data


import re
import json

def parse_cmdsetadv(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if line.startswith('PRODFAS0::>'):
            record = {'command': line.split('::>')[1].strip()}
        elif 'Warning:' in line:
            record['warning'] = line.strip()
        elif 'Do you want to continue?' in line:
            record['confirmation_prompt'] = line.strip()
        else:
            continue
        records.append(record)
    return records


import re
import json

def parse_cmdnfsstatusshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if 'Error:' not in line and ':' in line:
            parts = line.split(':')
            record = {
                'vserver': parts[0].strip(),
                'command': parts[1].strip(),
                'status': parts[2].strip()
            }
            records.append(record)
    return records


import re
import json

def parse_cmdnfsstatus(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'The NFS server is running on Vserver "(.+)"\.', line)
        if match:
            vserver_name = match.group(1)
            record = {'vserver_name': vserver_name}
            records.append(record)
    return records


import re
import json

def parse_cmdobjectstoreserverauditeventselectorshow(text_content):
    lines = text_content.strip().split('\n')
    headers = [header.strip() for header in lines[2].split()]
    data = []
    
    for line in lines[3:-1]:
        if not line.strip():
            continue
        values = [value.strip() for value in line.split()]
        if len(values) == len(headers):
            record = dict(zip(headers, values))
            data.append(record)
    
    return data


import re
import json

def parse_cmdvservershow(text_content):
    lines = text_content.strip().split('\n')
    headers = [h.strip() for h in lines[3].split()]
    result = []
    
    for line in lines[4:-1]:
        if not line.strip():
            continue
        fields = [f.strip() for f in line.split()]
        if len(fields) != len(headers):
            continue
        record = dict(zip(headers, fields))
        result.append(record)
    
    return result


import re
import json

def parse_cmdnetintshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.startswith('Cluster') and not line.startswith('prodfassvm'):
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 7:
                record = {
                    'Vserver': parts[0],
                    'Interface': parts[1],
                    'Admin/Oper': parts[2],
                    'Address/Mask': parts[3],
                    'Node': parts[4],
                    'Port': parts[5],
                    'Home': parts[6]
                }
                records.append(record)
    return records


import re
import json

def parse_cmdvolshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header_line = lines[2]
    fields = [field.strip() for field in header_line.split()]
    
    for line in lines[3:]:
        if not line:
            continue
        values = [value.strip() for value in line.split()]
        if len(values) != len(fields):
            continue
        record = {fields[i]: values[i] for i in range(len(fields))}
        records.append(record)
    
    return records


import re
import json

def parse_cmdvolshowfieldsnode(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header_line = lines[0]
    field_names = [field.strip() for field in header_line.split()[2:]]
    
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = re.split(r'\s{2,}', line)
        if len(fields) != len(field_names):
            continue
        record = {field_names[i]: fields[i] for i in range(len(field_names))}
        records.append(record)
    
    return records


import re
import json

def parse_cmdprivsetdiag(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if line.startswith('s3_audit_prodfassvm2_'):
            match = re.match(r's3_audit_prodfassvm2_(D\d{4}-\d{2}-\d{2}-T\d{2}-\d{2}-\d{2}_\d{10})\.json', line)
            if match:
                records.append({'filename': line, 'date': match.group(1)})
    return records


import re
import json

def parse_puttycmd(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<host>\w+)::> (?P<command>.+)$', line)
        if match:
            command_parts = match.group('command').strip().split()
            record = {'host': match.group('host'), 'command': command_parts[0], 'args': command_parts[1:]}
            records.append(record)
    return records


import re
import json

def parse_cmdvolmodifyvolumesauditpolicys(text_content):
    records = []
    pattern = r'^(?P<host>\w+)::>\s+vol\s+modify\s+-volume\s+(?P<volume>\S+)\s+-policy\s+(?P<policy>\S+)'
    
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            records.append(match.groupdict())
    
    return records


import re
import json

def parse_cmdvolmodifyvolumesauditpolicyexportsaudit(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'PRODFAS\d+::> vol modify -volume (\S+) -policy (\S+)', line)
        if match:
            volume, policy = match.groups()
            record = {
                'command': 'vol modify',
                'volume': volume,
                'policy': policy
            }
            records.append(record)
    return records


import re
import json

def parse_cmdvolmodifyvolumesauditpolicyexportsauditvserverprodfassvm(text_content):
    records = []
    pattern = r'PRODFAS\d+::> vol modify -volume (\S+) -policy (\S+) -vserver (\S+)'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            volume = match.group(1)
            policy = match.group(2)
            vserver = match.group(3)
            records.append({'volume': volume, 'policy': policy, 'vserver': vserver})
    return records


import re
import json

def parse_cmdnfsstatus(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'The NFS server is running on Vserver "(.+)"\.', line)
        if match:
            vserver_name = match.group(1)
            record = {'vserver_name': vserver_name}
            records.append(record)
    return records


import re
import json

def parse_cmdnfsoffvserverprodfassvm(text_content):
    records = []
    pattern = r'^(?P<vserver>\w+)::> nfs off -vserver (?P<target_vserver>\w+)$'
    
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = match.groupdict()
            records.append(record)
    
    return records


import re
import json

def parse_cmdnfsstopvserverprodfassvm(text_content):
    records = []
    pattern = r'^(?P<vserver>\w+)::> nfs stop -vserver (?P<target_vserver>\w+)$'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = match.groupdict()
            records.append(record)
    return records


import re
import json

def parse_cmdnfsonvserverprodfassvm(text_content):
    records = []
    pattern = r'^(?P<vserver>\w+)::> nfs on -vserver (?P<target_vserver>\w+)$'
    
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = match.groupdict()
            records.append(record)
    
    return records


import re
import json

def parse_cmdnfsstartvserverprodfassvm(text_content):
    records = []
    pattern = r'^(?P<vserver>\w+)::> nfs start -vserver (?P<target_vserver>\w+)$'
    
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = match.groupdict()
            records.append(record)
    
    return records


import re
import json

def parse_cmdexportpolicyruleshowinstancevserverprodfassvm(text_content):
    records = []
    lines = text_content.strip().split('\n')
    current_record = {}
    
    for line in lines:
        if line.startswith('Vserver:'):
            if current_record:
                records.append(current_record)
            current_record = {'Vserver': line.split(': ')[1]}
        elif line.startswith('Policy Name:'):
            current_record['Policy Name'] = line.split(': ')[1]
        elif line.startswith('Rule Index:'):
            current_record['Rule Index'] = int(line.split(': ')[1])
        elif line.startswith('Access Protocol:'):
            current_record['Access Protocol'] = line.split(': ')[1].split(', ')
        elif line.startswith('List of Client Match Hostnames, IP Addresses, Netgroups, or Domains:'):
            current_record['Client Match'] = line.split(': ')[1]
        elif line.startswith('RO Access Rule:'):
            current_record['RO Access Rule'] = line.split(': ')[1]
        elif line.startswith('RW Access Rule:'):
            current_record['RW Access Rule'] = line.split(': ')[1]
        elif line.startswith('User ID To Which Anonymous Users Are Mapped:'):
            current_record['Anonymous User ID'] = int(line.split(': ')[1])
        elif line.startswith('Superuser Security Types:'):
            current_record['Superuser Security Types'] = line.split(': ')[1]
        elif line.startswith('Honor SetUID Bits in SETATTR:'):
            current_record['SetUID Honor'] = line.split(': ')[1].lower() == 'true'
        elif line.startswith('Allow Creation of Devices:'):
            current_record['Device Creation Allow'] = line.split(': ')[1].lower() == 'true'
    
    if current_record:
        records.append(current_record)
    
    return records


import re
import json

def parse_puttycmd(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                record = {
                    'module': parts[0],
                    'command': parts[1]
                }
                if len(parts) > 2:
                    record['subcommands'] = parts[2:]
                records.append(record)
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvm(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'^(?P<vserver>\S+)\s+(?P<vservers>.+)$', line)
        if match:
            record = {
                'vserver': match.group('vserver'),
                'vservers': match.group('vservers').split()
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientip(text_content):
    records = []
    pattern = r'PRODFAS0::> export-policy check-access -vserver (.*?) -volume (.*?) -client-ip (.*?)'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = {
                'vserver': match.group(1),
                'volume': match.group(2),
                'client_ip': match.group(3)
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsys(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'^(?P<vserver>\S+)::> export-policy check-access -vserver (?P<svr>\S+) -volume (?P<vol>\S+) -client-ip (?P<ip>\S+) -authentication-method sys$', line)
        if match:
            records.append(match.groupdict())
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfs(text_content):
    records = []
    pattern = r'PRODFAS0::> export-policy check-access -vserver (.*?) -volume (.*?) -client-ip (.*?) -authentication-method sys -protocol nfs\s+(.*?)\s+'
    matches = re.finditer(pattern, text_content)
    for match in matches:
        record = {
            'vserver': match.group(1),
            'volume': match.group(2),
            'client_ip': match.group(3),
            'protocols': match.group(4).split()
        }
        records.append(record)
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfs(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'^(?P<vserver>\S+)::> export-policy check-access -vserver (?P<svr>\S+) -volume (?P<vol>\S+) -client-ip (?P<ip>\S+) -authentication-method sys -protocol nfs3$', line)
        if match:
            records.append(match.groupdict())
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccess(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'^(?P<vserver>\S+)::> export-policy check-access -vserver (?P<target_vserver>\S+) -volume (?P<volume>\S+) -client-ip (?P<client_ip>\S+) -authentication-method sys -protocol nfs3 -access$', line)
        if match:
            records.append(match.groupdict())
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccesstyperead(text_content):
    records = []
    pattern = r'PRODFAS0::> export-policy check-access -vserver prodfassvm0 -volume S3AUDITLOG_RO -client-ip (\d+\.\d+\.\d+\.\d+) -authentication-method sys -protocol nfs3 -access-type (read|read-write)'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            client_ip = match.group(1)
            access_type = match.group(2)
            records.append({'client_ip': client_ip, 'access_type': access_type})
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccesstyperead(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<path>.*?)(?P<policy>.*?)(?P<owner>.*?)(?P<ownertype>.*?)(?P<index>\d+)(?P<access>.*)$', line)
        if match:
            record = {
                'path': match.group('path').strip(),
                'policy': match.group('policy').strip(),
                'owner': match.group('owner').strip(),
                'ownertype': match.group('ownertype').strip(),
                'index': int(match.group('index')),
                'access': match.group('access').strip()
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccesstyperead(text_content):
    lines = text_content.strip().split('\n')
    result = []
    
    for line in lines:
        if not line.strip():
            continue
        
        match = re.match(r'^(?P<path>.*?)(?:\s+(?P<policy>.*?))?(?:\s+(?P<owner>.*?))?(?:\s+(?P<ownertype>.*?))?(?:\s+(?P<index>\d+))?\s+(?P<access>.*)$', line)
        if match:
            result.append(match.groupdict())
    
    return result


import re
import json

def parse_cmdexportpolicyrulecreatevserverprodfassvmpolicynamedefaultrorulesys(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'PRODFAS0::> export-policy rule create -vserver prodfassvm0 -policyname default -rorule sys', line)
        if match:
            records.append({'command': 'export-policy rule create', 'vserver': 'prodfassvm0', 'policyname': 'default', 'rorule': 'sys'})
    return records


import re
import json

def parse_cmdexportpolicyrulecreatevserverprodfassvmpolicynamedefaultrorulesysclientmatch(text_content):
    records = []
    pattern = r'PRODFAS0::> export-policy rule create -vserver (.*?) -policyname (.*?) -rorule sys -clientmatch (.*?)'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = {
                'vserver': match.group(1),
                'policyname': match.group(2),
                'rorule': match.group(3)
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicyrulecreatevserverprodfassvmpolicynamedefaultrorulesysclientmatchrwrule(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'PRODFAS0::> export-policy rule create -vserver (\S+) -policyname (\S+) -rorule sys -clientmatch (\S+/\d+) -rwrule', line)
        if match:
            vserver, policyname, clientmatch = match.groups()
            records.append({
                'vserver': vserver,
                'policyname': policyname,
                'clientmatch': clientmatch
            })
    return records


import re
import json

def parse_cmdexportpolicyrulecreatevserverprodfassvmpolicynamedefaultrorulesysclientmatchrwrulenone(text_content):
    records = []
    pattern = r'PRODFAS0::> export-policy rule create -vserver (.*?) -policyname (.*?) -rorule (.*?) -clientmatch (.*?) -rwrule (.*?)'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = {
                'vserver': match.group(1),
                'policyname': match.group(2),
                'rorule': match.group(3),
                'clientmatch': match.group(4),
                'rwrule': match.group(5)
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicyrulecreatevserverprodfassvmpolicynamedefaultrorulesysclientmatchrwrulenone(text_content):
    pattern = r'PRODFAS\d+::> export-policy rule create -vserver (.*?) -policyname (.*?) -rorule (.*?) -clientmatch (.*?) -rwrule (.*?)'
    matches = re.findall(pattern, text_content)
    result = []
    for match in matches:
        record = {
            'vserver': match[0],
            'policyname': match[1],
            'rorule': match[2],
            'clientmatch': match[3],
            'rwrule': match[4]
        }
        result.append(record)
    return result


import re
import json

def parse_cmdexportpolicyruleshow(text_content):
    lines = text_content.strip().split('\n')
    headers = [header.strip() for header in lines[3].split()]
    result = []
    
    for line in lines[4:]:
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split()]
        if len(fields) == len(headers):
            record = {headers[i]: fields[i] for i in range(len(headers))}
            result.append(record)
    
    return result


import re
import json

def parse_cmdexportpolicyrulemodifyvserverprodfassvm(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        match = re.match(r'^(?P<vserver>\S+)\s+(?P<rules>.+)$', line)
        if match:
            record = {
                'vserver': match.group('vserver'),
                'rules': match.group('rules').split()
            }
            records.append(record)
    return records


import re
import json

def parse_cmdexportpolicyrulemodifyvserverprodfassvmpolicynamedefaultruleindexclientmatch(text_content):
    pattern = r'PRODFAS\d+::> export-policy rule modify -vserver (.*?) -policyname (.*?) -ruleindex (\d+) -clientmatch (.*?)'
    matches = re.findall(pattern, text_content)
    result = []
    for match in matches:
        record = {
            'vserver': match[0],
            'policyname': match[1],
            'ruleindex': int(match[2]),
            'clientmatch': match[3]
        }
        result.append(record)
    return result


import re
import json

def parse_cmdexportpolicyruleshow(text_content):
    lines = text_content.strip().split('\n')
    headers = [header.strip() for header in lines[3].split()]
    result = []
    
    for line in lines[4:]:
        if not line.strip():
            continue
        fields = [field.strip() for field in re.split(r'\s+', line, maxsplit=len(headers)-1)]
        if len(fields) == len(headers):
            record = {headers[i]: fields[i] for i in range(len(headers))}
            result.append(record)
    
    return result


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccesstyperead(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if 'Policy' in line and 'Path' in line:
            continue
        match = re.match(r'/\s+(?P<path>.+?)\s+(?P<policy>.+?)\s+(?P<owner>.+?)\s+(?P<ownertype>.+?)\s+(?P<index>\d+)\s+(?P<access>.+)', line)
        if match:
            records.append(match.groupdict())
    return records


import re
import json

def parse_cmdexportpolicycheckaccessvserverprodfassvmvolumesauditlogroclientipauthenticationmethodsysprotocolnfsaccesstyperead(text_content):
    lines = text_content.strip().split('\n')
    result = []
    
    for line in lines:
        if not line.strip():
            continue
        
        match = re.match(r'^(?P<path>.*?)(?:\s+(?P<policy>.+?)\s+(?P<owner>.+?)\s+(?P<ownertype>.+?)\s+(?P<index>\d+)\s+(?P<access>.+))?', line)
        if match:
            result.append(match.groupdict())
    
    return result


import re
import json

def parse_cmdeventlogshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header_line = lines[2]
    fields = [field.strip() for field in header_line.split()]
    
    pattern = re.compile(r'(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{1,2}:\d{1,2})\s+(\S+)\s+(\S+)\s+(.*)')
    
    for line in lines[3:]:
        match = pattern.match(line)
        if match:
            record = {fields[i]: match.group(i+1) for i in range(len(fields))}
            records.append(record)
    
    return records


import re
import json

def parse_cmdobjectstore(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<key>\S+):(?P<value>.*)$', line)
        if match:
            record = {match.group('key'): match.group('value').strip()}
            records.append(record)
    return records


import re
import json

def parse_cmdobjectstoreserverauditeventselectorshow(text_content):
    lines = text_content.strip().split('\n')
    headers = [header.strip() for header in lines[2].split()]
    data = []
    
    for line in lines[3:-1]:
        if not line.strip():
            continue
        values = [value.strip() for value in line.split()]
        if len(values) == len(headers):
            record = dict(zip(headers, values))
            data.append(record)
    
    return data


import re
import json

def parse_cmdvolshowfieldspolicyjunctionpathjunctionparentjunctionpathsourcejunctionactiveaudit(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header = lines[1].strip().split()
    
    for line in lines[2:]:
        fields = line.strip().split()
        if len(fields) == len(header):
            record = {header[i]: fields[i] for i in range(len(header))}
            records.append(record)
    
    return records


import re
import json

def parse_cmdexportpolicyruleshowpolicyexportsaudit(text_content):
    lines = text_content.strip().split('\n')
    headers = [header.strip() for header in lines[2].split()]
    result = []
    
    for line in lines[3:]:
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split()]
        if len(fields) != len(headers):
            continue
        record = {headers[i]: fields[i] for i in range(len(headers))}
        try:
            json_record = json.loads(json.dumps(record))
            result.append(json_record)
        except ValueError:
            pass
    
    return result


import re
import json

def parse_cmdnetintshowvserverprodfassvm(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
        if match:
            records.append({
                'Vserver': match.group(1),
                'Interface': match.group(2),
                'Admin/Oper': match.group(3),
                'Address/Mask': match.group(4),
                'Node': match.group(5),
                'Port': match.group(6)
            })
    return records


import re
import json

def parse_puttycmd(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<host>\w+)\*> (?P<command>ls /vol/S3AUDITLOG_RO)', line)
        if match:
            records.append(match.groupdict())
        else:
            try:
                json_record = json.loads(line)
                records.append(json_record)
            except json.JSONDecodeError:
                continue
    return records


import re
import json

def parse_migrationstepsformigrationactivity(text_content):
    records = []
    lines = text_content.strip().split('\n')
    current_record = {}
    
    for line in lines:
        if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.') or line.startswith('6.') or line.startswith('7.') or line.startswith('8.') or line.startswith('9.') or line.startswith('10.') or line.startswith('11.') or line.startswith('12.'):
            if current_record:
                records.append(current_record)
            current_record = {'step': line.strip('.').strip()}
        elif line.startswith('**********< Steps by Appl Team >**********') or line.startswith('!!!! With only iDRAC LAN cable and no other network cable !!!!'):
            continue
        else:
            if 'steps' not in current_record:
                current_record['steps'] = []
            current_record['steps'].append(line.strip())
    
    if current_record:
        records.append(current_record)
    
    return records


import re
import json

def parse_cmdigroupshowv(text_content):
    records = []
    pattern = re.compile(r'Vserver Name:\s+(?P<vserver_name>.+?)\n\s*Igroup Name:\s+(?P<igroup_name>.+?)\n\s*Protocol:\s+(?P<protocol>.+?)\n\s*OS Type:\s+(?P<os_type>.+?)\n\s*Portset Binding Igroup:\s+(?P<portset_binding>.+?)\n\s*Igroup UUID:\s+(?P<igroup_uuid>.+?)\n\s*ALUA:\s+(?P<alua>.+?)\n\s*Initiators:\s+(?P<initiators>.+)', re.DOTALL)
    for match in pattern.finditer(text_content):
        record = match.groupdict()
        record['initiators'] = [initiator.strip() for initiator in record['initiators'].split('\n') if initiator]
        records.append(record)
    return records


import re
import json

def parse_puttycmd(text_content):
    lines = text_content.strip().split('\n')
    headers = None
    data = []
    
    for line in lines:
        if not headers:
            if 'Node' in line and 'Health' in line:
                headers = [header.strip() for header in line.split()]
        else:
            match = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', line)
            if match:
                data.append(dict(zip(headers, match.groups())))
    
    return data


import re
import json

def parse_cmdnetintshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'(\S+)\s+(\S+)\s+(\S+)\s+(.*?)\s+(\S+)\s+(\S+)\s+(\S+)', line)
        if match:
            vserver, interface, admin_oper, address_mask, node, port, home = match.groups()
            records.append({
                'Vserver': vserver,
                'Interface': interface,
                'Admin/Oper': admin_oper,
                'Address/Mask': address_mask,
                'Node': node,
                'Port': port,
                'Home': home
            })
    return records


import re
import json

def parse_cmdnetworkrouteshow(text_content):
    lines = text_content.strip().split('\n')
    header_line = next((line for line in lines if 'Vserver' in line), None)
    if not header_line:
        return []
    
    headers = [header.strip() for header in re.split(r'\s+', header_line) if header]
    records = []
    
    for line in lines[1:]:
        if not line.strip():
            continue
        fields = [field.strip() for field in re.split(r'\s+', line) if field]
        if len(fields) == len(headers):
            record = {headers[i]: fields[i] for i in range(len(headers))}
            records.append(record)
    
    return records


import re
import json

def parse_puttycmd(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<vserver>\S+)\s+(?P<group>\S+)\s+(?P<targets>.+)$', line)
        if match:
            records.append(match.groupdict())
    return records


import re
import json

def parse_cmdnetintshowfailover(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<vserver>\S+)\s+(?P<interface>\S+)\s+(?P<node_port>\S+)\s+(?P<policy>\S+)\s+(?P<group>\S+)', line)
        if match:
            record = match.groupdict()
            records.append(record)
    return records


import re
import json

def parse_cmdnetintshowfailover(text_content):
    lines = text_content.strip().split('\n')
    result = []
    
    for line in lines:
        if not line.strip():
            continue
        
        fields = re.split(r'\s+', line.strip())
        record = {}
        
        for field in fields:
            if field.startswith('-'):
                key = field[1:]
                record[key] = None
        
        if record:
            result.append(record)
    
    return result


import re
import json

def parse_cmdnetintshowfailoverpolicy(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        match = re.match(r'^(?P<interface>\S+)\s+(?P<status>\S+)', line)
        if match:
            record = {
                'interface': match.group('interface'),
                'status': match.group('status')
            }
            records.append(record)
    return records


import re
import json

def parse_cmdnetintshowfieldsfailoverpolicyfailovergroup(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header_line = lines[2]
    field_names = [field.strip() for field in header_line.split()]
    
    for line in lines[3:]:
        if not line.strip():
            continue
        fields = [field.strip() for field in line.split()]
        if len(fields) == len(field_names):
            record = dict(zip(field_names, fields))
            records.append(record)
    
    return records


import re
import json

def parse_cmdobjectstoreservershowinstance(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if 'Error:' not in line and ':' in line:
            parts = line.split(':')
            record = {
                'command': parts[0].strip(),
                'output': ':'.join(parts[1:]).strip()
            }
            records.append(record)
    return records


import re
import json

def parse_cmdnetportshow(text_content):
    records = []
    lines = text_content.strip().split('\n')
    header_line = None
    for line in lines:
        if 'Node:' in line:
            node = line.split('Node:')[1].strip()
        elif 'Port' in line and 'IPspace' in line:
            header_line = line
        elif not line.strip():
            continue
        else:
            parts = re.split(r'\s{2,}', line)
            if len(parts) == 7:
                record = {
                    'Node': node,
                    'Port': parts[0],
                    'IPspace': parts[1],
                    'Broadcast Domain': parts[2],
                    'Link': parts[3],
                    'MTU': parts[4],
                    'Admin/Oper': parts[5],
                    'Status': parts[6]
                }
                records.append(record)
    return records
