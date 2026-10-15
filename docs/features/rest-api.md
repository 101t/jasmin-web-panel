# REST API

The panel exposes a REST API under `/api/` for managing the Jasmin gateway from scripts and other systems. It uses the
same jcli code as the web interface, so the same rules and validations apply.

Open `/api/` in a browser while signed in to explore the endpoints interactively.

## Authentication

Use a panel account (the one you sign in with), with either:

- **Basic authentication**: `curl -u admin:secret http://localhost:8999/api/groups/`
- **Session authentication**: requests from a browser that is signed in to the panel.

Requests are rate limited (`API_THROTTLE_ANON`, `API_THROTTLE_USER`; see [Configuration](../getting-started/configuration.md)).

## Requests and responses

Send JSON (`-H "Content-Type: application/json"`). Lists, such as route connectors and filters, can be JSON arrays or
comma-separated strings; with form-encoded bodies, use comma-separated strings.

Errors always have the same shape:

```json
{"error": "Unknown user: bob", "detail": "Unknown user: bob"}
```

| Status | Meaning |
|--------|---------|
| `400` | Jasmin rejected the request (invalid value, missing field, duplicate id); `error` holds Jasmin's message |
| `401` / `403` | Not authenticated |
| `404` | The group, user, connector, filter or route does not exist |
| `503` | The panel cannot reach Jasmin's jcli (gateway down, wrong `TELNET_*` settings) |

## Health check

`GET /api/health_check` needs no authentication; use it for load balancer and container health checks.

```json
{"version": "3.0.3", "status": "ok"}
```

## Groups

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/groups/` | | List groups: `{"groups": [{"name": "g1", "status": "enabled"}]}` |
| `POST` | `/api/groups/` | `{"gid": "g1"}` | Create a group (`201`) |
| `DELETE` | `/api/groups/<gid>/` | | Delete a group |
| `PUT` | `/api/groups/<gid>/enable/` | | Enable a group |
| `PUT` | `/api/groups/<gid>/disable/` | | Disable a group and, with it, its users |

## Users

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/users/` | | List users with their credentials and status |
| `POST` | `/api/users/` | `{"uid", "gid", "username", "password"}` | Create a user (`201`); the group must exist |
| `GET` | `/api/users/<uid>/` | | One user (passwords are never returned) |
| `PATCH` | `/api/users/<uid>/` | `{"updates": [[...], ...]}` | Update a user, see below |
| `DELETE` | `/api/users/<uid>/` | | Delete a user |
| `PUT` | `/api/users/<uid>/enable/` | | Enable a user |
| `PUT` | `/api/users/<uid>/disable/` | | Disable a user |

`updates` is a list of jcli `user -u` lines, each written as a list of words:

```bash
curl -u admin:secret -X PATCH -H "Content-Type: application/json" \
  -d '{"updates": [
        ["gid", "partners"],
        ["mt_messaging_cred", "quota", "balance", "100"],
        ["mt_messaging_cred", "quota", "sms_count", "None"],
        ["mt_messaging_cred", "authorization", "http_send", "False"]
      ]}' \
  http://localhost:8999/api/users/user1/
```

Use `None` for an unlimited quota. `uid` and `username` cannot be changed.

## SMPP client connectors

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/smppccm/` | | List connectors with configuration and live status (`status`, `session`) |
| `POST` | `/api/smppccm/` | `{"cid", "host", "port", "username", "password", ...}` | Create a connector (`201`); keys are jcli `smppccm` keys |
| `GET` | `/api/smppccm/<cid>/` | | One connector |
| `PATCH` | `/api/smppccm/<cid>/` | `{"submit_throughput": "10", ...}` | Update; only values that differ are sent to Jasmin |
| `DELETE` | `/api/smppccm/<cid>/` | | Delete a connector |
| `PUT` | `/api/smppccm/<cid>/start/` | | Start (bind) the connector |
| `PUT` | `/api/smppccm/<cid>/stop/` | | Stop the connector |

Connector ids are 3 to 25 letters, digits, `_` or `-`.

## HTTP client connectors

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/httpccm/` | | List connectors: `cid`, `type`, `method`, `url` |
| `POST` | `/api/httpccm/` | `{"cid", "url", "method"}` | Create a connector (`201`); `method` is `GET` or `POST` |
| `GET` | `/api/httpccm/<cid>/` | | One connector |
| `DELETE` | `/api/httpccm/<cid>/` | | Delete a connector |

## Filters

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/filters/` | | List filters: `fid`, `type`, `routes` (`MO`, `MT` or `MO MT`), `description` |
| `POST` | `/api/filters/` | `{"type", "fid", "parameter"}` | Create a filter (`201`) |
| `GET` | `/api/filters/<fid>/` | | One filter |
| `DELETE` | `/api/filters/<fid>/` | | Delete a filter |

`type` is one of `transparentfilter` (no parameter), `connectorfilter`, `userfilter`, `groupfilter`, `sourceaddrfilter`,
`destinationaddrfilter`, `shortmessagefilter`, `dateintervalfilter`, `timeintervalfilter`, `tagfilter`, `evalpyfilter`.
See [Gateway Management](gateway-management.md#filters) for the parameter of each type.

## MT routes

| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/api/mtrouter/` | | List routes |
| `POST` | `/api/mtrouter/` | see below | Create a route (`201`) |
| `GET` | `/api/mtrouter/<order>/` | | One route |
| `DELETE` | `/api/mtrouter/<order>/` | | Delete a route |
| `POST` | `/api/mtrouter/flush/` | | Delete **all** MT routes |

```bash
curl -u admin:secret -X POST -H "Content-Type: application/json" \
  -d '{"type": "RandomRoundrobinMTRoute", "order": "10", "rate": "0.015",
       "smppconnectors": ["smsc1", "smsc2"], "filters": ["partners"]}' \
  http://localhost:8999/api/mtrouter/
```

- `type`: `DefaultRoute`, `StaticMTRoute`, `RandomRoundrobinMTRoute` or `FailoverMTRoute`.
- `smppconnectors`: SMPP client connector ids. Static and Default routes take one, RoundRobin and Failover at least two.
- `filters`: MT-compatible filter ids; required except for `DefaultRoute`.
- `order`: routes are evaluated from the highest order down; a `DefaultRoute` is always order `0`.
- `rate`: price per message, used for billing (defaults to `0`).

## MO routes

Same endpoints under `/api/morouter/`. MO routes deliver incoming messages:

- `httpconnectors`: HTTP connector ids, delivered as `http(cid)`.
- `smppconnectors`: **usernames** of Jasmin users bound to the SMPP server, delivered as `smpps(username)`.

A `FailoverMORoute` cannot mix HTTP connectors and SMPP users, and MT-only filters (`UserFilter`, `GroupFilter`) are
refused.
