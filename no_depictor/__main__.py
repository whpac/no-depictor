from time import sleep
from rich.console import Console
from rich.status import Status
from rich.markup import escape
from urllib.parse import quote, unquote
from requests import Session
import sys

from .clients import CommonsAPI, Depictor, PetScan, WikidataAPI
from .config import getConfig
from .data._category_descriptor import CategoryDescriptor
from .interrupt_handler import interruptible, InterruptHandler

# General algorithm:
# 1. Fetch subcategories of a given category using PetScan.
# 2. For each subcategory, check if it is done in Depictor (action=items-done).
# 3. For these not done, search them on Commons to get a list of images not depicting the subject.
# 4. For each list of files, check if they were done in Depictor (action=files-exists).
# 5. For every of the undone files, mark them as not depicting the subject (action=add-file).

def main():
    console = Console()
    try:
        args = getConfig(console)

        rootCategories = getCategories(args, console)
        rootCategories = [
            c if not c.startswith('Category:') else c[len('Category:'):]  # Remove 'Category:' prefix if present
            for c in rootCategories
        ]

        session = Session()
        session.headers.update({
            'User-Agent': 'NoDepictor/1.0 (User:Msz2001)'
        })

        commons = CommonsAPI(session)
        wikidata = WikidataAPI(session)
        petscan = PetScan(session)
        depictor = Depictor(args['user'], args['sessid'], session)
    except KeyboardInterrupt:
        console.print('[bold red]Interrupted by user.')
        sys.exit(1)

    with console.status('Initializing') as status, InterruptHandler() as ih:
        for rootCategory in interruptible(rootCategories, ih):
            if '|' in rootCategory:
                rootCategory, depth = rootCategory.split('|', 1)
                rootCategory = unquote(rootCategory.strip())
                console.rule(catlink(rootCategory))
                depth = int(depth.strip())
                status.update(status=f'Fetching subcategories for {catlink(rootCategory)} with depth {depth}')
                
                try:
                    categories = petscan.getSubcategories(rootCategory, depth)
                except Exception as e:
                    console.print(f'[red]Failed to fetch subcategories for {catlink(rootCategory)}:[/red] {escape(str(e))}')
                    continue
            else:
                rootCategory = unquote(rootCategory.strip())
                console.rule(catlink(rootCategory))
                status.update(status=f'Getting QID for {catlink(rootCategory)}')
                try:
                    categories = [wikidata.getItemForCommonsCategory(rootCategory)]
                except Exception as e:
                    console.print(f'[red]Failed to get QID for {catlink(rootCategory)}:[/red] {escape(str(e))}')
                    continue

            if not categories:
                console.print(f'No subcategories of {catlink(rootCategory)} found.')
                continue

            console.print(f'Found {len(categories)} categories in total.')
            status.update(status=f'Finding categories already done in Depictor')

            try:
                undoneCategories = depictor.getUndoneCategories(categories)
            except Exception as e:
                console.print(f'[red]Failed to fetch check which categories of were done:[/red] {escape(str(e))}')
                continue

            if not undoneCategories:
                console.print(f'All categories of have already been done in Depictor.')
                continue

            console.print(f'Found {len(undoneCategories)} categories not done in Depictor.')
            doWorkForUndoneCategories(undoneCategories, commons, depictor, wikidata, status, console, ih)


def getCategories(args: dict, console: Console) -> list[str]:
    if args.get('category'):
        return [args['category']]
    if args.get('categoryfile'):
        try:
            with open(args['categoryfile'], 'r') as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            console.print(f'[bold red]Error: Category file `{args["categoryfile"]}` not found.')
            sys.exit(1)

    console.print('[bold red]Error: No category specified. Use --category or --categoryfile.')
    sys.exit(1)


def doWorkForUndoneCategories(
        undoneCategories: list[CategoryDescriptor],
        commons: CommonsAPI,
        depictor: Depictor,
        wikidata: WikidataAPI,
        status: Status,
        console: Console,
        ih: InterruptHandler
    ):
    for category in interruptible(undoneCategories, ih):
        qId, catName = category

        status.update(status=f'Checking if {catlink(catName)} ({qId}) has an image set on Wikidata (P18)')
        try:
            if not wikidata.hasImageClaim(qId):
                console.print(f'[cyan]Skipping ({catlink(catName)}) ({qId}) because it has no image.[/cyan]')
                continue
        except Exception as e:
            console.print(f'[red]Failed to check Wikidata item {qId} ({catlink(catName)}) for P18:[/red] {escape(str(e))}')
            continue

        status.update(status=f'Searching for files not depicting subject {qId} in {catlink(catName)}')
        try:
            files = list(commons.getFilesNotDepictingSubject(catName, qId))
            undoneFiles = depictor.getUndoneFiles(files)
        except Exception as e:
            console.print(f'[red]Failed to fetch files for {catlink(catName)}:[/red] {escape(str(e))}')
            continue

        if not undoneFiles:
            console.print(f'No files to process in {catlink(catName)}.')
            continue

        i = -1 # To be able to print the "Interrupted" message even before first item
        for i, (mId, fileName) in interruptible(enumerate(undoneFiles), ih):
            status.update(status=f'Processing {catlink(catName)} ({i+1}/{len(undoneFiles)}): {pagelink(fileName)} ({mId})')
            try:
                depictor.markFileAsNotDepictingSubject(mId, category)
            except Exception as e:
                console.print(f'[red]Failed to mark {pagelink(fileName)} ({mId}) as not depicting {qId}:[/red] {escape(str(e))}')
            sleep(0.5) # To avoid overloading the server

        # They won't be equal only if we interrupted the loop early
        if i+1 < len(undoneFiles):
            console.print(f'[yellow]Interrupted processing {catlink(catName)} after {i+1}/{len(undoneFiles)} files.')
        else:
            status.update(status=f'Marking category {catlink(catName)} as done')
            try:
                depictor.markCategoryAsDone(qId)
            except Exception as e:
                console.print(f'[red]Failed to mark category {catlink(catName)} as done:[/red] {escape(str(e))}')
            console.print(f'Processed {catlink(catName)} with {len(undoneFiles)} files.')


def catlink(categoryName: str) -> str:
    return pagelink('Category:' + categoryName)

def pagelink(pageName: str) -> str:
    urlencoded = quote(pageName.replace(' ', '_'), safe=':/')
    displayName = pageName.replace('_', ' ')
    return f'[[[link=https://commons.wikimedia.org/wiki/{urlencoded}]{displayName}[/link]]]'


main()