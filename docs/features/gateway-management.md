# Gateway Management

Every page of the panel manages one kind of Jasmin object through the jcli console, the same way an administrator would
with `telnet localhost 8990`. Changes are persisted immediately, so they survive a Jasmin restart. When Jasmin refuses a
change, the panel shows Jasmin's own message.

The usual order to set up a gateway is: **groups → users → connectors → filters → routes**.

## Groups and users

Every Jasmin user belongs to a group. Disabling a group disables all of its users.

| Field | Rule |
|-------|------|
| Group id (`gid`), user id (`uid`) | 1–16 letters, digits, `_` or `-` |
| Username | 1–15 letters, digits, `_` or `-`; this is the login for the HTTP API and the SMPP `system_id` |
| Password | 1–16 characters |

When editing a user:

- `uid` and `username` cannot be changed (Jasmin does not allow renaming); delete and recreate the user instead.
- The password field is always empty: leave it empty to keep the current password.
- Quotas left empty (or set to `ND`) are unlimited.
- Only the values you change are sent to Jasmin. A balance or SMS count consumed while the form was open is not overwritten.
- Unchecking an authorization revokes it (for example *HTTP Send* to stop a user from sending through the HTTP API).

The service menu enables or disables a user, and can unbind (or unbind and ban) a user from the SMPP server.

!!! note "Duplicates"
    jcli silently replaces an object when you add one with an existing id, which would reset a user's quotas and
    authorizations. The panel refuses duplicates instead: *"User u1 already exists"*.

## Connectors

**SMPP client connectors** (`smppccm`) connect Jasmin to your SMSC providers and carry MT messages. Connector ids are 3–25
letters, digits, `_` or `-`. The list shows whether each connector is started and its session state (`BOUND_TRX`, …).
Editing a connector only sends the fields you changed: changing `host`, `port`, `username`, `password` or `systype`
makes Jasmin restart the connector.

**HTTP client connectors** (`httpccm`) are URLs Jasmin calls to deliver MO messages to your application.

## Filters

Filters decide which messages a route matches. Not every filter works on both route directions:

| Type | Parameter | MO routes | MT routes |
|------|-----------|:---------:|:---------:|
| TransparentFilter | — (matches everything) | ✓ | ✓ |
| ConnectorFilter | `cid` of the source connector | ✓ | |
| UserFilter | `uid` of the sending user | | ✓ |
| GroupFilter | `gid` of the sending user | | ✓ |
| SourceAddrFilter | regex on the source address | ✓ | ✓ |
| DestinationAddrFilter | regex on the destination address | ✓ | ✓ |
| ShortMessageFilter | regex on the content | ✓ | ✓ |
| DateIntervalFilter | `2024-01-01;2024-12-31` | ✓ | ✓ |
| TimeIntervalFilter | `08:00:00;18:00:00` | ✓ | ✓ |
| TagFilter | numeric tag | ✓ | ✓ |
| EvalPyFilter | path to a Python script | ✓ | ✓ |

The router pages only offer the filters that fit the route direction.

## Routes

Routes are evaluated from the highest `order` down to `0`; the first route whose filters all match is used. A
`DefaultRoute` takes no filter and always has order `0`, so it catches whatever no other route matched.

| Type | Connectors | Filters |
|------|-----------|---------|
| DefaultRoute | exactly one | none |
| Static route | exactly one | required |
| RandomRoundrobin route | two or more, one picked at random | required |
| Failover route | two or more, the first available one is used | required |

**MT routes** (outgoing) deliver through SMPP client connectors and can carry a `rate` used for billing.

**MO routes** (incoming) deliver to HTTP connectors, or to users bound to Jasmin's SMPP server. The *SMPP Users* list
shows Jasmin users by username: the message is delivered as `smpps(username)` to whichever session that user has bound.
A Failover MO route cannot mix HTTP connectors and SMPP users.

## When the gateway is unreachable

If the panel cannot reach jcli, each page says so instead of showing an empty table, for example
*"Could not connect to Jasmin jcli at 127.0.0.1:8990. Is the gateway running and reachable?"*, with a **Retry** button.
See [Troubleshooting](../troubleshooting.md).
