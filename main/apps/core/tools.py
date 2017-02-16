from django.conf import settings

from .exceptions import (CanNotModifyError, JasminSyntaxError,
                        JasminError, UnknownError)

STANDARD_PROMPT = settings.STANDARD_PROMPT
INTERACTIVE_PROMPT = settings.INTERACTIVE_PROMPT


def set_ikeys(telnet, keys2vals):
    "set multiple keys for interactive command"
    for key, val in keys2vals.items():
        print key, val
        telnet.sendline("%s %s" % (key, val))
        matched_index = telnet.expect([
            r'.*(Unknown .*)' + INTERACTIVE_PROMPT,
            r'(.*) can not be modified.*' + INTERACTIVE_PROMPT,
            r'(.*)' + INTERACTIVE_PROMPT
        ])
        result = telnet.match.group(1).strip()
        if matched_index == 0:
            raise UnknownError(result)
        if matched_index == 1:
            raise CanNotModifyError(result)
    telnet.sendline('ok')
    ok_index = telnet.expect([
        r'ok(.* syntax is invalid).*' + INTERACTIVE_PROMPT,
        r'.*' + STANDARD_PROMPT,
    ])
    if ok_index == 0:
        #remove whitespace and return error
        raise JasminSyntaxError(" ".join(telnet.match.group(1).split()))
    return


def split_cols(lines):
    "split columns into lists, skipping blank and non-data lines"
    parsed = []
    for line in lines:
        raw_split = line.split()
        fields = [s for s in raw_split if (s and raw_split[0][0] == '#')]
        parsed.append(fields)
    return parsed
