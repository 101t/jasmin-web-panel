"""
Tests for core models.
"""
import pytest
from django.utils import timezone
from main.core.models import SubmitLog
from main.core.models.smpp import FiltersModel, GroupsModel


@pytest.mark.django_db
class TestSubmitLogModel:
    def _make_submit_log(self, **kwargs):
        defaults = {
            'msgid': 'test-msg-001',
            'destination_addr': '255700000001',
            'status': 'ESME_ROK',
            'uid': 'user1',
            'created_at': timezone.now(),
            'status_at': timezone.now(),
        }
        defaults.update(kwargs)
        return SubmitLog.objects.create(**defaults)

    def test_create_submit_log(self):
        log = self._make_submit_log()
        assert log.pk is not None
        assert log.msgid == 'test-msg-001'
        assert str(log) == 'test-msg-001'

    def test_decoded_destination_addr_plain_string(self):
        log = self._make_submit_log(destination_addr='255700000001')
        assert log.decoded_destination_addr == '255700000001'

    def test_decoded_destination_addr_bytes(self):
        # Set bytes on an unsaved instance to exercise the bytes-handling branch
        # (passing bytes to objects.create() would coerce to str via CharField)
        log = self._make_submit_log()
        log.destination_addr = b'255700000001'
        assert log.decoded_destination_addr == '255700000001'

    def test_decoded_destination_addr_empty(self):
        # destination_addr is required (not blank), but test N/A for short_message
        log = self._make_submit_log(short_message=None)
        assert log.decoded_short_message == 'N/A'

    def test_decoded_short_message_plain(self):
        log = self._make_submit_log(short_message=b'Hello World')
        assert log.decoded_short_message == 'Hello World'

    def test_decoded_source_addr_plain(self):
        log = self._make_submit_log(source_addr='INFO')
        assert log.decoded_source_addr == 'INFO'

    def test_decoded_source_addr_none(self):
        log = self._make_submit_log(source_addr=None)
        assert log.decoded_source_addr == 'N/A'

    def test_meta_ordering(self):
        self._make_submit_log(
            msgid='msg-001',
            created_at=timezone.now() - timezone.timedelta(minutes=5),
        )
        log2 = self._make_submit_log(
            msgid='msg-002',
            created_at=timezone.now(),
        )
        logs = list(SubmitLog.objects.all())
        assert logs[0].msgid == log2.msgid  # newest first


@pytest.mark.django_db
class TestFiltersModel:
    def test_create_filter(self):
        f = FiltersModel.objects.create(
            type='TransparentFilter',
            fid='f1',
            parameters='',
        )
        assert str(f) == 'f1'

    def test_filter_unique_fid(self):
        from django.db import IntegrityError
        FiltersModel.objects.create(type='TransparentFilter', fid='unique-fid', parameters='')
        with pytest.raises(IntegrityError):
            FiltersModel.objects.create(type='ConnectorFilter', fid='unique-fid', parameters='')


@pytest.mark.django_db
class TestGroupsModel:
    def test_create_group(self):
        g = GroupsModel.objects.create(gid='grp1', status=True)
        assert str(g) == 'grp1'
        assert g.status is True

    def test_group_default_status(self):
        g = GroupsModel.objects.create(gid='grp2')
        assert g.status is True
