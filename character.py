from pydantic import BaseModel
from typing import List, Literal, Optional
import mongodb
import uuid

CHARACTER_MONGO_DB_COLLECTION = "characters"


class Character(BaseModel):
    id: Optional[str] = None
    name: str
    age: int
    gender: Literal["weiblich", "männlich"]
    personality_traits: List[str]
    interests: List[str]

    async def create(self):
        try:
            self.id = str(uuid.uuid4())
            if await mongodb.characters.insert_one(self.model_dump()):
                my_character = await mongodb.characters.find_one({"id": self.id})
                print(my_character)
                return Character(**my_character)
            else:
                raise Exception(
                    "Could not create new character in collection '{CHARACTER_MONGO_DB_COLLECTION}'."
                )
        except Exception as e:
            print(
                f"Could not create new character in collection '{CHARACTER_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e

    async def save(self):
        try:
            filter = {"id": self.id}

            new_doc = ({"$set": self.model_dump()},)
            if update_character := await mongodb.characters.update_one(filter, new_doc):
                return self.__class__(**update_character)
            else:
                return None
        except Exception as e:
            print(
                f"Could not update character in collection '{CHARACTER_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e
