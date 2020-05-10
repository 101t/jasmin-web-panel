ENVIROO=./env/bin/python
MANAGER=manage.py

if [ "$1" == "--init" ] || [ "$1" == "-i" ]; then
	echo "- Deleting sqlite database if exist ..."
	rm -rf db.sqlite3
	echo "- Reset all migrations files ..."
	$ENVIROO $MANAGER reseter
	echo "- Make new migrations files ..."
	$ENVIROO $MANAGER makemigrations
	echo "- Migrate database ..."
	$ENVIROO $MANAGER migrate
	echo "- Loading new data samples ..."
	$ENVIROO $MANAGER load_new
fi

RUN_PROJECT="$ENVIROO $MANAGER runserver 0.0.0.0:8000"
echo $RUN_PROJECT
$RUN_PROJECT