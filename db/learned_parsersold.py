# This file contains AI-generated parsers.
import re


def parse_adhoc(text_content):
    results = []
    if not text_content:
        return results
    
    for line in text_content.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        
        parts = [p.strip() for p in line.split(';') if p.strip()]
        row_id = None
        commands = []
        
        for part in parts:
            if part.lower().startswith('row '):
                row_val = part.split(' ', 1)[1].strip()
                try:
                    row_id = int(row_val)
                except ValueError:
                    row_id = row_val
            else:
                commands.append(part)
        
        results.append({
            'row': row_id,
            'commands': commands
        })
        
    return results


import shlex

def parse_asupcmd(text_content):
    results = []
    if not text_content:
        return results

    for line in text_content.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            # Parse tokens using shlex to respect quotes and handle escaping
            tokens = shlex.split(line, posix=True)
        except ValueError:
            # Fallback to standard split if quotes are unbalanced
            tokens = line.split()

        # Group tokens into separate commands split by ';'
        commands_tokens = []
        current_command = []
        for token in tokens:
            if token == ';':
                if current_command:
                    commands_tokens.append(current_command)
                    current_command = []
            else:
                current_command.append(token)
        if current_command:
            commands_tokens.append(current_command)

        # Parse each command sequence
        for cmd_tokens in commands_tokens:
            if not cmd_tokens:
                continue

            command_parts = []
            arguments = {}
            positionals = []
            
            i = 0
            while i < len(cmd_tokens):
                token = cmd_tokens[i]
                if token.startswith('-'):
                    # It's an argument flag (e.g., -node)
                    key = token.lstrip('-')
                    # Look ahead for value
                    if i + 1 < len(cmd_tokens) and not cmd_tokens[i+1].startswith('-'):
                        arguments[key] = cmd_tokens[i+1]
                        i += 2
                    else:
                        arguments[key] = True  # Boolean flag
                        i += 1
                else:
                    if not arguments:
                        # Before any flags, tokens are part of the command name
                        command_parts.append(token)
                    else:
                        # Positional argument occurring after flags
                        positionals.append(token)
                    i += 1

            parsed_cmd = {
                "command": " ".join(command_parts),
                "arguments": arguments
            }
            if positionals:
                parsed_cmd["positionals"] = positionals

            results.append(parsed_cmd)

    return results


import re
import shlex

def parse_commoncommands(text_content):
    if not text_content:
        return []
    
    # Split by semicolons that are not inside double quotes
    parts = re.split(r';(?=(?:[^"]*"[^"]*")*[^"]*$)', text_content)
    
    results = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if the command is an echo command
        if part.lower().startswith('echo '):
            echo_content = part[5:].strip()
            # Strip surrounding quotes if present
            if (echo_content.startswith('"') and echo_content.endswith('"')) or \
               (echo_content.startswith("'") and echo_content.endswith("'")):
                echo_text = echo_content[1:-1].strip()
            else:
                echo_text = echo_content
            
            results.append({
                "raw": part,
                "command": "echo",
                "arguments": echo_text,
                "is_echo": True
            })
        else:
            # Parse non-echo commands
            try:
                tokens = shlex.split(part)
            except ValueError:
                tokens = part.split()
            
            command_parts = []
            arg_parts = []
            found_arg = False
            
            for token in tokens:
                # We assume arguments start with a hyphen '-'
                if not found_arg and token.startswith('-'):
                    found_arg = True
                if found_arg:
                    arg_parts.append(token)
                else:
                    command_parts.append(token)
            
            command = " ".join(command_parts)
            arguments = " ".join(arg_parts)
            
            results.append({
                "raw": part,
                "command": command,
                "arguments": arguments,
                "is_echo": False
            })
            
    return results


def parse_servernames(text_content):
    results = []
    if not text_content:
        return results
    for line in text_content.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            results.append({
                "code": parts[0],
                "hostname": parts[1]
            })
    return results


import re

