# Submit Log Integration

The Submit Log feature allows you to track every SMS message submitted to the Jasmin Gateway in real-time.

## Enabling the Feature

1. **Env Configuration**: Set `SUBMIT_LOG=True` in your `.env` file.
2. **Jasmin Configuration**: Ensure `publish_submit_sm_resp` is enabled in `jasmin.cfg`.

```ini
[sm-listener]
publish_submit_sm_resp = True
```

## How it Works

1. Jasmin Gateway publishes submit responses to RabbitMQ.
2. The **SMS Logger** service consumes these messages.
3. Messages are saved to the `submit_log` table in the database.
4. The Web Panel reads from this table to display the dashboard.

## Dashboard Features

- **Status Badges**: Easily identify Delivered, Failed, or Queued messages.
- **Search**: Filter by Receiver (Destination), Sender (Source), or Message ID.
- **Pagination**: Browse through millions of logs efficiently.
