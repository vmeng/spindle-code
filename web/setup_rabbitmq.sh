#!/bin/sh

echo '* Checking for rabbitmq ...'
rabbitmqctl status || exit 1

echo "* Creating 'spindle' vhost"
rabbitmqctl create_vhost spindle || exit 1

echo "* Creating 'spindle' user"
read -p "Enter password: " -s pw

rabbitmqctl add_user spindle "$pw" || exit 1

echo "* Setting permissions for 'spindle' on vhost 'spindle'"
rabbitmqctl set_permissions -p spindle spindle '.*' '.*' '.*' || exit 1

echo '* Done!'
exit 0