def parse_systemstatistics(text_content):
    results = []
    if not text_content:
        return results
        
    lines = [line.strip() for line in text_content.strip().split('\n') if line.strip()]
    header = None
    
    for line in lines:
        # Check for command execution pattern
        cmd_match = re.search(r'run\s+-node\s+(\S+)\s+-command\s+"([^"]+)"', line)
        if cmd_match:
            node = cmd_match.group(1)
            command = cmd_match.group(2)
            
            cmd_info = {
                'type': 'command',
                'node': node,
                'command': command
            }
            
            # Parse sysstat options if present
            if 'sysstat' in command:
                count_match = re.search(r'-c\s+(\d+)', command)
                if count_match:
                    cmd_info['count'] = int(count_match.group(1))
                if '-x' in command:
                    cmd_info['extended'] = True
                interval_match = re.search(r'\b(\d+)\s*$', command)
                if interval_match:
                    cmd_info['interval'] = int(interval_match.group(1))
                    
            results.append(cmd_info)
            continue
            
        # Filter out shell command syntax noise
        if line.startswith('ro ') or line.startswith('exit') or line == ';':
            continue
            
        # Parse potential tabular output
        parts = re.split(r'\s+', line)
        if len(parts) > 1:
            # Simple heuristic: headers don't typically contain numbers, data rows do
            is_data = any(re.search(r'\d', p) for p in parts)
            if not header and not is_data:
                header = parts
            elif header:
                row_dict = {}
                for i, h in enumerate(header):
                    if i < len(parts):
                        row_dict[h] = parts[i]
                if row_dict:
                    results.append(row_dict)
                    
    return results


import re

def parse_storageservers(text_content):
    results = []
    if not text_content:
        return results
    
    # Pattern to match: prefix(3 chars) + region(4 chars) + node(digits) + domain
    pattern = re.compile(r'^([a-z]{3})([a-z]{4})(\d+)\.(.+)$', re.IGNORECASE)
    
    for line in text_content.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        
        match = pattern.match(line)
        if match:
            prefix, region, node, domain = match.groups()
            results.append({
                "hostname": line,
                "prefix": prefix,
                "region": region,
                "node": int(node),
                "domain": domain
            })
        else:
            results.append({
                "hostname": line
            })
            
    return results


import re

def parse_newprompt(text_content):
    if not text_content:
        return []

    # Find all occurrences of "Role:" to split multiple prompts if they exist
    pattern = re.compile(r'(?:^|\s)Role\s*:', re.IGNORECASE)
    matches = list(pattern.finditer(text_content))

    blocks = []
    if not matches:
        # Fallback: if "Role:" is not found, treat the whole text as a single block
        blocks.append(text_content)
    else:
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text_content)
            blocks.append(text_content[start:end])

    results = []
    for block in blocks:
        # Extract fields using regex with lookaheads to stop at the next field
        role_match = re.search(
            r'(?:^|\s)Role\s*:\s*(.*?)(?=(?:^|\s)Task\s*:|(?:^|\s)Output Requirement\s*:|(?:^|\s)Data Dictionary|(?:^|\s)Role\s*:|$)', 
            block, 
            re.DOTALL | re.IGNORECASE
        )
        task_match = re.search(
            r'(?:^|\s)Task\s*:\s*(.*?)(?=(?:^|\s)Output Requirement\s*:|(?:^|\s)Data Dictionary|(?:^|\s)Role\s*:|$)', 
            block, 
            re.DOTALL | re.IGNORECASE
        )
        out_match = re.search(
            r'(?:^|\s)Output Requirement\s*:\s*(.*?)(?=(?:^|\s)Data Dictionary|(?:^|\s)Role\s*:|(?:^|\s)Task\s*:|$)', 
            block, 
            re.DOTALL | re.IGNORECASE
        )
        data_match = re.search(
            r'(?:^|\s)Data Dictionary & Extraction Logic\s*:\s*(.*?)(?=(?:^|\s)Role\s*:|(?:^|\s)Task\s*:|(?:^|\s)Output Requirement\s*:|$)', 
            block, 
            re.DOTALL | re.IGNORECASE
        )

        role = role_match.group(1).strip() if role_match else ""
        task = task_match.group(1).strip() if task_match else ""
        output_requirement = out_match.group(1).strip() if out_match else ""
        data_dictionary = data_match.group(1).strip() if data_match else ""

        # Skip empty blocks, or capture raw text if no fields matched but content exists
        if not any([role, task, output_requirement, data_dictionary]):
            if block.strip():
                results.append({
                    "role": "",
                    "task": block.strip(),
                    "output_requirement": "",
                    "data_dictionary_raw": ""
                })
            continue

        results.append({
            "role": role,
            "task": task,
            "output_requirement": output_requirement,
            "data_dictionary_raw": data_dictionary
        })

    return results


