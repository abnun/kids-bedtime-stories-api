import os
import json
from typing import List, Literal, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import requests
import time

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
class Character(BaseModel):
    id: Optional[int] = None
    name: str
    age: int
    gender: Literal["weiblich", "männlich"]
    personality_traits: List[str]
    interests: List[str]


class StoryRequest(BaseModel):
    characters: List[Character]
    location: str
    educational_topic: str
    age_group: str


class Story(BaseModel):
    id: Optional[int] = None
    text: str


# Hugging Face API URL and headers
API_URL = "https://api-inference.huggingface.co/models/dbmdz/german-gpt2"
headers = {"Authorization": "Bearer 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"}


class StoryGenerator:
    def generate_story(self, story_request: StoryRequest) -> str:
        """Generate a personalized bedtime story in German"""
        # Construct a prompt based on input parameters
        prompt = self._construct_story_prompt(story_request)

        # Generate story using AI
        payload = {"inputs": prompt, "parameters": {"max_tokens": 1000}}
        response = requests.post(API_URL, headers=headers, json=payload)

        print(f"response.json(): {response.json()}")

        if response.json() and "error" not in response.json():
            return response.json()[0]["generated_text"]
        return "No story could be generated."

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

    def generate_bedtime_story_google(self, story_request: StoryRequest, language="de"):
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

    def generate_bedtime_story(
        self, story_request: StoryRequest, max_retries=5, wait_seconds=20
    ):
        """Generate a personalized bedtime story in German"""
        # Construct a prompt based on input parameters
        prompt = self._construct_story_prompt(story_request)

        for attempt in range(max_retries):
            response = requests.post(
                API_URL,
                headers=headers,
                json={"inputs": prompt, "parameters": {"max_tokens": 3000}},
            )
            result = response.json()

            print(f"result: {result}")
            # Check if model is still loading
            if "error" in result and "loading" in result["error"]:
                print(
                    f"Attempt {attempt + 1}: Model is loading. Retrying in {wait_seconds} seconds..."
                )
                time.sleep(wait_seconds)
            else:
                # Return the generated text if no loading error
                return result[0]["generated_text"]

        raise RuntimeError("Model failed to load after multiple attempts.")

    def _construct_story_prompt(self, story_request: StoryRequest) -> str:
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
                f"{get_gender_specific_pronoun(char.gender)} gerne {', '.join(char.interests)} mag"
                for char in story_request.characters
            ]
        )

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
            "gesunde ernährung": "Erkunde nahrhaftes und leckeres Essen",
            "persönlichkeitsentwicklung": "Baue Selbstvertrauen und Freundlichkeit auf",
            "emotionale intelligenz": "Verstehe und teile Gefühle",
            "teamarbeit": "Lerne die Kraft der Zusammenarbeit",
            "freundlichkeit": "Entdecke die Bedeutung von Mitgefühl und Güte",
            "umweltschutz": "Lerne, unseren Planeten zu schützen und zu respektieren",
            "respekt": "Verstehe die Wichtigkeit, andere zu achten und zu behandeln",
            "mut": "Finde Kraft und Selbstvertrauen in herausfordernden Situationen",
        }.get(story_request.educational_topic.lower(), "Ein magisches Lern-Abenteuer")

        prompt = f"""Schreibe eine Gute-Nacht-Geschichte für {story_request.age_group} über {character_descriptions}. 
        Die Geschichte spielt in dieser Umgebung: {story_request.location}. 
        Die Geschichte soll auf eine subtile Art und Weise über {educational_context} lehren. 
        Die Geschichte soll fesselnd, lehrreich und mit einer positiven moralischen Lektion versehen sein.
        Die Geschichte soll mindestens 3 DIN A4 Seiten lang sein.
        Die Geschichte soll in einfachen Worten und kurzen Sätzen erzählt werden.
        {age_appropriate_choice_of_words()}
        """

        print(f"Prompt: {prompt}")

        return prompt


CHARACTER_JSON_FILE_PATH = "characters.json"
STORIES_JSON_FILE_PATH = "stories.json"


def get_next_character_id(characters: List[Character]) -> int:
    """Generate the next available ID for a character."""
    if not characters:
        return 1
    return max(character.id for character in characters) + 1


def save_characters_to_json(
    characters: List[Character], file_path: str = CHARACTER_JSON_FILE_PATH
):
    """Save the list of characters to a JSON file."""
    with open(file_path, "w") as file:
        json.dump([character.model_dump() for character in characters], file, indent=4)


def load_characters_from_json(
    file_path: str = CHARACTER_JSON_FILE_PATH,
) -> List[Character]:
    """Load characters from a JSON file and return a list of Character objects."""
    try:
        with open(file_path, "r") as file:
            characters_data = json.load(file)
            return [Character(**data) for data in characters_data]
    except FileNotFoundError:
        return []  # Return an empty list if the file does not exist
    except json.JSONDecodeError:
        return []  # Return an empty list if the file is empty or invalid


def find_character_by_names(name: str) -> Character:
    """
    Find a character by name
    """
    for character in load_characters_from_json():
        if character.name.lower() == name.lower():
            return character
    return None


def find_character_by_id(
    characters: List[Story], character_id: int
) -> Optional[Character]:
    for character in characters:
        if character.id == character_id:
            return character
    return None


def find_characters_by_id(
    characters: List[Story], character_ids: list[int]
) -> list[Character]:
    return [character for character in characters if character.id in character_ids]


