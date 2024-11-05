import os
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import mongodb

import character
import creature
import story

# from openai import OpenAI
import google.generativeai as genai

# client = OpenAI(api_key="")  # os.environ["OPENAI_API_KEY"])

genai.configure(api_key=os.environ["GOOGLE_GEMINI_API_KEY"])

# Create FastAPI app with prefix
app = FastAPI(
    title="Personalisierte Gute-Nacht-Geschichten",
    docs_url="/api/docs",  # Update Swagger UI path
    openapi_url="/api/openapi.json",  # Update OpenAPI path
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Next.js development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Character and Story Models
# class Character(BaseModel):
#     id: Optional[int] = None
#     name: str
#     age: int
#     gender: Literal["weiblich", "männlich"]
#     personality_traits: List[str]
#     interests: List[str]


# class Creature(character.Character):
#     age: int = 0
#     looks_like: str


# Standorte in deutscher Sprache
LOCATIONS = [
    "Alte Burg",
    "Bauernhof",
    "Berglandschaft",
    "Flussufer",
    "Garten hinter dem Haus",
    "Kletterhalle",
    "Mystischer Wald",
    "Märchenland",
    "Musikzimmer",
    "Piratenschiff",
    "Raumstation",
    "Stadtpark",
    "Steinzeit",
    "Strandküste",
    "Verzauberter Garten",
]

# Pädagogische Themen in deutscher Sprache
EDUCATIONAL_TOPICS = [
    "Achtsamkeit",
    "Christlicher Glaube",
    "Emotionale Intelligenz",
    "Finanzielle Bildung",
    "Freundlichkeit",
    "Gesunde Ernährung",
    "Musik",
    "Mut",
    "Persönlichkeitsentwicklung",
    "Respekt",
    "Teamarbeit",
    "Umweltschutz",
    "Vogelkunde",
]


class StoryGenerator:
    # def generate_bedtime_story_openai(self, story_request: StoryRequest, language="de"):
    #     """Generate a personalized bedtime story in German"""
    #     # Construct a prompt based on input parameters
    #     prompt = self._construct_story_prompt(story_request)

    #     response = client.chat.completions.create(
    #         model="gpt-3.5-turbo",
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": prompt,
    #             },
    #         ],
    #     )
    #     story = response.choices[0].message.content
    #     return story

    def generate_bedtime_story_google(
        self, story_request: story.StoryRequest, language="de"
    ):
        """Generate a personalized bedtime story in German"""
        # Construct a prompt based on input parameters
        prompt = self._construct_story_prompt(story_request)

        # Create the model
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            # "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-002",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(history=[])

        response = chat_session.send_message(prompt)

        print(f"response: {response.text}")
        return response.text

    def _construct_story_prompt(self, story_request: story.StoryRequest) -> str:
        """Create a structured prompt for story generation in German"""

        def get_gender_specific_article(gender: str) -> str:
            return "eine" if gender == "weiblich" else "einen"

        def get_gender_specific_ending(gender: str) -> str:
            return "e" if gender == "weiblich" else "en"

        def get_gender_specific_pronoun(gender: str) -> str:
            return "die" if gender == "weiblich" else "der"

        character_descriptions = " und ".join(
            [
                f"{char.name}, {get_gender_specific_article(char.gender)} "
                f"{char.age}-jährig{get_gender_specific_ending(char.gender)}, "
                f"{get_gender_specific_pronoun(char.gender)} diese Persönlichkeit hat: {', '.join(char.personality_traits)} und "
                f"{get_gender_specific_pronoun(char.gender)} gerne {', '.join(char.interests)} mag und macht"
                for char in story_request.characters
            ]
        )

        if story_request.creatures:
            creature_descriptions = " und ".join(
                [
                    f"{creature.name}, {get_gender_specific_article(creature.gender)} "
                    f"{creature.looks_like}, "
                    f"{get_gender_specific_pronoun(creature.gender)} diese Persönlichkeit hat: {', '.join(creature.personality_traits)} und "
                    f"{get_gender_specific_pronoun(creature.gender)} sich besonders gut mit {', '.join(creature.interests)} auskennt"
                    for creature in story_request.creatures
                ]
            )

            creature_introduction = f"In der Geschichte soll zusätzlich dieses Wesen mitspielen und mit den anderen Charakteren interagieren: {creature_descriptions}"
        else:
            creature_introduction = ""

        def age_appropriate_choice_of_words():
            age_appropriate_choice_of_words_beginning = (
                "Der Stil und die Wörter der Geschichte müssen in"
            )
            age_appropriate_choice_of_words_ending = "-gerechter Sprache geschrieben sein und es dürfen keine sexuellen Inhalte in der Geschichte vorkommen!"
            if story_request.age_group == "Kinder":
                return f"{age_appropriate_choice_of_words_beginning} {story_request.age_group.lower()}{age_appropriate_choice_of_words_ending}"

            elif story_request.age_group == "Jugendliche":
                return f"{age_appropriate_choice_of_words_beginning} {story_request.age_group.lower()}n{age_appropriate_choice_of_words_ending}"
            else:
                return ""

        educational_context = {
            "finanzielle bildung": "Lerne über Sparen und kluges Ausgeben",
            "achtsamkeit": "Entdecke die Kraft des Gegenwärtig-Seins",
            "christlicher glaube": "Lerne über Gott, Jesus und die Bibel",
            "gesunde ernährung": "Erkunde nahrhaftes und leckeres Essen",
            "persönlichkeitsentwicklung": "Baue Selbstvertrauen und Freundlichkeit auf",
            "emotionale intelligenz": "Verstehe und teile Gefühle",
            "teamarbeit": "Lerne die Kraft der Zusammenarbeit",
            "freundlichkeit": "Entdecke die Bedeutung von Mitgefühl und Güte",
            "umweltschutz": "Lerne, unseren Planeten zu schützen und zu respektieren",
            "vogelkunde": "Entdecke Vögel und ihre Besonderheiten und Lebensweise",
            "respekt": "Verstehe die Wichtigkeit, andere zu achten und zu behandeln",
            "musik": "Entdecke Instrumente und Gesang",
            "mut": "Finde Kraft und Selbstvertrauen in herausfordernden Situationen",
        }.get(story_request.educational_topic.lower(), "Ein magisches Lern-Abenteuer")

        prompt = f"""Schreibe eine Gute-Nacht-Geschichte für {story_request.age_group} über {character_descriptions}. 
        Die Geschichte spielt in dieser Umgebung: {story_request.location}.
        {creature_introduction} 
        Die Geschichte soll auf eine subtile Art und Weise über das folgende Thema lehren: {educational_context}. 
        Die Geschichte soll fesselnd, lehrreich und mit einer positiven moralischen Lektion versehen sein.
        Die Geschichte soll mindestens 3 DIN A4 Seiten lang sein.
        Die Geschichte soll in einfachen Worten und kurzen Sätzen erzählt werden.
        {age_appropriate_choice_of_words()}
        """

        print(f"Prompt: {prompt}")

        return prompt


story_generator = StoryGenerator()


# {"name":"Vinca","age":6,"gender":"weiblich","interests":["Turnen"],"personality_traits":["fröhlich","spontan"]}
@app.post(
    "/api/characters/create",
    name="Charakter erstellen",
    description="Erstelle einen neuen Charakter für Geschichten",
    tags=["Charaktere"],
)
async def create_character(character: character.Character):
    """Erstelle einen neuen Charakter"""
    try:
        # all_characters = load_characters_from_json()
        # character.id = get_next_character_id(all_characters)
        # print(f"New Character ID: {character.id}")
        # all_characters.append(character)
        # save_characters_to_json(all_characters)
        new_character = await character.create()

        return new_character
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Fehler beim Erstellen des Charakters: {str(e)}"
        )


