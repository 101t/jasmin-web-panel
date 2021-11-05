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

    class Meta:
        db_table = "submit_log"
        verbose_name = _("Submit Log")
        verbose_name_plural = _("Submit Logs")
        ordering = ("-created_at",)

    def __str__(self):
        return self.msgid  # noqa
