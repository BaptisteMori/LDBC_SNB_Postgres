from pathlib import Path
import pandas as pd
import psycopg2
import time
import re, os
from datetime import datetime


map_queries_params = {
    "interactive-short-1.sql": {"param_file": "interactive-personId.csv", "params": ["personId"]},
    "interactive-short-2.sql": {"param_file": "interactive-personId.csv", "params": ["personId"]},
    "interactive-short-3.sql": {"param_file": "interactive-personId.csv", "params": ["personId"]},
    "interactive-short-4.sql": {"param_file": "interactive-messageId.csv", "params": ["messageId"]},
    "interactive-short-5.sql": {"param_file": "interactive-messageId.csv", "params": ["messageId"]},
    "interactive-short-6.sql": {"param_file": "interactive-messageId.csv", "params": ["messageId"]},
    "interactive-short-7.sql": {"param_file": "interactive-messageId.csv", "params": ["messageId"]},
    "interactive-complex-1.sql": {"param_file": "interactive-1.csv", "params": ["personId", "firstName"]},
    "interactive-complex-2.sql": {"param_file": "interactive-2.csv", "params": ["personId", "maxDate"]},
    "interactive-complex-3.sql": {"param_file": "interactive-3.csv", "params": ["personId", "countryXName", "countryXName", "startDate", "durationDays"]},
    "interactive-complex-4.sql": {"param_file": "interactive-4.csv", "params": ["personId", "startDate", "durationDays"]},
    "interactive-complex-5.sql": {"param_file": "interactive-5.csv", "params": ["personId", "minDate"]},
    "interactive-complex-6.sql": {"param_file": "interactive-6.csv", "params": ["personId", "tagName"]},
    "interactive-complex-7.sql": {"param_file": "interactive-7.csv", "params": ["personId"]},
    "interactive-complex-8.sql": {"param_file": "interactive-8.csv", "params": ["personId"]},
    "interactive-complex-9.sql": {"param_file": "interactive-9.csv", "params": ["personId", "maxDate"]},
    "interactive-complex-10.sql": {"param_file": "interactive-10.csv", "params": ["personId", "month"]},
    "interactive-complex-11.sql": {"param_file": "interactive-11.csv", "params": ["personId", "countryName", "workFromYear"]},
    "interactive-complex-12.sql": {"param_file": "interactive-12.csv", "params": ["personId", "tagClassName"]},
    "interactive-complex-13.sql": {"param_file": "interactive-13a.csv", "params": ["person1Id", "person2Id"]},
    "interactive-complex-14.sql": {"param_file": "interactive-14a.csv", "params": ["person1Id", "person2Id"]},
}


def get_queries_files(queries_path: Path, short=True, complex=False, update=False, delete=False):
    queries_list = {}
    if short: queries_list["short"] = []
    if complex: queries_list["complex"] = []
    if update: queries_list["update"] = []
    if delete: queries_list["delete"] = []

    for sql_file in queries_path.glob("*.sql"):
        if "short" in sql_file.name and short:
            queries_list["short"].append(sql_file)
        elif "complex" in sql_file.name and complex:
            queries_list["complex"].append(sql_file)
        elif "update" in sql_file.name and update:
            queries_list["update"].append(sql_file)
        elif "delete" in sql_file.name and delete:
            queries_list["delete"].append(sql_file)

    return queries_list


def load_parameter(path: Path):
    return pd.read_csv(path)


def remove_multiline_comments(sql):
    pattern = r"/\*(.*?)\*/"
    result = re.sub(pattern, "", sql, flags=re.DOTALL)
    return result


