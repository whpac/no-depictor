from requests import Session
from typing import Iterator
from ..data import FileDescriptor


class CommonsAPI:
    
    def __init__(self, session: Session = Session()):
        self.httpSession = session


    def getFilesNotDepictingSubject(self, categoryName: str, qId: str, wholeCategory: bool = False) -> Iterator[FileDescriptor]:
        requestParams = {
            'action': 'query',
            'list': 'search',
            'srlimit': 500,
            'srnamespace': 6,  # Namespace for files
            'srsearch': f'-haswbstatement:P180={qId} incategory:"{categoryName}" filetype:bitmap',
            'format': 'json',
            'formatversion': 2,
        }

        while True:
            response = self.httpSession.get(
                'https://commons.wikimedia.org/w/api.php',
                params=requestParams,
                timeout=60,
            ).json()

            searchResults = response.get('query', {}).get('search', [])
            for result in searchResults:
                if 'pageid' not in result:
                    continue
                pageId = result['pageid']
                yield FileDescriptor(f'M{pageId}', result.get('title', ''))
            
            if 'continue' not in response:
                break

            requestParams['sroffset'] = response['continue'].get('sroffset', 0)

            # Normally, we should continue listing files until we reach the limit.
            # However, Depictor seems to ignore the possibility of continuation,
            # so it relies on the user coming back and running the search again
            # in modified circumstances (e.g. with more P180 set).
            if not wholeCategory:
                break
