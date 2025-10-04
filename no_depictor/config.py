from argparse import ArgumentParser, Namespace
import json
import os
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm

def getConfig(console: Console):
    DEFAULT_CONFIG_FILE = 'config.json'

    parser = ArgumentParser(description='A tool for mass-marking Wikimedia Commons images as not-depiciting a given subject.')
    parser.add_argument('--category', type=str, help='Category name whose subcategories to process')
    parser.add_argument('--categoryfile', type=str, help='File containing category names whose subcategories to process')
    parser.add_argument('--logfile', type=str, help='Path to the log file (default: no_depictor.log)')
    parser.add_argument('--user', type=str, help='Username for Depictor API')
    parser.add_argument('--sessid', type=str, help='PHP session ID for Depictor API')
    parser.add_argument('--config', type=str, help='Path to the configuration file, set to "-" to disable')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making any changes')

    args = parser.parse_args()
    combinedArgs = { key: getattr(args, key, None) for key in vars(args) }
    if combinedArgs.get('dry_run') == False:
        combinedArgs['dry_run'] = None  # False is the default, for not set

    if args.config != '-':
        try:
            with open(args.config or DEFAULT_CONFIG_FILE, 'r') as configFile:
                configData = json.load(configFile)
                for key, value in configData.items():
                    if combinedArgs.get(key) is None:
                        combinedArgs[key] = value

        except FileNotFoundError:
            # Don't throw if we're using the default config file
            if args.config:
                console.print(f'[bold red]Configuration file `{args.config}` not found.')
                sys.exit(1)
        except json.JSONDecodeError:
            console.print(f'[bold red]Error decoding JSON from configuration file `{args.config}`.')
            sys.exit(1)

    combinedArgs = _askUserForMissingArgs(combinedArgs, args, console)
    del combinedArgs['config']  # Remove the config argument from the final dictionary; no longer needed

    if args.config != '-':
        # Save the configuration back to the file
        try:
            with open(args.config or DEFAULT_CONFIG_FILE, 'w') as configFile:
                json.dump(combinedArgs, configFile, indent=4)
        except IOError as e:
            console.print(f'[bold red]Error writing to configuration file `{args.config}`: {e}')
            sys.exit(1)

    return combinedArgs


def _askUserForMissingArgs(allArgs: dict, cliArgs: Namespace, console: Console) -> dict:
    if _absent('category', cliArgs) and _absent('categoryfile', cliArgs):
        _askForCategory(allArgs, console)
    elif not _absent('category', cliArgs) and not _absent('categoryfile', cliArgs):
        console.print(f'[bold red]You cannot specify both --category and --categoryfile at the same time.')
        sys.exit(1)
    else:
        # Ensure that CLI value takes precedence and that we have only one of these two
        if _absent('category', cliArgs):
            allArgs['category'] = None
        else:
            allArgs['categoryfile'] = None

    if _absent('user', cliArgs):
        allArgs['user'] = (Prompt.ask(
            'Your username',
            default=allArgs.get('user'),
            console=console
        ) or '').strip()

    if _absent('sessid', cliArgs):
        REUSE_LAST = 'reuse last'
        response = (Prompt.ask(
            'Value of PHPSESSID cookie for Depictor',
            default=REUSE_LAST if allArgs.get('sessid') is not None else None,
            console=console
        ) or '').strip()

        if response != REUSE_LAST:
            allArgs['sessid'] = response

    if _absent('logfile', cliArgs):
        allArgs['logfile'] = Prompt.ask(
            'Path to the log file',
            default=allArgs.get('logfile', 'no_depictor.log'),
            console=console
        ) or 'no_depictor.log'

    if not allArgs.get('dry_run', False):
        allArgs['dry_run'] = False

    return allArgs


def _askForCategory(allArgs: dict, console: Console):
    file = Confirm.ask(
        'Do you want to read categories from a file?',
        default=allArgs.get('category') is None,
        console=console
    )

    if file:
        while True:
            response = Prompt.ask(
                'Enter the path to the file containing category names',
                default=allArgs.get('categoryfile', ''),
                console=console
            )
            response = response.strip('"\'') # Remove quotes that might have been copied with the path
            if os.path.isfile(response):
                break
            console.print(f'[bold red]Error: File `{response}` does not exist. Please try again.')
        
        allArgs['categoryfile'] = response.strip()
        allArgs['category'] = None
    else:
        allArgs['category'] = Prompt.ask(
            'Enter the name of the category whose subcategories to process (without "Category:" prefix)',
            default=allArgs.get('category', ''),
            console=console
        )
        allArgs['categoryfile'] = None


def _absent(key: str, cliArgs: Namespace) -> bool:
    '''Check if to ask the user for a missing argument.'''
    return getattr(cliArgs, key, None) is None
