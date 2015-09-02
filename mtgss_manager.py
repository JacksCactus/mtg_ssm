#!/usr/bin/env python3
"""Script to manage magic collection spreadsheets."""

import argparse
import os

import sqlalchemy as sqla
import sqlalchemy.orm as sqlo

from mtgcdb import manager_helper
from mtgcdb import profiling


MTGCDB_DATA_PATH = os.path.expanduser(os.path.join('~', '.mtgcdb'))


def get_parser():
    """Create and return application argument parser."""
    parser = argparse.ArgumentParser(
        description='Magice Collection Spreadsheet Manager')
    parser.add_argument(
        '--data_path', default=MTGCDB_DATA_PATH,
        help='Path to mtgcdb\'s data storage folder. Default={0}'.format(
            MTGCDB_DATA_PATH))
    parser.add_argument(
        '--include_online_only', default=False, action='store_true',
        help='Include online only sets (e.g. Masters sets) in the database.')
    parser.add_argument(
        '--debug_stats', default=False, action='store_true',
        help='Output additional debugging statistics.')
    parser.add_argument(
        'spreadsheet_file', help='Spreadsheet (xlsx) filename to work with.')

    cmd_subparser = parser.add_subparsers(
        dest='command', help='Operation to perform with the spreadsheet.')
    cmd_subparser.required = True

    cmd_subparser.add_parser(
        'create', help='Create a new, empty spreadsheet.',
        description='Create a new, empty spreadsheet.')

    cmd_subparser.add_parser(
        'update', help='Update card data in spreadsheet.',
        description='Update card data in spreadsheet.')

    export_cmd = cmd_subparser.add_parser(
        'export', help='Export data from spreadsheet in another format.',
        description='Export data from spreadsheet in another format.')
    export_cmd.add_argument(
        '--format', choices=['csv'], default='csv',
        help='Data format for export file.')
    export_cmd.add_argument(
        'export_file', help='Target file for export.')

    import_cmd = cmd_subparser.add_parser(
        'import', help=(
            'Import data to spreadsheet in another format. NOTE: Data in the '
            'spreadsheet will be overwritten (It will be backed up first).'),
        description=(
            'Import data to spreadsheet in another format. NOTE: Data in the '
            'spreadsheet will be overwritten (It will be backed up first).'))
    import_cmd.add_argument(
        '--format', choices=['csv'], default='csv',
        help='Data format of import file.')
    import_cmd.add_argument(
        'import_file', help='Source file for import.')

    return parser


def run_commands(args):
    """Run the requested operations."""
    engine = sqla.create_engine('sqlite://')
    session_factory = sqlo.sessionmaker(engine)
    session = session_factory()
    try:
        manager_helper.read_mtgjson(
            session, args.data_path, args.include_online_only)
        session.commit()

        if args.command in {'update', 'export'}:
            manager_helper.read_xlsx(session, args.spreadsheet_file)
        session.commit()

        if args.command in {'import'}:
            if args.format == 'csv':
                manager_helper.read_csv(session, args.import_file)
        session.commit()

        if args.command in {'create', 'update'}:
            manager_helper.write_xlsx(session, args.spreadsheet_file)

        if args.command in {'export'}:
            if args.format == 'csv':
                manager_helper.write_csv(session, args.export_file)
    finally:
        session.close()


def main():
    """Process user input and run commands.."""
    parser = get_parser()
    args = parser.parse_args()
    if not os.path.exists(args.data_path):
        os.makedirs(args.data_path)
    elif not os.path.isdir(args.data_path):
        raise Exception(
            'data_path: {} must be a folder'.format(args.data_path))

    profiler = None
    if args.debug_stats:
        profiler = profiling.start()
    try:
        run_commands(args)
    finally:
        if profiler is not None:
            profiling.finish(profiler)


if __name__ == '__main__':
    main()
