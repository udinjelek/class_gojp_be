from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()

class params_create_assistant(BaseModel):
    instructions: str
    name: str
    type: str
    model: str
    key: str

@router.post("/create_assistant")
async def func_create_assistant(request: params_create_assistant):
    try:  
        client = OpenAI(api_key=request.key)

        my_assistant = client.beta.assistants.create(
            instructions=request.instructions,
            name=request.name,
            tools=[{"type": request.type}],
            model=request.model,
        )
        print(my_assistant)

        return {"result": my_assistant}
    except Exception as e:
        return {"error": str(e)}

@router.get("/get_assistants")
async def func_get_assistants(key: str):
    try:
        # Check if the assistant with the given key exists
        client = OpenAI(api_key=key)

        my_assistants = client.beta.assistants.list(
            order="desc",
            limit="20",
        )
        print(my_assistants.data)
        return {"result": my_assistants.data}
    except Exception as e:
        return {"error": str(e)}
    
@router.delete("/delete_assistant")
async def func_delete_assistant(id: str, key: str):
    try:
        # Check if the assistant with the given key exists
        client = OpenAI(api_key=key)
        response = client.beta.assistants.delete(id)
        print(response)
        return {"result": response}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/get_files")
async def func_get_files(key: str):
    try:
        # Check if the assistant with the given key exists
        client = OpenAI(api_key=key)

        my_files = client.files.list()
        print(my_files.data)
        return {"result": my_files.data}
    except Exception as e:
        return {"error": str(e)}

@router.get("/get_assistant_files")
async def func_get_assistant_files(key: str, id: str):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)

        assistant_files = client.beta.assistants.files.list(
            assistant_id= id
        )
        print(assistant_files)
        return {"result": assistant_files.data}
    except Exception as e:
        return {"error": str(e)}