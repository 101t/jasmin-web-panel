import logging
import re

import pexpect
from django.conf import settings

from ..exceptions import (
    JasminError,
    ObjectNotFoundError,
    TelnetConnectionTimeout,
    TelnetLoginFailed,
    TelnetUnexpectedResponse,
    ValidationError,
)

logger = logging.getLogger(__name__)

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT

# jcli prompts always start a new line. Anchoring on the line break matters: jcli prints
# text such as "<class 'jasmin.routing.Routes.DefaultRoute'> arguments:" and filter reprs
# such as "<U (uid=u1)> ", and a bare "> " pattern matched those, shifting every later
# response onto the wrong command.
STANDARD_PROMPT_RE = r'\r?\n' + re.escape(STANDARD_PROMPT)
INTERACTIVE_PROMPT_RE = r'\r?\n' + re.escape(INTERACTIVE_PROMPT)

# The only non-empty responses jcli gives to a valid key inside an interactive session.
# Anything else ("Error: ...", "Unknown ...", "... can not be modified !") is a rejection.
INFO_RESPONSES = (
    re.compile(r"^<class '[\w.]+'> arguments:"),
    re.compile(r'^Route order forced to 0'),
)

NOT_FOUND_RE = re.compile(r'^Unknown (?:User|Group|Filter|connector|Httpcc|MO Route|MT Route): ')


class TelnetConnection(object):
    """A logged-in jcli session.

    Use as a context manager (``with Users() as users: ...``) so the session is closed as soon
    as the work is done; ``__del__`` remains as a fallback.
    """

    def __init__(self):
        self.telnet = None
        target = '%s:%s' % (settings.TELNET_HOST, settings.TELNET_PORT)
        try:
            telnet = pexpect.spawn(
                'telnet', [settings.TELNET_HOST, str(settings.TELNET_PORT)],
                timeout=settings.TELNET_TIMEOUT, encoding='utf-8', codec_errors='replace',
            )
        except pexpect.ExceptionPexpect as e:
            raise TelnetUnexpectedResponse('Could not start the telnet client: %s' % e)
        try:
            telnet.expect_exact('Username: ')
            telnet.sendline(settings.TELNET_USERNAME)
            telnet.expect_exact('Password: ')
            telnet.sendline(settings.TELNET_PW)
            # A wrong password prints this message and asks for the username again.
            index = telnet.expect([STANDARD_PROMPT_RE, 'Incorrect Username/Password'])
        except pexpect.EOF:
            telnet.close(force=True)
            raise TelnetUnexpectedResponse(
                'Could not connect to Jasmin jcli at %s. Is the gateway running and reachable?' % target)
        except pexpect.TIMEOUT:
            telnet.close(force=True)
            raise TelnetConnectionTimeout('Connection to Jasmin jcli at %s timed out' % target)
        if index != 0:
            telnet.close(force=True)
            raise TelnetLoginFailed('Jasmin jcli login failed, check TELNET_USERNAME and TELNET_PW')
        self.telnet = telnet

    def close(self):
        """Quit jcli and terminate the telnet client."""
        telnet, self.telnet = self.telnet, None
        if telnet is None:
            return
        try:
            if telnet.isalive():
                telnet.sendline('quit')
        except pexpect.ExceptionPexpect:
            pass
        finally:
            telnet.close(force=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        "Make sure telnet connection is closed when unleashing response back to client"
        try:
            self.close()
        except Exception:  # never raise from a finalizer
            pass

    @staticmethod
    def clean_output(text, sent=None):
        """Normalise jcli output: drop carriage returns, the echoed command and blank lines."""
        lines = [line.rstrip() for line in text.replace('\r', '').split('\n')]
        if sent is not None and lines and lines[0].strip() == sent.strip():
            lines = lines[1:]
        return '\n'.join(line for line in lines if line.strip())

    def _send(self, line, prompts):
        """Send ``line`` and wait for one of ``prompts``; return ``(index, output)``."""
        if '\n' in line or '\r' in line:
            # A line break would let a form value run its own jcli command.
            raise ValidationError('Values must not contain line breaks')
        self.telnet.sendline(line)
        try:
            index = self.telnet.expect(prompts)
        except pexpect.TIMEOUT:
            raise TelnetConnectionTimeout('Jasmin did not answer "%s" in time' % line.split(' ', 1)[0])
        except pexpect.EOF:
            raise TelnetUnexpectedResponse('Jasmin closed the jcli connection')
        return index, self.clean_output(self.telnet.before, line)

    @staticmethod
    def error_for(output):
        """Map a jcli failure message to the matching API exception."""
        message = output.strip() or 'Jasmin rejected the request'
        if NOT_FOUND_RE.match(message):
            return ObjectNotFoundError(message)
        return JasminError(message)

    def run_command(self, command):
        """Run a command from the standard prompt and return its output (echo removed)."""
        index, output = self._send(command, [STANDARD_PROMPT_RE, INTERACTIVE_PROMPT_RE])
        if index != 0:
            # The command opened an interactive session nobody asked for; leave it unchanged.
            self._send('ko', [STANDARD_PROMPT_RE])
            raise JasminError(output or 'Unexpected interactive prompt for "%s"' % command)
        return output

    def run_action(self, command, success_prefix='Successfully'):
        """Run a one-shot command (enable, remove, start, ...) and raise unless it succeeded."""
        output = self.run_command(command)
        if not output.startswith(success_prefix):
            raise self.error_for(output)
        return output

    def run_session(self, command, lines):
        """Open an interactive session (``user -a``, ``smppccm -u cid``, ...), send ``lines``, save.

        ``lines`` are sent verbatim, e.g. ``['uid foo', 'gid bar']``. The first line jcli rejects
        aborts the session with ``ko`` and raises with jcli's own message, so a failed edit never
        leaves the connection stuck in interactive mode.
        """
        index, output = self._send(command, [INTERACTIVE_PROMPT_RE, STANDARD_PROMPT_RE])
        if index != 0:
            raise self.error_for(output)
        for line in lines:
            index, output = self._send(line, [INTERACTIVE_PROMPT_RE, STANDARD_PROMPT_RE])
            if index != 0:
                raise self.error_for(output)
            if output and not any(pattern.match(output) for pattern in INFO_RESPONSES):
                self._send('ko', [STANDARD_PROMPT_RE])
                raise JasminError('%s: %s' % (line.split(' ', 1)[0], output))
        index, output = self._send('ok', [STANDARD_PROMPT_RE, INTERACTIVE_PROMPT_RE])
        if index != 0:
            self._send('ko', [STANDARD_PROMPT_RE])
            raise JasminError(output)
        return output

    def persist(self):
        """Persist the running configuration so it survives a Jasmin restart."""
        output = self.run_command('persist')
        if 'Cannot persist' in output or 'Unknown error' in output:
            raise JasminError(output)
        return output