def parse_alliplist(text_content):
    if not text_content:
        return []
    
    results = []
    for line in text_content.strip().splitlines():
        ip = line.strip()
        if ip:
            results.append({"ip": ip})
    return results


import re

def parse_allippingresults(text_content):
    results = []
    # Regex to capture the IP address and the trailing status text
    pattern = re.compile(r'^\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(.*)$')
    
    for line in text_content.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            ip = match.group(1)
            status_text = match.group(2).lower()
            
            # Determine status based on presence of 'not' or 'reach'
            if 'not' in status_text:
                status = 'unreachable'
                reachable = False
            elif 'reach' in status_text:
                status = 'reachable'
                reachable = True
            else:
                status = 'unknown'
                reachable = None
                
            results.append({
                'ip': ip,
                'status': status,
                'reachable': reachable
            })
            
    return results


import re

def parse_allserverspingresults(text_content):
    # Split the input text into blocks for each ping attempt
    # This split matches the word "Pinging" at a word boundary
    parts = re.split(r'\bPinging\s+', text_content)
    results = []
    
    for part in parts:
        if not part.strip():
            continue
        
        # Extract the host/IP from the start of the block
        host_match = re.match(r'^([^\s:]+)', part)
        if not host_match:
            continue
        host = host_match.group(1)
        
        # Initialize the entry with default None values
        entry = {
            "host": host,
            "bytes": None,
            "reply_from": None,
            "reply_bytes": None,
            "reply_time_ms": None,
            "ttl": None,
            "packets_sent": None,
            "packets_received": None,
            "packets_lost": None,
            "packet_loss_pct": None,
            "min_rtt_ms": None,
            "max_rtt_ms": None,
            "avg_rtt_ms": None,
            "status": "Unknown"
        }
        
        # Parse the 'bytes of data' from the initial ping command
        bytes_match = re.search(r'with\s+(\d+)\s+bytes\s+of\s+data', part, re.IGNORECASE)
        if bytes_match:
            entry["bytes"] = int(bytes_match.group(1))
            
        # Check for common failure states
        if "Request timed out" in part:
            entry["status"] = "Timed Out"
        elif "Destination host unreachable" in part:
            entry["status"] = "Unreachable"
            
        # Parse successful reply line: "Reply from 172.31.0.100: bytes=32 time=2ms TTL=59"
        # Handles both "time=2ms" and "time<1ms"
        reply_match = re.search(
            r'Reply\s+from\s+([^:]+):\s+bytes=(\d+)\s+time[=<]\s*(\d+)ms\s+TTL=(\d+)', 
            part, 
            re.IGNORECASE
        )
        if reply_match:
            entry["status"] = "Success"
            entry["reply_from"] = reply_match.group(1)
            entry["reply_bytes"] = int(reply_match.group(2))
            entry["reply_time_ms"] = int(reply_match.group(3))
            entry["ttl"] = int(reply_match.group(4))
            
        # Parse packet statistics: "Packets: Sent = 1, Received = 1, Lost = 0 (0% loss)"
        packets_match = re.search(
            r'Packets:\s+Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)\s*\((\d+)%\s+loss\)', 
            part, 
            re.IGNORECASE
        )
        if packets_match:
            entry["packets_sent"] = int(packets_match.group(1))
            entry["packets_received"] = int(packets_match.group(2))
            entry["packets_lost"] = int(packets_match.group(3))
            entry["packet_loss_pct"] = int(packets_match.group(4))
            
        # Parse round trip times (with ms suffix)
        rtt_match = re.search(
            r'Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms', 
            part, 
            re.IGNORECASE
        )
        if rtt_match:
            entry["min_rtt_ms"] = int(rtt_match.group(1))
            entry["max_rtt_ms"] = int(rtt_match.group(2))
            entry["avg_rtt_ms"] = int(rtt_match.group(3))
        else:
            # Fallback for round trip times without 'ms' suffix in the numbers
            rtt_match_no_ms = re.search(
                r'Minimum\s*=\s*(\d+),\s*Maximum\s*=\s*(\d+),\s*Average\s*=\s*(\d+)', 
                part, 
                re.IGNORECASE
            )
            if rtt_match_no_ms:
                entry["min_rtt_ms"] = int(rtt_match_no_ms.group(1))
                entry["max_rtt_ms"] = int(rtt_match_no_ms.group(2))
                entry["avg_rtt_ms"] = int(rtt_match_no_ms.group(3))
                
        results.append(entry)
        
    return results


