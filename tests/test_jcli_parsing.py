"""
Tests for the jcli layer without a gateway: output parsers fed with real jcli transcripts
(Jasmin 0.11), and the interactive-session logic driven by a scripted fake jcli.
"""
import re

import pytest

from main.core.exceptions import JasminError, ObjectNotFoundError, ValidationError
from main.core.smpp import Filters, Groups, HTTPCCM, MORouter, MTRouter, SMPPCCM, Users
from main.core.smpp.conn import INTERACTIVE_PROMPT_RE, STANDARD_PROMPT_RE, TelnetConnection
from main.core.tools import as_list, split_filters, table_rows

GROUP_LIST = "#Group id\n#g1\n#!grp_01\nTotal Groups: 2"
USER_LIST = (
    "#User id          Group id         Username         Balance MT SMS Throughput\n"
    "#u1               g1               user1            ND (!)  ND (!) ND/ND\n"
    "#!usr_01          !grp_01          bob              ND (!)  ND (!) ND/ND\n"
    "#u3               g1               carol            100.0   42     10.0/ND\n"
    "Total Users: 3")
USER_SHOW = (
    "uid usr_01\ngid grp_01\nusername bob\n"
    "mt_messaging_cred authorization http_send True\n"
    "mt_messaging_cred authorization hex_content True\n"
    "mt_messaging_cred valuefilter priority ^[0-3]$\n"
    "mt_messaging_cred valuefilter content hello world.*\n"
    "mt_messaging_cred defaultvalue src_addr None\n"
    "mt_messaging_cred quota balance ND\n"
    "smpps_cred authorization bind True\n"
    "smpps_cred quota max_bindings ND")
SMPPCCM_LIST = (
    "#Connector id                        Service Session          Starts Stops\n"
    "#conn_01                             started BOUND_TRX        1      0\n"
    "#conn_02                             stopped NONE             0      0\n"
    "Total connectors: 2")
SMPPCCM_SHOW = "cid conn_01\nhost 127.0.0.1\nport 2775\nsystype\nsubmit_throughput 1\naddr_range None"
HTTPCCM_LIST = (
    "#Httpcc id        Type                   Method URL\n"
    "#http1            HttpConnector          GET    http://127.0.0.1/recv\n"
    "Total Httpccs: 1")
HTTPCCM_SHOW = "HttpConnector:\ncid = cap_h1\nbaseurl = http://127.0.0.1/mo\nmethod = POST"
FILTER_LIST = (
    "#Filter id        Type                   Routes Description\n"
    "#cap_fu           UserFilter             MT     <U (uid=cap_u)>\n"
    "#cap_ft           TransparentFilter      MO MT  <T>\n"
    "#cap_fm           ShortMessageFilter     MO MT  <SM (msg=^hello, <world>$)>\n"
    "Total Filters: 3")
MT_LIST = (
    "#Order Type                    Rate       Connector ID(s)                                  Filter(s)\n"
    "#20    RandomRoundrobinMTRoute 1.50000    smppc(cap_c1), smppc(cap_c2)                     "
    "<U (uid=cap_u)>, <SM (msg=^hello, <world>$)>\n"
    "#0     DefaultRoute            0 (!)      smppc(cap_c1)\n"
    "Total MT Routes: 2")
MO_LIST = (
    "#Order Type                    Connector ID(s)                                  Filter(s)\n"
    "#8     StaticMORoute           smpps(capn)                                      <SM (msg=^hello, <world>$)>, <T>\n"
    "#7     FailoverMORoute         http(cap_h1), http(cap_h1)                       <T>\n"
    "Total MO Routes: 2")


