"""This script will log all sent sms through Jasmin with user information.

Requirement:
- Activate publish_submit_sm_resp in jasmin.cfg
- submit_log table:
  CREATE TABLE submit_log (
    `msgid`            VARCHAR(45) PRIMARY KEY,
    `source_connector` VARCHAR(15),
    `routed_cid`       VARCHAR(30),
    `source_addr`      VARCHAR(40),
    `destination_addr` VARCHAR(40) NOT NULL CHECK (`destination_addr` <> ''),
    `rate`             DECIMAL(12, 7),
    `pdu_count`        TINYINT(3) DEFAULT 1,
    `short_message`    BLOB,
    `binary_message`   BLOB,
    `status`           VARCHAR(15) NOT NULL CHECK (`status` <> ''),
    `uid`              VARCHAR(15) NOT NULL CHECK (`uid` <> ''),
    `trials`           TINYINT(4) DEFAULT 1,
    `created_at`       DATETIME NOT NULL,
    `status_at`        DATETIME NOT NULL,
    INDEX `sms_log_1` (`status`),
    INDEX `sms_log_2` (`uid`),
    INDEX `sms_log_3` (`routed_cid`),
    INDEX `sms_log_4` (`created_at`),
    INDEX `sms_log_5` (`created_at`, `uid`),
    INDEX `sms_log_6` (`created_at`, `uid`, `status`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
"""

import binascii
from django.utils.translation import gettext as _
from django.db import models


class SubmitLog(models.Model):
    msgid = models.CharField(_("Message ID"), max_length=45)  # noqa
    source_connector = models.CharField(_("Source Connector"), max_length=15)
    routed_cid = models.CharField(_("Routed CID"), max_length=30, db_index=True)
    source_addr = models.CharField(_("Source Address"), max_length=40)  # noqa
    destination_addr = models.CharField(_("Destination Address"), max_length=40, null=False, blank=False)  # noqa
    rate = models.DecimalField(_("Rate"), default=0.0, decimal_places=2, max_digits=8)
    pdu_count = models.PositiveIntegerField(_("PDU Count"), default=1)
    short_message = models.BinaryField(_("Short Message"))
    binary_message = models.BinaryField(_("Binary Message"))
    status = models.CharField(_("Status"), max_length=15, null=False, blank=False, db_index=True)
    uid = models.CharField(_("UID"), max_length=15, null=False, blank=False, db_index=True)
    trials = models.PositiveIntegerField(_("Trials"), default=1)
    created_at = models.DateTimeField(_("Created At"), null=False, db_index=True)
    status_at = models.DateTimeField(_("Status At"), null=False)

    @property
    def decoded_destination_addr(self):
        if self.destination_addr:
            # Remove the '\x' prefix and decode from hex to bytes, then to UTF-8 string
            try:
                # The data might already be in bytes format in Python
                if isinstance(self.destination_addr, bytes):
                    return self.destination_addr.decode('utf-8')
                # Otherwise, it might be a memoryview or hex string
                elif isinstance(self.destination_addr, memoryview):
                    return self.destination_addr.tobytes().decode('utf-8')
                # Handle the case where it's a string with \x prefix
                elif isinstance(self.destination_addr, str) and self.destination_addr.startswith('\\x'):
                    hex_string = self.destination_addr[2:]  # Remove \x prefix
                    return binascii.unhexlify(hex_string).decode('utf-8')
                return str(self.destination_addr)
            except (UnicodeDecodeError, binascii.Error):
                return "Undecodable"
        return "N/A"

    @property
    def decoded_short_message(self):
        if self.short_message:
            # Remove the '\x' prefix and decode from hex to bytes, then to UTF-8 string
            try:
                # The data might already be in bytes format in Python
                if isinstance(self.short_message, bytes):
                    return self.short_message.decode('utf-8')
                # Otherwise, it might be a memoryview or hex string
                elif isinstance(self.short_message, memoryview):
                    return self.short_message.tobytes().decode('utf-8')
                # Handle the case where it's a string with \x prefix
                elif isinstance(self.short_message, str) and self.short_message.startswith('\\x'):
                    hex_string = self.short_message[2:]  # Remove \x prefix
                    return binascii.unhexlify(hex_string).decode('utf-8')
                return str(self.short_message)
            except (UnicodeDecodeError, binascii.Error):
                return "Undecodable"
        return "N/A"

    @property
    def decoded_source_addr(self):
        if self.source_addr:
            # Remove the '\x' prefix and decode from hex to bytes, then to UTF-8 string
            try:
                # The data might already be in bytes format in Python
                if isinstance(self.source_addr, bytes):
                    return self.source_addr.decode('utf-8')
                # Otherwise, it might be a memoryview or hex string
                elif isinstance(self.source_addr, memoryview):
                    return self.source_addr.tobytes().decode('utf-8')
                # Handle the case where it's a string with \x prefix
                elif isinstance(self.source_addr, str) and self.source_addr.startswith('\\x'):
                    hex_string = self.source_addr[2:]  # Remove \x prefix
                    return binascii.unhexlify(hex_string).decode('utf-8')
                return str(self.source_addr)
            except (UnicodeDecodeError, binascii.Error):
                return "Undecodable"
        return "N/A"

    class Meta:
        db_table = "submit_log"
        verbose_name = _("Submit Log")
        verbose_name_plural = _("Submit Logs")
        ordering = ("-created_at",)

    def __str__(self):
        return self.msgid  # noqa