def get_next_story_id(stories: List[Story]) -> int:
    """Generate the next available ID for a story."""
    if not stories:
        return 1
    return max(story.id for story in stories) + 1


def save_stories_to_json(stories: List[Story], file_path: str = STORIES_JSON_FILE_PATH):
    """Save the list of stories to a JSON file."""
    with open(file_path, "w") as file:
        json.dump([story.model_dump() for story in stories], file, indent=4)


def load_stories_from_json(
    file_path: str = STORIES_JSON_FILE_PATH,
) -> List[Story]:
    """Load stories from a JSON file and return a list of Story objects."""
    try:
        with open(file_path, "r") as file:
            stories_data = json.load(file)
            return [Story(**data) for data in stories_data]
    except FileNotFoundError:
        return []  # Return an empty list if the file does not exist
    except json.JSONDecodeError:
        return []  # Return an empty list if the file is empty or invalid


def find_story_by_id(stories: List[Story], story_id: int) -> Optional[Story]:
    for story in stories:
        if story.id == story_id:
            return story
    return None


story_generator = StoryGenerator()


# {"name":"Vinca","age":6,"gender":"weiblich","interests":["Turnen"],"personality_traits":["fröhlich","spontan"]}
@app.post(
    "/api/characters/create",
    name="Charakter erstellen",
    description="Erstelle einen neuen Charakter für Geschichten",
)
def create_character(character: Character):
    """Erstelle einen neuen Charakter"""
    try:
        all_characters = load_characters_from_json()
        character.id = get_next_character_id(all_characters)
        print(f"New Character ID: {character.id}")
        all_characters.append(character)
        save_characters_to_json(all_characters)
        return character
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Fehler beim Erstellen des Charakters: {str(e)}"
        )


@app.get(
    "/api/characters",
    name="Charaktere auflisten",
    description="Zeige alle verfügbaren Charaktere",
)
def list_characters():
    """Liste alle verfügbaren Charaktere auf"""
    return load_characters_from_json()


@app.delete(
    "/api/characters/delete",
    name="Charakter löschen",
    description="Lösche einen Charakter mit der ID.",
)
def delete_characters(character_id: int):
    """Lösche den Charaktere mit der ID"""
    all_characters = load_characters_from_json()
    delete_character = find_character_by_id(all_characters, character_id)
    if delete_character in all_characters:
        all_characters.remove(delete_character)
        save_characters_to_json(all_characters)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f"Character with character_id '{character_id}' successfully deleted.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{status.HTTP_404_NOT_FOUND}: Character with character_id '{character_id} not found.",
        )


# {"characters":["Vinca"],"location":"Verzauberter Garten","educational_topic":"Achtsamkeit","age_group":"Kinder"}
@app.post(
    "/api/stories/generate",
    name="Geschichte generieren",
    description="Generiere eine personalisierte Gute-Nacht-Geschichte",
)
def generate_story(story_request: StoryRequest):
    """Generiere eine personalisierte Gute-Nacht-Geschichte"""
    try:
        print(f"story_request: {story_request}")

        new_story_request = StoryRequest(
            characters=story_request.characters,
            location=story_request.location,
            educational_topic=story_request.educational_topic,
            age_group=story_request.age_group,
        )
        generated_story = story_generator.generate_bedtime_story_google(
            new_story_request
        )
        print(f"Generated story: {generated_story}")

        all_stories = load_stories_from_json()
        next_story_id = get_next_story_id(all_stories)
        print(f"New Story ID: {next_story_id}")
        new_story = Story(id=next_story_id, text=generated_story)
        all_stories.append(new_story)
        save_stories_to_json(all_stories)

        return new_story

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Fehler bei der Geschichtsgenerierung: {str(e)}"
        )


@app.get(
    "/api/stories/{story_id}",
    name="Geschichte abrufen",
    description="Rufe eine zuvor generierte Geschichte ab",
)
def retrieve_story(story_id: str):
    """Rufe eine zuvor generierte Geschichte ab"""
    all_stories = load_stories_from_json()
    story_ids = [story.id for story in all_stories]
    if story_id not in story_ids:
        raise HTTPException(status_code=404, detail="Geschichte nicht gefunden")
    return {"story": find_story_by_id(all_stories, story_id)}


# Standorte in deutscher Sprache
LOCATIONS = [
    "Alte Burg",
    "Bauernhof",
    "Berglandschaft",
    "Flussufer",
    "Garten hinter dem Haus",
    "Mystischer Wald",
    "Märchenland",
    "Raumstation",
    "Stadtpark",
    "Strandküste",
    "Verzauberter Garten",
]

# Pädagogische Themen in deutscher Sprache
EDUCATIONAL_TOPICS = [
    "Achtsamkeit",
    "Emotionale Intelligenz",
    "Finanzielle Bildung",
    "Freundlichkeit",
    "Gesunde Ernährung",
    "Mut",
    "Persönlichkeitsentwicklung",
    "Respekt",
    "Teamarbeit",
    "Umweltschutz",
]


@app.get(
    "/api/metadata",
    name="Metadaten abrufen",
    description="Rufe vordefinierte Standorte und Themen ab",
)
def get_story_metadata():
    """Liefere alle Charakter, vordefinierte Standorte und Themen"""
    return {
        "characters": load_characters_from_json(),
        "locations": LOCATIONS,
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
