# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from sys import argv, exit
from json import load
from datetime import date, datetime
from helpers import check_binary, check_path, check_root, run_command


def do_backup(username, database, path, dump_name):
    db_exists = run_command(
        "su - postgres -c \"psql -lt\" | grep %s | awk '{print $1}' | grep -xE %s"
        % (username, database)
    )
    if db_exists:
        run_command(
            'su - postgres -c "/usr/bin/pg_dump %s --format=c --file=%s%s-%s.dump"'
            % (database, path, database, dump_name)
        )


def make_checks():
    mail = check_binary('mail', True)
    root = check_root()
    if mail and root:
        return True
    else:
        return False


def parse_args():
    parser = ArgumentParser(
        prog='odoo_backup',
        description="Python script to backup Odoo databases",
        epilog="'mailutils' package is required in order to run this script"
    )

    parser.add_argument("-m", "--monthly",
                        help="Save output file with monthly format",
                        action="store_true")
    parser.add_argument("-t", "--time",
                        help="Save output file with time format",
                        action="store_true")
    parser.add_argument("-f", "--environments-file",
                        help="JSON file with environments data",
                        dest="filename")
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    if len(argv) > 4:
        print("\n***ERROR: Many arguments.\n")
        parser.print_help()
        exit()

    if not args.filename:
        print("\n***ERROR: Environments file is required.\n")
        parser.print_help()
        exit()
    else:
        with open(args.filename) as f:
            environments = load(f)
            f.close()

    today = date.today()
    now = datetime.now()

    if args.monthly:
        return today.strftime("%d-%m-yy"), environments
    elif args.time:
        return '%shs' % now.strftime("%H"), environments
    else:
        return today.strftime("%d-mm-yy"), environments


if __name__ == "__main__":
    # if not make_checks():
    #     exit()

    dump_name, json = parse_args()

    for environment, values in json.items():

        username = values[0]['username']
        backup_dir = values[0]['system_path'] + 'backups/'
        databases = values[0]['databases']

        try:
            if not run_command('id %s' % username):
                raise Exception
            check_path(backup_dir)
            run_command('/bin/chown postgres:postgres %s' % backup_dir)
        except:
            continue

        try:
            if isinstance(databases, unicode) and databases == 'all':
                databases = run_command(
                    "su - postgres -c \"psql -lt\" | grep %s | awk '{print $1}'"
                    % (username)
                ).split()
            if isinstance(databases, list):
                for database in databases:
                    do_backup(username, database, backup_dir, dump_name)
        except:
            print 'error'