import re

def parse_opensshprocedure(text_content):
    def is_header(line):
        line = line.strip()
        if not line:
            return False
        if re.match(r'^\d+\)', line):
            return False
        if line[-1] in ('.', ':', ',', ')', '"', "'", '\\', '/'):
            return False
        if len(line) > 60:
            return False
        if not line[0].isupper():
            return False
        return True

    url_pattern = re.compile(r'https?://[^\s]+')
    cmd_pattern = re.compile(r'(?:^|>\s*)(cd\s+|mkdir\s+|ssh-keygen(?:\.exe)?\s+|type\s+|ssh\s+)(.*)', re.IGNORECASE)
    note_pattern = re.compile(r'(Note:|Example:)(.*?)(?=(?:Note:|Example:|\Z))', re.DOTALL | re.IGNORECASE)

    parts = re.split(r'(\d+\)\s+)', text_content)
    if not parts:
        return []

    current_section = None
    for line in parts[0].splitlines():
        if is_header(line):
            current_section = line.strip()

    steps_list = []
    for i in range(1, len(parts), 2):
        step_num_str = parts[i].strip().replace(')', '')
        try:
            step_num = int(step_num_str)
        except ValueError:
            continue

        raw_body = parts[i+1] if i+1 < len(parts) else ""

        lines = raw_body.splitlines()
        step_lines = []
        trailing_headers = []
        in_header_zone = True
        for line in reversed(lines):
            if not line.strip():
                if in_header_zone:
                    continue
                else:
                    step_lines.append(line)
            elif in_header_zone and is_header(line):
                trailing_headers.append(line.strip())
            else:
                in_header_zone = False
                step_lines.append(line)

        step_lines.reverse()
        trailing_headers.reverse()
        step_body = "\n".join(step_lines).strip()

        urls = url_pattern.findall(step_body)

        note_matches = list(note_pattern.finditer(step_body))
        notes = []
        instruction_text = step_body
        spans = [m.span() for m in note_matches]
        spans.sort(reverse=True)
        for start, end in spans:
            note_text = step_body[start:end].strip()
            notes.append(note_text)
            instruction_text = instruction_text[:start] + instruction_text[end:]

        commands = []
        for line in step_body.splitlines():
            line_strip = line.strip()
            if not line_strip:
                continue
            cmd_match = cmd_pattern.search(line_strip)
            if cmd_match:
                cmd = cmd_match.group(1) + cmd_match.group(2)
                commands.append(cmd.strip())

        instruction_lines = []
        for line in instruction_text.splitlines():
            line_strip = line.strip()
            if not line_strip:
                continue
            if cmd_pattern.search(line_strip):
                continue
            instruction_lines.append(line)
        instruction = "\n".join(instruction_lines).strip()

        steps_list.append({
            'step': step_num,
            'section': current_section,
            'instruction': instruction,
            'commands': commands,
            'urls': urls,
            'notes': notes,
            'raw_text': (parts[i] + raw_body).strip()
        })

        if trailing_headers:
            current_section = trailing_headers[0]

    return steps_list


import re

def parse_readme(text_content):
    lines = text_content.splitlines()
    entries = []
    current_title = None
    current_content = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if the next line is an underline of '=' of at least length 3
        if i + 1 < len(lines) and re.match(r'^=+$', lines[i+1].strip()) and len(lines[i+1].strip()) >= 3:
            if current_title is not None:
                entries.append({
                    'title': current_title,
                    'content': '\n'.join(current_content).strip()
                })
            current_title = line
            current_content = []
            i += 2  # Skip the underline
            continue
        
        if current_title is not None:
            current_content.append(lines[i])
        i += 1

    if current_title is not None:
        entries.append({
            'title': current_title,
            'content': '\n'.join(current_content).strip()
        })

    return entries


