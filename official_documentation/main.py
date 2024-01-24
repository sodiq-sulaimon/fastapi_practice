
from fastapi import FastAPI, Query, Path, Body, Form, File, UploadFile, status, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import Annotated

# Simple API
app = FastAPI()

@app.get("/")
def root():
    return "Hey there! Welcome to my API"


# Path parameters with types
@app.get("/items/{item_id}")
async def read_items(item_id: int):
    return {"Item Id: ": item_id}

# Path parameters containing paths
@app.get("/files/{file_path:path}")
def read_file(file_path: str):
    return {"File path": file_path}

# Request Body
#from pydantic import BaseModel

class Item(BaseModel):
    name: str
    description: str | None = None 
    price: float 
    tax: float | None = None

@app.post("/items")
async def create_item(item: Item):
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"Price with tax": price_with_tax})
        return {item.name: item_dict["Price with tax"]}
    return {item.name: item.price}

# Query parameters
dummy_items = [{1 : "Mango"}, {2 : "Banana"}, {3 : "Orange"}, {4 : "Apple"}]

@app.get("/items_query")
def read_item(skip: int, limit: int = 10, sort: bool | None = None): # not giving default values to query parameters makes it required, sort is added to show optional query parameter.
    return dummy_items[skip: skip + limit]

# Request body + path parameters
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}

# Query parameters and string validation
# from fastapi import Query
# from typing import Annotated

dummy_items = [{1 : "Mango"}, {2 : "Banana"}, {3 : "Orange"}, {4 : "Apple"}]

@app.get("/items_valquery")
async def read_item(skip: int = 0, limit: Annotated[int | None, Query(le=50)] = None): # Used to set the max number for option query parameter 'limit'
    if limit:
        return dummy_items[skip:skip + limit]
    return dummy_items[skip:2]

# Path parameters and numeric validations
# from FastAPI import Path

@app.get("/items_path/{item_id}")
async def read_item(item_id: Annotated[int, Path(title = "Id of the item", ge=1)],
                    q: Annotated[str | None, Query(alias = 'item-query')]):
    results = {"Item_id": item_id}
    if q:
        results.update({"q": q})
    return results

# Multiple body parameters
# from FastAPI import Body

class User(BaseModel):
    username: str
    name: str

# Item class for Body parameters already declared above

@app.put("/items_body/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(ge=1)],
    item: Item,
    user: User,
    rating: Annotated[int, Body(gt=0, le=5)]):
    results = {"Item id": item_id, "Item details": item, "User":user, "Rating": rating}
    return results
    

# Body - Nested models

#from pydantic import HttpUrl

class Image(BaseModel): # submodel
    url: str
    name: HttpUrl | str

class Item(BaseModel):
    name: str
    description: str | None = None 
    price: float 
    tax: float | None = None
    image: Image | None = None # submodel used as type

@app.put("/items_nested_body/{item_id}")
async def update_item(
    item_id: Annotated[int, Path(ge=1)],
    item: Item):
    results = {"Item id": item_id, "Item details": item}
    return results

# Response model - return type

@app.post("/create_items/")
async def create_item(item: Item) -> Item:
    return item

@app.get("/create_items/")
def get_items() -> list[Item]:
    return [Item(name="soya milk", price=1.49),
            Item(name="Banana", price=2.5, tax=0.25)]

# Form data
# from fastapi import Form
@app.get("/login")
async def login_home():
    return "Enter your login info"

@app.post("/login")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return f"{username}: Login successful!"


# Request files
# from fastapi import File, UploadFile

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"Filesize": len(file)}

@app.post("/uploadfile/")
async def upload_file(file: UploadFile):
    # return {"Filename": file.filename}
    content = await file.read()
    file.close()
    return {"Filename": file.filename, "Content": content}

# Response status code
# from fastapi import status

items = {"cold": "winter", "hot": "summer"}

@app.get("/itemsstat", status_code=status.HTTP_200_OK)
def read_item():
    return items

# Handling Exceptions
# from fastapi import HTTPException

@app.get("/itemsexc/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"Item": items[item_id]}

# Body - Updates (Put & Patch)
from fastapi.encoders import jsonable_encoder

winter_items = {
    "jacket": {"name": "Jacket", "price": 50.2},
    "boot": {"name": "Boot", "description": "Winter boot", "price": 62, "tax": 20.2},
    "beanie": {"name": "Beanie", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}

@app.get("/itemsbody", status_code=status.HTTP_200_OK)
def read_item():
    return winter_items

# Update with PUT Method

@app.put("/itemsbody/{item_id}", response_model=Item)
async def update_item(item_id: str, item: Item):
    update_item_encoded = jsonable_encoder(item)
    winter_items[item_id] = update_item_encoded
    return update_item_encoded
# Warning: if the new items does not have some values available in the original item, the input model (PUT) will 
# use the default value set in the item basemodel.

# Partial Update with PATCH Method
@app.patch("/itemsbody/{item_id}", response_model=Item)
async def update_item(item_id: str, item: Item):
    stored_item_data = winter_items[item_id]
    stored_item_model = Item(**stored_item_data)
    update_data = item.model_dump(exclude_unset=True)
    updated_item = stored_item_model.copy(update=update_data)
    winter_items[item_id] = jsonable_encoder(updated_item)
    return updated_item