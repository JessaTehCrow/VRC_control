#!/usr/bin/env bash
if ! command -v php &> /dev/null
then
    echo "PHP not installed"
    echo "Please instal PHP >= 8.2.15"
    echo
    echo "-- If you do have PHP installed, make sure you run this with bash and not sh --"
    echo "Example:"
    echo "bash setup.sh"
    exit
fi

php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php -r "if (hash_file('sha384', 'composer-setup.php') === 'dac665fdc30fdd8ec78b38b9800061b4150413ff2e3b6f88543c636f7cd84f6db9189d43a81e5503cda447da73c7e5b6') { echo 'Installer verified'; } else { echo 'Installer corrupt'; unlink('composer-setup.php'); } echo PHP_EOL;"
php composer-setup.php
php -r "unlink('composer-setup.php');"

php composer.phar update
rm composer.phar