import re

def parse_releasenotes(text_content):
    if not text_content:
        return []

    lines = text_content.splitlines()
    sections = []
    
    # Initialize preamble section for any text before the first formal section
    current_section = {
        "section_id": None,
        "title": "Preamble",
        "paragraphs": [],
        "list_items": []
    }
    
    header_regex = re.compile(r'^\s*(\d+(?:\.\d+)*)\.?\s+(.*?)\s*$')
    divider_regex = re.compile(r'^\s*[-=~_]{3,}\s*$')
    bullet_regex = re.compile(r'^\s*[\*\-•]\s+(.*)$')
    
    current_para = []
    
    def flush_para():
        if current_para:
            para_text = " ".join(current_para).strip()
            if para_text:
                current_section["paragraphs"].append(para_text)
            current_para.clear()
            
    for line in lines:
        # Skip divider lines (like dashes under headers)
        if divider_regex.match(line):
            continue
            
        # Check for section headers (e.g., "1. Introduction" or "2.1 Supported...")
        header_match = header_regex.match(line)
        if header_match:
            flush_para()
            # Save the previous section if it has any collected content
            if current_section["paragraphs"] or current_section["list_items"] or (current_section["section_id"] is not None):
                sections.append(current_section)
                
            sec_id = header_match.group(1)
            sec_title = header_match.group(2).rstrip(':').strip()
            current_section = {
                "section_id": sec_id,
                "title": sec_title,
                "paragraphs": [],
                "list_items": []
            }
            continue
            
        # Check for bullet points
        bullet_match = bullet_regex.match(line)
        if bullet_match:
            flush_para()
            current_section["list_items"].append(bullet_match.group(1).strip())
            continue
            
        # Handle regular text and paragraphs
        stripped = line.strip()
        if not stripped:
            flush_para()
        else:
            current_para.append(stripped)
            
    flush_para()
    # Append the last active section
    if current_section["paragraphs"] or current_section["list_items"] or (current_section["section_id"] is not None):
        sections.append(current_section)
        
    # Remove preamble if it ended up completely empty
    if sections and sections[0]["section_id"] is None and not sections[0]["paragraphs"] and not sections[0]["list_items"]:
        sections.pop(0)
        
    return sections


import re

def parse_perfstatgui(text_content):
    results = []
    if not text_content:
        return results
    
    pattern = re.compile(
        r'^\[\[(?P<timestamp>[\d\-:,\s]+)\]:(?P<filename>[^:]+):(?P<line>\d+)\s*-\s*(?P<function>[^\]]+)\]\s*(?P<message>.*)$'
    )
    
    for line in text_content.splitlines():
        line = line.strip()
        if not line:
            continue
        match = pattern.match(line)
        if match:
            gd = match.groupdict()
            results.append({
                "timestamp": gd["timestamp"].strip(),
                "filename": gd["filename"].strip(),
                "line": int(gd["line"]),
                "function": gd["function"].strip(),
                "message": gd["message"].strip()
            })
            
    return results


import re

def parse_howtorun(text_content):
    # Regular expression to match PowerShell prompt and the command on the same line
    # e.g., "PS C:\WINDOWS\system32> Set-ExecutionPolicy..."
    prompt_pattern = re.compile(r'^(PS\s+[A-Za-z]:\\[^>]*>)\s*(.*)$', re.MULTILINE)
    
    matches = list(prompt_pattern.finditer(text_content))
    parsed_steps = []
    
    for i, match in enumerate(matches):
        prompt = match.group(1).strip()
        command = match.group(2).strip()
        
        # The output for this command is everything between the end of this command line
        # and the start of the next prompt (or end of the text if it's the last command).
        start_pos = match.end()
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(text_content)
            
        output = text_content[start_pos:end_pos].strip()
        
        parsed_steps.append({
            'prompt': prompt,
            'command': command,
            'output': output
        })
        
    return parsed_steps


import re

