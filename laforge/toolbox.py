""" Handful of utility functions

.. note:: These intentionally *only* depend on builtins.

.. note:: Some copyright information within this file is identified per-block below.
"""

import logging
import math
import time
from keyword import kwlist
from pathlib import Path
from typing import Any, Iterator, Sequence, Set, Union

logger = logging.getLogger(__name__)


def round_up(n: Union[int, float], nearest: int = 1) -> int:
    """Round up ``n`` to the nearest ``nearest``.

    :param n:
    :param nearest:  (Default value = 1)

    """
    return nearest * math.ceil(n / nearest)


def prepare_to_access(path: Path) -> None:
    """Make directory exist and verify that file would be writable"""
    if path.exists():
        verify_file_is_writable(path)
    else:
        if not path.parent.exists():
            path.parent.mkdir(parents=True)


def verify_file_is_writable(
    path: Path, retry_attempts: int = 3, retry_seconds: int = 5
) -> None:
    """Check for locked file (e.g. Excel has CSV open)"""
    plural_sec = "" if retry_seconds == 1 else "s"
    for i in range(retry_attempts):
        try:
            with path.open("a"):
                return None
        except PermissionError:
            error_message = (
                f"Permission denied to {path}. Is it open in another program?"
            )
            logger.error(error_message)
        remaining = retry_attempts - i
        plural_rem = "" if remaining == 1 else "s"
        logger.error(
            "%s attempt%s remaining. Trying %s again in %s second%s...",
            remaining,
            plural_rem,
            path,
            retry_seconds,
            plural_sec,
        )
        time.sleep(retry_seconds)
    raise PermissionError(f"Permission denied to {path}")


def flatten(foo: Sequence[Any]) -> Iterator[Any]:
    """Take any set of nests in an iterator Fquand reduce it into one generator.

    'Nests' include any iterable except strings.

    :param foo:

    .. note::

        :py:func:`flatten` was authored
        by `Amber Yust <https://stackoverflow.com/users/148870/amber>`_
        at https://stackoverflow.com/a/5286571.

    """
    # pylint: disable=invalid-name,blacklisted-name
    for x in foo:
        if hasattr(x, "__iter__") and not isinstance(x, str):
            for y in flatten(x):
                yield y
        else:
            yield x


