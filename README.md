## Test LDBC SNB on Postgres

Following the instruction on the LDBC team on their Github pages:
- [Interactive implementation](https://github.com/ldbc/ldbc_snb_interactive_impls/tree/main/postgres)
- [Dataset generation](https://github.com/ldbc/ldbc_snb_datagen_spark)
- [Parameters generation](https://github.com/ldbc/ldbc_snb_interactive_driver)

### Initialisation

Set environment variables : 
- POSTGRES_PATH : path for a custom directory for postgres
- POSTGRES_DB : name of the db use to save the tables
- POSTGRES_USER : user to use during the test
- POSTGRES_PASSWORD : the extremely secret password

Use the script ```initiate.sh``` to initiate.

#### pg_stat_statements
In the part Running benchmark, the script use [pg_stat_statements](https://www.postgresql.org/docs/current/pgstatstatements.html) 
to collect the stats of the queries

If you don't need it, comment the part at the end of ```initiate.sh```:
```
echo "shared_preload_libraries = 'pg_stat_statements'" >> postgresql.conf
echo "pg_stat_statements.track = top" >> postgresql.conf

pg_ctl -D /path/custom/directory/ restart
```

### DataSet

#### Generate the dataset
In order to generate the dataset follow there [datagen](https://github.com/ldbc/ldbc_snb_interactive_impls/tree/main/postgres#generating-the-data-set), using docker if you are on windows is easier


I generated the dataset I used docker and the following command :
```
docker run --mount type=bind,source=$POSTGRES_CSV_DIR,target=/out ldbc/datagen-standalone --parallelism 4 --memory 10G -- --mode raw --scale-factor 10 --mode bi --generate-factors
```
With :
- $POSTGRES_CSV_DIR : path where the dataset should be saved

#### Load the dataset
To load the dataset you can follow there [instructions](https://github.com/ldbc/ldbc_snb_interactive_impls/tree/main/postgres#loading-the-data-set).
But you might use the ```load2.py``` scripts, because the ```load.py``` doesn't seem to work.


### Running benchmark

This is the part where I change from there [implementation](https://github.com/ldbc/ldbc_snb_interactive_impls/tree/main/postgres#running-the-benchmark), 
during the benchmark the queries are executed randomly and in order to test another solution I would execute every query in the same order without random.

To setup this test you will need to do the following:
- git clone https://github.com/ldbc/ldbc_snb_interactive_impls.git
- export LDBC_IMPL_DIR="path/to/ldbc_snb_interactive_impls/"
- export LDBC_PARAM_DIR="path/to/the/parameters/"
- export POSTGRES_HOST="" 
  - the endpoint to use to communicate with postgres
- pip install psycopg2 
  - if not already done

And if you change something higher you will need to export those variables: 
- POSTGRES_PORT
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

When every things is set juste run:
```commandline
python3 scripts/main.py
```