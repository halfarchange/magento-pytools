# magento-pytools
Set of tools written in python for Magento 1 community and entreprise used in production on a large ecommerce platform

# Install

1. Unzip/copy all scripts in the `{magento_root}/shell/` subdirectory
1. edit `shell/pylib/__init__.py` file and adapt your configuration at the top (there is no need to put any of the DB details, the scripts will look for them in Magento local.xml directly).
1. in a shell, go to `shell/` subdirectory and fire any scripts you like

# How to use

All scripts be fired without any arguments will **not** perform anything but give you a small help on how to use them which means if you dont know or remember how a script work, _simply running it without any parameter is safe and will not break anything_.

# List of Scripts

Script | Notes
-------|--------
adminUsersReport.py | script to be executed every 28th of the month, it will disable automatically all admin users that were not connected since the beginning of the month and send a html report by email. The users can be reactivated in Magento backend (or in the database)
backupDB.py | Small tool to quickly backup and restore your magento database. Beware that this script can be used against a live system **without annoying** it BUT the resulting data set **may not be integrous if you backup the whole database** and should not be considered as a real backup of your production system but to make a **copy** of your production database for test or debugguing. The resulting data set can be used on any other environments directly. You **can** use this script to make **real integrous backup** of your production database but you have to put your site (and your crontab) down first (or block any write to your DB) then restart them after. Usually real backups are done by other means in production system. This tool is very handy to quickly backup one or more tables such as config or cms prior to make a SQL command that may go wrong, you invoke the backup in one command without the need for the password then perform the SQL command, and if this goes wrong you can almost instantly "reload" the table again without the need to get the password or go through a phpMyAdmin-like interface.
syncOrderGrid.py | small script that can be fired by cron or manually to resync the sales_flat_order and its grid, for some reason usually with high traffic and number or orders there are sometimes glitches and the observers supposed to take care of the sync do not work most probably due to custom code or third-party such as PSP. Only a few seconds of execution on 3+ million orders on a good server.


