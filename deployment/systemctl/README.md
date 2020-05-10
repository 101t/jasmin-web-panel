# Django-AIO Systemd Way

You know - that tool you didn’t really knew you would need when you started to work on your app project. Sometime before you found out that deploying your app can turn into much more work than expected.

Let’s make sure you have a broad overview, and enough understanding of useful commands to get going. After reading this, you should have just the right amount of information to interact with systemd and continue climbing the steep deployment learning curve.

## What systemd does

You need a process supervisor to keep your services running. Systemd help to keep your web app and its backing services (NGiNX, PostgreSQL) running smoothly.

Systemd is an excellent choice. It’s used in many mainstream distros, and can do everything you need. You can start, stop or restart any services with a simple command, check their status and view logs - all via systemd.

If something crashes, systemd will make sure to start a new process (if you configure it right), so you don’t have to do it manually.

## Telling systemd about a new service

Systemd uses configuration files to keep track of all service it manages.

The folder you care about is `/etc/systemd/system`. If you look inside, you’ll see (among other content) lots of `.service` files.

If you type a command like `systemctl status django-projectname`, systemd will look for a file names `django-projectname.service`. The `/etc/systemd/system` folder is the first place it looks.

That django-projectname.service file is called a “unit file”, and it tells systemd:

* That your service exists
* How to describe it
* How and when to run it

The file name "django-projectname" is arbitrary, you can just name it "projectname", or some other string. Lower-case letters with dashes is how most services are named. Make sure it doesn’t clash with existing system services.

## An example Django unit file

Here’s how a `.service` file for a Django project can look like:
```sh
[Unit]
Description=A useful description to be shown in command-line tools

[Service]
Restart=on-failure
WorkingDirectory=/var/www/django-projectname/projectname
ExecStart=/var/www/django-projectname/env/bin/gunicorn config.wsgi -b 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```
A lot of nuance is missing there, so don’t use it for your project. Consult a more in-depth tutorial on the topic of writing a great unit file for your service. This one’s here to get you started with the topic.

The [Service] section tells systemd how to run your app. We want it to restart if something goes wrong, and tell systemd the directory and exact command to run. A few assumptions about folder structure is made here - this can vary and is a matter of taste. I like to create a `/var/www/django-projectname` directory where everything related to a single project can be found.

The [Install] section, is used when you `enable` the service, so it’s started automatically after the service restarts.

## Most useful commands

You interact with systemd-managed services, by using the command-line tools `systemctl` and `journalctl`.

You’ll need to have superuser privileges for most of those, so add a `sudo` in the beginning of each command if needed.

Once the file above is in place, you should tell systemd to take a look at its own configurations, so it can notice that stuff has changed.

```sh
# added a new unit file? let systemd know
systemctl daemon-reload
```
Now, you can:
```sh
# check the status of the service
systemctl status django-projectname

# you can start the service
systemctl start django-projectname

# restart it (stop and then start again in one command)
systemctl restart django-projectname

# just stop it
systemctl stop django-projectname
```
If you want the service to be started by default after a reboot, use:

```sh
systemctl enable django-projectname
```

You’ll need the [Install] section in your unit file for this to have any effect.

To view the logs of a service, you can use:

```sh
journalctl -u django-projectname
```

You can add a `-b` to view all lines since the last reboot

## One more thing

Here’s some cool but mostly useless knowledge I really like!

If you want to get a quick overview of all services which are started when your server boots up, you can use:

```sh
systemctl list-dependencies multi-user.target
```

If you want to know what your new service needs, just take a look:

```sh
systemctl list-dependencies django-projectname
```