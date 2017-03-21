# magento-pytools
Set of tools written in python for Magento 1 community and entreprise used in production on a large ecommerce platform

# List of Scripts

Script | Notes
-------|--------
backupDB.py | small tool to quickly backup and restore your magento database. Beware that this script is can be used against a live system **without annoying** it BUT the resulting data set may not be integrous if you backup the whole database and should not be considered as a real backup of your production system but to make a **copy** of your production database for test or debugguing. The resulting data set can be used on any other environments directly. You **can** use this script to make **real integrous backup** of your production database but you have to put your site (and your crontab) down first (or block any write to your DB) then restart them after. Usually real backups are done by other means in production system. This tool is very handy to quickly backup one or more tables such as config or cms prior to make a SQL command that may go wrong, you invoke the backup in one command without the need for the password then perform the SQL command, and if this goes wrong you can almost instantly "reload" the table again without the need to get the password or go through a phpMyAdmin-like interface.