class TestListParsers:
    def test_empty_listing(self):
        assert table_rows("Total Groups: 0") == []
        assert Groups.parse_list("Total Groups: 0") == []

    def test_groups(self):
        assert Groups.parse_list(GROUP_LIST) == [
            {'name': 'g1', 'status': 'enabled'}, {'name': 'grp_01', 'status': 'disabled'}]

    def test_users(self):
        assert Users.parse_list(USER_LIST) == [('u1', True), ('usr_01', False), ('u3', True)]
        summary = Users.parse_summary(USER_LIST)
        assert summary[1] == {'uid': 'usr_01', 'gid': 'grp_01', 'username': 'bob', 'status': 'disabled',
                              'balance': 'ND', 'sms_count': 'ND', 'throughput': 'ND/ND'}
        assert summary[2]['balance'] == '100.0' and summary[2]['sms_count'] == '42'
        assert summary[2]['throughput'] == '10.0/ND'

    def test_user_details_keep_values_with_spaces(self):
        user = Users.parse_user(USER_SHOW)
        assert user['uid'] == 'usr_01' and user['gid'] == 'grp_01'
        assert user['mt_messaging_cred']['authorization'] == {'http_send': 'True', 'hex_content': 'True'}
        assert user['mt_messaging_cred']['valuefilter']['content'] == 'hello world.*'
        assert user['smpps_cred']['quota']['max_bindings'] == 'ND'

    def test_smppccm(self):
        assert SMPPCCM.parse_list(SMPPCCM_LIST)[0] == {
            'cid': 'conn_01', 'status': 'started', 'session': 'BOUND_TRX', 'starts': '1', 'stops': '0'}
        show = SMPPCCM.parse_show(SMPPCCM_SHOW)
        assert show['systype'] == '' and show['addr_range'] == 'None' and show['port'] == '2775'

    def test_httpccm(self):
        assert HTTPCCM.parse_list(HTTPCCM_LIST) == [
            {'cid': 'http1', 'type': 'HttpConnector', 'method': 'GET', 'url': 'http://127.0.0.1/recv'}]
        assert HTTPCCM.parse_show(HTTPCCM_SHOW) == {
            'cid': 'cap_h1', 'baseurl': 'http://127.0.0.1/mo', 'method': 'POST'}

    def test_filters_routes_and_description(self):
        filters = Filters.parse_list(FILTER_LIST)
        assert filters[0] == {'fid': 'cap_fu', 'type': 'UserFilter', 'routes': 'MT', 'description': '<U (uid=cap_u)>'}
        assert filters[1]['routes'] == 'MO MT' and filters[1]['description'] == '<T>'
        assert filters[2]['description'] == '<SM (msg=^hello, <world>$)>'

    def test_mt_routes(self):
        rr, default = MTRouter.parse_list(MT_LIST)
        assert rr == {
            'order': '20', 'type': 'RandomRoundrobinMTRoute', 'rate': '1.50000',
            'connectors': ['smppc(cap_c1)', 'smppc(cap_c2)'],
            'filters': ['<U (uid=cap_u)>', '<SM (msg=^hello, <world>$)>'],
        }
        assert default == {'order': '0', 'type': 'DefaultRoute', 'rate': '0',
                           'connectors': ['smppc(cap_c1)'], 'filters': []}

    def test_mo_routes(self):
        static, failover = MORouter.parse_list(MO_LIST)
        assert static['connectors'] == ['smpps(capn)']
        assert static['filters'] == ['<SM (msg=^hello, <world>$)>', '<T>']
        assert failover['connectors'] == ['http(cap_h1)', 'http(cap_h1)']

    def test_split_filters_keeps_commas_inside_parentheses(self):
        assert split_filters('<SM (msg=a, b)>, <T>') == ['<SM (msg=a, b)>', '<T>']
        assert split_filters('') == []

    @pytest.mark.parametrize('value, expected', [
        (None, []), ('', []), ('a', ['a']), ('a, b,,c', ['a', 'b', 'c']), (['a', ' b ', ''], ['a', 'b']),
    ])
    def test_as_list(self, value, expected):
        assert as_list(value) == expected


class TestPrompts:
    def test_class_repr_is_not_an_interactive_prompt(self):
        """jcli prints "<class '...DefaultRoute'> arguments:"; its "> " is not the prompt."""
        output = ("type DefaultRoute\r\r\r\n<class 'jasmin.routing.Routes.DefaultRoute'> arguments:"
                  "\r\r\r\nconnector, rate\r\r\r\n> ")
        match = re.search(INTERACTIVE_PROMPT_RE, output)
        assert match.end() == len(output)

    def test_filter_repr_is_not_an_interactive_prompt(self):
        output = "#f1  UserFilter  MT  <U (uid=u1)> \r\r\r\nTotal Filters: 1\r\r\r\njcli : "
        assert re.search(INTERACTIVE_PROMPT_RE, output) is None
        assert re.search(STANDARD_PROMPT_RE, output).end() == len(output)