@app.get(
    "/api/characters",
    name="Charaktere auflisten",
    description="Zeige alle verfügbaren Charaktere",
    tags=["Charaktere"],
)
async def list_characters():
    """Liste alle verfügbaren Charaktere auf"""
    db_characters = mongodb.characters.find()
    all_characters = []
    if db_characters:
        async for my_character in db_characters:
            try:
                all_characters.append(character.Character(**my_character))
            except Exception as e:
                print(str(e))
        return all_characters
    else:
        return []


@app.delete(
    "/api/characters/delete",
    name="Charakter löschen",
    description="Lösche einen Charakter mit der ID.",
    tags=["Charaktere"],
)
async def delete_character(character_id: str):
    """Lösche den Charaktere mit der ID"""
    try:
        my_character = await mongodb.characters.find_one({"id": character_id})
        if my_character:
            result = await mongodb.characters.delete_one({"id": character_id})

            if result.deleted_count > 0:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=f"Charakter mit id '{character_id}' erfolgreich gelöscht.",
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{status.HTTP_404_NOT_FOUND}: Charakter mit id '{character_id}' nicht gefunden.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{status.HTTP_500_INTERNAL_SERVER_ERROR}: Charakter mit id '{character_id}' konnte nicht gelöscht werden. Exception:\n{str(e)}",
        )


