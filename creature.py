import mongodb
import uuid

import character

CREATURE_MONGO_DB_COLLECTION = "creatures"


class Creature(character.Character):
    age: int = 0
    looks_like: str

    async def create(self):
        try:
            self.id = str(uuid.uuid4())
            if await mongodb.creatures.insert_one(self.model_dump()):
                my_creature = await mongodb.creatures.find_one({"id": self.id})
                print(my_creature)
                return Creature(**my_creature)
            else:
                raise Exception(
                    f"Could not create new creature in collection '{CREATURE_MONGO_DB_COLLECTION}'."
                )
        except Exception as e:
            print(
                f"Could not create new creature in collection '{CREATURE_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e

    async def save(self):
        try:
            filter = {"id": self.id}

            new_doc = ({"$set": self.model_dump()},)
            if update_creature := await mongodb.users.update_one(filter, new_doc):
                return self.__class__(**update_creature)
            else:
                return None
        except Exception as e:
            print(
                f"Could not update creature in collection '{CREATURE_MONGO_DB_COLLECTION}'. Exception:\n{str(e)}"
            )
            raise e