class FakeJcli:
    """Replays a jcli conversation: each sent line must match the script, in order."""

    def __init__(self, script):
        self.script = list(script)
        self.sent = []
        self.before = ''
        self._prompt = None

    def sendline(self, line):
        expected, output, prompt = self.script.pop(0)
        assert line == expected, 'sent %r, script expected %r' % (line, expected)
        self.sent.append(line)
        self.before = line + '\r\r\r\n' + output.replace('\n', '\r\r\r\n') + '\r\r'
        self._prompt = STANDARD_PROMPT_RE if prompt == 'std' else INTERACTIVE_PROMPT_RE

    def expect(self, patterns):
        return patterns.index(self._prompt)

    def isalive(self):
        return False

    def close(self, force=False):
        pass


def connection(script, cls=TelnetConnection):
    conn = cls.__new__(cls)
    conn.telnet = FakeJcli(script)
    return conn


class TestSessions:
    def test_session_saves(self):
        conn = connection([
            ('group -a', 'Adding a new Group: (ok: save, ko: exit)', 'int'),
            ('gid g1', '', 'int'),
            ('ok', 'Successfully added Group [g1]', 'std'),
        ])
        assert conn.run_session('group -a', ['gid g1']) == 'Successfully added Group [g1]'

    def test_type_arguments_hint_is_not_an_error(self):
        conn = connection([
            ('mtrouter -a', 'Adding a new MT Route: (ok: save, ko: exit)', 'int'),
            ('type DefaultRoute', "<class 'jasmin.routing.Routes.DefaultRoute'> arguments:\nconnector, rate", 'int'),
            ('ok', 'Successfully added MTRoute [DefaultRoute] with order:0', 'std'),
        ])
        conn.run_session('mtrouter -a', ['type DefaultRoute'])

    def test_rejected_line_aborts_with_ko(self):
        conn = connection([
            ('user -u u1', 'Updating User id [u1]: (ok: save, ko: exit)', 'int'),
            ('mt_messaging_cred quota balance ND', "Error: could not convert string to float: 'ND'", 'int'),
            ('ko', '', 'std'),
        ])
        with pytest.raises(JasminError, match="could not convert string to float"):
            conn.run_session('user -u u1', ['mt_messaging_cred quota balance ND', 'never sent'])
        assert conn.telnet.sent[-1] == 'ko'

    def test_failed_save_aborts_with_ko(self):
        conn = connection([
            ('morouter -a', 'Adding a new MO Route: (ok: save, ko: exit)', 'int'),
            ('ok', 'Error: FailoverMORoute cannot have mixed connector types', 'int'),
            ('ko', '', 'std'),
        ])
        with pytest.raises(JasminError, match='mixed connector types'):
            conn.run_session('morouter -a', [])

    def test_unknown_object_is_not_found(self):
        conn = connection([('user -u nope', 'Unknown User: nope', 'std')])
        with pytest.raises(ObjectNotFoundError):
            conn.run_session('user -u nope', [])

    def test_action_failure(self):
        conn = connection([('smppccm -1 c1', 'Failed starting connector, check log for details', 'std')])
        with pytest.raises(JasminError, match='Failed starting connector'):
            conn.run_action('smppccm -1 c1')

    def test_line_breaks_are_rejected(self):
        conn = connection([])
        with pytest.raises(ValidationError):
            conn.run_command('group -r x\npersist')
        assert conn.telnet.sent == []

    def test_duplicate_user_is_refused_before_jcli_replaces_it(self):
        conn = connection([('user -s u1', USER_SHOW, 'std')], cls=Users)
        with pytest.raises(Exception, match='already exists'):
            conn.create({'uid': 'u1', 'gid': 'g1', 'username': 'bob', 'password': 'pw'})
        assert conn.telnet.sent == ['user -s u1']

    def test_smppccm_update_sends_only_changed_keys(self):
        conn = connection([
            ('smppccm -s conn_01', SMPPCCM_SHOW, 'std'),
            ('smppccm -u conn_01', 'Updating connector id [conn_01]: (ok: save, ko: exit)', 'int'),
            ('submit_throughput 5', '', 'int'),
            ('ok', 'Successfully updated connector [conn_01]', 'std'),
            ('persist', 'smppcc configuration persisted (profile:jcli-prod)', 'std'),
            ('smppccm -s conn_01', SMPPCCM_SHOW.replace('submit_throughput 1', 'submit_throughput 5'), 'std'),
        ], cls=SMPPCCM)
        result = conn.partial_update({'cid': 'conn_01', 'host': '127.0.0.1', 'port': '2775', 'status': 'started',
                                      'submit_throughput': '5'}, cid='conn_01')
        assert result['connector']['submit_throughput'] == '5'
