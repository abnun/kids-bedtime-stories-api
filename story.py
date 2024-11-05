from pydantic import BaseModel
from typing import List, Optional
import datetime

import mongodb
import uuid

import character
import creature

STORY_MONGO_DB_COLLECTION = "stories"


class StoryRequest(BaseModel):
    characters: List[character.Character]
    creatures: List[creature.Creature]
    location: str
    educational_topic: str
    age_group: str


class Story(BaseModel):
    id: Optional[str] = None
    created: Optional[datetime.datetime] = datetime.datetime(2024, 11, 2)
    request: Optional[StoryRequest] = None
    text: str

    async def create(self):
        try:
            self.id = str(uuid.uuid4())
            self.created = datetime.datetime.now(datetime.timezone.utc)
            if await mongodb.stories.insert_one(self.model_dump()):
                my_story = await mongodb.stories.find_one({"id": self.id})
                print(my_story)
                return Story(**my_story)
            else:
                raise Exception(
                    f"Could not create new story in collection '{STORY_MONGO_DB_COLLECTION}'."
                )
        except Exception as e:
            print(
                f"Could not create new story in collection '{STORY_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e

    async def save(self):
        try:
            filter = {"id": self.id}

            new_doc = ({"$set": self.model_dump()},)
            if update_story := await mongodb.users.update_one(filter, new_doc):
                return Story(**update_story)
            else:
                return None
        except Exception as e:
            print(
                f"Could not update story in collection '{STORY_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e
