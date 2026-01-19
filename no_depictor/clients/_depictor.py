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
        try:
            doneDictionary = response.json()
        except Exception as e:
            raise Exception(
                'Depictor API responded with invalid JSON (response code: ' +
                str(response.status_code) + '). Beginning of the response: ' + response.text[:200]
            ) from e

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
        try:
            doneMids = response.json()
        except Exception as e:
            raise Exception(
                'Depictor API responded with invalid JSON (response code: ' +
                str(response.status_code) + '). Beginning of the response: ' + response.text[:200]
            ) from e

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

        rawResponse = self.httpSession.get(
            'https://hay.toolforge.org/depictor/api/index.php?category=' + urlencodedCategory,
            params=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        try:
            response = rawResponse.json()
        except Exception as e:
            raise Exception(
                'Depictor API responded with invalid JSON (response code: ' +
                str(rawResponse.status_code) + '). Beginning of the response: ' + rawResponse.text[:200]
            ) from e
        
        success = rawResponse.status_code == 200 and response.get('ok') == 'Added'
        if not success:
            raise Exception(
                f'Failed to mark file {mId} as not depicting {category.qId} in category {category.title}: {rawResponse.text}'
            )


    def markCategoryAsDone(self, qId: str) -> None:
        requestParams = {
            'action': 'item-done',
            'qid': qId,
            'user': self.userName,
        }

        rawResponse = self.httpSession.post(
            'https://hay.toolforge.org/depictor/api/index.php',
            json=requestParams,
            cookies={
                'PHPSESSID': self.phpSessionId,
            },
            timeout=60,
        )
        try:
            response = rawResponse.json()
        except Exception as e:
            raise Exception(
                'Depictor API responded with invalid JSON (response code: ' +
                str(rawResponse.status_code) + '). Beginning of the response: ' + rawResponse.text[:200]
            ) from e
        
        success = rawResponse.status_code == 200 and response.get('ok') == 'Added'
        if not success:
            raise Exception(
                f'Failed to mark category of {qId} as done: {rawResponse.text}'
            )
