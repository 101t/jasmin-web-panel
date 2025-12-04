#!/usr/bin/env python3
"""
sms_logger.py — Jasmin SMS logger (improved)

Improvements over original:
- Enable TCP keepalive on the Twisted transport (best-effort).
- Reconnect loop with capped exponential backoff (no reactor.stop()).
- Warn about AMQP spec heartbeat == 0 (encourage editing amqp0-9-1.xml).
- Periodic qmap cleanup.
- Defensive DB handling on connection checks.

Notes:
- Protocol-level AMQP heartbeat should be enabled by editing the AMQP spec
  or ensuring the client requests a heartbeat. This script logs a warning
  if it detects 'heartbeat' set to 0 in the spec file content.
- Keepalive settings are best-effort; not all platforms expose the same socket options.
"""

import os
import sys
import time
import pickle
import binascii
import logging
from datetime import datetime, timedelta
from functools import partial
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.python import log as twisted_log
import txamqp.spec
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate

# database libs
from psycopg2 import pool as pg_pool, Error as PGError, DatabaseError as PGDatabaseError
import psycopg2
from psycopg2.extras import register_default_json, Json
import mysql.connector
from mysql.connector import pooling as mysql_pooling

# SMPP data coding type used originally
from smpp.pdu.pdu_types import DataCoding

# low-level socket options
import socket

# ---------- Configuration ----------
DB_TYPE_MYSQL = int(os.getenv("DB_TYPE_MYSQL", "0")) == 1
DB_HOST = os.getenv("DB_HOST", "db")
DB_DATABASE = os.getenv("DB_DATABASE", "jasmin")
DB_TABLE = os.getenv("DB_TABLE", "submit_log")
DB_USER = os.getenv("DB_USER", "jasmin")
DB_PASS = os.getenv("DB_PASS", "jasmin")

AMQP_BROKER_HOST = os.getenv("AMQP_BROKER_HOST", "rabbitmq")
AMQP_BROKER_PORT = int(os.getenv("AMQP_BROKER_PORT", "5672"))
AMQP_SPEC_FILE = os.getenv("AMQP_SPEC_FILE", "/etc/jasmin/resource/amqp0-9-1.xml")

# consumer tuning
PREFETCH_COUNT = int(os.getenv("SMS_LOG_PREFETCH", "50"))
QUEUE_NAME = os.getenv("SMS_LOG_QUEUE", "sms_logger_queue")
EXCHANGE = os.getenv("SMS_LOG_EXCHANGE", "messaging")
BINDINGS = [
    "submit.sm.*",
    "submit.sm.resp.*",
    "dlr_thrower.*"
]

# logger
logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sms_logger")

# internal in-memory mapping of message-id -> metadata
qmap = {}
QMAP_TTL_SECONDS = int(os.getenv("QMAP_TTL_SECONDS", str(60*60*4)))  # drop items older than 4h

# Pools (initialized at startup)
_pg_pool = None
_mysql_pool = None

# backoff/connect config
CONNECT_BACKOFF_BASE = 1
CONNECT_BACKOFF_MAX = 60

# ---------- DB pool helpers ----------
def init_postgres_pool():
    global _pg_pool
    if _pg_pool is None:
        logger.info("Initializing Postgres pool -> %s@%s/%s", DB_USER, DB_HOST, DB_DATABASE)
        _pg_pool = pg_pool.SimpleConnectionPool(
            1, 20,
            user=DB_USER, password=DB_PASS,
            host=DB_HOST, database=DB_DATABASE,
            connect_timeout=10)
    return _pg_pool

def get_postgres_conn():
    pool = init_postgres_pool()
    return pool.getconn()

def put_postgres_conn(conn):
    if _pg_pool and conn:
        _pg_pool.putconn(conn)

def init_mysql_pool():
    global _mysql_pool
    if _mysql_pool is None:
        logger.info("Initializing MySQL pool -> %s@%s/%s", DB_USER, DB_HOST, DB_DATABASE)
        _mysql_pool = mysql_pooling.MySQLConnectionPool(
            pool_name="sms_logger_pool",
            pool_size=20,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            database=DB_DATABASE,
            autocommit=False
        )
    return _mysql_pool

def get_mysql_conn():
    pool = init_mysql_pool()
    return pool.get_connection()

