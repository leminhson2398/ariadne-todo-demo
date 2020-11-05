from ariadne import QueryType, SubscriptionType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
import asyncio
from starlette.routing import Route, WebSocketRoute
from graphql import GraphQLResolveInfo

from fastapi import FastAPI


type_defs = """
    type Todo {
        id: Int!
        name: String!
        completed: Boolean!
    }

    type Query {
        todos: [Todo]!
        todoById(id: Int!): Todo
    }

    input AddTodoInput {
        name: String!
        completed: Boolean
    }

    input DelTodoInput {
        id: Int!
    }

    input UpdateTodoInput {
        id: Int!
        name: String!
        completed: Boolean
    }

    type Mutation {
        createTodo(input: AddTodoInput!): Todo
        deleteTodo(input: DelTodoInput!): Todo
        updateTodo(input: UpdateTodoInput!): Todo
    }

    type Subscription {
        todoAdded: Todo!
        todoUpdated: Todo!
        todoDeleted: Todo!
        counter: Int!
    }
"""

todos = [
    {"id": 1, "name": "First", "completed": False},
    {"id": 2, "name": "Second todo", "completed": True},
]

subscription = SubscriptionType()
query = QueryType()
mutation = MutationType()

# Subscription


@subscription.source("createTodo")
async def counter_generator(parent, info: GraphQLResolveInfo, **kwargs):
    print(kwargs)
    yield 1


@subscription.field("counter")
async def counter_resolver(todo, info: GraphQLResolveInfo):
    print(todo)
    return todo

# Query


@query.field("todos")
async def resolve_todos(parent, info: GraphQLResolveInfo):
    return todos


@query.field("todoById")
async def resolve_todoById(parent, info: GraphQLResolveInfo, **kwargs):
    try:
        intID = int(kwargs["id"])
        for todo in todos:
            if todo["id"] == intID:
                return todo
        # if did not find match todo
        return None
    except Exception:
        return None

# Mutation


@mutation.field("createTodo")
async def resolve_createTodo(parent, info: GraphQLResolveInfo, **kwargs):
    name = kwargs["input"]["name"]
    completed = kwargs["input"]["completed"]

    maxID = 0
    for todo in todos:
        if todo["id"] > maxID:
            maxID = todo["id"]

    newTodo = {
        "id": maxID + 1,
        "name": name,
        "completed": completed
    }
    todos.append(newTodo)
    return newTodo


@mutation.field("deleteTodo")
async def resolve_deleteTodo(parent, info: GraphQLResolveInfo, **kwargs):
    id = kwargs["input"]["id"]
    if isinstance(id, int):
        for todo in todos:
            if todo["id"] == id:
                todos.remove(todo)
                return todo
        return None
    else:
        return None


@mutation.field("updateTodo")
async def resolve_updateTodo(parent, info: GraphQLResolveInfo, **kwargs):
    id = kwargs["input"]["id"]
    if isinstance(id, int):
        for i in range(len(todos)):
            if todos[i]["id"] == id:
                todos[i] = {
                    "id": id,
                    "name": kwargs["input"]["name"],
                    "completed": kwargs["input"]["completed"]
                }
                return todos[i]
        return None
    else:
        return None


schema = make_executable_schema(type_defs, query, mutation, subscription)


routes = [
    Route("/graphql", GraphQL(schema=schema, debug=True)),
    WebSocketRoute("/graphql", GraphQL(schema=schema, debug=True)),
]

app = FastAPI(debug=True, routes=routes)
