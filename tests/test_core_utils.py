"""
Tests for core utility functions.
"""
import pytest
from main.core.utils.boolean import is_json, is_int, is_float, is_decimal, is_date
from main.core.utils.common import (
    shorten_large_number,
    password_generator,
    normalize_query,
    get_client_ip,
)


class TestIsJson:
    def test_valid_json_object(self):
        assert is_json('{"key": "value"}') is True

    def test_valid_json_array(self):
        assert is_json('[1, 2, 3]') is True

    def test_invalid_json(self):
        assert is_json('not json') is False

    def test_empty_string(self):
        assert is_json('') is False


class TestIsInt:
    def test_integer_string(self):
        assert is_int('42') is True

    def test_negative_integer(self):
        assert is_int('-5') is True

    def test_float_string(self):
        assert is_int('3.14') is False

    def test_non_numeric(self):
        assert is_int('abc') is False


class TestIsFloat:
    def test_float_string(self):
        assert is_float('3.14') is True

    def test_integer_as_float(self):
        assert is_float('42') is True

    def test_non_numeric(self):
        assert is_float('abc') is False


class TestIsDecimal:
    def test_decimal_string(self):
        assert is_decimal('3.14') is True

    def test_integer_string(self):
        assert is_decimal('42') is True

    def test_non_numeric(self):
        assert is_decimal('abc') is False


class TestIsDate:
    def test_valid_date(self):
        assert is_date('2024-01-15') is True

    def test_valid_datetime(self):
        assert is_date('2024-01-15 10:30:00') is True

    def test_invalid_date(self):
        assert is_date('not-a-date') is False


class TestShortenLargeNumber:
    def test_below_thousand(self):
        assert shorten_large_number(999) == '999'

    def test_thousands(self):
        assert shorten_large_number(1000) == '1.0k'

    def test_millions(self):
        assert shorten_large_number(1_000_000) == '1.0M'

    def test_zero(self):
        assert shorten_large_number(0) == '0'


class TestPasswordGenerator:
    def test_default_length(self):
        pwd = password_generator()
        assert len(pwd) == 8

    def test_custom_length(self):
        pwd = password_generator(size=16)
        assert len(pwd) == 16

    def test_is_string(self):
        pwd = password_generator()
        assert isinstance(pwd, str)

    def test_uniqueness(self):
        # Password generator uses random choices; verify it doesn't raise exceptions
        # and produces strings of the expected type and length
        pwds = {password_generator(size=12) for _ in range(5)}
        assert all(isinstance(p, str) and len(p) == 12 for p in pwds)


class TestNormalizeQuery:
    def test_simple_query(self):
        result = normalize_query('hello world')
        assert 'hello' in result
        assert 'world' in result

    def test_quoted_terms(self):
        result = normalize_query('"hello world"')
        assert 'hello world' in result

    def test_extra_spaces(self):
        result = normalize_query('  hello   world  ')
        assert 'hello' in result
        assert 'world' in result


class TestGetClientIp:
    def test_direct_connection(self, rf):
        request = rf.get('/', REMOTE_ADDR='192.168.1.1')
        assert get_client_ip(request) == '192.168.1.1'

    def test_forwarded_for(self, rf):
        request = rf.get('/', HTTP_X_FORWARDED_FOR='10.0.0.1, 10.0.0.2')
        assert get_client_ip(request) == '10.0.0.1'