# ---------- SQL helpers ----------
def ensure_table_and_indexes(conn, cursor):
    """
    Create table and indexes if not exist.
    Keep implementation simple and idempotent.
    """
    if DB_TYPE_MYSQL:
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            msgid VARCHAR(45) UNIQUE NOT NULL,
            source_connector VARCHAR(15),
            routed_cid VARCHAR(30),
            source_addr VARCHAR(40),
            destination_addr VARCHAR(40) NOT NULL,
            rate DECIMAL(12,7),
            charge DECIMAL(12,7),
            pdu_count TINYINT DEFAULT 1,
            short_message BLOB,
            binary_message BLOB,
            status VARCHAR(50) NOT NULL,
            uid VARCHAR(15) NOT NULL,
            trials TINYINT DEFAULT 1,
            created_at DATETIME NOT NULL,
            status_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
        """
        cursor.execute(create_table_sql)
        conn.commit()
    else:
        # Postgres
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {DB_TABLE} (
            id SERIAL PRIMARY KEY,
            msgid VARCHAR(45) UNIQUE NOT NULL,
            source_connector VARCHAR(15) NULL,
            routed_cid VARCHAR(30) NULL,
            source_addr VARCHAR(40) NULL,
            destination_addr VARCHAR(40) NOT NULL,
            rate DECIMAL(12,7) NULL,
            charge DECIMAL(12,7) NULL,
            pdu_count SMALLINT NULL DEFAULT 1,
            short_message BYTEA NULL,
            binary_message BYTEA NULL,
            status VARCHAR(50) NOT NULL,
            uid VARCHAR(15) NOT NULL,
            trials SMALLINT NULL DEFAULT 1,
            created_at TIMESTAMP(0) NOT NULL,
            status_at TIMESTAMP(0) NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        # indexes
        idxs = [
            ("source_connector",),
            ("routed_cid",),
            ("source_addr",),
            ("destination_addr",),
            ("status",),
            ("uid",),
            ("created_at",),
        ]
        for cols in idxs:
            idxname = f"{DB_TABLE}_{cols[0]}_idx"
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idxname} ON {DB_TABLE} ({cols[0]});")
            except Exception:
                pass
        conn.commit()

# ---------- message processing helpers ----------
def decode_short_message(pdu):
    sm = pdu.params.get("short_message", b"")
    pdu_count = 1
    # multipart handling (original logic)
    while hasattr(pdu, "nextPdu"):
        if pdu_count == 1:
            sm = sm[6:]
        pdu = pdu.nextPdu
        pdu_count += 1
        sm += pdu.params.get("short_message", b"")[6:]
    return sm, pdu_count

def is_ucs2(dc):
    if dc is None:
        return False
    if isinstance(dc, int):
        return dc == 8
    try:
        return str(dc.schemeData) == "UCS2"
    except Exception:
        return False

def cleanup_qmap():
    """Remove old entries from qmap to avoid memory leak"""
    cutoff = datetime.utcnow() - timedelta(seconds=QMAP_TTL_SECONDS)
    keys_to_remove = [k for k, v in qmap.items() if v.get("ts") and v["ts"] < cutoff]
    for k in keys_to_remove:
        logger.debug("Cleaning qmap old entry %s", k)
        qmap.pop(k, None)

def periodic_qmap_cleanup():
    try:
        cleanup_qmap()
    except Exception as e:
        logger.debug("Periodic qmap cleanup failed: %s", e)
    # reschedule
    reactor.callLater(300, periodic_qmap_cleanup)

# ---------- Keepalive AMQClient (Twisted) ----------
class KeepAliveAMQClient(AMQClient):
    """
    AMQClient subclass that enables TCP keepalive on connectionMade and logs
    connectionLost. Best-effort: different OSes have different socket options.
    """

    def connectionMade(self):
        # Try Twisted transport API
        try:
            tr = self.transport
            if hasattr(tr, "setTcpKeepAlive"):
                try:
                    tr.setTcpKeepAlive(True)
                    logger.debug("Transport.setTcpKeepAlive(True) called")
                except Exception as e:
                    logger.debug("transport.setTcpKeepAlive failed: %s", e)

            # Try to set low-level socket options
            try:
                sock = tr.getHandle()
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                # linux-specific tunables (best-effort)
                if hasattr(socket, "TCP_KEEPIDLE"):
                    try:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                    except Exception as e:
                        logger.debug("TCP_KEEPIDLE set failed: %s", e)
                if hasattr(socket, "TCP_KEEPINTVL"):
                    try:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                    except Exception as e:
                        logger.debug("TCP_KEEPINTVL set failed: %s", e)
                if hasattr(socket, "TCP_KEEPCNT"):
                    try:
                        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
                    except Exception as e:
                        logger.debug("TCP_KEEPCNT set failed: %s", e)
                logger.info("TCP keepalive enabled on transport")
            except Exception as e:
                logger.debug("Could not set low-level TCP keepalive options: %s", e)

        except Exception as e:
            logger.debug("Keepalive enabling raised: %s", e)

        return super().connectionMade()

    def connectionLost(self, reason):
        logger.warning("AMQ connection lost: %s", reason)
        # Let parent handle cleanup
        super().connectionLost(reason)
        # Schedule a reconnect attempt quickly (connect_attempt is defined below)
        try:
            # small delay before reconnect
            reactor.callLater(1, lambda: connect_attempt(CONNECT_BACKOFF_BASE))
        except Exception as e:
            logger.debug("Failed to schedule reconnect: %s", e)

# ---------- main AMQP handling ----------
@inlineCallbacks
def gotConnection(conn, username, password):
    """
    Called once the TCP connection is established and Twisted created an AMQClient instance.
    This function performs authentication, channel setup, queue declarations and enters
    the consumer loop (yielding on queue.get()).
    """
    logger.info("Connected to broker, authenticating %s", username)
    yield conn.start({"LOGIN": username, "PASSWORD": password})

    chan = yield conn.channel(1)
    yield chan.channel_open()

    # QoS
    yield chan.basic_qos(prefetch_count=PREFETCH_COUNT)

    # durable queue and bindings
    yield chan.queue_declare(queue=QUEUE_NAME, durable=True)
    for rk in BINDINGS:
        yield chan.queue_bind(queue=QUEUE_NAME, exchange=EXCHANGE, routing_key=rk)

    yield chan.basic_consume(queue=QUEUE_NAME, no_ack=False, consumer_tag="sms_logger")
    queue = yield conn.queue("sms_logger")

    # open DB pool and ensure table
    if DB_TYPE_MYSQL:
        db_conn = get_mysql_conn()
        cursor = db_conn.cursor()
    else:
        db_conn = get_postgres_conn()
        cursor = db_conn.cursor()

    # Ensure schema
    try:
        ensure_table_and_indexes(db_conn, cursor)
    except Exception as e:
        logger.exception("Failed to ensure table/indexes: %s", e)

    logger.info("Ready to receive messages (prefetch=%d)", PREFETCH_COUNT)

    # consumer loop
    while True:
        msg = yield queue.get()
        try:
            props = msg.content.properties or {}
            headers = props.get("headers", {}) or {}
            routing_key = msg.routing_key or ""
            logger.debug("Got message route=%s id=%s", routing_key, props.get("message-id"))

            # periodic qmap cleanup (also used elsewhere)
            if len(qmap) % 1000 == 0:
                cleanup_qmap()

            # Ensure DB connection is alive and get fresh cursor if pool used
            if DB_TYPE_MYSQL:
                try:
                    db_conn.ping(reconnect=True, attempts=3, delay=1)
                except Exception as e:
                    logger.warning("MySQL ping failed, reconnecting: %s", e)
                    try:
                        db_conn = get_mysql_conn()
                    except Exception as e2:
                        logger.exception("Failed to re-get MySQL connection: %s", e2)
                        # ack message to avoid duplicate stuck processing
                        yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                        continue
                cursor = db_conn.cursor()
            else:
                # Postgres: ensure connection is usable
                try:
                    cursor.execute("SELECT 1")
                except Exception as e:
                    logger.warning("Postgres connection check failed, re-getting connection: %s", e)
                    try:
                        put_postgres_conn(db_conn)
                    except Exception:
                        pass
                    try:
                        db_conn = get_postgres_conn()
                        cursor = db_conn.cursor()
                    except Exception as e2:
                        logger.exception("Failed to re-get Postgres connection: %s", e2)
                        yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                        continue

            # Process submit.sm (new submit)
            if routing_key.startswith("submit.sm.") and not routing_key.startswith("submit.sm.resp."):
                pdu = pickle.loads(msg.content.body)
                short_message, pdu_count = decode_short_message(pdu)
                binary_message = binascii.hexlify(short_message)
                # handle data coding
                dc = pdu.params.get("data_coding")
                if is_ucs2(dc):
                    short_message = short_message.decode("utf_16_be", "ignore").encode("utf_8")

                message_id = props.get("message-id")
                billing_headers = headers
                billing_pickle = billing_headers.get("submit_sm_resp_bill") or billing_headers.get("submit_sm_bill")
                submit_sm_bill = None
                if billing_pickle:
                    try:
                        submit_sm_bill = pickle.loads(billing_pickle)
                    except Exception:
                        submit_sm_bill = None

                src_connector = headers.get("source_connector")
                routed_cid = routing_key[10:] if len(routing_key) > 10 else None

                qmap[message_id] = {
                    "source_connector": src_connector,
                    "routed_cid": routed_cid,
                    "rate": 0,
                    "charge": 0,
                    "uid": 0,
                    "destination_addr": pdu.params.get("destination_addr"),
                    "source_addr": pdu.params.get("source_addr"),
                    "pdu_count": pdu_count,
                    "short_message": short_message,
                    "binary_message": binary_message,
                    "ts": datetime.utcnow()
                }
                if submit_sm_bill is not None:
                    try:
                        qmap[message_id]["rate"] = submit_sm_bill.getTotalAmounts()
                        qmap[message_id]["charge"] = submit_sm_bill.getTotalAmounts() * pdu_count
                        qmap[message_id]["uid"] = submit_sm_bill.user.uid
                    except Exception:
                        pass

                # ack the submit.sm message (we don't need to block)
                yield chan.basic_ack(delivery_tag=msg.delivery_tag)

            # Process submit.sm.resp (submit response)
            elif routing_key.startswith("submit.sm.resp."):
                pdu = pickle.loads(msg.content.body)
                message_id = props.get("message-id")
                if message_id not in qmap:
                    logger.warning("Got resp of unknown submit_sm: %s", message_id)
                    yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                    continue

                qmsg = qmap.pop(message_id)
                # Build insert / upsert
                created_at = headers.get("created_at") or datetime.utcnow()
                status_str = str(pdu.status).replace("CommandStatus.", "")

                if DB_TYPE_MYSQL:
                    insert_sql = (f"INSERT INTO {DB_TABLE} "
                                  "(msgid, source_addr, rate, pdu_count, charge, destination_addr, short_message, "
                                  "status, uid, created_at, binary_message, routed_cid, source_connector, status_at) "
                                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) "
                                  "ON DUPLICATE KEY UPDATE trials = trials + 1, status = VALUES(status), status_at = VALUES(status_at);")
                    params = (
                        message_id,
                        qmsg.get("source_addr") or "",
                        qmsg.get("rate"),
                        qmsg.get("pdu_count"),
                        qmsg.get("charge"),
                        qmsg.get("destination_addr"),
                        qmsg.get("short_message"),
                        status_str,
                        qmsg.get("uid"),
                        created_at,
                        qmsg.get("binary_message"),
                        qmsg.get("routed_cid"),
                        qmsg.get("source_connector"),
                        created_at
                    )
                    cursor.execute(insert_sql, params)
                    db_conn.commit()
                else:
                    # Try INSERT ... ON CONFLICT DO NOTHING then UPDATE incrementally
                    insert_sql = (f"INSERT INTO {DB_TABLE} (msgid, source_addr, rate, pdu_count, charge, destination_addr, "
                                  "short_message, status, uid, created_at, binary_message, routed_cid, source_connector, status_at) "
                                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (msgid) DO NOTHING;")
                    params = (
                        message_id,
                        qmsg.get("source_addr") or "",
                        qmsg.get("rate"),
                        qmsg.get("pdu_count"),
                        qmsg.get("charge"),
                        qmsg.get("destination_addr"),
                        psycopg2.Binary(qmsg.get("short_message") or b""),
                        status_str,
                        qmsg.get("uid"),
                        created_at,
                        psycopg2.Binary(qmsg.get("binary_message") or b""),
                        qmsg.get("routed_cid"),
                        qmsg.get("source_connector"),
                        created_at
                    )
                    cursor.execute(insert_sql, params)
                    if cursor.rowcount == 0:
                        # Row existed already -> increment trials and update status/time
                        update_sql = f"UPDATE {DB_TABLE} SET trials = COALESCE(trials,1) + 1, status = %s, status_at = %s WHERE msgid = %s;"
                        cursor.execute(update_sql, (status_str, created_at, message_id))
                    db_conn.commit()

                yield chan.basic_ack(delivery_tag=msg.delivery_tag)

            # Process DLRs
            elif routing_key.startswith("dlr_thrower."):
                # skip ESME_ statuses from submit_sm_resp
                msg_status = headers.get("message_status", "")
                if msg_status.startswith("ESME_"):
                    yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                    continue

                message_id = props.get("message-id")
                if message_id not in qmap:
                    logger.warning("Got dlr of unknown submit_sm: %s", message_id)
                    yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                    continue

                status_time = datetime.utcnow()
                # update DB
                update_sql = f"UPDATE {DB_TABLE} SET status = %s, status_at = %s WHERE msgid = %s;"
                status_val = headers.get("message_status")
                try:
                    cursor.execute(update_sql, (status_val, status_time, message_id))
                    db_conn.commit()
                except Exception as e:
                    logger.exception("Failed to update DLR status in DB: %s", e)

                # remove from qmap (we got final status)
                qmap.pop(message_id, None)
                yield chan.basic_ack(delivery_tag=msg.delivery_tag)

            else:
                logger.warning("Unknown routing_key %s", routing_key)
                yield chan.basic_ack(delivery_tag=msg.delivery_tag)

        except Exception as e:
            logger.exception("Error processing message: %s", e)
            # Reject and requeue? careful: repeated failures will cause loop.
            try:
                yield chan.basic_reject(delivery_tag=msg.delivery_tag, requeue=False)
            except Exception:
                # final fallback: ack to remove
                try:
                    yield chan.basic_ack(delivery_tag=msg.delivery_tag)
                except Exception:
                    pass

    # never reached, but tidy
    # yield chan.basic_cancel("sms_logger")
    # yield chan.channel_close()
    # conn0 = yield conn.channel(0)
    # yield conn0.connection_close()
    # reactor.stop()

# ---------- connect / reconnect logic ----------
def connect_attempt(backoff=CONNECT_BACKOFF_BASE):
    """
    Try to establish a new AMQP TCP connection and set callbacks.
    On failure schedule another attempt with exponential backoff (capped).
    """
    logger.info("Attempting AMQP connect to %s:%d (backoff=%ds)", AMQP_BROKER_HOST, AMQP_BROKER_PORT, backoff)
    d = ClientCreator(reactor,
                      KeepAliveAMQClient,
                      delegate=TwistedDelegate(),
                      vhost="/",
                      spec=spec).connectTCP(AMQP_BROKER_HOST, AMQP_BROKER_PORT)
    d.addCallback(gotConnection, username, password)

    def _on_err(err):
        logger.exception("AMQP connection failed: %s", err)
        next_backoff = min(backoff * 2, CONNECT_BACKOFF_MAX)
        logger.info("Reconnecting in %d seconds", backoff)
        try:
            reactor.callLater(backoff, lambda: connect_attempt(next_backoff))
        except Exception as e:
            logger.debug("Failed to schedule reconnect callLater: %s", e)

    d.addErrback(_on_err)

# ---------- bootstrap ----------
if __name__ == "__main__":
    twisted_log.startLogging(sys.stdout)

    logger.info("Starting sms_logger (DB driver: %s)", "MySQL" if DB_TYPE_MYSQL else "Postgres")
    # init DB pools now (best-effort)
    try:
        if DB_TYPE_MYSQL:
            init_mysql_pool()
            # test conn
            c = get_mysql_conn()
            c.close()
        else:
            init_postgres_pool()
            conn = get_postgres_conn()
            put_postgres_conn(conn)
    except Exception as e:
        logger.exception("DB pool initialisation failed: %s", e)
        # continue - we'll try again in runtime

    username = os.getenv("AMQP_USER", "guest")
    password = os.getenv("AMQP_PASS", "guest")
    host = AMQP_BROKER_HOST
    port = AMQP_BROKER_PORT
    vhost = "/"
    spec_file = AMQP_SPEC_FILE

    # Load AMQP spec file
    try:
        spec = txamqp.spec.load(spec_file)
    except Exception as e:
        logger.exception("Failed to load AMQP spec file '%s': %s", spec_file, e)
        raise

    # Quick heuristic: if the spec file contains an explicit heartbeat set to 0, warn the user.
    try:
        with open(spec_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # naive check for 'heartbeat' 0; helpful to catch the common Jasmin spec issue
            if "heartbeat" in content:
                # check for patterns like heartbeat="0" or <heartbeat>0</heartbeat>
                if 'heartbeat="0"' in content or ">0<" not in content and ("<heartbeat>0" in content or "heartbeat>0" not in content and "heartbeat>0" not in content and 'heartbeat="0"' in content):
                    # above condition is conservative; simply warn if explicit 0 found
                    if 'heartbeat="0"' in content or "<heartbeat>0" in content or "heartbeat>0" in content:
                        logger.warning("AMQP spec file '%s' appears to have heartbeat set to 0 (disabled). Edit it to a non-zero value (e.g. 30) to negotiate AMQP heartbeats with the broker.", spec_file)
    except Exception:
        # not fatal; skip
        pass

    # start periodic qmap cleanup timer
    reactor.callLater(300, periodic_qmap_cleanup)

    # Start initial connect attempt (connect_attempt defined above)
    try:
        connect_attempt(CONNECT_BACKOFF_BASE)
        reactor.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        try:
            reactor.stop()
        except Exception:
            pass