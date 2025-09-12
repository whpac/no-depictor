from requests import Session
from ..data import CategoryDescriptor, FileDescriptor
import urllib.parse


class Depictor:

    def __init__(self, userName: str, phpSessionId: str, session: Session = Session()):
        self.userName = userName
        self.phpSessionId = phpSessionId
        self.httpSession = session


    def getUndoneCategories(self, categories: list[CategoryDescriptor]) -> list[CategoryDescriptor]:
        requestParams = {
            'action': 'items-done',
            'qids': [cat.qId for cat in categories],
        }

        response = self.httpSession.post(
            'https://hay.toolforge.org/depictor/api/index.php',
            json=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        doneDictionary = response.json()

        return [
            cat for cat in categories
            if not doneDictionary.get(cat.qId, False)
        ]


    def getUndoneFiles(self, files: list[FileDescriptor]) -> list[FileDescriptor]:
        requestParams = {
            'action': 'files-exists',
            'mids': [ file.mId for file in files ],
        }

        response = self.httpSession.post(
            'https://hay.toolforge.org/depictor/api/index.php',
            json=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        doneMids = response.json()

        return [
            file for file in files
            if not doneMids.get(file.mId, False)
        ]


    def markFileAsNotDepictingSubject(self, mId: str, category: CategoryDescriptor) -> None:
        requestParams = {
            'mid': mId,
            'qid': category.qId,
            'user': self.userName,
            'status': 'not-depicted',
            'action': 'add-file',
        }
        # The category is encoded separately, as by default .get() encodes spaces as '+'.
        # But Depictor client uses %20 for that purpose. In order not to break anything,
        # encode it manually to match the expected format.
        urlencodedCategory = urllib.parse.quote(category.title, safe='')

        response = self.httpSession.get(
            'https://hay.toolforge.org/depictor/api/index.php?category=' + urlencodedCategory,
            params=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        
        success = response.status_code == 200 and response.json().get('ok') == 'Added'
        if not success:
            raise Exception(
                f'Failed to mark file {mId} as not depicting {category.qId} in category {category.title}: {response.text}'
            )


    def markCategoryAsDone(self, qId: str) -> None:
        requestParams = {
            'action': 'item-done',
            'qid': qId,
            'user': self.userName,
        }

        response = self.httpSession.post(
            'https://hay.toolforge.org/depictor/api/index.php',
            json=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        
        success = response.status_code == 200 and response.json().get('ok') == 'Added'
        if not success:
            raise Exception(
                f'Failed to mark category of {qId} as done: {response.text}'
            )
