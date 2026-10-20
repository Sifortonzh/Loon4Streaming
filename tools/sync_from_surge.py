#!/usr/bin/env python3
"""Generate a routing-only Loon profile from the public Surge shared template."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SURGE = ROOT.parent / 'Config4Streaming/templates/Surge.shared.conf'
OUTPUT = ROOT / 'Loon4Streaming_rebuilt.conf'
LOCAL = ROOT / '.loon-sync'
TEST_URL = 'http://cp.cloudflare.com/generate_204'
REGIONS = {
    'HK': r'🇭🇰|香港|Hong[ -]?Kong|(?<![A-Za-z])HK(?:G)?(?![A-Za-z])',
    'US': r'🇺🇸|🇺🇲|美国|美國|United[ -]?States|America|(?<![A-Za-z])US(?:A)?(?![A-Za-z])',
    'SG': r'🇸🇬|新加坡|Singapore|(?<![A-Za-z])SG(?:P)?(?![A-Za-z])',
    'JP': r'🇯🇵|日本|东京|東京|大阪|Japan|(?<![A-Za-z])JP(?:N)?(?![A-Za-z])',
    'TW': r'🇹🇼|台湾|台灣|台北|Taiwan|(?<![A-Za-z])TW(?:N)?(?![A-Za-z])',
    'KR': r'🇰🇷|韩国|韓國|首尔|首爾|Korea|Seoul|(?<![A-Za-z])(?:KR|KOR|SK)(?![A-Za-z])',
    'UK': r'🇬🇧|英国|英國|伦敦|倫敦|United[ -]?Kingdom|Britain|(?<![A-Za-z])(?:UK|GB|GBR)(?![A-Za-z])',
    'DE': r'🇩🇪|德国|德國|Germany|(?<![A-Za-z])DE(?:U)?(?![A-Za-z])',
    'FR': r'🇫🇷|法国|法國|France|(?<![A-Za-z])FR(?:A)?(?![A-Za-z])',
    'AU': r'🇦🇺|澳大利亚|澳大利亞|澳洲|Australia|(?<![A-Za-z])AU(?:S)?(?![A-Za-z])',
    'CA': r'🇨🇦|加拿大|Canada|(?<![A-Za-z])CA(?:N)?(?![A-Za-z])',
    'MO': r'🇲🇴|澳门|澳門|Maca[ou]|(?<![A-Za-z])MO(?![A-Za-z])',
    'IN': r'🇮🇳|印度|India|(?<![A-Za-z])IN(?:D)?(?![A-Za-z])',
    'MY': r'🇲🇾|马来西亚|馬來西亞|Malaysia|(?<![A-Za-z])MY(?:S)?(?![A-Za-z])',
    'PH': r'🇵🇭|菲律宾|菲律賓|Philippines|(?<![A-Za-z])PH(?:L)?(?![A-Za-z])',
}
GROUP_REGION = dict(zip(('🇭🇰Hong Kong', '🇺🇸United States', '🇸🇬Singapore', '🇯🇵Japan', '🇨🇳Taiwan', '🇰🇷South Korea', '🇬🇧United Kingdom', '🇩🇪Germany', '🇫🇷France', '🇦🇺Australia', '🇨🇦Canada', '🇲🇴Macau', '🇮🇳India', '🇲🇾Malaysia', '🇵🇭Philippines'), REGIONS))
META = r'群|邀请|邀請|返利|官网|官網|客服|订阅|訂閱|流量|总计|總計|到期|过期|過期|剩余|剩餘|重置|工单|工單|通知|教程|Traffic|Expire'
SUPPORTED = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'DOMAIN-WILDCARD', 'IP-CIDR', 'IP-CIDR6', 'IP-ASN', 'GEOIP', 'USER-AGENT', 'URL-REGEX', 'PROCESS-NAME', 'PROCESS-PATH'}
ALLOWED_URL_HOSTS = {'raw.githubusercontent.com'}


def parts(line):
    # Split outside quotes; unlike csv, preserves regex backslashes and += text.
    return [s.strip().strip('"') for s in re.split(r',(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)', line)]


def sections(text):
    out, section = {}, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            out[section] = []
        elif section and line and not line.startswith(('#', ';')):
            out[section].append(line)
    return out


def write(path, data, private=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.' + path.name)
    try:
        os.fchmod(fd, 0o600 if private else 0o644)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def fetch(url, offline=False, refresh=False):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ALLOWED_URL_HOSTS or parsed.query or parsed.username:
        raise ValueError('Only public, credential-free raw GitHub resources are accepted')
    cache = LOCAL / 'cache' / hashlib.sha256(url.encode()).hexdigest()
    if cache.exists() and (offline or (not refresh and time.time() - cache.stat().st_mtime < 3600)):
        return cache.read_text()
    if offline:
        raise ValueError('Missing cached public resource: ' + url)
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Loon4Streaming-sync/1.0'}), timeout=30) as response:
                text = response.read().decode('utf-8-sig')
            if not text.strip() or '<html' in text[:200].lower():
                raise ValueError('Empty or HTML rule response: ' + url)
            write(cache, text, private=True)
            return text
        except Exception:
            if attempt == 2:
                raise ValueError('Public resource download failed; no output replaced: ' + url)
    raise AssertionError('unreachable')


def pattern(region):
    if region == 'ALL':
        return '(?i)^(?!.*(?:' + META + ')).+$'
    if region == 'RA':
        return '(?i)^(?!.*(?:' + META + '|' + '|'.join(REGIONS.values()) + ')).+$'
    return '(?i)^(?!.*(?:' + META + ')).*(?:' + REGIONS[region] + ')'


def convert_rule(line, policy):
    if line.startswith(('OR,', 'AND,', 'NOT,')):
        kind, rest = line.split(',', 1)
        depth = 0
        for i, char in enumerate(rest):
            depth += (char == '(') - (char == ')')
            if depth == 0:
                if not rest.startswith('('):
                    break
                return kind + ',' + rest[:i + 1] + ',' + policy
        raise ValueError('Invalid logical rule expression')
    row = parts(line)
    if len(row) < 2 or row[0] not in SUPPORTED:
        raise ValueError('Unsupported rule type (not silently dropped): ' + row[0])
    kind, value = row[:2]
    if kind in ('IP-CIDR', 'IP-CIDR6'):
        ipaddress.ip_network(value, strict=False)
    # Surge external lists may already contain a policy. The caller's policy wins.
    options = [s for s in row[2:] if s == 'no-resolve']
    return ','.join([kind, value, policy, *options])


def groups(source):
    result, names = [], []
    if not any(line.split('=', 1)[0].strip() == 'Privilege' for line in source['Proxy Group']):
        result.append('Privilege = select,Sub-ALL')
        names.append('Privilege')
    for line in source['Proxy Group']:
        name, value = line.split('=', 1)
        name = name.strip()
        row = parts(value)
        names.append(name)
        opts = {t.split('=', 1)[0].strip(): t.split('=', 1)[1].strip() for t in row[1:] if '=' in t}
        icon = opts.get('icon-url') or opts.get('icon')
        if name == 'Privilege':
            out = ['select', 'Sub-ALL']
        elif row[0] == 'smart':
            region = 'RA' if name == '🇺🇳Rare Areas' else GROUP_REGION[name]
            out = ['url-test', 'Sub-' + region, 'url=' + TEST_URL, 'interval=600', 'tolerance=100']
        elif row[0] == 'select':
            out = ['select', *[v for v in row[1:] if '=' not in v]]
        else:
            raise ValueError('Unsupported Surge group: ' + name)
        if icon:
            out.append('img-url=' + icon)
        result.append(name + ' = ' + ','.join(out))
    allowed = set(names) | {'DIRECT', 'REJECT', 'REJECT-DROP'}
    for line in result:
        for child in parts(line.split('=', 1)[1])[1:]:
            if '=' not in child and child not in allowed and not child.startswith('Sub-'):
                raise ValueError('Unknown child group: ' + child)
    return result, names


def lan_rules():
    return ['IP-CIDR,' + subnet + ',DIRECT,no-resolve' for subnet in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', '127.0.0.0/8', '169.254.0.0/16', '100.64.0.0/10')]


def generate(surge_text, resources):
    source = sections(surge_text)
    group_lines, names = groups(source)
    rules, dropped, manifest = [], [], []
    for line in source['Rule']:
        row = parts(line)
        if row[0] in ('RULE-SET', 'DOMAIN-SET'):
            url, policy = row[1:3]
            if url == 'LAN':
                rules.extend(lan_rules())
                continue
            converted, ignored = [], []
            for raw in resources[url].splitlines():
                raw = raw.strip()
                if not raw or raw.startswith(('#', ';', '//')):
                    continue
                if row[0] == 'DOMAIN-SET':
                    if ',' in raw or not re.fullmatch(r'\.?[A-Za-z0-9_.-]+', raw):
                        raise ValueError('Invalid domain-set entry')
                    converted.append(('DOMAIN-SUFFIX,' if raw.startswith('.') else 'DOMAIN,') + raw.lstrip('.') + ',' + policy)
                    continue
                # iPad cannot match macOS process names; use domain/IP rules.
                if parts(raw)[0] in ('PROCESS-NAME', 'PROCESS-PATH'):
                    ignored.append(raw.split(',', 1)[0])
                    continue
                converted.append(convert_rule(raw, policy))
            if not converted:
                raise ValueError('Rule source has no usable rules: ' + url)
            rules.append('# Source: ' + url + ' → ' + policy)
            rules.extend(converted)
            manifest.append({'url': url, 'policy': policy, 'rules': len(converted), 'sha256': hashlib.sha256(resources[url].encode()).hexdigest(), 'process_rules_omitted': len(ignored)})
        elif row[0] in ('PROCESS-NAME', 'PROCESS-PATH'):
            dropped.append(line)
        elif row[0] == 'FINAL':
            rules.append('FINAL,' + row[1])
        else:
            rules.append(convert_rule(line, row[2]))
    allowed = set(names) | {'DIRECT', 'REJECT', 'REJECT-DROP'}
    for rule in rules:
        if rule.startswith('#'):
            continue
        policy = rule.rsplit(',', 1)[1] if rule.startswith(('FINAL,', 'OR,', 'AND,', 'NOT,')) else parts(rule)[2]
        if policy not in allowed:
            raise ValueError('Missing rule policy: ' + policy)
    header = '''# Generated from the public Surge shared template. Do not paste private subscriptions here.
# Import with Keep Nodes/Subscriptions enabled, or replace the example URLs below.
# Node filters deliberately include ALL enabled subscriptions regardless of their alias.
# Rules are expanded into a single local sequence to avoid Loon local/remote priority changes.
# Loon still evaluates domain rules before IP rules (native engine behavior).
# No plugins, rewrites, MitM or third-party subscription converters are enabled.

[General]
ip-mode = ipv4-only
ipv6-vif = off
dns-server = system,223.5.5.5,119.29.29.29
doh-server = https://dns.alidns.com/dns-query,https://doh.pub/dns-query
hijack-dns = *:53
test-timeout = 5
proxy-test-url = http://cp.cloudflare.com/generate_204
internet-test-url = http://www.baidu.com
allow-wifi-access = false
udp-fallback-mode = REJECT
domain-reject-mode = Request
dns-reject-mode = NXDOMAIN
skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,127.0.0.1,localhost,*.local
bypass-tun = 10.0.0.0/8,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.168.0.0/16,100.64.0.0/10

[Proxy]

[Remote Proxy]
# Disabled placeholders. Use the provider's LOON subscription, not its Surge full profile.
MESL = https://example.com/loon-mesl,enabled=false
SNTP = https://example.com/loon-sntp,enabled=false

[Remote Filter]
'''
    filters = ['Sub-' + region + ' = NameRegex,FilterKey="' + pattern(region) + '"' for region in ('ALL', *REGIONS, 'RA')]
    result = header + '\n'.join(filters) + '\n\n[Proxy Group]\n' + '\n'.join(group_lines) + '\n\n[Rule]\n' + '\n'.join(rules) + '\n'
    report = {'source_sha256': hashlib.sha256(surge_text.encode()).hexdigest(), 'groups': names, 'rule_count': sum(not r.startswith('#') for r in rules), 'sources': manifest, 'omitted_local_macos_process_rules': len(dropped), 'limitations': ['Domain rules take precedence over IP rules in the Loon engine.', 'url-test selects lowest test latency; it does not reproduce Surge smart or test streaming unlock.', 'Run on-device subscription updates, filter checks and playback checks after import.']}
    return result, report


def validate_icons(group_lines, offline=False):
    icons = list(dict.fromkeys(re.findall(r'img-url=(https://[^,\s]+)', '\n'.join(group_lines))))
    def check(url):
        # Use a ranged GET; some raw GitHub edges do not handle HEAD reliably.
        if offline:
            return
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers={'User-Agent': 'Loon4Streaming', 'Range': 'bytes=0-31'}), timeout=20) as response:
                    if response.read(8) != b'\x89PNG\r\n\x1a\n':
                        raise ValueError('not PNG')
                return
            except Exception:
                if attempt == 2:
                    raise ValueError('Icon unavailable: ' + url)
    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(check, icons))
    return len(icons)


def private_config(generated, private_text):
    private_sections = sections(private_text)
    if not private_sections.get('Remote Proxy'):
        raise ValueError('No subscriptions in private source; refusing an empty private export')
    chunks = re.split(r'(?m)^(\[[^]\n]+\])\s*$', generated)
    for index in range(1, len(chunks), 2):
        key = chunks[index][1:-1]
        if key in ('Proxy', 'Remote Proxy'):
            chunks[index + 1] = '\n' + '\n'.join(private_sections.get(key, [])) + '\n\n'
    return ''.join(chunks)


def main():
    parser = argparse.ArgumentParser(description='Generate Loon from Surge; default is preview only.')
    parser.add_argument('--source', type=Path, default=SURGE)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--private-profile', type=Path, help='Copy ONLY local/remote nodes from an existing Loon profile into ignored private output')
    args = parser.parse_args()
    if args.publish and (not args.apply or args.offline):
        parser.error('--publish requires --apply and online validation')
    text = args.source.read_text(encoding='utf-8')
    # Accept ONLY a public source; never ingest a live Surge/iCloud file.
    if re.search(r'(?i)(?:policy-path\s*=\s*(?!https://example\.com)[^,\s]+|ca-p12\s*=|ca-passphrase\s*=|[?&](?:token|sign|password|key)=)', text):
        raise ValueError('Source contains private fields; select the sanitized shared template instead')
    LOCAL.mkdir(exist_ok=True, mode=0o700)
    os.chmod(LOCAL, 0o700)
    subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', '.loon-sync/state.json'], check=True)
    urls = list(dict.fromkeys(parts(l)[1] for l in sections(text)['Rule'] if l.startswith(('RULE-SET,', 'DOMAIN-SET,')) and parts(l)[1] != 'LAN'))
    with ThreadPoolExecutor(max_workers=8) as pool:
        contents = dict(zip(urls, pool.map(lambda u: fetch(u, args.offline, args.refresh), urls)))
    generated, report = generate(text, contents)
    report['verified_icons'] = validate_icons(groups(sections(text))[0], args.offline)
    report['output_sha256'] = hashlib.sha256(generated.encode()).hexdigest()
    old_report = ROOT / 'validation-report.json'
    if old_report.exists() and OUTPUT.exists():
        expected = json.loads(old_report.read_text()).get('output_sha256')
        if expected and hashlib.sha256(OUTPUT.read_bytes()).hexdigest() != expected:
            raise ValueError('Generated output was manually edited; merge edits into Surge first. No file replaced.')
    targets = {OUTPUT: generated, ROOT / 'validation-report.json': json.dumps(report, ensure_ascii=False, indent=2) + '\n'}
    changed = [p for p, content in targets.items() if not p.exists() or p.read_text() != content]
    print(f'Validated: {len(report["groups"])} groups, {report["rule_count"]} rules, {len(urls)} public rule sources, {report["verified_icons"]} icons. Changed files: {len(changed)}')
    if not args.apply:
        print('Preview only. Use --apply to save; --apply --publish to push GitHub.')
        return
    if args.source.read_text(encoding='utf-8') != text:
        raise ValueError('Source changed during generation; retry. No output replaced.')
    if changed:
        backup = LOCAL / 'backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup.mkdir(parents=True, mode=0o700)
        for path in changed:
            if path.exists():
                shutil.copy2(path, backup / path.name)
        for path in changed:
            write(path, targets[path])
        print('Saved with backup: ' + str(backup))
    if args.private_profile:
        # No upload or remote subscription conversion: credentials remain local.
        private_text = args.private_profile.read_text(encoding='utf-8')
        if args.private_profile.is_symlink() or '[Remote Proxy]' not in private_text:
            raise ValueError('Expected a regular local Loon profile with Remote Proxy section')
        private_generated = private_config(generated, private_text)
        private_output = LOCAL / 'Loon4Streaming.private.conf'
        if private_output.exists():
            backup = LOCAL / 'backups' / datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            backup.mkdir(parents=True, mode=0o700)
            shutil.copy2(private_output, backup / private_output.name)
        write(private_output, private_generated, private=True)
        print('Private import profile saved locally: ' + str(private_output))
    if args.publish:
        if subprocess.check_output(['git', '-C', str(ROOT), 'diff', '--cached', '--name-only'], text=True).strip():
            raise ValueError('Existing staged changes; refusing to publish them')
        remote = subprocess.check_output(['git', '-C', str(ROOT), 'remote', 'get-url', '--push', 'origin'], text=True).strip()
        if remote != 'git@github.com:Sifortonzh/Loon4Streaming.git':
            raise ValueError('Unexpected publishing target; requires configured SSH repository')
        subprocess.run(['git', '-C', str(ROOT), 'fetch', 'origin', 'main'], check=True)
        subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', 'origin/main', 'HEAD'], check=True)
        allow = ['.gitignore', 'Loon4Streaming_rebuilt.conf', 'tools/sync_from_surge.py', 'tools/test_sync_from_surge.py', 'tools/sync.command', 'validation-report.json', 'README.md', 'README_ZH.md']
        subprocess.run(['git', '-C', str(ROOT), 'add', '--', *allow], check=True)
        subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--check'], check=True)
        if subprocess.run(['git', '-C', str(ROOT), 'diff', '--cached', '--quiet']).returncode:
            subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', 'feat: generate Loon routing and icons from shared Surge template'], check=True)
        subprocess.run(['git', '-C', str(ROOT), 'push', 'origin', 'HEAD:main'], check=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