class PostgresExecute:
    def __init__(self, endpoint, port=5432, user="postgres", password="mysecretpassword",database="ldbcsnb", statfile: Path = ""):
        self.database = database
        self.endpoint = endpoint
        self.port = port
        self.user = user
        self.password = password
        self.pg_con = psycopg2.connect(
            dbname=self.database,
            host=self.endpoint,
            user=self.user,
            password=self.password,
            port=self.port
        )
        self.cursor = self.pg_con.cursor()

        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")

        self.columns = ["query_name", "calls", "min_exec_time", "max_exec_time", "mean_exec_time", "stddev_exec_time", "time_client", "nb_empty"]

        self.statfile = statfile

    def __del__(self):
        self.pg_con.close()

    def load_query(self, query_path: Path):
        with open(query_path, 'r') as fp:
            query = fp.read()
        return query

    def load_params(self, params_path: Path):
        return pd.read_csv(params_path, dtype=str)

    def execute_query(self, query_path: Path, params_path: Path, parameters):
        query_name = query_path.stem
        print(f"testing {query_name} ...")
        query = remove_multiline_comments(self.load_query(query_path))
        params = self.load_params(params_path)
        empty = 0

        times_client = []
        nb_param = params.shape[0]
        t_start_g = time.time()
        t_tmp = t_start_g

        print(f"0/{nb_param} : 0%")
        params = params[10:]
        for i, row in params.iterrows():
            self.cursor.execute("select pg_stat_statements_reset()")
            t_now = time.time()
            print(f"{i}/{nb_param} : {100 * i//nb_param} % | t_loop : {t_now - t_tmp} | t_total : {t_now - t_start_g} | start : {datetime.now()}")
            t_tmp = t_now
            q_tmp = query

            cpt = 1
            param_s = []
            for p in row.keys():
                p1 = str(p[0].lower()) + str(p[1:])
                param = str(row[p])
                if "Date" in p1:
                    p_tmp = param.split("  ")[0]
                    param = f"'{p_tmp}'::Date"
                else:
                    param = f"'{param}'"

                q_tmp = q_tmp.replace(f":{p1}", param)
                param_s.append(str(row[p]))
                cpt += 1

            print(param_s)
            t_start = time.time()
            self.cursor.execute(q_tmp)
            result = self.cursor.fetchall()
            t_end = time.time()
            print(result)

            if result == []:
                empty += 1

            times_client.append(t_end - t_start)

            self.cursor.execute("""select
                query, 
                calls,
                min_exec_time,
                max_exec_time,
                mean_exec_time,
                stddev_exec_time
                from pg_stat_statements
            """)
            stats = self.cursor.fetchall()

            stat: None | [] = None
            for s in stats:
                if s[0] != "select pg_stat_statements_reset()": #q_tmpt.replace("\n;\n", "")[1:]:
                    stat = s
                    break

            if stat:
                stat = [x for x in stat]
                stat.append(sum(times_client)/len(times_client))
                stat.append(empty)
                stat = [str(x) for x in stat]
                stat[0] = query_name
                if self.statfile:
                    e = True
                    if not os.path.exists(self.statfile):
                        e = False

                    with open(self.statfile, "a") as fp:
                        if not e:
                            fp.write(",".join(self.columns) + "\n")

                        l = ",".join(stat)+ "," + ",".join(param_s) + "\n"
                        print(l)
                        fp.write(l)
            # exit()


if __name__ == "__main__":

    QUERIES_PATH = Path(os.environ["LDBC_IMPL_DIR"]).joinpath("postgres\queries")
    PARAMS_PATH = Path(os.environ["LDBC_PARAM_DIR"])

    a = get_queries_files(QUERIES_PATH, complex=True)

    database = os.environ.get("POSTGRES_DB", "ldbcsnb")
    endpoint = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", 5432))
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "mysecretpassword")
    r = PostgresExecute(endpoint, port, user, password, database, Path("stats_postgres.csv"))

    queries_list = [x for x in a["complex"] + a["short"]]

    for i in range(len(queries_list)):
        q = queries_list[i]

        print(f"{i}/{len(queries_list)} | perfoming : {q.stem}")
        p_path = PARAMS_PATH.joinpath(map_queries_params[q.name]["param_file"].replace("a.", "."))

        r.execute_query(q, p_path, map_queries_params[q.name]["params"])
