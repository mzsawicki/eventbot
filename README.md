# EventBot

I didn't like Discord's event system, so I made my own.

NOTE: Currently, only Polish language is supported.

## Running
Create environment file by coping the example one:
```shell
cp example.env prod.env
```
And replacing its content with your own configuration.

Install all the required packages (virtual environment usage recommended):
```shell
pip install -r requirements.txt
```

Start the database; you can use provided docker-compose file:
```shell
docker-compose up db -d
```

Prepare the database schema with the bootstrap script (note this will purge the existing schema):
```shell
chmod +x bootstrap.sh
./bootstrap.sh
```

Then, you can run the bot:
```shell
chmod +x run.sh
./run.sh
```