def parse_windowspowershell(text_content):
    prompt_pattern = re.compile(r"^PS\s+([^>]+)>\s*(.*)$")
    
    lines = text_content.splitlines()
    parsed_commands = []
    
    current_dir = None
    current_cmd = None
    current_output = []
    
    for line in lines:
        match = prompt_pattern.match(line)
        if match:
            if current_cmd is not None:
                parsed_commands.append({
                    "directory": current_dir,
                    "command": current_cmd,
                    "output": "\n".join(current_output).rstrip()
                })
            current_dir = match.group(1).strip()
            current_cmd = match.group(2).strip()
            current_output = []
        else:
            if current_cmd is not None:
                current_output.append(line)
                
    if current_cmd is not None:
        parsed_commands.append({
            "directory": current_dir,
            "command": current_cmd,
            "output": "\n".join(current_output).rstrip()
        })
        
    return parsed_commands


import re

def parse_ocumreq(text_content):
    # Extract global AIQUM version if available
    aiqum_match = re.search(r"Compatible common AIQUM version[^-\n]*-\s*([^\n]+)", text_content, re.IGNORECASE)
    aiqum_version = aiqum_match.group(1).strip() if aiqum_match else None

    # Split by separator lines of '='
    blocks = re.split(r'=+', text_content)
    results = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        
        # Pattern to match: Name: Type , ONTAP <version>
        match = re.match(r"^([^:]+):\s*([^,]+),\s*(.*)$", lines[0])
        if match:
            name = match.group(1).strip()
            env_type = match.group(2).strip()
            ontap = match.group(3).strip()
            platform = " ".join(lines[1:]) if len(lines) > 1 else ""
            
            record = {
                "name": name,
                "type": env_type,
                "ontap": ontap,
                "platform": platform
            }
            if aiqum_version:
                record["aiqum_version"] = aiqum_version
            results.append(record)
            
    return results


import re

def parse_adhoc(text_content):
    records = []
    pattern = r'row (\d+) ; node show -fields serial ; exit ;'
    for line in text_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            record = {'row': int(match.group(1))}
            records.append(record)
    return records


import re

def parse_asupcmd(text_content):
    records = []
    pattern = r'(\S+)\s+(\S+)\s+-node\s+(\S+)\s+-type\s+(\S+)\s+-message\s+"([^"]+)"\s*;.*'
    for line in text_content.splitlines():
        match = re.match(pattern, line)
        if match:
            records.append({
                'command': match.group(1),
                'subcommand': match.group(2),
                'node': match.group(3),
                'type': match.group(4),
                'message': match.group(5)
            })
    return records


import re

def parse_servernames(text_content):
    pattern = r'([A-Za-z]{2}\d{2})\s+(\S+)'
    return [dict(servername=match.group(2), code=match.group(1)) for line in text_content.splitlines() if (match := re.match(pattern, line))]


import re

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

