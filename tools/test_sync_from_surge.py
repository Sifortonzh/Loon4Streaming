import importlib.util
from pathlib import Path
import re
import unittest

spec = importlib.util.spec_from_file_location('sync', Path(__file__).with_name('sync_from_surge.py'))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class ConverterTests(unittest.TestCase):
    def test_regions_accept_compact_labels_and_exclude_metadata(self):
        samples = {'HK': ['HK01', '香港-09', 'Hong-Kong 家宽'], 'SG': ['SGP05', '新加坡 02'], 'TW': ['🇨🇳 台湾 07', '台灣 01', 'TW2'], 'KR': ['SK01', 'KR03', '韓國'], 'US': ['US08', '🇺🇲 美国'], 'PH': ['PH01', '菲律賓 01'], 'UK': ['GB01', 'UK09']}
        for region, names in samples.items():
            for name in names:
                self.assertRegex(name, sync.pattern(region))
                self.assertNotRegex(name, sync.pattern('RA'))
        for name in ['剩余流量 200GB', '套餐到期', '订阅官网 HK']:
            self.assertNotRegex(name, sync.pattern('ALL'))
        self.assertNotRegex('🇨🇳 中国 北京', sync.pattern('TW'))
        self.assertRegex('🇨🇭 Switzerland 01', sync.pattern('RA'))

    def test_smart_is_converted_and_icons_preserved(self):
        group_lines, names = sync.groups({'Proxy Group': ['🇭🇰Hong Kong = smart, policy-regex-filter=香港', 'Group = select, "🇭🇰Hong Kong", Privilege, icon-url=https://example.com/icon.png']})
        self.assertIn('Privilege', names)
        self.assertIn('🇭🇰Hong Kong = url-test,Sub-HK', '\n'.join(group_lines))
        self.assertIn('img-url=https://example.com/icon.png', '\n'.join(group_lines))
        self.assertNotIn('smart,', '\n'.join(group_lines))

    def test_external_policy_replaced_without_duplicate_fields(self):
        self.assertEqual(sync.convert_rule('DOMAIN-SUFFIX,hayu.com,OLD', 'Hayu'), 'DOMAIN-SUFFIX,hayu.com,Hayu')
        self.assertEqual(sync.convert_rule('IP-CIDR,1.2.3.0/24,no-resolve', 'DIRECT'), 'IP-CIDR,1.2.3.0/24,DIRECT,no-resolve')
        self.assertEqual(sync.convert_rule('OR,((IP-ASN,1,no-resolve),(IP-ASN,2,no-resolve))', 'Telegram'), 'OR,((IP-ASN,1,no-resolve),(IP-ASN,2,no-resolve)),Telegram')
        with self.assertRaises(ValueError):
            sync.convert_rule('UNKNOWN,foo', 'DIRECT')

    def test_rules_order_and_international_streaming(self):
        template = '[Proxy Group]\nGroup = select,Privilege\nBilibili = select,DIRECT\n[Rule]\nRULE-SET,https://raw.githubusercontent.com/example/bili.list,Bilibili\nDOMAIN-SUFFIX,biliintl.com,Bilibili\nRULE-SET,https://raw.githubusercontent.com/example/china.list,DIRECT\nFINAL,Group,dns-failed\n'
        resources = {'https://raw.githubusercontent.com/example/bili.list': 'DOMAIN-SUFFIX,bilibili.tv\nPROCESS-NAME,com.bstar.intl', 'https://raw.githubusercontent.com/example/china.list': 'DOMAIN-SUFFIX,bilibili.tv\nDOMAIN-SUFFIX,cn\n'}
        output, report = sync.generate(template, resources)
        self.assertLess(output.index('DOMAIN-SUFFIX,bilibili.tv,Bilibili'), output.index('DOMAIN-SUFFIX,bilibili.tv,DIRECT'))
        self.assertIn('DOMAIN-SUFFIX,biliintl.com,Bilibili', output)
        self.assertNotIn('PROCESS-NAME', output)
        self.assertTrue(output.endswith('FINAL,Group\n'))
        self.assertEqual(report['sources'][0]['process_rules_omitted'], 1)

    def test_domain_set_exact_and_suffix_translation(self):
        template = '[Proxy Group]\nGroup = select,Privilege\nApple = select,DIRECT\n[Rule]\nDOMAIN-SET,https://raw.githubusercontent.com/example/apple.list,Apple\nFINAL,Group\n'
        output, _ = sync.generate(template, {'https://raw.githubusercontent.com/example/apple.list': '# domains\n.apple.com\nexact.example\n'})
        self.assertIn('DOMAIN-SUFFIX,apple.com,Apple', output)
        self.assertIn('DOMAIN,exact.example,Apple', output)

    def test_private_nodes_never_change_public_output_or_copy_mitm(self):
        public = '[General]\nip-mode = ipv4-only\n[Proxy]\n[Remote Proxy]\nExample = https://example.com/sub,enabled=false\n[Remote Filter]\nSub-ALL = NameRegex,FilterKey=".+"\n[Rule]\nFINAL,DIRECT\n'
        private = '[Proxy]\nLocal = Trojan,private.test,443,"private-password"\n[Remote Proxy]\nMyProvider = https://private.test/loon?token=private-token,enabled=true\n[MITM]\nca-p12 = private-certificate\n[Plugin]\nhttps://private.test/plugin\n'
        merged = sync.private_config(public, private)
        self.assertIn('private-token', merged)
        self.assertIn('private-password', merged)
        self.assertNotIn('private-token', public)
        self.assertNotIn('private-certificate', merged)
        self.assertNotIn('[Plugin]', merged)
        self.assertIn('[Remote Filter]', merged)
        self.assertIn('FINAL,DIRECT', merged)

    def test_real_generated_profile(self):
        path = sync.OUTPUT
        if not path.exists() or not (sync.ROOT / 'validation-report.json').exists():
            self.skipTest('No generated profile yet')
        text = path.read_text()
        sections = sync.sections(text)
        self.assertNotIn('Remote Rule', sections)
        self.assertNotIn('Plugin', sections)
        self.assertNotIn('MITM', sections)
        self.assertNotIn('parser-enabled=true', text)
        groups = dict(line.split(' = ', 1) for line in sections['Proxy Group'])
        for name in ('Apple', 'WeChat', 'PikPak', 'Bilibili', 'Hayu'):
            self.assertIn(name, groups)
            self.assertIn('img-url=', groups[name])
        for name in ('STARZ', 'Peacock', 'Hulu', 'Spotify', 'Gemini', 'Pinterest'):
            self.assertNotIn(name, groups)
        self.assertTrue(groups['Apple'].startswith('select,DIRECT'))
        self.assertTrue(groups['WeChat'].startswith('select,DIRECT'))
        self.assertTrue(groups['PikPak'].startswith('select,🇸🇬Singapore'))
        self.assertEqual(sections['Rule'][-1], 'FINAL,Group')
        for line in sections['Remote Filter']:
            self.assertNotIn('PAOPAO', line)
            self.assertNotIn('Mitce', line)
            regex = line.split('FilterKey="', 1)[1][:-1]
            self.assertNotIn('\\\\b', regex)
            re.compile(regex)

    def test_real_domain_policies(self):
        if not (sync.ROOT / 'validation-report.json').exists():
            self.skipTest('No generated profile')
        rules = sync.sections(sync.OUTPUT.read_text())['Rule']
        def match(host):
            for rule in rules:
                row = sync.parts(rule)
                if row[0] == 'DOMAIN' and host == row[1]:
                    return row[2]
                if row[0] == 'DOMAIN-SUFFIX' and (host == row[1] or host.endswith('.' + row[1])):
                    return row[2]
                if row[0] == 'DOMAIN-KEYWORD' and row[1] in host:
                    return row[2]
            return 'Group'
        expected = {'www.apple.com': 'Apple', 'api.wechat.com': 'WeChat', 'im.qq.com': 'WeChat', 'www.bilibili.tv': 'Bilibili', 'api.biliintl.com': 'Bilibili', 'www.bilibili.com': 'Bilibili', 'www.netflix.com': 'Netflix', 'www.youtube.com': 'YouTube', 'www.hayu.com': 'Hayu', 'mypikpak.com': 'PikPak', 'www.paypal.com': 'PayPal', 'api.telegram.org': 'Telegram', 'github.com': 'GitHub', 'www.google.com': 'Google', 'chatgpt.com': 'ChatGPT', 'www.wetv.vip': 'WeTV'}
        for host, policy in expected.items():
            self.assertEqual(match(host), policy, host)


if __name__ == '__main__':
    unittest.main()