PRESPEC_RESERVED_WORD_DICT = {
    # https://docs.microsoft.com/en-us/sql/t-sql/language-elements/reserved-keywords-transact-sql?view=sql-server-2017
    "MSSQL": "absolute action add admin after aggregate alias all allocate alter "
    "and any are array as asc asensitive assertion asymmetric at atomic "
    "authorization backup before begin between binary bit blob boolean "
    "both breadth break browse bulk by call called cardinality cascade "
    "cascaded case cast catalog char character check checkpoint class "
    "clob close clustered coalesce collate collation collect column "
    "commit completion compute condition connect connection constraint "
    "constraints constructor contains containstable continue convert corr "
    "corresponding create cross cube current cursor cycle data database "
    "date day dbcc deallocate dec decimal declare default deferrable "
    "deferred delete deny depth deref desc describe descriptor destroy "
    "destructor deterministic diagnostics dictionary disconnect disk "
    "distinct distributed domain double drop dump dynamic each element "
    "else end equals errlvl escape every except exception exec execute "
    "exists exit external false fetch file fillfactor filter first float "
    "for foreign found free freetext freetexttable from full "
    "fulltexttable function fusion general get global go goto grant "
    "group grouping having hold holdlock host hour identity identitycol "
    "if ignore immediate in index indicator initialize initially inner "
    "inout input insert int integer intersect intersection interval into "
    "is isolation iterate join key kill language large last lateral "
    "leading left less level like limit lineno ln load local localtime "
    "localtimestamp locator map match member merge method minute mod "
    "modifies modify module month multiset names national natural nchar "
    "nclob new next no nocheck nonclustered none normalize not null "
    "nullif numeric object of off offsets old on only open "
    "opendatasource openquery openrowset openxml operation option or "
    "order ordinality out outer output over overlay pad parameter "
    "parameters partial partition path percent pivot plan postfix "
    "precision prefix preorder prepare preserve primary print prior "
    "privileges proc procedure public raiserror range read reads "
    "readtext real reconfigure recursive ref references referencing "
    "relative release replication restore restrict result return "
    "returns revert revoke right role rollback rollup routine row "
    "rowcount rowguidcol rows rule save savepoint schema scope scroll "
    "search second section securityaudit select semantickeyphrasetable "
    "semanticsimilaritydetailstable semanticsimilaritytable sensitive "
    "sequence session set sets setuser shutdown similar size smallint "
    "some space specific specifictype sql sqlexception sqlstate "
    "sqlwarning start state statement static statistics structure "
    "submultiset symmetric system table tablesample temporary terminate "
    "textsize than then time timestamp to top trailing tran transaction "
    "translation treat trigger true truncate tsequal uescape under "
    "union unique unknown unnest unpivot update updatetext usage use "
    "user using value values varchar variable varying view waitfor when "
    "whenever where while window with within without work write "
    "writetext xmlagg xmlattributes xmlbinary xmlcast xmlcomment "
    "xmlconcat xmldocument xmlelement xmlexists xmlforest xmliterate "
    "xmlnamespaces xmlparse xmlpi xmlquery xmlserialize xmltable "
    "xmltext xmlvalidate year zone",
    "ODBC": "absolute action ada add all allocate alter and any are as asc "
    "assertion at authorization avg begin between bit bit_length both by "
    "cascade cascaded case cast catalog char character character_length "
    "char_length check close coalesce collate collation column commit "
    "connect connection constraint constraints continue convert "
    "corresponding count create cross current current_date current_time "
    "current_timestamp current_user cursor date day deallocate dec decimal "
    "declare default deferrable deferred delete desc describe descriptor "
    "diagnostics disconnect distinct domain double drop else end end-exec "
    "escape except exception exec execute exists external extract false "
    "fetch first float for foreign fortran found from full get global go "
    "goto grant group having hour identity immediate in include index "
    "indicator initially inner input insensitive insert int integer "
    "intersect interval into is isolation join key language last leading "
    "left level like local lower match max min minute module month names "
    "national natural nchar next no none not null nullif numeric "
    "octet_length of on only open option or order outer output overlaps "
    "pad partial pascal position precision prepare preserve primary prior "
    "privileges procedure public read real references relative restrict "
    "revoke right rollback rows schema scroll second section select "
    "session session_user set size smallint some space sql sqlca sqlcode "
    "sqlerror sqlstate sqlwarning substring sum system_user table "
    "temporary then time timestamp timezone_hour timezone_minute to "
    "trailing transaction translate translation trim true union unique "
    "unknown update upper usage user using value values varchar varying "
    "view when whenever where with work write year zone",
    # https://dev.mysql.com/doc/refman/5.5/en/keywords.html
    "MYSQL": "accessible action add after against aggregate algorithm all alter "
    "analyze and any as asc ascii asensitive at authors auto_increment "
    "autoextend_size avg avg_row_length backup before begin between bigint "
    "binary binlog bit blob block bool boolean both btree by byte cache "
    "call cascade cascaded case catalog_name chain change changed char "
    "character charset check checksum cipher class_origin client close "
    "coalesce code collate collation column column_name columns comment "
    "commit committed compact completion compressed concurrent condition "
    "connection consistent constraint constraint_catalog constraint_name "
    "constraint_schema contains context continue contributors convert cpu "
    "create cross cube current_date current_time current_timestamp "
    "current_user cursor cursor_name data database databases datafile "
    "date datetime day day_hour day_microsecond day_minute day_second "
    "deallocate dec decimal declare default definer delay_key_write "
    "delayed delete des_key_file desc describe deterministic directory "
    "disable discard disk distinct distinctrow div do double drop dual "
    "dumpfile duplicate dynamic each else elseif enable enclosed end ends "
    "engine engines enum error errors escape escaped event events every "
    "execute exists exit expansion explain extended extent_size false fast "
    "faults fetch fields file first fixed float float4 float8 flush for "
    "force foreign found frac_second from full fulltext function general "
    "geometry geometrycollection get_format global grant grants group "
    "handler hash having help high_priority host hosts hour "
    "hour_microsecond hour_minute hour_second identified if ignore "
    "ignore_server_ids import in index indexes infile initial_size inner "
    "innobase innodb inout insensitive insert insert_method install int "
    "int1 int2 int3 int4 int8 integer interval into invoker io io_thread "
    "ipc is isolation issuer iterate join key key_block_size keys kill "
    "language last leading leave leaves left less level like limit linear "
    "lines linestring list load local localtime localtimestamp lock locks "
    "logfile logs long longblob longtext loop low_priority master "
    "master_connect_retry master_heartbeat_period master_host "
    "master_log_file master_log_pos master_password master_port "
    "master_server_id master_ssl master_ssl_ca master_ssl_capath "
    "master_ssl_cert master_ssl_cipher master_ssl_key "
    "master_ssl_verify_server_cert master_user match "
    "max_connections_per_hour max_queries_per_hour max_rows max_size "
    "max_updates_per_hour max_user_connections maxvalue medium mediumblob "
    "mediumint mediumtext memory merge message_text microsecond middleint "
    "migrate min_rows minute minute_microsecond minute_second mod mode "
    "modifies modify month multilinestring multipoint multipolygon mutex "
    "mysql_errno name names national natural nchar ndb ndbcluster new next "
    "no no_wait no_write_to_binlog nodegroup none not null numeric "
    "nvarchar offset old_password on one one_shot open optimize option "
    "optionally options or order out outer outfile owner pack_keys page "
    "parser partial partition partitioning partitions password phase "
    "plugin plugins point polygon port precision prepare preserve prev "
    "primary privileges procedure processlist profile profiles proxy purge "
    "quarter query quick range read read_only read_write reads real "
    "rebuild recover redo_buffer_size redofile redundant references "
    "regexp relay relay_log_file relay_log_pos relay_thread relaylog "
    "release reload remove rename reorganize repair repeat repeatable "
    "replace replication require reset resignal restore restrict resume "
    "return returns revoke right rlike rollback rollup routine row "
    "row_format rows rtree savepoint schedule schema schema_name schemas "
    "second second_microsecond security select sensitive separator serial "
    "serializable server session set share show shutdown signal signed "
    "simple slave slow smallint snapshot socket some soname sounds source "
    "spatial specific sql sql_big_result sql_buffer_result sql_cache "
    "sql_calc_found_rows sql_no_cache sql_small_result sql_thread "
    "sql_tsi_day sql_tsi_frac_second sql_tsi_hour sql_tsi_minute "
    "sql_tsi_month sql_tsi_quarter sql_tsi_second sql_tsi_week "
    "sql_tsi_year sqlexception sqlstate sqlwarning ssl start starting "
    "starts status stop storage straight_join string subclass_origin "
    "subject subpartition subpartitions super suspend swaps switches "
    "table table_checksum table_name tables tablespace temporary temptable "
    "terminated text than then time timestamp timestampadd timestampdiff "
    "tinyblob tinyint tinytext to trailing transaction trigger triggers "
    "true truncate type types uncommitted undefined undo undo_buffer_size "
    "undofile unicode uninstall union unique unknown unlock unsigned until "
    "update upgrade usage use use_frm user user_resources using utc_date "
    "utc_time utc_timestamp value values varbinary varchar varcharacter "
    "variables varying view wait warnings week when where while with work "
    "wrapper write x509 xa xml xor year year_month zerofill",
    # https://www.sqlite.org/lang_keywords.html
    "SQLITE": "abort action add after all alter analyze and as asc attach "
    "autoincrement before begin between by cascade case cast check collate "
    "column commit conflict constraint create cross current current_date "
    "current_time current_timestamp database default deferrable deferred "
    "delete desc detach distinct do drop each else end escape except "
    "exclusive exists explain fail filter following for foreign from full "
    "glob group having if ignore immediate in index indexed initially "
    "inner insert instead intersect into is isnull join key left like "
    "limit match natural no not nothing notnull null of offset on or order "
    "outer over partition plan pragma preceding primary query raise range "
    "recursive references regexp reindex release rename replace restrict "
    "right rollback row rows savepoint select set table temp temporary "
    "then to transaction trigger unbounded union unique update using "
    "vacuum values view virtual when where window with without",
    # https://www.postgresql.org/docs/7.3/sql-keywords-appendix.html
    "SQL92_99": "abort absolute access action add admin after aggregate alias all "
    "allocate alter analyse analyze and any are array as asc assertion at "
    "authorization backward before begin bigint binary bit blob boolean "
    "both breadth by cache call cascade cascaded case cast catalog char "
    "character characteristics check checkpoint class clob close cluster "
    "collate collation column comment commit completion connect connection "
    "constraint constraints constructor continue conversion copy "
    "corresponding create createdb createuser cross cube current "
    "current_date current_path current_role current_time current_timestamp "
    "current_user cursor cycle data database date day deallocate dec "
    "decimal declare default deferrable deferred delete delimiter "
    "delimiters depth deref desc describe descriptor destroy destructor "
    "deterministic diagnostics dictionary disconnect distinct do domain "
    "double drop dynamic each else encoding encrypted end end-exec equals "
    "escape every except exception exclusive exec execute explain external "
    "false fetch first float for force foreign forward found free freeze "
    "from full function general get global go goto grant group grouping "
    "handler having host hour identity ignore ilike immediate immutable "
    "implicit in increment index indicator inherits initialize initially "
    "inner inout input insert instead int integer intersect interval into "
    "is isnull isolation iterate join key lancompiler language large last "
    "lateral leading left less level like limit listen load local "
    "localtime localtimestamp location locator lock map match maxvalue "
    "minute minvalue mode modifies modify module month move names national "
    "natural nchar nclob new next no nocreatedb nocreateuser none not "
    "nothing notify notnull null numeric object of off offset oids old on "
    "only open operation operator option or order ordinality out outer "
    "output owner pad parameter parameters partial password path pendant "
    "placing postfix precision prefix preorder prepare preserve primary "
    "prior privileges procedural procedure public read reads real recheck "
    "recursive ref references referencing reindex relative rename replace "
    "reset restrict result return returns revoke right role rollback "
    "rollup routine row rows rule savepoint schema scope scroll search "
    "second section select sequence session session_user set setof sets "
    "share show size smallint some space specific specifictype sql sqlcode "
    "sqlerror sqlexception sqlstate sqlwarning stable start state "
    "statement static statistics stdin stdout storage strict structure "
    "sysid system_user table temp template temporary terminate than then "
    "time timestamp timezone_hour timezone_minute to toast trailing "
    "transaction translation treat trigger true truncate trusted under "
    "unencrypted union unique unknown unlisten unnest until update usage "
    "user using vacuum valid validator value values varchar variable "
    "varying verbose version view volatile when whenever where with "
    "without work write year zone",
    # includes both reserved words and "non-reserved" keywords:
    "POSTGRESQL": "abort absolute access action add after aggregate all alter analyse "
    "analyze and any as asc assertion assignment at authorization backward "
    "before begin between bigint binary bit boolean both by cache called "
    "cascade case cast chain char character characteristics check "
    "checkpoint class close cluster coalesce collate column comment commit "
    "committed constraint constraints conversion convert copy create "
    "createdb createuser cross current_date current_time current_timestamp "
    "current_user cursor cycle database day deallocate dec decimal declare "
    "default deferrable deferred definer delete delimiter delimiters desc "
    "distinct do domain double drop each else encoding encrypted end "
    "escape except exclusive execute exists explain external extract false "
    "fetch float for force foreign forward freeze from full function get "
    "global grant group handler having hour ilike immediate immutable "
    "implicit in increment index inherits initially inner inout input "
    "insensitive insert instead int integer intersect interval into "
    "invoker is isnull isolation join key lancompiler language leading "
    "left level like limit listen load local localtime localtimestamp "
    "location lock match maxvalue minute minvalue mode month move names "
    "national natural nchar new next no nocreatedb nocreateuser none not "
    "nothing notify notnull null nullif numeric of off offset oids old on "
    "only operator option or order out outer overlaps overlay owner "
    "partial password path pendant placing position precision prepare "
    "primary prior privileges procedural procedure read real recheck "
    "references reindex relative rename replace reset restrict returns "
    "revoke right rollback row rule schema scroll second security select "
    "sequence serializable session session_user set setof share show "
    "similar simple smallint some stable start statement statistics stdin "
    "stdout storage strict substring sysid table temp template temporary "
    "then time timestamp to toast trailing transaction treat trigger trim "
    "true truncate trusted type unencrypted union unique unknown unlisten "
    "until update usage user using vacuum valid validator values varchar "
    "varying verbose version view volatile when where with without work "
    "write year zone",
    # https://cran.r-project.org/doc/manuals/R-lang.pdf
    "R": "if else repeat while function for in next break "
    "TRUE FALSE NULL Inf NaN NA NA_integer_ NA_real_ NA_complex_ NA_character_",
}
PRESPEC_RESERVED_WORDS = (x.split() for x in PRESPEC_RESERVED_WORD_DICT.values())
RESERVED_WORDS: Set[str] = {
    x.lower() for x in flatten((kwlist, PRESPEC_RESERVED_WORDS))
}


def is_reserved_word(s: str) -> bool:
    return s.lower() in RESERVED_WORDS