# {"name":"Drago","gender":"männlich","looks_like": "Drache", "interests":["Feuer speien"],"personality_traits":["fröhlich","positiv"]}
@app.post(
    "/api/creatures/create",
    name="Fabelwesen erstellen",
    description="Erstelle ein neues Fabelwesen für Geschichten",
    tags=["Fabelwesen"],
)
async def create_creature(creature: creature.Creature):
    """Erstelle ein neues Fabelwesen"""
    try:
        new_creature = await creature.create()

        return new_creature
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Fehler beim Erstellen des Fabelwesens: {str(e)}"
        )


@app.get(
    "/api/creatures",
    name="Fabelwesen auflisten",
    description="Zeige alle verfügbaren Fabelwesen",
    tags=["Fabelwesen"],
)
async def list_creatures():
    """Liste alle verfügbaren Fabelwesen auf"""
    db_creatures = mongodb.creatures.find()
    all_creatures = []
    if db_creatures:
        async for my_creature in db_creatures:
            try:
                all_creatures.append(creature.Creature(**my_creature))
            except Exception as e:
                print(str(e))
        return all_creatures
    else:
        return []


@app.delete(
    "/api/creatures/delete",
    name="Fabelwesen löschen",
    description="Lösche ein Fabelwesen mit der ID.",
    tags=["Fabelwesen"],
)
async def delete_creature(creature_id: str):
    """Lösche das Fabelwesen mit der ID"""
    try:
        my_creature = await mongodb.creatures.find_one({"id": creature_id})
        if my_creature:
            result = await mongodb.creatures.delete_one({"id": creature_id})

            if result.deleted_count > 0:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=f"Fabelwesen mit id '{creature_id}' erfolgreich gelöscht.",
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{status.HTTP_404_NOT_FOUND}: Fabelwesen mit id '{creature_id}' nicht gefunden.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{status.HTTP_500_INTERNAL_SERVER_ERROR}: Fabelwesen mit id '{creature_id}' konnte nicht gelöscht werden. Exception:\n{str(e)}",
        )


# {"characters":["Vinca"],"location":"Verzauberter Garten","educational_topic":"Achtsamkeit","age_group":"Kinder"}
@app.post(
    "/api/stories/create",
    name="Geschichte erstellen",
    description="Erstelle eine neue Geschichte",
    tags=["Geschichten"],
)
async def create_story(story: story.Story):
    """Erstelle ein neue Geschichte"""
    try:
        new_story = await story.create()

        return new_story
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Fehler beim Erstellen der Geschichte: {str(e)}"
        )