def parse_tafcopscmdinstallconfigurev(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if line.startswith('[') and line.endswith(']'):
            continue
        match = re.match(r'^(?P<timestamp>\S+\s\S+)\s(?P<command>.+)$', line)
        if match:
            records.append(match.groupdict())
    return records


import re

def parse_saudit(text_content):
    records = []
    lines = text_content.strip().split('\n')
    for line in lines:
        if line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.'):
            parts = line.split(':')
            if len(parts) >= 2:
                key = parts[0].strip()
                value = ':'.join(parts[1:]).strip()
                records.append({key: value})
    return records


import re

def parse_obj(text_content):
    records = []
    lines = text_content.strip().split('\n')
    current_record = {}
    
    for line in lines:
        if line.startswith('login as:'):
            current_record['user'] = line.split(': ')[1]
        elif line.startswith('Last login time:'):
            current_record['last_login_time'] = line.split(': ')[1]
        elif line.startswith('vol modify -volume'):
            match = re.match(r'vol modify -volume (\S+) (-\w+)(?: -(\S+))?', line)
            if match:
                volume, key, value = match.groups()
                current_record[f'vol_modify_{key}'] = value if value else True
        elif line.startswith('export-policy show'):
            match = re.match(r'Vserver\s+(\S+)\s+Policy Name\s+(\S+)', line)
            if match:
                vserver, policy_name = match.groups()
                current_record[f'export_policy_{vserver}_{policy_name}'] = True
        elif line.startswith('export-policy rule show'):
            match = re.match(r'\s+Vserver:\s+(\S+)\s+Policy Name:\s+(\S+)\s+Rule Index:\s+(\d+)', line)
            if match:
                vserver, policy_name, rule_index = match.groups()
                current_record[f'export_policy_rule_{vserver}_{policy_name}_{rule_index}'] = True
        elif line.startswith('nfs status'):
            match = re.match(r'The NFS server is running on Vserver "(.+)"', line)
            if match:
                vserver = match.group(1)
                current_record[f'nfs_status_{vserver}'] = True
        elif line.startswith('nfs off -vserver'):
            match = re.match(r'nfs off -vserver (\S+)', line)
            if match:
                vserver = match.group(1)
                current_record[f'nfs_off_{vserver}'] = True
        elif line.startswith('nfs stop -vserver'):
            match = re.match(r'nfs stop -vserver (\S+)', line)
            if match:
                vserver = match.group(1)
                current_record[f'nfs_stop_{vserver}'] = True
        elif line.startswith('nfs on -vserver'):
            match = re.match(r'nfs on -vserver (\S+)', line)
            if match:
                vserver = match.group(1)
                current_record[f'nfs_on_{vserver}'] = True
        elif line.startswith('nfs start -vserver'):
            match = re.match(r'nfs start -vserver (\S+)', line)
            if match:
                vserver = match.group(1)
                current_record[f'nfs_start_{vserver}'] = True
        elif line.startswith('export-policy check-acc'):
            current_record['export_policy_check_acc'] = True
        
        if not line.strip():
            records.append(current_record)
            current_record = {}
    
    if current_record:
        records.append(current_record)
    
    return records


import re

def parse_object(text_content):
    records = []
    lines = text_content.strip().split('\n')
    current_record = {}
    
    for line in lines:
        if line.startswith('vserver'):
            if current_record:
                records.append(current_record)
            current_record = {'vserver': line.split()[0]}
        elif line.startswith('prodfassvm') or line.startswith('prodfas2*'):
            continue
        elif line.strip():
            fields = line.split()
            for i in range(1, len(fields)):
                key = re.sub(r'[^a-zA-Z0-9_]', '_', fields[0].replace('-', '_'))
                value = fields[i]
                current_record[key] = value
    
    if current_record:
        records.append(current_record)
    
    return records


import re

def parse_migrationstepsformigrationactivity(text_content):
    records = []
    lines = text_content.strip().split('\n')
    current_record = {}
    
    for line in lines:
        if line.startswith('STEPS:'):
            continue
        elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.') or line.startswith('6.') or line.startswith('7.') or line.startswith('8.') or line.startswith('9.') or line.startswith('10.') or line.startswith('11.') or line.startswith('12.'):
            if current_record:
                records.append(current_record)
            current_record = {'step': line.strip('.').strip()}
        elif line.startswith('::>'):
            command = line.strip().lstrip('::>')
            current_record['command'] = command
        else:
            if 'description' in current_record:
                current_record['description'] += '\n' + line.strip()
            else:
                current_record['description'] = line.strip()
    
    if current_record:
        records.append(current_record)
    
    return records


import re

def parse_ceirlabfcnewconfigformigrationofceirlabfc(text_content):
    records = []
    pattern = re.compile(r'Vserver Name:\s+(?P<vserver_name>.+?)\n\s*Igroup Name:\s+(?P<igroup_name>.+?)\n\s*Protocol:\s+(?P<protocol>.+?)\n\s*OS Type:\s+(?P<os_type>.+?)\n\s*Initiators:\s+(?P<initiators>.+)', re.DOTALL)
    for match in pattern.finditer(text_content):
        record = {
            'vserver_name': match.group('vserver_name').strip(),
            'igroup_name': match.group('igroup_name').strip(),
            'protocol': match.group('protocol').strip(),
            'os_type': match.group('os_type').strip(),
            'initiators': [initiator.strip() for initiator in match.group('initiators').split('\n') if initiator.strip()]
        }
        records.append(record)
    return records