@app.get(
    "/api/stories",
    name="Geschichten auflisten",
    description="Zeige alle verfügbaren Geschichten",
    tags=["Geschichten"],
)
async def list_stories():
    """Liste alle verfügbaren Geschichten auf"""
    db_stories = mongodb.stories.find().sort("_id", -1)
    all_stories = []
    if db_stories:
        async for my_story in db_stories:
            try:
                all_stories.append(story.Story(**my_story))
            except Exception as e:
                print(str(e))
        return all_stories
    else:
        return []


@app.delete(
    "/api/stories/delete",
    name="Geschichte löschen",
    description="Lösche eine Geschichte mit der ID.",
    tags=["Geschichten"],
)
async def delete_story(story_id: str):
    """Lösche die Geschichte mit der ID"""
    try:
        my_story = await mongodb.stories.find_one({"id": story_id})
        if my_story:
            result = await mongodb.stories.delete_one({"id": story_id})

            if result.deleted_count > 0:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=f"Geschichte mit id '{story_id}' erfolgreich gelöscht.",
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{status.HTTP_404_NOT_FOUND}: Geschichte mit id '{story_id}' nicht gefunden.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{status.HTTP_500_INTERNAL_SERVER_ERROR}: Geschichte mit id '{story_id}' konnte nicht gelöscht werden. Exception:\n{str(e)}",
        )


# {"characters":[{"id":"6d0d8f31-8e1c-4d75-8934-b588dd5ba36e","name":"Vinca","age":29,"gender":"weiblich","personality_traits":["fröhlich","spontan"],"interests":["Turnen"]}],"creatures":[{"id":"edbaf694-d7c5-42be-aedc-4dd125c378ee","name":"Balu","age":0,"gender":"männlich","personality_traits":["ruhig, gelassen"],"interests":["Achtsamkeit"],"looks_like":"Bär"}],"location":"Garten hinter dem Haus","educational_topic":"Gesunde Ernährung","age_group":"Kinder"}
@app.post(
    "/api/stories/generate",
    name="Geschichte generieren",
    description="Generiere eine personalisierte Gute-Nacht-Geschichte",
)
async def generate_story(story_request: story.StoryRequest):
    """Generiere eine personalisierte Gute-Nacht-Geschichte"""
    try:
        print(f"story_request: {story_request}")

        new_story_request = story.StoryRequest(
            characters=story_request.characters,
            creatures=story_request.creatures,
            location=story_request.location,
            educational_topic=story_request.educational_topic,
            age_group=story_request.age_group,
        )
        generated_story = story_generator.generate_bedtime_story_google(
            new_story_request
        )

        new_story = await create_story(
            story.Story(text=generated_story, request=new_story_request)
        )
        return new_story

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Fehler bei der Geschichtsgenerierung: {str(e)}"
        )


@app.get(
    "/api/metadata",
    name="Metadaten abrufen",
    description="Rufe vordefinierte Standorte und Themen ab",
)
async def get_story_metadata():
    """Liefere alle Charakter, vordefinierte Standorte und Themen"""

    characters = await list_characters()
    creatures = await list_creatures()
    stories = await list_stories()

    return {
        "characters": characters,
        "creatures": creatures,
        "locations": LOCATIONS,
        "stories": stories,
        "educational_topics": EDUCATIONAL_TOPICS,
    }


# Zusätzliche Konfiguration
# Erweiterter Fehlerbehandlungskontext
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Angepasste Fehlerbehandlung mit deutschen Fehlermeldungen"""
    error_messages = {
        400: "Ungültige Anfrage. Bitte überprüfen Sie Ihre Eingaben.",
        404: "Die angeforderte Ressource wurde nicht gefunden.",
        500: "Ein interner Serverfehler ist aufgetreten. Bitte versuchen Sie es später wieder.",
    }
    return {
        "status_code": exc.status_code,
        "message": error_messages.get(exc.status_code, str(exc.detail)),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
